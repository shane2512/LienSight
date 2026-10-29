"""Real OS-level input helpers (cursor, click, scroll, keys, typing) so a screen recording shows a genuine cursor and real typing."""
import ctypes, ctypes.wintypes as wt, math, random, time
user32 = ctypes.windll.user32
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: user32.SetProcessDPIAware()
    except Exception: pass

class RECT(ctypes.Structure): _fields_ = [("l", wt.LONG), ("t", wt.LONG), ("r", wt.LONG), ("b", wt.LONG)]
def work_area():
    r = RECT(); user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA (physical px, DPI-aware)
    return r.l, r.t, r.r - r.l, r.b - r.t
def screen_size(): return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
def cursor():
    p = wt.POINT(); user32.GetCursorPos(ctypes.byref(p)); return p.x, p.y
def foreground_title():
    h = user32.GetForegroundWindow(); n = user32.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(n + 1); user32.GetWindowTextW(h, b, n + 1); return b.value
def _ease(t): return t * t * (3 - 2 * t)
def move_to(x, y, dur=0.7):
    x0, y0 = cursor(); n = max(12, int(dur * 120))
    # slight arc so it doesn't look robotic
    dx, dy = x - x0, y - y0; nx, ny = -dy, dx; L = math.hypot(nx, ny) or 1
    bow = min(40, L * 0.06) * random.choice([-1, 1])
    for i in range(1, n + 1):
        t = _ease(i / n); off = math.sin(math.pi * t) * bow
        user32.SetCursorPos(int(x0 + dx * t + nx / L * off), int(y0 + dy * t + ny / L * off)); time.sleep(dur / n)
    user32.SetCursorPos(int(x), int(y))
def click(double=False):
    for _ in range(2 if double else 1):
        user32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.06); user32.mouse_event(0x0004, 0, 0, 0, 0); time.sleep(0.09)
def wheel(clicks, step=0.03):  # negative = scroll down
    d = 120 if clicks > 0 else -120
    for _ in range(abs(clicks)): user32.mouse_event(0x0800, 0, 0, d & 0xFFFFFFFF, 0); time.sleep(step)
VK = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "enter": 0x0D, "l": 0x4C, "t": 0x54, "tab": 0x09, "esc": 0x1B, "plus": 0xBB, "minus": 0xBD, "0": 0x30}
def key(*names):
    codes = [VK[n] for n in names]
    for c in codes: user32.keybd_event(c, 0, 0, 0); time.sleep(0.03)
    for c in reversed(codes): user32.keybd_event(c, 0, 2, 0); time.sleep(0.03)
class KI(ctypes.Structure): _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
class INP(ctypes.Structure):
    class _U(ctypes.Union): _fields_ = [("ki", KI), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",); _fields_ = [("type", wt.DWORD), ("u", _U)]
def type_text(s, per=0.045, jitter=0.03):
    for ch in s:
        for flags in (0x0004, 0x0004 | 0x0002):  # KEYEVENTF_UNICODE, then | KEYUP
            i = INP(type=1); i.ki = KI(0, ord(ch), flags, 0, None); user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(per + random.random() * jitter)

WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
def find_window(substr):
    res = []
    def cb(h, l):
        if user32.IsWindowVisible(h):
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1); user32.GetWindowTextW(h, b, n + 1)
                if substr in b.value: res.append(h)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0); return res[0] if res else None
def force_foreground(h, tries=6):
    """Bring exactly this window to the front. Windows blocks background apps from stealing focus, so lift the lock (Alt tap) and attach to the current foreground thread."""
    k32 = ctypes.windll.kernel32
    for _ in range(tries):
        if _ > 0: user32.keybd_event(0x12, 0, 0, 0); user32.keybd_event(0x12, 0, 2, 0)   # Alt tap only as a fallback
        if user32.IsIconic(h): user32.ShowWindow(h, 9)
        fg = user32.GetForegroundWindow(); ft = user32.GetWindowThreadProcessId(fg, None); ct = k32.GetCurrentThreadId()
        if ft and ft != ct: user32.AttachThreadInput(ct, ft, True)
        user32.BringWindowToTop(h); user32.SetForegroundWindow(h); user32.SwitchToThisWindow(h, True)
        if ft and ft != ct: user32.AttachThreadInput(ct, ft, False)
        time.sleep(0.4)
        if user32.GetForegroundWindow() == h: return True
    return False
def foreground_is(h): return user32.GetForegroundWindow() == h
