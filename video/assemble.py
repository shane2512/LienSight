import subprocess
ORDER = ["title", "landing", "check", "tests", "cre", "eth_new", "proof", "cast", "eth_events", "eth_old", "security", "closing"]
FADE = 0.35
def dur(n):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"build/{n}.mp4"]).decode().strip())
inputs, filt, starts, t = [], [], [], 0.0
for i, n in enumerate(ORDER):
    d = dur(n); starts.append(round(t, 2)); t += d
    inputs += ["-i", f"build/{n}.mp4"]
    filt.append(f"[{i}:v]fade=t=in:st=0:d={FADE},fade=t=out:st={d - FADE:.3f}:d={FADE}[v{i}]")
filt.append("".join(f"[v{i}]" for i in range(len(ORDER))) + f"concat=n={len(ORDER)}:v=1:a=0,format=yuv420p[out]")
cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-r", "30",
       "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", "liensight-demo-silent.mp4"]
subprocess.run(cmd, check=True)
print("total %.1fs" % t)
with open("scene-timeline.txt", "w") as f:
    for n, s in zip(ORDER, starts): f.write(f"{s:7.1f}s  {n}\n")
print(open("scene-timeline.txt").read())
