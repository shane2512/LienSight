---
workflow: general-video
flow: automation
storyboard: no
message: "A lien lands on a New York building and the token finds out: Liensight restricts transfers automatically, proven live on Sepolia."
destination: hackathon pitch (BLI Legal Tech Hackathon 2, DoraHacks) + showreel
aspect: 16:9 (1920x1080, 30fps)
language: en
audience: hackathon judges
length: under 3 minutes
---

## Intent
A professional-grade motion-graphic pitch, not a slideshow. Must cover: the problem, why it is being built, how it works, a LIVE DEMO that is a genuine screen recording (real Chrome and real terminal, real cursor, real transaction), why it fits the hackathon (RWA track, Chainlink CRE bounty requirement, tests, security review), honest limits, roadmap.

## Assets
- Voiceover: Fish Audio, voice 76e8d2175bc44e29be9885fb67a2b43a (assets/vo/*.mp3, script in narration.json).
- Real screen recordings (assets/footage): real Chrome window (checker + Etherscan), real Windows Terminal (forge, vitest, cre simulate --broadcast, cast). Only speed changes (terminal compile wait labelled on screen); no synthetic UI.

## Customizations
- Visual world taken from the Liensight landing page: sky gradient, drifting clouds, stipple headline, white cards, red accent; Archivo / Inter Tight / JetBrains Mono / Caveat.
- GSAP for all motion; one continuous world with camera moves, tone shifts (sky -> ink -> sky -> red -> sky).

## Notes
- No invented statistics. Numbers used: 16 submissions (our read, at time of writing), 14 ACRIS documents, 35 tests (18 + 17), 1 critical + 5 important review findings fixed.
- Honest limits stated: testnet via CRE simulator, ACRIS lag, no lis pendens in ACRIS.
