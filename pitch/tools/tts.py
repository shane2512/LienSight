"""Fish Audio TTS for the narration segments. Reads FISH_AUDIO_KEY from ../.env (never printed)."""
import json, os, sys, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE = "76e8d2175bc44e29be9885fb67a2b43a"
env = {}
for line in open(os.path.join(ROOT, "..", ".env"), encoding="utf-8", errors="replace"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
KEY = env["FISH_AUDIO_KEY"]

def synth(text, out, speed=1.0, model="s2.1-pro-free"):
    body = json.dumps({"text": text, "reference_id": VOICE, "format": "mp3", "sample_rate": 44100, "mp3_bitrate": 192, "normalize": True,
                       "language": "en", "latency": "normal", "temperature": 0.6, "top_p": 0.7,
                       "prosody": {"speed": speed, "volume": 0, "normalize_loudness": True}}).encode()
    req = urllib.request.Request("https://api.fish.audio/v1/tts", data=body, method="POST",
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json", "model": model, "User-Agent": "liensight-pitch"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        open(out, "wb").write(data)
        return 200, len(data)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]

if __name__ == "__main__":
    segs = json.load(open(os.path.join(ROOT, "narration.json")))
    only = sys.argv[1:]
    speed = float(os.environ.get("SPEED", "1.0"))
    for s in segs:
        if only and s["id"] not in only: continue
        out = os.path.join(ROOT, "assets", "vo", s["id"] + ".mp3")
        code, info = synth(s["text"], out, speed)
        print(s["id"], code, info, flush=True)
