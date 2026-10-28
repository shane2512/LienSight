// Liensight site: shared nav/footer, reveal-on-scroll, and the landing-page scroll animations.
(() => {
  const MARK = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M2 10.5 12 3l10 7.5V21h-7v-6.5H9V21H2z"/><path d="M12 3v8l10-.5z" opacity=".55"/></svg>`;
  const page = document.body.dataset.page;
  const links = [
    ["index.html", "Home", "home"],
    ["how-it-works.html", "How it works", "how"],
    ["check.html", "Check a property", "check"],
    ["evidence.html", "Evidence", "evidence"],
  ];

  const nav = document.getElementById("nav");
  if (nav) {
    nav.className = "nav";
    nav.innerHTML = `<div class="wrap">
      <a class="logo" href="index.html" aria-label="Liensight home">${MARK}Liensight</a>
      <nav class="nav-links" aria-label="Main">${links
        .map(([href, label, key]) => `<a href="${href}"${key === page ? ' aria-current="page"' : ""}>${label}</a>`)
        .join("")}</nav>
      <a class="btn" href="check.html">Check a property</a>
    </div>`;
    const onScroll = () => nav.classList.toggle("scrolled", scrollY > 8);
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  const footer = document.getElementById("footer");
  if (footer) {
    footer.className = "footer";
    footer.innerHTML = `<div class="wrap">
      <a class="logo" href="index.html">${MARK}Liensight</a>
      <p>Liensight is a hackathon prototype built for the BLI Legal Tech Hackathon 2. It runs on the Ethereum Sepolia testnet. No real funds, securities or investors are involved, and nothing on this site is legal, financial or title advice.</p>
      <p>The token represents equity in a property-owning SPV, not title to property. Transfer restrictions are issuer-governed under the SPV's operating agreement, not a statutory duty. The issuer multisig can clear a restriction by naming the exact liens it reviewed.</p>
      <p>Filing data comes from NYC ACRIS via NYC Open Data. ACRIS records can lag real events by days, and ACRIS has no lis pendens or foreclosure document type. Treat Liensight as an early-warning signal, not a title search.</p>
      <p>Reports were written through the Chainlink CRE simulator with the mock forwarder. A production deployment would use a deployed CRE workflow and the production KeystoneForwarder.</p>
      <div class="bottom"><span>© 2026 Liensight. Testnet prototype.</span>
        <span><a href="how-it-works.html#limits">Honest limits</a><a href="evidence.html">Evidence</a></span></div>
    </div>`;
  }

  // reveal on scroll
  const io = new IntersectionObserver(
    (es) => es.forEach((e) => e.isIntersecting && (e.target.classList.add("in"), io.unobserve(e.target))),
    { threshold: 0.15 },
  );
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  if (page !== "home") return;
  // ?motion=1 forces animation on (handy for previews that report reduced motion)
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches && !/[?&]motion=1/.test(location.search);

  // ---- hero card flip: keyframes over scroll progress ----
  const card = document.querySelector(".card-stage .tcard");
  const zone = document.querySelector(".flip-zone");
  const hero = document.querySelector(".hero");
  // p, rotateX, rotateY, rotateZ, translateY(vh), scale
  const K = [
    [0.0, 24, 96, -16, -6, 1.06],
    [0.28, 12, 168, -34, 2, 1.02],
    [0.55, 8, 214, -22, 3, 1],
    [0.82, 2, 318, -6, 1, 1],
    [1.0, 0, 360, 0, 0, 1],
  ];
  const ease = (t) => t * t * (3 - 2 * t);
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v) => Math.min(1, Math.max(0, v));
  function cardAt(p) {
    let i = 0;
    while (i < K.length - 2 && p > K[i + 1][0]) i++;
    const [a, b] = [K[i], K[i + 1]];
    const t = ease(clamp((p - a[0]) / (b[0] - a[0])));
    const v = a.map((x, j) => lerp(x, b[j], t));
    return `translateY(${v[4]}vh) rotateX(${v[1]}deg) rotateY(${v[2]}deg) rotateZ(${v[3]}deg) scale(${v[5]})`;
  }

  // ---- coverage fan ----
  const cov = document.querySelector(".coverage");
  const [c1, c2, c3] = [".fan .c1", ".fan .c2", ".fan .c3"].map((s) => document.querySelector(s));

  // ---- how-it-works widgets parallax ----
  const how = document.querySelector(".how");
  const widgets = [...document.querySelectorAll(".how .widget")];

  function frame() {
    if (card && zone && hero) {
      const end = hero.offsetHeight + innerHeight * 0.3;
      card.style.transform = cardAt(reduce ? 1 : clamp(scrollY / end));
    }
    if (cov && c2 && innerWidth > 900 && !reduce) {
      const r = cov.getBoundingClientRect();
      const p = clamp(-r.top / (r.height - innerHeight));
      c2.style.transform = `rotate(${lerp(-12, -4, p)}deg) translateX(${lerp(0, 22, p)}%) scale(${lerp(1, 1.32, p)})`;
      c1.style.transform = `rotate(-12deg) translate(${lerp(14, 30, p)}%, ${lerp(0, -30, p)}%)`;
      c3.style.transform = `rotate(-12deg) translate(${lerp(10, 26, p)}%, ${lerp(0, 30, p)}%)`;
    }
    if (how && !reduce) {
      const r = how.getBoundingClientRect();
      const p = (innerHeight - r.top) / (innerHeight + r.height) - 0.5;
      widgets.forEach((w, i) => (w.style.transform = `translateY(${p * (i % 2 ? -60 : 60)}px)`));
    }
    ticking = false;
  }
  let ticking = false;
  const req = () => !ticking && ((ticking = true), requestAnimationFrame(frame));
  addEventListener("scroll", req, { passive: true });
  addEventListener("resize", req);
  frame();
})();
