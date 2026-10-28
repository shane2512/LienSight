# Liensight

Early-warning transfer restriction for a property-SPV token, driven by public ACRIS filings through Chainlink CRE.

**Track:** RWA. **Bounty:** Chainlink, Best workflow with CRE. Built for BLI Legal Tech Hackathon 2.

## What it does
`LiensightToken` is SPV **equity** (not title to property) with an issuer-governed transfer restriction. A Chainlink CRE workflow makes every DON node query NYC ACRIS independently for one property (BBL). The nodes must agree on the exact set of `(documentId, docType)`. The workflow sends the result as a report to the token. A new adverse filing restricts transfers and cites the document IDs. Only the issuer multisig can clear it, and a discharge filing only emits `ClearSuggested`.

**Adverse types** (verified against ACRIS Document Control Codes, dataset `7isb-wh4c`): `FL, FTL, NTXL, TLS, LOCC, JUDG`. ACRIS has no lis pendens or foreclosure type (those are court and county-clerk filings), so we do not claim them. The map is versioned in `workflow/src/codeMap.json`; its hash is stored on the token.

## Why a DON for one public API?
No single server or operator decides what the chain sees, and every restriction cites document IDs anyone can check on ACRIS. The issuer multisig can still clear a restriction, but only by naming the exact set of liens it reviewed (`clearRestriction(citedHash, reason)`).

## Layout
- `contracts/`: Foundry. `forge test` runs 18 tests.
- `workflow/`: CRE workflow (`main.ts`, `workflow.ts`) and tested logic in `src/`. `npm test` runs 17 tests.
- `demo/`: the website. `index.html` (landing), `check.html` (live ACRIS check with the same adverse map), `how-it-works.html`, `evidence.html` (reads the token's live state from Sepolia). Serve it with `python -m http.server 5173 --directory demo`. Add `?motion=1` to force animations when the browser reports reduced motion. `demo/replay.sh` re-runs the CRE simulations.
- `docs/simulation-log.md`: CRE CLI simulation evidence.

## Run
```
cd contracts && forge test
cd workflow && npm i && npm test
cre login   # once
bash demo/replay.sh   # needs bun on PATH (npm i -D bun is in workflow/)
```

## Live on Sepolia (simulator broadcast)
Token `0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE`. Report tx `0xc0cc238205a36246731feddba275b3df50b4c781f3958b8d4cab8a862bda85ab`. After the report, `restricted()` is `true` and the cited-lien hash matches the ACRIS document `2026092900833001` (LOCC). See `docs/simulation-log.md`.

## Security notes
- The CRE forwarder is shared by all workflows, so the token only accepts reports from the expected workflow owner and the expected property key (constructor args `expectedWorkflowOwner`, `propertyKey`).
- The workflow refuses to report on a truncated ACRIS response (5000-row limit) or on a property with zero documents.

## Honest limits
- DON consensus was only exercised in the local simulator (single node), not on a live DON.
- The report was written via `cre workflow simulate --broadcast` with Chainlink's mock forwarder, not a deployed CRE workflow. The simulator uses a public placeholder workflow owner (`0xaaaa...aaaa`), so anyone using the mock forwarder could send reports to this demo token. A production setup would call `setExpectedWorkflowOwner` with the real deployed workflow's owner and use the production KeystoneForwarder (needs `cre account access`).
- Sepolia charges far more gas for contract code than Foundry's local estimate; deploying needs `--gas-estimate-multiplier 800`.
- ACRIS records lag real events by days. This is an early-warning signal, not a title search.
- One public source today. A second source (NYC DOF) is a stretch goal.
- Fixtures contain document IDs and types only, no party names.
