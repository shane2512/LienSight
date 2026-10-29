import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import win
ROOT = r"C:\dfol\legalhk\pitch"
RAW = os.path.join(ROOT, "raw"); OUT = os.path.join(RAW, "terminal.mp4")
for f in ("go.flag", "done.flag", "ready.flag"):
    try: os.remove(os.path.join(RAW, f))
    except FileNotFoundError: pass
wt = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe")
subprocess.Popen([wt, "-w", "new", "-M", "powershell.exe", "-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", os.path.join(ROOT, "tools", "driver_terminal.ps1")])
t0 = time.time()
while not os.path.exists(os.path.join(RAW, "ready.flag")):
    if time.time() - t0 > 40: sys.exit("terminal did not start")
    time.sleep(0.2)
time.sleep(1.5)
print("foreground:", win.foreground_title(), flush=True)
for _ in range(5): win.key("ctrl", "plus"); time.sleep(0.15)   # zoom the terminal text like a person would
time.sleep(1.0)
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-i", "desktop",
                       "-c:v", "libx264", "-preset", "ultrafast", "-crf", "15", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
time.sleep(1.0)
open(os.path.join(RAW, "go.flag"), "w").close()
t1 = time.time()
while not os.path.exists(os.path.join(RAW, "done.flag")):
    if time.time() - t1 > 240: print("timeout waiting for done"); break
    time.sleep(0.3)
time.sleep(1.2)
ff.stdin.write(b"q"); ff.stdin.flush(); ff.wait(timeout=30)
print("recorded %.1fs" % (time.time() - t1), flush=True)
