"""Records a REAL Chrome window on the real screen: real OS cursor, real scrolling, real typing in the address bar."""
import os, subprocess, sys, tempfile, time, shutil
sys.path.insert(0, os.path.dirname(__file__))
import win
from playwright.sync_api import sync_playwright
ROOT = r"C:\dfol\legalhk\pitch"; RAW = os.path.join(ROOT, "raw"); OUT = os.path.join(RAW, "browser.mp4")
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
TX = open(os.path.join(RAW, "latest_tx.txt")).read().strip()
TOKEN = "0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE"

def log(*a): print(*a, flush=True)
def ftext(pg, text):
    for f in pg.frames:
        loc = f.get_by_text(text)
        try:
            if loc.count(): return loc.first
        except Exception: pass
    return pg.get_by_text(text).first

HW = {}
def must_be_chrome():
    """Only act while OUR Chrome window is in front; retake it if something (a toast, another app) stole focus."""
    for i in range(30):
        if win.foreground_is(HW["h"]): return
        log("   focus is on %r, retaking Chrome" % win.foreground_title()); win.force_foreground(HW["h"]); time.sleep(0.6)
    raise RuntimeError("could not keep Chrome in front (foreground: %r)" % win.foreground_title())

with sync_playwright() as p:
    prof = tempfile.mkdtemp(prefix="pitch-chrome-")
    ctx = p.chromium.launch_persistent_context(prof, headless=False, executable_path=CHROME, viewport=None, no_viewport=True,
        args=["--start-maximized", "--window-position=0,0", "--no-first-run", "--no-default-browser-check", "--disable-infobars",
              "--disable-session-crashed-bubble", "--disable-features=Translate", "--force-device-scale-factor=1.5"], ignore_default_args=["--enable-automation", "--no-sandbox"])
    page = ctx.pages[0]; page.goto("about:blank"); page.evaluate("document.title = 'liensight-rec'"); time.sleep(1.0)
    HW["h"] = win.find_window("liensight-rec"); assert HW["h"], "could not find our Chrome window"
    win.user32.ShowWindow(HW["h"], 3); time.sleep(1.5)   # maximize OUR window, then let the layout settle
    assert win.force_foreground(HW["h"]), "could not bring Chrome to the front"; time.sleep(1.0)
    log("window:", page.evaluate("[screenX, screenY, outerWidth, outerHeight, innerWidth, innerHeight, devicePixelRatio]"))
    K = {"kx": 1.25, "ky": 1.25, "ox": 0.0, "oy": 110.0}
    def calibrate():
        """Map CSS px (current page + zoom) to physical screen px using two real cursor positions."""
        page.evaluate("window.__m = []; if (!window.__ml) { window.__ml = 1; addEventListener('mousemove', e => window.__m.push([e.clientX, e.clientY]), true) }")
        pts = []
        for sx, sy in ((760, 640), (1380, 860)):
            win.move_to(sx - 3, sy - 3, 0.25); time.sleep(0.15); win.move_to(sx, sy, 0.12); time.sleep(0.25)
            pts.append(((sx, sy), page.evaluate("window.__m.slice(-1)[0]")))
        (a, am), (b, bm) = pts
        K["kx"] = (b[0] - a[0]) / (bm[0] - am[0]); K["ky"] = (b[1] - a[1]) / (bm[1] - am[1])
        K["ox"] = a[0] - K["kx"] * am[0]; K["oy"] = a[1] - K["ky"] * am[1]
        log("calibration: kx=%.3f ky=%.3f ox=%.1f oy=%.1f" % (K["kx"], K["ky"], K["ox"], K["oy"]))
    page.goto("about:blank"); time.sleep(0.3)
    def scr(cx, cy): return K['ox'] + K['kx'] * cx, K['oy'] + K['ky'] * cy
    def center(loc):
        loc.scroll_into_view_if_needed(timeout=4000); b = loc.bounding_box(); return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    def go_to(loc, dur=0.8, dx=0, dy=0):
        must_be_chrome(); cx, cy = center(loc); x, y = scr(cx + dx, cy + dy); win.move_to(x, y, dur)
    def click_on(loc):
        go_to(loc); time.sleep(0.25); win.click()
    def navigate(url, wait_for=None):
        must_be_chrome(); target = "http://localhost:5190/" + url.split("localhost:5190/")[1] if url.startswith("localhost") else "https://" + url
        for attempt in range(3):
            try: page.goto(target, wait_until="commit", timeout=90000); break
            except Exception as e:
                log("   goto retry %d: %s" % (attempt + 1, str(e)[:80]))
                if attempt == 2: raise
        if wait_for: page.wait_for_selector(wait_for, timeout=60000)
    def zoom_in(n=2): pass

    page.goto("about:blank"); time.sleep(0.5); win.move_to(960, 560, 0.5)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-i", "desktop",
                           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "15", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    t0 = time.time(); time.sleep(1.2)
    try:
        # --- scene A: the live checker ---
        navigate("localhost:5190/check.html", ".result .status"); time.sleep(1.0); zoom_in(2); time.sleep(1.0); calibrate(); time.sleep(0.8)
        log("A loaded %.0fs" % (time.time() - t0))
        win.wheel(-4); time.sleep(1.4)
        go_to(page.locator(".result .status").first, 0.9); time.sleep(2.6)
        go_to(page.locator(".doclist a").first, 0.8); time.sleep(2.8)
        prs = page.locator("button[data-preset='1-905-1347']").first
        click_on(prs); page.wait_for_function("document.querySelector('.result .status')?.textContent.includes('No adverse')", timeout=60000)
        go_to(page.locator(".result .status").first, 0.9); time.sleep(3.6)
        log("A done %.0fs" % (time.time() - t0))
        # --- scene B: the block explorer ---
        navigate("sepolia.etherscan.io/tx/" + TX); time.sleep(7.0)
        try: page.get_by_text("Got it!").first.click(timeout=3000)   # via the browser: the banner is at the screen edge where the taskbar pops up
        except Exception: pass
        time.sleep(0.8); zoom_in(2); time.sleep(1.0); calibrate(); time.sleep(0.8)
        row = lambda lab: page.get_by_text(lab, exact=True).first
        go_to(row("Status:"), 0.9, dx=260); time.sleep(3.0)
        go_to(row("To:"), 0.8, dx=300); time.sleep(3.2)
        log("B1 done %.0fs" % (time.time() - t0))
        navigate("sepolia.etherscan.io/address/" + TOKEN); time.sleep(8.0); calibrate(); time.sleep(0.6)
        try: click_on(page.get_by_text("Events", exact=True).first)
        except Exception as e: log("   events tab click failed: %s" % str(e)[:80])
        time.sleep(5.0)
        win.wheel(-3); time.sleep(1.6)
        win.move_to(*scr(560, 400), 1.0); time.sleep(6.0)
        log("B2 done %.0fs" % (time.time() - t0))
    finally:
        time.sleep(0.8); ff.stdin.write(b"q"); ff.stdin.flush(); ff.wait(timeout=30)
        ctx.close(); shutil.rmtree(prof, ignore_errors=True)
    log("recorded %.1fs" % (time.time() - t0))
