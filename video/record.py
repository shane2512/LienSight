"""Records the Liensight demo scenes (silent, with on-screen captions). Usage: python record.py [scene ...]"""
import json, os, re, shutil, sys, time
from playwright.sync_api import sync_playwright

V = r"C:\dfol\legalhk\video"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
SITE = "http://localhost:5190"
TERM_URL = "file:///C:/dfol/legalhk/video/scenes/terminal.html"
OVERLAY = os.path.join(V, "scenes", "overlay.js")
TOKEN = "0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE"
OLD_TX = "0xc0cc238205a36246731feddba275b3df50b4c781f3958b8d4cab8a862bda85ab"
TERM = json.load(open(os.path.join(V, "raw", "terminal.json"), encoding="utf-8"))
NEW_TX = re.search(r"tx=(0x[0-9a-f]{64})", " ".join(l["t"] for l in TERM["cre"]["lines"])).group(1)
os.makedirs(os.path.join(V, "build"), exist_ok=True)


import base64, subprocess
FFMPEG = "ffmpeg"

class Recorder:
    """Records a page via CDP screencast (variable frame times) and encodes a constant-30fps mp4 with the system ffmpeg."""
    def __init__(self, ctx, pg, name):
        self.dir = os.path.join(V, "build", "frames_" + name); shutil.rmtree(self.dir, ignore_errors=True); os.makedirs(self.dir)
        self.cdp = ctx.new_cdp_session(pg); self.frames = []; self.name = name; self.on = False; self.raw = []
        self.cdp.on("Page.screencastFrame", self._frame)
    def _frame(self, ev):
        if not self.on: return
        i = len(self.frames); fn = f"{i:06d}.jpg"
        with open(os.path.join(self.dir, fn), "wb") as f: f.write(base64.b64decode(ev["data"]))
        self.raw.append((ev["metadata"]["timestamp"], time.time(), fn)); self.frames.append((0.0, fn))
        try: self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception: pass
    def start(self):
        self.on = True; self.t_start = time.time()
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 88, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1})
    def stop(self):
        self.t_end = time.time(); self.on = False
        try: self.cdp.send("Page.stopScreencast")
        except Exception: pass
    def encode(self, out):
        """Constant 30 fps: for each output frame pick the latest screencast frame at or before that moment."""
        import bisect
        if len(self.raw) < 1: raise RuntimeError("no frames")
        off = min(arr - ts for ts, arr, _ in self.raw)  # lowest-latency frame gives the true clock offset
        self.frames = [(ts + off, fn) for ts, _, fn in self.raw]
        times = [t for t, _ in self.frames]; names = [n for _, n in self.frames]
        n_out = max(2, int((self.t_end - self.t_start) * 30))
        lst = os.path.join(self.dir, "list.txt")
        with open(lst, "w") as f:
            for i in range(n_out):
                k = max(0, bisect.bisect_right(times, self.t_start + i / 30) - 1)
                f.write("file '" + names[k] + "'" + chr(10) + "duration 0.033333" + chr(10))
            f.write("file '" + names[-1] + "'" + chr(10))
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", "fps=30,format=yuv420p,scale=1920:1080",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out], check=True)
        return self.t_end - self.t_start

# ---------- helpers ----------
def cap(pg, t): pg.evaluate("t => window.__cap(t)", t)
def hl(pg, boxes): pg.evaluate("b => window.__hl(b)", boxes)
def wait(pg, s): pg.wait_for_timeout(int(s * 1000))

def box(pg, loc, pad=10, label=None, wide=None):
    try:
        loc.scroll_into_view_if_needed(timeout=3000)
        b = loc.bounding_box()
    except Exception as e:
        print("   box miss (error):", str(e)[:100], flush=True); return None
    if not b: print("   box miss (no bbox)", flush=True); return None
    x, w = (wide if wide else (b["x"], b["width"]))
    return {"x": x - pad, "y": b["y"] - pad, "w": w + 2 * pad, "h": b["height"] + 2 * pad, "label": label}

def move(pg, loc, steps=35):
    b = loc.bounding_box()
    if b: pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=steps)

def smooth(pg, y, ms=1600):
    pg.evaluate("([y,ms]) => window.__scrollTo(y, ms)", [y, ms]); wait(pg, ms / 1000 + 0.25)

def top_of(pg, sel, off=-110):
    return pg.evaluate("([s,o]) => document.querySelector(s).getBoundingClientRect().top + scrollY + o", [sel, off])

def cookies(pg):
    try: pg.get_by_text("Got it!").first.click(timeout=2500)
    except Exception: pass

def ftext(pg, text):
    """Find text in the main page or any child iframe (Etherscan renders tab content in iframes)."""
    for f in pg.frames:
        loc = f.get_by_text(text)
        try:
            if loc.count(): return loc.first
        except Exception: pass
    return pg.get_by_text(text).first

def zoom(pg, z): pg.evaluate("z => { document.body.style.zoom = z }", z)

def has_text(pg, text):
    try: return any(f.get_by_text(text).count() for f in pg.frames)
    except Exception: return False

def prep_eth(url, events_tab=False, z=1.25, expect="Etherscan"):
    def run(pg):
        for attempt in range(1, 5):
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000); wait(pg, 10); cookies(pg)
                if events_tab:
                    for _ in range(4):
                        try: pg.locator("a.nav-link", has_text="Events").first.click(timeout=5000)
                        except Exception as e: print("   tab click:", str(e)[:80], flush=True)
                        wait(pg, 5)
                        if has_text(pg, expect): break
                if has_text(pg, expect): break
                print(f"   prep attempt {attempt}: '{expect}' not on page, retrying", flush=True)
            except Exception as e:
                print(f"   prep attempt {attempt} error: {str(e)[:120]}", flush=True)
            wait(pg, 8)
        wait(pg, 0.8)
    return run

def row(pg, label):
    lab = pg.get_by_text(label, exact=True).first
    return lab.locator("xpath=ancestor::div[contains(@class,'row')][1]")

CARD_CSS = """body{margin:0;height:100vh;display:grid;place-items:center;text-align:center;color:#15181c;
  background:linear-gradient(180deg,#6fb0ea,#cfe7fb);font-family:'Inter Tight','Segoe UI',sans-serif}
  h1{font:900 118px/.95 'Archivo','Arial Black',sans-serif;text-transform:uppercase;letter-spacing:-.03em;margin:0}
  h1 em{font-style:normal;color:#d23a16} p{font:500 34px/1.4 'Inter Tight',sans-serif;margin:30px auto 0;max-width:1300px;color:#2c3440}
  .pill{display:inline-block;background:#fff;border-radius:999px;padding:12px 26px;font:700 24px 'JetBrains Mono',monospace;margin-bottom:34px}
  ul{list-style:none;padding:0;margin:34px auto 0;max-width:1250px;text-align:left;font:600 32px/1.5 'Inter Tight',sans-serif}
  li{padding:8px 0 8px 46px;position:relative}li:before{content:'';position:absolute;left:8px;top:22px;width:16px;height:16px;border-radius:50%;background:#d23a16}"""
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Inter+Tight:wght@500;600;700&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">'

# ---------- scenes ----------
def s_title(pg):
    pg.set_content(f"<!doctype html><meta charset=utf-8>{FONTS}<style>{CARD_CSS}</style><div><div class=pill>Chainlink CRE · Sepolia testnet · BLI Legal Hack 2026</div>"
                   "<h1>Liensight</h1><p>A property token that restricts its own transfers when a new lien is recorded on the building behind it.</p></div>")
    wait(pg, 1.5); wait(pg, 3.5)

def s_closing(pg):
    pg.set_content(f"<!doctype html><meta charset=utf-8>{FONTS}<style>{CARD_CSS}</style><div><h1>Where it <em>stops</em></h1>"
                   "<ul><li>Runs on the Sepolia testnet through Chainlink's simulator, not a deployed network.</li>"
                   "<li>ACRIS records filings days after the event: an early warning, not a title search.</li>"
                   "<li>Covers federal, tax and common-charge liens and judgments. No lis pendens (not in ACRIS).</li>"
                   "<li>Hackathon build, not audited, not legal advice.</li></ul></div>")
    wait(pg, 1.5); wait(pg, 9.5)

def s_landing(pg):
    pg.goto(SITE + "/"); wait(pg, 1.2)
    cap(pg, "Liensight watches New York City's public property record for the building behind a token.")
    wait(pg, 5.2)
    smooth(pg, top_of(pg, ".carousel", -150), 1700)
    cap(pg, "Real evidence from a real run: a Bronx lot with a lien, the Chainlink log, the token's on-chain state.")
    st = pg.locator(".ecard .stage").first; b = st.bounding_box()
    for _ in range(2):
        pg.mouse.move(b["x"] + b["width"] * .7, b["y"] + b["height"] * .5, steps=25); pg.mouse.down()
        pg.mouse.move(b["x"] + b["width"] * .1, b["y"] + b["height"] * .5, steps=40); pg.mouse.up(); wait(pg, 1.6)
    smooth(pg, top_of(pg, "#what .bento", -190), 1700)
    cap(pg, "What it does: 14 documents read, 1 lien cited on-chain, 35 tests passing.")
    wait(pg, 4.5)
    smooth(pg, top_of(pg, "#how .chat", -140), 1700)
    cap(pg, "How it works: every Chainlink node reads ACRIS on its own, and they must agree on the exact documents.")
    wait(pg, 3.5); smooth(pg, top_of(pg, "#how .chat", 110), 2200); wait(pg, 3.0)

def s_check(pg):
    pg.goto(SITE + "/check.html"); wait(pg, 1.0)
    cap(pg, "Check page: reading NYC's ACRIS records live, in the browser.")
    pg.wait_for_selector(".result .status", timeout=45000)
    smooth(pg, top_of(pg, ".plan", -120), 1200)
    cap(pg, "Bronx lot 2-5789-1022: 14 recorded documents, one of them an adverse lien of common charges (LOCC).")
    st = pg.locator(".result .status").first
    boxes = [box(pg, st, 12, "ADVERSE FILING FOUND")]
    first = pg.locator(".doclist a").first
    boxes.append(box(pg, first, 8, "LOCC · 2026092900833001"))
    hl(pg, [b for b in boxes if b]); move(pg, first); wait(pg, 5.5)
    cap(pg, "Each document links to the official ACRIS record, so anyone can verify it.")
    wait(pg, 3.0); hl(pg, [])
    prs = pg.locator("button[data-preset='1-905-1347']").first
    move(pg, prs); wait(pg, 0.5); prs.click()
    pg.wait_for_function("document.querySelector('.result .status')?.textContent.includes('No adverse')", timeout=45000)
    cap(pg, "Manhattan lot 1-905-1347: no tax lien, no federal lien, no judgment. Transfers stay open.")
    hl(pg, [box(pg, pg.locator(".result .status").first, 12, "CLEAN")]); wait(pg, 6.0)

def prep_term(pg):
    pg.goto(TERM_URL, wait_until="domcontentloaded"); pg.evaluate("document.fonts.ready.then(() => 1)"); wait(pg, 1.0)

def term_run(pg, steps):
    wait(pg, 0.8)
    for i, (key, text, opts) in enumerate(steps):
        if i: pg.evaluate("window.clearTerm()")
        cap(pg, text)
        _t = time.time()
        pg.evaluate("([sc,o]) => { window.__done = false; window.runScene(sc,o).then(() => { window.__done = true; }); }", [TERM[key], opts])
        while not pg.evaluate("window.__done"): wait(pg, 0.25)
        print(f"   step {key}: page took {time.time() - _t:.1f}s", flush=True)

def s_tests(pg):
    term_run(pg, [("forge", "Contract tests: 18 pass, covering access control, replays and stale clears.", {"hold": 3.6, "fs": 19, "minGap": 60}),
                  ("vitest", "Workflow tests: 17 pass, covering ordering, empty results, truncation and legacy IDs.", {"hold": 3.2})])

NOISE = ("Simulation complete", "╭", "╰", "│", "Update available", "cre update", "cre account access")

def s_cre(pg):
    TERM["cre"]["lines"] = [l for l in TERM["cre"]["lines"] if not any(n in l["t"] for n in NOISE)]
    while TERM["cre"]["lines"] and not TERM["cre"]["lines"][-1]["t"].strip(): TERM["cre"]["lines"].pop()
    term_run(pg, [("cre", "The Chainlink CRE workflow, live: it reads ACRIS, flags the lien, and sends a report to the token on Sepolia.", {"hold": 6.0, "gapCap": 2.6})])

def s_cast(pg):
    term_run(pg, [("restricted", "Reading the token directly on Sepolia: restricted() is true.", {"hold": 2.8}),
                  ("transfer", "Even the issuer can't move tokens now.", {"hold": 4.2, "note": "# 0xe827105e = TransferRestricted()"})])

def s_proof(pg):
    pg.goto(SITE + "/proof.html"); wait(pg, 1.0)
    pg.wait_for_function("[...document.querySelectorAll('[data-read]')].every(e => e.textContent !== '…')", timeout=45000)
    smooth(pg, top_of(pg, ".kv", -230), 1400)
    cap(pg, "Proof page: values read live from the token on Sepolia each time the page loads.")
    wait(pg, 3.0)
    hl(pg, [box(pg, pg.locator("[data-read=restricted]").first, 14, "restricted() = true")]); wait(pg, 4.0)
    cap(pg, "citedHash matches the hash of lien 2026092900833001, computed independently.")
    hl(pg, [box(pg, pg.locator("[data-read=citedHash]").first, 14, "citedHash")]); wait(pg, 5.5)

def s_eth_new(pg):
    cap(pg, "Block explorer: the transaction from the run you just saw. Status: Success on Sepolia.")
    boxes = [box(pg, row(pg, "Status:"), 10, "SUCCESS"), box(pg, row(pg, "To:"), 10, "CHAINLINK FORWARDER")]
    hl(pg, [b for b in boxes if b]); wait(pg, 6.5)
    cap(pg, "It's addressed to Chainlink's forwarder, which delivers the report to our token.")
    wait(pg, 4.5)

def s_eth_old(pg):
    cap(pg, "The first report, which restricted the token. Status: Success.")
    hl(pg, [b for b in [box(pg, row(pg, "Status:"), 10, "SUCCESS")] if b]); wait(pg, 4.5)
    hl(pg, []); lg = pg.get_by_text("Logs (2)").first; move(pg, lg); wait(pg, 0.5); lg.click(); wait(pg, 2.5)
    cap(pg, "Two logs: the first is emitted by our token contract (the restriction), the second by the forwarder.")
    try:
        tok = pg.get_by_text(re.compile("f813c584", re.I)).first
        hl(pg, [b for b in [box(pg, tok, 10, "OUR TOKEN 0xf813…04aE", wide=(tok.bounding_box()["x"], 760))] if b])
    except Exception: pass
    wait(pg, 8.0)

def s_eth_events(pg):
    smooth(pg, 330, 900)
    cap(pg, "The token's Events tab on the block explorer: the Restricted event from the report, and the mint from the deploy.")
    hdr = ftext(pg, "Latest 2 Contract Events")
    blk = hdr.locator("xpath=..")
    hl(pg, [b for b in [box(pg, blk, 14, "TOKEN EVENTS")] if b]); wait(pg, 9.0)

def s_security(pg):
    pg.goto(SITE + "/security.html"); wait(pg, 1.0)
    smooth(pg, top_of(pg, ".attacks", -140), 1500)
    cap(pg, "Security page: twelve attacks, each with the defense and the test that proves it.")
    wait(pg, 5.0)
    smooth(pg, top_of(pg, ".receipts", -200), 2200)
    cap(pg, "Our first test token rejected a real report because the simulator used a different workflow owner. The second accepted it.")
    wait(pg, 8.0)

SCENES = {"title": s_title, "landing": s_landing, "check": s_check, "tests": s_tests, "cre": s_cre, "eth_new": s_eth_new,
          "proof": s_proof, "cast": s_cast, "eth_events": s_eth_events, "eth_old": s_eth_old, "security": s_security, "closing": s_closing}
PREP = {"tests": prep_term, "cre": prep_term, "cast": prep_term,
        "eth_new": prep_eth(f"https://sepolia.etherscan.io/tx/{NEW_TX}", expect="Transaction Hash:"),
        "eth_old": prep_eth(f"https://sepolia.etherscan.io/tx/{OLD_TX}", expect="Transaction Hash:"),
        "eth_events": prep_eth(f"https://sepolia.etherscan.io/address/{TOKEN}", events_tab=True, z=1.15, expect="Latest 2 Contract Events")}
ORDER = ["title", "landing", "check", "tests", "cre", "eth_new", "proof", "cast", "eth_events", "eth_old", "security", "closing"]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME, args=["--hide-scrollbars"])
    for name in (sys.argv[1:] or ORDER):
        big = name.startswith("eth_")
        ctx = b.new_context(viewport={"width": 1600, "height": 900} if big else {"width": 1920, "height": 1080}, device_scale_factor=1.2 if big else 1,
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        ctx.add_init_script(path=OVERLAY)
        pg = ctx.new_page(); pg.set_default_timeout(60000)
        if name in PREP:
            try: PREP[name](pg); pg.evaluate("document.documentElement.style.setProperty('--capfs','24px')")
            except Exception as e: print(f"!! prep {name}: {str(e)[:200]}", flush=True)
        rec = Recorder(ctx, pg, name); rec.start(); t0 = time.time(); ok = True
        try: SCENES[name](pg)
        except Exception as e: ok = False; print(f"!! {name} failed: {str(e)[:300]}", flush=True)
        wait(pg, 0.4); rec.stop(); ctx.close()
        out = os.path.join(V, "build", name + ".mp4")
        try: dur = rec.encode(out); (None if os.environ.get('KEEP') else shutil.rmtree(rec.dir, ignore_errors=True))
        except Exception as e: dur = -1; ok = False; print(f"!! encode {name}: {e}", flush=True)
        if rec.frames: print(f"   dbg t0=0 first={rec.frames[0][0]-t0:.2f} last={rec.frames[-1][0]-t0:.2f} end={rec.t_end-t0:.2f} n={len(rec.frames)}", flush=True)
        print(f"{'ok ' if ok else 'ERR'} {name}: {time.time() - t0:.0f}s wall, {dur:.1f}s video, {len(rec.frames)} frames", flush=True)
    b.close()
