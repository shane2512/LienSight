# Liensight

Chain-enforced warning when a lien hits the property behind your token.

**Track:** RWA. **Bounty:** Chainlink, Best workflow with CRE. Built for BLI Legal Tech Hackathon 2.

## What it does
`LiensightToken` is SPV **equity** (not title to property) with an issuer-governed transfer restriction. A Chainlink CRE workflow makes every DON node query NYC ACRIS independently for one property (BBL). The nodes must agree on the exact set of `(documentId, docType)`. The workflow sends the result as a report to the token. A new adverse filing restricts transfers and cites the document IDs. Only the issuer multisig can clear it, and a discharge filing only emits `ClearSuggested`.

**Adverse types** (verified against ACRIS Document Control Codes, dataset `7isb-wh4c`): `FL, FTL, NTXL, TLS, LOCC, JUDG`. ACRIS has no lis pendens or foreclosure type (those are court and county-clerk filings), so we do not claim them. The map is versioned in `workflow/src/codeMap.json`; its hash is stored on the token.

## Why a DON for one public API?
No issuer or single server can hide or fabricate an adverse filing, and every restriction carries document IDs anyone can check on ACRIS.

## Layout
- `contracts/`: Foundry. `forge test` runs 11 tests.
- `workflow/`: CRE workflow (`main.ts`, `workflow.ts`) and tested logic in `src/`. `npm test` runs 13 tests.
- `demo/index.html`: live ACRIS check using the same adverse map. `demo/replay.sh` re-runs the CRE simulations.
- `docs/simulation-log.md`: CRE CLI simulation evidence.

## Run
```
cd contracts && forge test
cd workflow && npm i && npm test
cre login   # once
bash demo/replay.sh   # needs bun on PATH (npm i -D bun is in workflow/)
```

## Honest limits
- Report write is simulated (dry run); no live deployment yet. Deploy needs a funded Sepolia key and `cre account access`.
- ACRIS records lag real events by days. This is an early-warning signal, not a title search.
- One public source today. A second source (NYC DOF) is a stretch goal.
- Fixtures contain document IDs and types only, no party names.
