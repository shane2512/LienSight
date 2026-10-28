/* Liensight site behaviour: GSAP motion, live ACRIS checker, live Sepolia reads */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasGsap = typeof gsap !== "undefined";
  if (hasGsap) gsap.registerPlugin(ScrollTrigger, Draggable);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- sky ---------- */
  const sky = $(".sky");
  if (sky) {
    const spots = [[4, 14, ""], [70, 8, "soft"], [38, 30, "tiny"], [82, 40, ""], [10, 58, "soft"], [55, 66, "tiny"], [88, 80, ""], [24, 90, "tiny"]];
    spots.forEach(([x, y, k]) => {
      const c = document.createElement("div");
      c.className = "cloud " + k;
      c.style.left = x + "%";
      c.style.top = y + "%";
      sky.appendChild(c);
      if (hasGsap && !reduce) {
        gsap.to(c, { x: (Math.random() > 0.5 ? 1 : -1) * (60 + Math.random() * 90), duration: 18 + Math.random() * 14, ease: "sine.inOut", yoyo: true, repeat: -1 });
        gsap.to(c, { yPercent: -40 - Math.random() * 60, ease: "none", scrollTrigger: { start: 0, end: "max", scrub: 1 } });
      }
    });
  }

  /* ---------- ruler: playhead + live clock ---------- */
  const head = $(".ruler .playhead");
  const clock = $(".ruler .clock");
  const tick = () => {
    if (clock) clock.textContent = new Date().toISOString().slice(11, 19) + " UTC";
  };
  tick();
  setInterval(tick, 1000);
  const moveHead = () => {
    if (!head) return;
    const max = document.documentElement.scrollHeight - innerHeight;
    const p = max > 0 ? scrollY / max : 0;
    head.style.left = (p * 100).toFixed(2) + "%";
    head.textContent = Math.round(p * 1440);
  };
  addEventListener("scroll", moveHead, { passive: true });
  moveHead();

  /* ---------- multiplayer "you" cursor + drag pill ---------- */
  const you = $(".cursor-you");
  const drag = $(".drag-pill");
  if (you && matchMedia("(pointer: fine)").matches) {
    addEventListener("pointermove", (e) => {
      you.style.opacity = 1;
      you.style.transform = `translate(${e.clientX + 14}px, ${e.clientY + 16}px)`;
      if (drag) drag.style.left = e.clientX + "px", drag.style.top = e.clientY + "px";
    });
    $$("[data-drag-zone]").forEach((z) => {
      z.addEventListener("pointerenter", () => hasGsap && gsap.to(drag, { opacity: 1, scale: 1, duration: 0.25 }));
      z.addEventListener("pointerleave", () => hasGsap && gsap.to(drag, { opacity: 0, scale: 0.6, duration: 0.2 }));
    });
  }

  if (hasGsap && !reduce) {
    /* ---------- hero intro ---------- */
    const hero = $(".hero");
    if (hero) {
      gsap.timeline({ defaults: { ease: "power3.out" } })
        .from(".nav > *", { y: -24, autoAlpha: 0, stagger: 0.08, duration: 0.6 })
        .from(".hero .badge", { y: 16, autoAlpha: 0, duration: 0.5 }, "-=0.3")
        .from(".stipple .line", { yPercent: 60, autoAlpha: 0, rotateX: -50, transformOrigin: "50% 100%", stagger: 0.12, duration: 0.9 }, "-=0.2")
        .from(".hero .sub", { y: 20, autoAlpha: 0, duration: 0.6 }, "-=0.4")
        .add(() => $(".hero .sub")?.classList.add("on"))
        .from(".hero .ctas > *", { y: 14, autoAlpha: 0, stagger: 0.08, duration: 0.5 }, "-=0.3")
        .from(".hero .corners > *", { autoAlpha: 0, duration: 0.6 }, "-=0.2")
        .add(() => setTimeout(() => $(".hero .sub")?.classList.remove("on"), 1800));
    }

    /* ---------- generic reveals ---------- */
    $$("[data-reveal]").forEach((el) => {
      gsap.from(el, { y: 50, autoAlpha: 0, duration: 0.9, ease: "power3.out", scrollTrigger: { trigger: el, start: "top 85%" } });
    });
    $$("[data-stagger]").forEach((wrap) => {
      gsap.from(wrap.children, { y: 40, autoAlpha: 0, duration: 0.7, ease: "power3.out", stagger: 0.08, scrollTrigger: { trigger: wrap, start: "top 80%" } });
    });
    $$(".display").forEach((el) => {
      gsap.from(el, { yPercent: 30, autoAlpha: 0, duration: 0.9, ease: "power4.out", scrollTrigger: { trigger: el, start: "top 88%" } });
    });

    /* ---------- chat thread: messages arrive in order ---------- */
    $$(".chat .body").forEach((b) => {
      gsap.from(b.children, { y: 18, autoAlpha: 0, duration: 0.5, ease: "power2.out", stagger: 0.12, scrollTrigger: { trigger: b, start: "top 75%" } });
    });

    /* ---------- count-up stats ---------- */
    $$("[data-count]").forEach((el) => {
      const end = +el.dataset.count;
      const o = { v: 0 };
      gsap.to(o, { v: end, duration: 1.4, ease: "power2.out", scrollTrigger: { trigger: el, start: "top 85%" }, onUpdate: () => (el.firstChild.nodeValue = Math.round(o.v)) });
    });

    /* ---------- footer wordmark rise ---------- */
    const wm = $(".wordmark");
    if (wm) gsap.from(wm, { yPercent: 40, duration: 1.2, ease: "power4.out", scrollTrigger: { trigger: wm, start: "top 98%" } });
  }

  /* ---------- draggable evidence carousel ---------- */
  const track = $(".track");
  if (track && hasGsap) {
    const cards = $$(".ecard", track);
    const zone = track.parentElement;
    let bounds = { minX: 0, maxX: 0 };
    const measure = () => (bounds = { minX: Math.min(0, zone.clientWidth - track.scrollWidth), maxX: 0 });
    const markCenter = () => {
      const mid = innerWidth / 2;
      let best = null, bd = 1e9;
      cards.forEach((c) => {
        const r = c.getBoundingClientRect();
        const d = Math.abs(r.left + r.width / 2 - mid);
        if (d < bd) (bd = d), (best = c);
      });
      cards.forEach((c) => c.classList.toggle("on", c === best));
    };
    measure();
    const snapTo = (x) => {
      const pad = parseFloat(getComputedStyle(track).paddingLeft);
      const step = cards[0].offsetWidth + 28;
      const i = Math.round(-x / step);
      return gsap.utils.clamp(bounds.minX, 0, -i * step + (pad > 16 ? 0 : 0));
    };
    const d = Draggable.create(track, {
      type: "x",
      bounds,
      edgeResistance: 0.85,
      onDrag: markCenter,
      onDragEnd() {
        gsap.to(track, { x: snapTo(this.x), duration: 0.6, ease: "power3.out", onUpdate: markCenter, onComplete: () => d[0].update() });
      },
    });
    addEventListener("resize", () => { measure(); d[0].applyBounds(bounds); markCenter(); });
    markCenter();
    $$("[data-carousel]").forEach((b) =>
      b.addEventListener("click", () => {
        const step = cards[0].offsetWidth + 28;
        const nx = gsap.utils.clamp(bounds.minX, 0, gsap.getProperty(track, "x") + (b.dataset.carousel === "next" ? -step : step));
        gsap.to(track, { x: nx, duration: 0.6, ease: "power3.out", onUpdate: markCenter, onComplete: () => d[0].update() });
      })
    );
  }

  /* ---------- pinned sideways panels ---------- */
  const hrow = $(".hrow");
  if (hrow && hasGsap) {
    ScrollTrigger.matchMedia({
      "(min-width: 901px) and (prefers-reduced-motion: no-preference)": () => {
        const dist = () => hrow.scrollWidth - innerWidth;
        gsap.to(hrow, { x: () => -dist(), ease: "none", scrollTrigger: { trigger: ".hpin", start: "top top", end: () => "+=" + dist(), scrub: 1, pin: true, invalidateOnRefresh: true } });
      },
      "(max-width: 900px)": () => {
        hrow.style.flexDirection = "column";
        hrow.style.width = "auto";
        return () => { hrow.style.flexDirection = ""; hrow.style.width = ""; };
      },
    });
  }

  /* ---------- live ACRIS checker (same adverse map as the CRE workflow) ---------- */
  const ADVERSE = ["FL", "FTL", "NTXL", "TLS", "LOCC", "JUDG"];
  const DISCHARGE = ["RFL", "RFTL", "DTL", "DPFTL", "WFL", "RTXL", "TOLCC", "PWFL", "PRFL"];
  const BORO = { 1: "Manhattan", 2: "Bronx", 3: "Brooklyn", 4: "Queens", 5: "Staten Island" };
  const API = "https://data.cityofnewyork.us/resource";
  const esc = (x) => String(x).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const q = (p) => Object.entries(p).map(([k, v]) => encodeURIComponent(k) + "=" + encodeURIComponent(v)).join("&");
  const getJson = async (u) => {
    const r = await fetch(u);
    if (!r.ok) throw new Error("ACRIS " + r.status);
    return r.json();
  };

  $$("[data-checker]").forEach((root) => {
    const f = $("form", root), out = $(".result", root), fill = $(".track-bar .fill", root), big = $("[data-bbl-big]", root), boro = $("[data-boro]", root);
    const run = async (e) => {
      e && e.preventDefault();
      const b = +f.borough.value, k = parseInt(f.block.value, 10), l = parseInt(f.lot.value, 10);
      if (!BORO[b] || !(k > 0) || !(l > 0)) {
        out.innerHTML = `<div class="status bad">Check the numbers</div><div class="msgline">Borough is 1 to 5. Block and lot are whole numbers.</div>`;
        return;
      }
      if (big) big.textContent = `${b}-${k}-${l}`;
      if (boro) boro.textContent = "/ " + BORO[b];
      out.innerHTML = `<div class="msgline">Reading ACRIS for ${b}-${k}-${l}…</div>`;
      if (hasGsap) gsap.fromTo(fill, { width: "8%" }, { width: "70%", duration: 2.4, ease: "power1.out" });
      fill.textContent = "READING ACRIS";
      try {
        const legals = await getJson(`${API}/8h5j-fqxa.json?` + q({ $select: "document_id", $where: `borough='${b}' AND block='${k}' AND lot='${l}'`, $order: "document_id", $limit: 5000 }));
        const ids = [...new Set(legals.map((x) => x.document_id))];
        const master = [];
        for (let i = 0; i < ids.length; i += 80)
          master.push(...(await getJson(`${API}/bnx9-e6tj.json?` + q({ $select: "document_id,doc_type,recorded_datetime", $where: `document_id in(${ids.slice(i, i + 80).map((x) => `'${x}'`).join(",")})`, $order: "document_id", $limit: 5000 }))));
        const docs = [...new Map(master.map((m) => [m.document_id, m])).values()].sort((a, c) => (a.recorded_datetime < c.recorded_datetime ? 1 : -1));
        const adv = docs.filter((d) => ADVERSE.includes(d.doc_type));
        const dis = docs.filter((d) => DISCHARGE.includes(d.doc_type));
        if (hasGsap) gsap.to(fill, { width: "100%", duration: 0.4 });
        fill.textContent = docs.length + " DOCUMENTS";
        if (!docs.length) {
          out.innerHTML = `<div class="status bad">No documents found</div><div class="msgline">The workflow refuses to report a lot with zero documents: it is more likely a wrong BBL than a clean one.</div>`;
          return;
        }
        const head = adv.length
          ? `<div class="status bad">Transfers would be restricted: ${adv.length} adverse filing${adv.length > 1 ? "s" : ""}</div>`
          : `<div class="status good">No adverse filings: transfers stay open</div>`;
        const note = dis.length ? ` ${dis.length} discharge filing${dis.length > 1 ? "s" : ""} found: the token only suggests a clear, the issuer decides.` : "";
        out.innerHTML =
          head +
          `<div class="msgline">${docs.length} documents on record.${note}</div><div class="doclist">` +
          docs
            .slice(0, 30)
            .map((d) => {
              const cls = ADVERSE.includes(d.doc_type) ? "" : DISCHARGE.includes(d.doc_type) ? "dis" : "plain";
              const ic = cls === "" ? "!" : cls === "dis" ? "✓" : "·";
              return `<a class="${cls}" href="https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentDetail?doc_id=${encodeURIComponent(d.document_id)}" target="_blank" rel="noopener"><i>${ic}</i>${esc(d.doc_type)} · ${esc(d.document_id)}</a>`;
            })
            .join("") +
          `</div>` +
          (docs.length > 30 ? `<div class="msgline">Showing the 30 most recent.</div>` : "");
      } catch (err) {
        fill.textContent = "FAILED";
        out.innerHTML = `<div class="status bad">ACRIS didn't answer</div><div class="msgline">${esc(err.message)}. The workflow fails static in this case: no report, nothing changes.</div>`;
      }
    };
    f.addEventListener("submit", run);
    $$("[data-preset]", root).forEach((p) =>
      p.addEventListener("click", () => {
        const [b, k, l] = p.dataset.preset.split("-");
        f.borough.value = b; f.block.value = k; f.lot.value = l;
        run();
      })
    );
    if (root.hasAttribute("data-autorun")) run();
  });

  /* ---------- live reads from the Sepolia token ---------- */
  const TOKEN = "0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE";
  const RPC = "https://ethereum-sepolia-rpc.publicnode.com";
  const SEL = { restricted: "0x7072c6b1", citedHash: "0xd78d4599", lastDocSetHash: "0x5d9d65a5", expectedWorkflowOwner: "0xc8e9c186", issuerMultisig: "0xc655cb3a", totalSupply: "0x18160ddd", propertyKey: "0xf172667c" };
  const reads = $$("[data-read]");
  if (reads.length) {
    const call = async (sel) => {
      const r = await fetch(RPC, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_call", params: [{ to: TOKEN, data: sel }, "latest"] }) });
      const j = await r.json();
      if (j.error) throw new Error(j.error.message);
      return j.result;
    };
    reads.forEach(async (el) => {
      const fn = el.dataset.read;
      try {
        const v = await call(SEL[fn]);
        let txt = v;
        if (fn === "restricted") txt = BigInt(v) === 1n ? "true" : "false";
        else if (fn === "expectedWorkflowOwner" || fn === "issuerMultisig") txt = "0x" + v.slice(-40);
        else if (fn === "totalSupply") txt = (BigInt(v) / 10n ** 18n).toLocaleString() + " LSPV";
        el.textContent = txt;
        el.classList.add(fn === "restricted" ? (txt === "true" ? "is-red" : "is-ok") : "is-live");
      } catch (e) {
        el.textContent = "read failed (" + e.message + ")";
      }
    });
  }

  addEventListener("load", () => hasGsap && ScrollTrigger.refresh());
})();
