#!/usr/bin/env python3
#& by @synko & hashref sec

import os, sys, subprocess, argparse, shutil, platform, datetime, signal, time

script_dir = os.path.dirname(os.path.abspath(__file__))
FFMPEG = "ffmpeg"

C = {
    "r": "\033[91m", "g": "\033[92m", "y": "\033[93m",
    "b": "\033[94m", "w": "\033[0m", "bd": "\033[1m"}

def log(t, m): print(f"{C[t]}{m}{C['w']}")

def banner():
    print(f"""{C['bd']}{C['b']}
██████╗ ███████╗ ██████╗
██╔══██╗██╔════╝██╔════╝
██████╔╝█████╗  ██║     
██╔══██╗██╔══╝  ██║     
██║  ██║███████╗╚██████╗
╚═╝  ╚═╝╚══════╝ ╚═════╝
 TERMINAL SCREEN RECORDER
{C['w']}""")

def help_menu():
    print("""
Usage:
 python register.py [options]

Options:
 -f FPS            (défaut 60)
 -q QUALITÉ        4k | 1440p | 1080p | 720p | 512p
 -r RÉPERTOIRE     dossier sortie
 -t SECONDES       durée max
 -s ÉCRANS         p | all | 0,1,2
 -a on|off         audio (défaut on)
 -n NOM            nom fichier
 --list-screens    afficher écrans
 --no-ui           silencieux

Exemples:
 python register.py
 python register.py -f 120 -q 4k -t 30
 python register.py -a off -r /videos
""")

def die(m):
    log("r", "[!] " + m)
    sys.exit(1)

def ensure_ffmpeg():
    if shutil.which(FFMPEG): return
    log("y", "[*] FFmpeg manquant")
    if platform.system().lower() == "linux":
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
    else: die("Installe FFmpeg et ajoute-le au PATH")

def has_encoder(enc):
    try: return enc in subprocess.check_output([FFMPEG, "-encoders"], text=True)
    except: return False

def res(q):
    return {
        "4k": "3840x2160",
        "2160p": "3840x2160",
        "1440p": "2560x1440",
        "1080p": "1920x1080",
        "720p": "1280x720",
        "512p": "512x512"}.get(q.lower(), "1920x1080")

def record(a):
    ensure_ffmpeg()
    os.makedirs(a.r, exist_ok=True)
    if not a.n: a.n = datetime.datetime.now().strftime("vid_%d-%m-%Y_%H-%M-%S-%f")
    out = os.path.join(a.r, a.n + ".mp4")
    encoder = "libx264"
    enc_extra = ["-preset", "ultrafast", "-tune", "zerolatency"]
    if has_encoder("h264_nvenc"):
        encoder = "h264_nvenc"
        enc_extra = ["-preset", "p1"]
        log("g", "[+] NVENC actif")
    elif has_encoder("h264_vaapi"):
        encoder = "h264_vaapi"
        enc_extra = ["-vaapi_device", "/dev/dri/renderD128"]
        log("g", "[+] VAAPI actif")
    else:
        log("y", "[*] x264 CPU")
    cmd = [FFMPEG, "-y", "-thread_queue_size", "1024"]
    sysname = platform.system().lower()
    if sysname == "windows":
        cmd += ["-f", "gdigrab", "-framerate", str(a.f), "-i", "desktop"]
        if a.a == "on":
            cmd += ["-f", "dshow", "-i", "audio=virtual-audio-capturer"]
    else:
        cmd += [
            "-f", "x11grab",
            "-video_size", res(a.q),
            "-framerate", str(a.f),
            "-i", os.getenv("DISPLAY", ":0.0")]
        if a.a == "on":
            cmd += ["-f", "pulse", "-i", "default"]
    if a.t:
        cmd += ["-t", str(a.t)]
    cmd += [
        "-c:v", encoder,
        *enc_extra,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out]
    log("g", "[+] RECORD START")
    print(" ".join(cmd))
    start = time.time()
    def stop(sig, f):
        log("y", f"[*] STOP ({int(time.time()-start)}s)")
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)
    subprocess.run(cmd)

def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-f", type=int, default=60)
    p.add_argument("-q", default="1080p")
    p.add_argument("-r", default=os.getcwd())
    p.add_argument("-t", type=int)
    p.add_argument("-s", default="p")
    p.add_argument("-a", default="on")
    p.add_argument("-n")
    p.add_argument("--list-screens", action="store_true")
    p.add_argument("--no-ui", action="store_true")
    a = p.parse_args()
    if "-h" in sys.argv or "--help" in sys.argv:
        help_menu(); return
    if not a.no_ui:
        banner()
    record(a)

if __name__ == "__main__":
    main()
