"""Synthesize the background score for the pitch film (deterministic: fixed seed, no samples).

Sections follow the root timeline; risers/whooshes land on the wipes; the bed ducks under the voice.
Run from pitch/:  python tools/score.py   ->  assets/score/score.mp3
"""
import json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR, DUR = 48000, 179.9
N = int(SR * DUR)
rng = np.random.default_rng(7)
L, R = np.zeros(N), np.zeros(N)          # dry bus
RL, RR = np.zeros(N), np.zeros(N)        # reverb send
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
BEAT = 0.6                                # 100 bpm


def add(sig, t, gain=1.0, pan=0.0, verb=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i]
    l, r = gain * np.cos((pan + 1) * np.pi / 4), gain * np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l; R[i:i + len(sig)] += sig * r
    if verb:
        RL[i:i + len(sig)] += sig * l * verb; RR[i:i + len(sig)] += sig * r * verb


def lp(x, f, order=2): return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def env(n, a, r, hold=None):
    t = np.arange(n) / SR; d = n / SR
    e = np.minimum(1, t / max(a, 1e-4))
    return e * np.clip((d - t) / max(r, 1e-4), 0, 1)


def tone(f, d, harm=10, bright=1.0, det=0.0):
    t = np.arange(int(d * SR)) / SR
    out = np.zeros_like(t)
    for k in range(1, harm + 1):
        if f * k > 9000: break
        out += np.sin(2 * np.pi * f * k * (1 + det) * t + k) * (1 / k) ** (1.6 / bright)
    return out


# ---------- instruments ----------
def pad(notes, t0, d, gain=0.05, cutoff=1800, a=1.2, r=1.6):
    n = int(d * SR)
    for m in notes:
        for det, pan in ((-0.004, -0.6), (0.0, 0.0), (0.0045, 0.6)):
            s = lp(tone(hz(m), d, 12, 1.0, det), cutoff) * env(n, a, r)
            add(s, t0, gain / len(notes) ** 0.5, pan, verb=0.5)


def bass(m, t0, d, gain=0.22):
    n = int(d * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t)) * env(n, 0.01, 0.12) * np.exp(-t * 2.2)
    add(lp(s, 900), t0, gain)


def pluck(m, t0, gain=0.07, pan=0.0, dec=5.0, verb=0.6):
    d = 1.2; n = int(d * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * hz(m) * t) + 0.35 * np.sin(4 * np.pi * hz(m) * t) + 0.12 * np.sin(6 * np.pi * hz(m) * t)) * np.exp(-t * dec) * env(n, 0.003, 0.05)
    add(s, t0, gain, pan, verb)


def kick(t0, gain=0.5):
    d = 0.45; n = int(d * SR); t = np.arange(n) / SR
    f = 46 + 90 * np.exp(-t * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    add(s, t0, gain)


def hat(t0, gain=0.035, pan=0.25, d=0.035):
    n = int(d * SR)
    add(hp(rng.standard_normal(n), 7500) * np.exp(-np.arange(n) / SR * 90), t0, gain, pan)


def clap(t0, gain=0.09):
    n = int(0.25 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 900, 2600) * (np.exp(-t * 28) + 0.5 * np.exp(-np.maximum(t - 0.012, 0) * 30) * (t > 0.012))
    add(s, t0, gain, 0.0, verb=0.5)


def impact(t0, gain=0.6):
    d = 2.2; n = int(d * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.2)
    crack = lp(rng.standard_normal(n), 3500) * np.exp(-t * 14) * 0.5
    add(boom + crack, t0, gain, 0.0, verb=0.35)


def riser(t_end, d=1.4, gain=0.12):
    n = int(d * SR); t = np.arange(n) / SR; x = t / d
    noise = rng.standard_normal(n)
    s = np.zeros(n); seg = n // 14
    for k in range(14):  # stepped band-pass sweep upward
        a, b = k * seg, (k + 1) * seg if k < 13 else n
        fc = 300 * (16 ** (k / 13))
        s[a:b] = bp(noise[a:b], fc * 0.7, min(fc * 1.4, 20000))
    add(s * x ** 2.2, t_end - d, gain, 0.0, verb=0.4)


def whoosh(t_mid, gain=0.16):
    d = 0.9; n = int(d * SR); t = np.arange(n) / SR
    e = np.exp(-((t - d / 2) / 0.16) ** 2)
    s = bp(rng.standard_normal(n), 500, 4500) * e
    sweep = np.linspace(-0.8, 0.8, n)  # pans with the panels (left to right)
    i = int((t_mid - d / 2) * SR)
    L[i:i + n] += s * gain * np.cos((sweep + 1) * np.pi / 4); R[i:i + n] += s * gain * np.sin((sweep + 1) * np.pi / 4)


def ping(t0, m=81, gain=0.06):
    pluck(m, t0, gain, 0.3, dec=3.2, verb=0.9); pluck(m + 7, t0 + 0.09, gain * 0.6, -0.3, dec=3.2, verb=0.9)


# ---------- harmony ----------
CH = {
    "Dm": ([50, 53, 57, 64], 38), "Bb": ([46, 50, 53, 60], 34), "Gm": ([43, 46, 50, 57], 43), "A": ([45, 49, 52, 55], 45),
    "F": ([53, 57, 60, 67], 41), "C": ([48, 52, 55, 62], 36), "Am": ([45, 48, 52, 59], 45),
}


def progression(t0, t1, chords, bars_per, fn):
    bar = 4 * BEAT; k = 0; t = t0
    while t < t1 - 0.05:
        d = min(bars_per * bar, t1 - t)
        fn(chords[k % len(chords)], t, d); t += d; k += 1


def arp(notes, t0, d, step, gain, up=12, dec=5.0):
    seq = notes + [notes[1] + up, notes[2] + up]
    t, k = t0, 0
    while t < t0 + d - 0.01:
        pluck(seq[k % len(seq)] + 12, t, gain, (-0.4, 0.4)[k % 2], dec); t += step; k += 1


# A. hook 0 - 11.0: ticking build, stamp, logo
pad(CH["Dm"][0], 0.0, 11.4, 0.05, 1400, a=2.5, r=1.0)
for k, t in enumerate(np.arange(1.2, 10.9, BEAT / 2)):
    hat(t, 0.02 + 0.012 * (k % 2 == 0), 0.3)
impact(3.05, 0.55); bass(38, 3.05, 1.6, 0.25)
riser(9.25, 1.1, 0.08); impact(9.25, 0.4); pad([53, 57, 62, 69], 9.25, 2.0, 0.05, 2600, a=0.05, r=1.4)
riser(11.0, 1.2, 0.1); whoosh(11.0)

# B. problem 11.0 - 30.7: dark pulse, the liens land
progression(11.0, 30.7, ["Dm", "Bb", "Gm", "A"], 2, lambda c, t, d: pad(CH[c][0], t, d, 0.045, 1100, a=0.8, r=1.0))
progression(11.0, 30.7, ["Dm", "Bb", "Gm", "A"], 2, lambda c, t, d: [bass(CH[c][1], t + i * BEAT / 2, 0.3, 0.16) for i in range(int(d / (BEAT / 2)))])
for t in np.arange(16.9, 30.4, BEAT): kick(t, 0.32)
for t in (19.15, 20.35, 21.4): impact(t, 0.32)
riser(30.7, 1.3, 0.1); whoosh(30.7)

# C. why Chainlink CRE 30.7 - 51.6: lighter, arpeggio; accents on each idea and each workflow step
for t in (37.1, 38.85, 40.0, 41.35, 45.9, 46.9, 48.9, 49.8): ping(t, 76, 0.05)
progression(30.7, 51.6, ["F", "C", "Dm", "Bb"], 2, lambda c, t, d: (pad(CH[c][0], t, d, 0.045, 2200), arp(CH[c][0], t, d, BEAT / 2, 0.035)))
progression(30.7, 51.6, ["F", "C", "Dm", "Bb"], 2, lambda c, t, d: bass(CH[c][1], t, d * 0.9, 0.16))
riser(51.6, 1.2, 0.1); whoosh(51.6)

# D. how 51.6 - 73.3: driving groove, restriction hit
progression(51.6, 73.3, ["Dm", "Bb", "F", "C"], 1, lambda c, t, d: (pad(CH[c][0], t, d, 0.04, 2000, a=0.3, r=0.6), arp(CH[c][0], t, d, BEAT / 4, 0.028, dec=7)))
progression(51.6, 73.3, ["Dm", "Bb", "F", "C"], 1, lambda c, t, d: [bass(CH[c][1], t + i * BEAT / 2, 0.28, 0.15) for i in range(int(d / (BEAT / 2)))])
for t in np.arange(51.6, 73.0, BEAT): kick(t, 0.36)
for t in np.arange(51.6 + BEAT / 2, 73.0, BEAT): hat(t, 0.03)
impact(69.6, 0.45)
riser(73.4, 1.2, 0.09)

# E. live demo 73.3 - 136.3: minimal bed, a ping on every callout
progression(73.3, 136.3, ["Dm", "Bb", "F", "C"], 2, lambda c, t, d: (pad(CH[c][0], t, d, 0.04, 1500), arp(CH[c][0], t, d, BEAT, 0.02, dec=4)))
progression(73.3, 136.3, ["Dm", "Bb", "F", "C"], 2, lambda c, t, d: bass(CH[c][1], t, d * 0.9, 0.12))
for t in (81.0, 87.7, 102.4, 107.15, 113.7, 114.8, 124.4, 128.9, 131.9): ping(t)
for t in (91.2, 109.6, 116.8, 126.1): whoosh(t + 0.3, 0.08)
riser(136.3, 1.4, 0.11); whoosh(136.3)

# F. why this fits 136.3 - 158.7: the lift
progression(136.3, 158.7, ["F", "C", "Dm", "Bb"], 1, lambda c, t, d: (pad(CH[c][0], t, d, 0.045, 2800, a=0.2, r=0.6), arp(CH[c][0], t, d, BEAT / 4, 0.03, dec=6)))
progression(136.3, 158.7, ["F", "C", "Dm", "Bb"], 1, lambda c, t, d: [bass(CH[c][1], t + i * BEAT / 2, 0.28, 0.16) for i in range(int(d / (BEAT / 2)))])
for t in np.arange(136.3, 158.4, BEAT): kick(t, 0.36)
for t in np.arange(136.3 + BEAT, 158.4, 2 * BEAT): clap(t, 0.07)
for t in np.arange(136.3 + BEAT / 2, 158.4, BEAT): hat(t, 0.03)
riser(158.7, 1.2, 0.09); whoosh(158.7)

# G. honest 158.7 - 174.9: reflective
progression(158.7, 174.9, ["Bb", "F", "C", "Dm"], 2, lambda c, t, d: (pad(CH[c][0], t, d, 0.045, 1600), arp(CH[c][0], t, d, BEAT, 0.022, dec=3.5)))
progression(158.7, 174.9, ["Bb", "F", "C", "Dm"], 2, lambda c, t, d: bass(CH[c][1], t, d * 0.9, 0.12))
riser(175.0, 1.6, 0.1)

# H. close 174.9 - 179.9: resolve on F
impact(175.05, 0.5); bass(41, 175.05, 3.5, 0.22)
pad([53, 57, 60, 65, 72], 175.05, 4.85, 0.07, 3000, a=0.08, r=2.6)
for k, m in enumerate([65, 69, 72, 77]): pluck(m + 12, 175.1 + k * 0.15, 0.04, (-0.5, -0.15, 0.15, 0.5)[k], dec=2.5, verb=1.0)

# ---------- reverb, duck, master ----------
ir_n = int(2.6 * SR); it = np.arange(ir_n) / SR
irl = rng.standard_normal(ir_n) * np.exp(-it * 2.6); irr = rng.standard_normal(ir_n) * np.exp(-it * 2.6)
irl, irr = lp(irl, 5000), lp(irr, 5000)
L += fftconvolve(RL, irl)[:N] * 0.12; R += fftconvolve(RR, irr)[:N] * 0.12

# duck under the voice (where each clip actually speaks)
words = json.load(open("assets/vo/words.json", encoding="utf-8"))
PLACE = [("s1_hook", 0, 99, 1.2), ("s2_problem", 0, 99, 11.1), ("s3_cre", 0, 99, 30.85), ("s4_how", 0, 99, 51.8), ("s5a_check", 0, 99, 74.1),
         ("s5b1_cli", 0, 99, 91.5), ("s5b2_flag", 0, 99, 101.5), ("s5c_chain", 0, 5.9, 110.6), ("s5c_chain", 5.9, 99, 118.1),
         ("s5d_events", 0, 99, 126.7), ("s6_fit", 0, 99, 137.3), ("s7_honest", 0, 99, 159.2), ("s8_close", 0, 99, 175.5)]
g = np.ones(N)
for cid, c0, c1, at in PLACE:
    ws = [w for w in words[cid] if c0 <= w["s"] < c1]
    a, b = at + ws[0]["s"] - c0 - 0.1, at + ws[-1]["e"] - c0 + 0.15
    g[int(a * SR):int(b * SR)] = 0.38
k = int(0.25 * SR); c = np.cumsum(np.concatenate([np.full(k // 2, g[0]), g, np.full(k - k // 2, g[-1])]))
g = (c[k:] - c[:-k])[:N] / k  # moving average: smooth attack/release
L, R = hp(L * g, 30), hp(R * g, 30)
mix = np.stack([L, R], 1)
mix *= 10 ** (-10 / 20) / np.max(np.abs(mix))       # bed peaks at -10 dBFS
fade = int(0.35 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libmp3lame", "-b:a", "224k", "assets/score/score.mp3"], input=pcm.tobytes(), check=True)
print("score written", DUR, "s")
