# Liensight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A property-SPV share token whose secondary transfers are restricted automatically when a Chainlink CRE workflow, with DON consensus, sees a new adverse filing for the property in NYC ACRIS.

**Architecture:** A CRE cron workflow has every node independently query the ACRIS Socrata datasets for one BBL, reduce the result to a canonical sorted list of `(documentId, docType)`, and reach consensus on that exact list. The workflow writes a report to a Solidity token; the token compares the list's hash with its stored one, and if a document with an adverse doc-type code is new, sets `restricted = true` with the cited document IDs. Only the issuer multisig can clear. The adverse-code map is a public versioned JSON file whose hash is stored on-chain. An LLM, if used at all, only writes display text and never touches the restrict decision.

**Tech Stack:** Foundry (Solidity ^0.8.24, OpenZeppelin ERC20), CRE SDK (TypeScript) + CRE CLI, Bun/Node + Vitest for pure logic, NYC Open Data Socrata API, Base Sepolia (or whichever testnet the CRE CLI supports).

**Spec:** this plan's Goal/Architecture plus the brainstorm decisions in the chat session of 2026-10-25: name **Liensight**, RWA track, Chainlink CRE bounty target, equity-in-SPV framing (token is not title), restriction is issuer-governed per operating agreement (not a statutory duty), live poll of a real BBL plus recorded backup, consensus on document IDs not on a summary. No standalone spec file exists.

## Global Constraints

- Deadline: 2026-10-31 (about 6 days). Cut scope before cutting the CRE simulation.
- Chainlink bounty needs: a CRE workflow that joins a blockchain to an external API, shown by a successful `cre` CLI simulation or live deploy.
- Framing in all copy: the token is SPV **equity**, never "title" or "deed". The restriction is "issuer-governed transfer restriction", never "legal disclosure duty".
- Consensus is on the set of document IDs and types, never on an LLM output.
- A failed or partial fetch must never set or clear a restriction (fail static).
- Only the issuer multisig can clear a restriction. Clearing is an on-chain event with a reason string.
- The adverse-code map is versioned JSON, and its keccak256 hash is stored on-chain.
- Testnet only. No real funds, no real investor data.
- ACRIS datasets (NYC Open Data): Real Property Master `bnx9-e6tj`, Legals `8h5j-fqxa`, Document Control Codes `7isb-wh4c`. Verify these IDs and the exact column names in Task 2 before coding against them.

## Review Focus

1. BBL with zero ACRIS documents: must return an empty list and not error. The token stays unrestricted.
2. ACRIS 5xx, timeout, or 429 on some nodes: no consensus, so no report is written and state is unchanged.
3. Same document ID returned twice, or in a different order per node: canonicalisation must give identical bytes.
4. A discharge or satisfaction of a previously flagged lien: must not auto-clear. It emits a `ClearSuggested` event and waits for the multisig.
5. Doc type not in the map: ignored as non-adverse, but listed in the report's document set.

---

### Task 1: Repo scaffold and LiensightToken contract

**Files:**
- Create: `contracts/foundry.toml`, `contracts/src/LiensightToken.sol`, `contracts/test/LiensightToken.t.sol`
- Run once: `git init` in `C:\dfol\legalhk` (not a git repo yet)

**Interfaces:**
- Produces:
  - `constructor(string name, string symbol, address issuerMultisig, address reportReceiver, bytes32 codeMapHash)`
  - `function onReport(bytes32 propertyKey, bytes32 docSetHash, bytes32[] calldata newAdverseDocIds, bytes32[] calldata dischargeDocIds) external`, callable only by `reportReceiver`
  - `function clearRestriction(string calldata reason) external`, callable only by `issuerMultisig`
  - `bool public restricted`, `bytes32 public lastDocSetHash`, `bytes32[] public citedDocIds`, `bytes32 public immutable codeMapHash`
  - events `Restricted(bytes32 docSetHash, bytes32[] docIds)`, `Cleared(string reason)`, `ClearSuggested(bytes32[] dischargeDocIds)`
  - transfers revert with `TransferRestricted()` while `restricted`, except mint
- Consumes: nothing.

- [ ] **Step 1: Write failing tests** in `LiensightToken.t.sol`:
  `test_transferWorksWhenUnrestricted`, `test_onReportWithAdverseDocRestrictsTransfers` (expects `TransferRestricted`), `test_onReportFromNonReceiverReverts`, `test_onlyIssuerCanClear`, `test_clearReenablesTransfers`, `test_dischargeEmitsClearSuggestedButStaysRestricted`, `test_unchangedDocSetHashIsNoOp`, `test_emptyAdverseListNeverRestricts`.
- [ ] **Step 2:** Run `forge test --root contracts`. Expected: FAIL (contract missing).
- [ ] **Step 3: Implement** `LiensightToken is ERC20` overriding `_update` (OpenZeppelin v5) for the restriction. `onReport` returns early if `docSetHash == lastDocSetHash`. It restricts only when `newAdverseDocIds.length > 0`. A non-empty `dischargeDocIds` emits `ClearSuggested`.
- [ ] **Step 4:** Run `forge test --root contracts`. Expected: all PASS.
- [ ] **Step 5: Commit** `git add . && git commit -m "feat: LiensightToken with issuer-governed transfer restriction"`

### Task 2: Adverse-code map and classifier

**Files:**
- Create: `workflow/src/codeMap.json`, `workflow/src/classify.ts`, `workflow/src/classify.test.ts`, `workflow/package.json`

**Interfaces:**
- Produces:
  - `type AcrisDoc = { documentId: string; docType: string }`
  - `function classify(docs: AcrisDoc[], map: CodeMap): { adverse: AcrisDoc[]; discharge: AcrisDoc[]; other: AcrisDoc[] }`
  - `function codeMapHash(map: CodeMap): string` (keccak256 of canonical JSON)
  - `codeMap.json` shape: `{ "version": 1, "adverse": [..codes], "discharge": [..codes] }`
- Consumes: nothing.

- [ ] **Step 1:** Fetch the ACRIS Document Control Codes dataset (`7isb-wh4c`) and confirm the exact codes for lis pendens, foreclosure-related filings, mortgages and satisfactions. Put the chosen codes in `codeMap.json` with a comment field citing the dataset. Do not guess codes from memory.
- [ ] **Step 2: Write failing tests** `classify.test.ts`: `classifies lis pendens as adverse`, `classifies satisfaction as discharge`, `unknown code goes to other`, `codeMapHash is stable under key reorder`.
- [ ] **Step 3:** Run `npx vitest run workflow/src/classify.test.ts`. Expected: FAIL.
- [ ] **Step 4: Implement** `classify` and `codeMapHash`. Use a deterministic key-sorted JSON stringify.
- [ ] **Step 5:** Run vitest. Expected: PASS. Commit.

### Task 3: ACRIS fetch and canonicalisation

**Files:**
- Create: `workflow/src/acris.ts`, `workflow/src/acris.test.ts`, `workflow/fixtures/acris-legals.json`, `workflow/fixtures/acris-master.json`

**Interfaces:**
- Consumes: `AcrisDoc` from Task 2.
- Produces:
  - `type Bbl = { borough: 1|2|3|4|5; block: number; lot: number }`
  - `function legalsUrl(bbl: Bbl): string` and `function masterUrl(ids: string[]): string` (Socrata SoQL URLs)
  - `function canonicalDocs(legals: unknown[], master: unknown[]): AcrisDoc[]`, sorted by `documentId`, deduped, and `[]` for empty input
  - `function docSetHash(docs: AcrisDoc[]): string`

- [ ] **Step 1:** Save one real response each from the Legals and Master datasets for a chosen BBL into `fixtures/`. Pick a BBL that has a lis pendens in its history, and note the BBL in the fixture filename.
- [ ] **Step 2: Write failing tests:** `canonicalDocs sorts and dedupes`, `canonicalDocs returns [] for zero rows`, `same docs in different order give same docSetHash`, `legalsUrl encodes borough/block/lot`.
- [ ] **Step 3:** Run vitest. Expected: FAIL.
- [ ] **Step 4: Implement.** Confirm the column names (`borough`, `block`, `lot`, `document_id`, `doc_type`) against the fixture first.
- [ ] **Step 5:** Run vitest. Expected: PASS. Commit.

### Task 4: CRE workflow and simulation

**Files:**
- Create: `workflow/main.ts`, `workflow/config.staging.json`, `workflow/workflow.yaml`, `workflow/project.yaml`
- Modify: `contracts/` deploy script `contracts/script/Deploy.s.sol`

**Interfaces:**
- Consumes: `canonicalDocs`, `docSetHash`, `legalsUrl`, `masterUrl` (Task 3), `classify`, `codeMapHash` (Task 2), `LiensightToken.onReport` (Task 1).
- Produces: a cron-triggered workflow whose config has `{ bbl, tokenAddress, chainSelectorName, schedule }`.

- [ ] **Step 1:** Read the CRE CLI quickstart and the template in `smartcontractkit/cre-templates` that combines an HTTP fetch with an EVM write. Copy its project layout, `cre` CLI commands and consensus API names exactly. Do not invent SDK calls.
- [ ] **Step 2:** Implement the handler. Every node fetches Legals then Master, runs `canonicalDocs`, and the nodes reach consensus on the identical `AcrisDoc[]`. It then reads `lastDocSetHash` from the contract. If the hash is unchanged it writes nothing. Otherwise it runs `classify` and writes the report `(propertyKey, docSetHash, newAdverseDocIds, dischargeDocIds)`. On any fetch error the handler throws and writes nothing.
- [ ] **Step 3:** Deploy `LiensightToken` to the testnet with `Deploy.s.sol`, pass the CRE forwarder as `reportReceiver`, and put the address into `config.staging.json`.
- [ ] **Step 4:** Run `cre workflow simulate` against the fixture BBL. Expected: the simulation completes with a successful write, and `restricted()` reads `true` with the cited document IDs.
- [ ] **Step 5:** Run the simulation against a BBL with no adverse filings. Expected: no write, and `restricted()` stays `false`.
- [ ] **Step 6:** Save the simulation transcript to `docs/simulation-log.md` as bounty evidence. Commit.

### Task 5: Demo and submission

**Files:**
- Create: `demo/index.html` (single static page), `README.md`, `docs/pitch.md`

**Interfaces:**
- Consumes: deployed token address and the simulation log (Task 4).

- [ ] **Step 1:** Build a one-page viewer that reads `restricted`, `citedDocIds` and recent events from the token via a public RPC. Each cited document ID links to its ACRIS page. Add a "Transfer" button that shows the revert reason when restricted.
- [ ] **Step 2:** Add the recorded-backup flow: a script `demo/replay.sh` that runs the simulation against the fixture BBL, so the demo works if live ACRIS is slow.
- [ ] **Step 3:** Write the README and pitch. It needs the one-line answer to "why a DON for one public API?": no issuer or single server can hide or fabricate an adverse filing, and every restriction cites document IDs anyone can verify on ACRIS. State plainly that the token is SPV equity and that the restriction is issuer-governed.
- [ ] **Step 4:** Submit on DoraHacks under the RWA track and apply to the Chainlink CRE bounty. Link the repo, the simulation log and the demo.

## Stretch (only if Days 1-5 finish early)

- Second source (NYC DOF/PLUTO or similar) so consensus compares two sources, not one.
- LLM plain-English summary of each cited document type, display only.

## Schedule

| Day | Work |
|---|---|
| 1 (Oct 25) | Task 1, plus Task 2 step 1 (verify codes) |
| 2 | Tasks 2 and 3 |
| 3 | Task 4 steps 1-3 (CRE project running, contract deployed) |
| 4 | Task 4 steps 4-6 (simulation passing, log saved) |
| 5 | Task 5 steps 1-2 |
| 6 (Oct 30-31) | Task 5 steps 3-4, submit with buffer before the 21:01 UTC-4 deadline |

## Self-review notes

- Spec coverage: equity framing (Global Constraints, Task 5), consensus on IDs (Tasks 3-4), multisig-only clear (Task 1), hash of code map on-chain (Tasks 1-2), live plus recorded demo (Tasks 4-5).
- Open item for the executor: exact CRE SDK calls and ACRIS doc-type codes are deliberately not written here, because they must be taken from the CRE templates and the ACRIS control-codes dataset.
