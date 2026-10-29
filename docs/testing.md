# Testing

35 tests: 18 for the contract (Foundry) and 17 for the workflow logic (Vitest).

```bash
cd contracts && forge test          # 18 passed
cd workflow && npm test             # 17 passed (3 files)
forge test -vvv --match-test test_onReportWithAdverseDocRestrictsTransfers   # one test, with traces
```

## Contract: `contracts/test/LiensightToken.t.sol`

| Test | Proves |
|---|---|
| `test_transferWorksWhenUnrestricted` | Normal ERC-20 behavior before any lien |
| `test_onReportWithAdverseDocRestrictsTransfers` | An adverse report restricts and blocks transfers |
| `test_onReportFromNonReceiverReverts` | Only the forwarder can report |
| `test_onlyIssuerCanClear` | Nobody else can lift a restriction |
| `test_clearReenablesTransfers` | Clearing restores transfers |
| `test_dischargeEmitsClearSuggestedButStaysRestricted` | A release only suggests a clear |
| `test_unchangedDocSetHashIsNoOp` | Replaying the same document set changes nothing |
| `test_emptyAdverseListNeverRestricts` | Clean lots never restrict |
| `test_clearedLienDoesNotRestrictAgainOnUnrelatedFiling` | A reviewed lien can’t re-lock the token |
| `test_newLienAfterClearRestrictsAgain` | A genuinely new lien still restricts |
| `test_supportsReceiverInterface` | ERC-165 / CRE `IReceiver` support |
| `test_reportFromWrongWorkflowOwnerReverts` | Other workflows on the shared forwarder are rejected |
| `test_shortMetadataReverts` | Malformed metadata is rejected |
| `test_reportForWrongPropertyReverts` | Reports for another building are rejected |
| `test_clearWithStaleReviewedHashReverts` | The issuer can’t clear liens it didn’t review |
| `test_manyNewAdverseDocsFitInGasBudget` | Many liens in one report fit the gas limit |
| `test_issuerCanRotateExpectedWorkflowOwner` | The issuer can move to a deployed workflow |
| `test_nonIssuerCannotRotateWorkflowOwner` | Nobody else can |

## Workflow: `workflow/src/*.test.ts`

| File | Tests |
|---|---|
| `acris.test.ts` (10) | Canonical sort and dedupe · zero rows → `[]` · document-set hash independent of order · Legals URL encodes the BBL · Master URL lists IDs · numeric ID padding is reversible · legacy `FT_`/`BK_` IDs don’t throw · queries are ordered so nodes page the same rows · 5,000-row limit fails closed · zero documents refuse to report |
| `classify.test.ts` (4) | Federal lien and judgment are adverse · release of federal lien is a discharge · unknown codes are “other” · code-map hash is stable under key reorder |
| `report.test.ts` (3) | Encodes key, hash, adverse and discharge IDs · empty lists encode empty arrays · identical regardless of input order (determinism for consensus) |

## End-to-end

The CRE simulations against live ACRIS are the integration test ([Quickstart](quickstart.md#5-simulate-the-workflow-against-live-acris)). Their recorded output, including the Sepolia broadcast and the on-chain checks afterwards, is in [simulation-log.md](simulation-log.md). Recorded ACRIS responses for the demo lot are in [`workflow/fixtures/`](../workflow/fixtures/), with document IDs and types only, no party names.
