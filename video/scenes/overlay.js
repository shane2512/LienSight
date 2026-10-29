/* Injected into every recorded page: captions, highlight boxes, visible cursor. */
(() => {
  if (window.__overlayReady) return;
  window.__overlayReady = true;
  const boot = () => {
    const st = document.createElement("style");
    st.textContent = `
      #__cap{position:fixed;left:50%;bottom:48px;transform:translateX(-50%) translateY(8px);max-width:1480px;padding:16px 30px;
        background:rgba(14,16,20,.9);color:#fff;font-family:"Inter Tight","Segoe UI",system-ui,sans-serif;font-weight:600;font-size:var(--capfs,30px);line-height:1.3;border-radius:14px;
        border-left:7px solid #ef4f26;text-align:center;opacity:0;transition:opacity .35s,transform .35s;z-index:2147483646;pointer-events:none;
        box-shadow:0 14px 40px rgba(0,0,0,.35)}
      #__cap.on{opacity:1;transform:translateX(-50%) translateY(0)}
      #__hl{position:fixed;inset:0;pointer-events:none;z-index:2147483645}
      #__hl .b{position:absolute;border:4px solid #ef4f26;border-radius:10px;box-shadow:0 0 0 6px rgba(239,79,38,.18);
        animation:__pop .35s ease-out}
      #__hl .t{position:absolute;transform:translateY(-100%);background:#ef4f26;color:#fff;font:700 18px/1 "JetBrains Mono",monospace;
        padding:7px 11px;border-radius:8px 8px 0 0;white-space:nowrap}
      @keyframes __pop{from{opacity:0;transform:scale(1.04)}to{opacity:1;transform:scale(1)}}
      #__cur{position:fixed;left:-60px;top:-60px;width:34px;height:34px;z-index:2147483647;pointer-events:none;
        filter:drop-shadow(0 3px 4px rgba(0,0,0,.45));transition:transform .05s}
    `;
    document.documentElement.appendChild(st);
    const cap = document.createElement("div"); cap.id = "__cap";
    const hl = document.createElement("div"); hl.id = "__hl";
    const cur = document.createElement("div"); cur.id = "__cur";
    cur.innerHTML = '<svg viewBox="0 0 24 24" width="34" height="34"><path d="M3 2l7.5 19 2.6-7.6L21 10.8z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.append(cap, hl, cur);
    addEventListener("mousemove", (e) => { cur.style.left = e.clientX - 3 + "px"; cur.style.top = e.clientY - 2 + "px"; }, true);
    window.__cap = (t) => { if (!t) { cap.classList.remove("on"); return; } cap.classList.remove("on"); void cap.offsetWidth; cap.textContent = t; cap.classList.add("on"); };
    window.__hl = (boxes) => {
      hl.innerHTML = "";
      (boxes || []).forEach((b) => {
        const d = document.createElement("div"); d.className = "b";
        Object.assign(d.style, { left: b.x + "px", top: b.y + "px", width: b.w + "px", height: b.h + "px" });
        hl.appendChild(d);
        if (b.label) { const t = document.createElement("div"); t.className = "t"; t.textContent = b.label; Object.assign(t.style, { left: b.x + "px", top: b.y + "px" }); hl.appendChild(t); }
      });
    };
    window.__scrollTo = (y, ms) => new Promise((res) => {
      const y0 = scrollY, t0 = performance.now();
      const ease = (t) => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
      const step = (now) => { const p = Math.min(1, (now - t0) / ms); scrollTo(0, y0 + (y - y0) * ease(p)); p < 1 ? requestAnimationFrame(step) : res(); };
      requestAnimationFrame(step);
    });
  };
  if (document.documentElement) boot(); else addEventListener("DOMContentLoaded", boot);
})();
