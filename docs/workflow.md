# Workflow reference

The workflow is TypeScript on `@chainlink/cre-sdk`, compiled to WebAssembly by the CRE CLI and run on every node of a DON. Entry point: [`workflow/main.ts`](../workflow/main.ts) → [`workflow/workflow.ts`](../workflow/workflow.ts) (73 lines). Helpers are in [`workflow/src/`](../workflow/src/), each with tests.

## One run, step by step

1. **Trigger.** `CronCapability().trigger({ schedule })` fires on `"0 */10 * * * *"` (cron with seconds: every 10 minutes).
2. **Fetch.** Inside `HTTPClient.sendRequest`, each node runs `fetchDocs`:
   - GET ACRIS **Legals** (`8h5j-fqxa`) for every `document_id` on the BBL.
   - GET ACRIS **Master** (`bnx9-e6tj`) for those IDs’ `doc_type`, 80 IDs per request so URLs stay short.
3. **Fail closed.** Any non-200 status throws; a response with 5,000 rows (the query limit) throws as possibly truncated. No report is written.
4. **Canonicalize.** `canonicalDocs` keeps documents present in both datasets, dedupes, and sorts by ID. The node returns that as JSON.
5. **Consensus.** `consensusIdenticalAggregation<string>()`: every node must return the identical string.
6. **Guard.** `assertNonEmpty` throws on zero documents: a 200 with nothing is more likely an outage or a wrong BBL than a clean lot.
7. **Classify and encode.** `buildReport` splits documents with the code map and ABI-encodes the report. The run logs `ACRIS docs=<n> adverse=<id:type,…|none>`.
8. **Sign.** `runtime.report(prepareReportRequest(payload))`.
9. **Write.** `EVMClient.writeReport({ receiver: tokenAddress, report, gasConfig })` sends it through the forwarder. A non-success status throws; success logs `report written tx=<hash>`.

## Functions

| Function | File | Description |
|---|---|---|
| `main()` | `main.ts` | Creates the CRE `Runner` with the Zod `configSchema` and runs `initWorkflow`. |
| `initWorkflow(config)` | `workflow.ts` | Registers one handler: the cron trigger → `onCronTrigger`. |
| `onCronTrigger(runtime, payload)` | `workflow.ts` | Orchestrates fetch, consensus, report and write; returns the tx hash. |
| `fetchDocs(sendRequester, config)` | `workflow.ts` | Per-node HTTP work; returns canonical JSON. |
| `legalsUrl(bbl)` | `src/acris.ts` | Socrata query for document IDs on a BBL, ordered by ID, limit 5,000. |
| `masterUrl(ids)` | `src/acris.ts` | Socrata query for `doc_type` of the given IDs, ordered, limit 5,000. |
| `canonicalDocs(legals, master)` | `src/acris.ts` | Intersect, dedupe, sort → `AcrisDoc[]`. |
| `docSetHash(docs)` | `src/acris.ts` | `keccak256` of `documentId:docType` lines joined by `\n`. |
| `docIdToBytes32(id)` | `src/acris.ts` | Numeric IDs left-padded to 32 bytes; legacy IDs (`FT_…`, `BK_…`) hashed. |
| `assertComplete(rows)` | `src/acris.ts` | Throws if `rows.length >= 5000`. |
| `assertNonEmpty(docs)` | `src/acris.ts` | Throws if there are no documents. |
| `classify(docs, map)` | `src/classify.ts` | Returns `{ adverse, discharge, other }`. |
| `codeMapHash(map)` | `src/classify.ts` | `keccak256` of the map’s canonical JSON (key order doesn’t matter). |
| `propertyKey(bbl)` | `src/report.ts` | `keccak256("BBL:<borough>-<block>-<lot>")`. |
| `buildReport(bbl, docs, map)` | `src/report.ts` | ABI payload `(bytes32, bytes32, bytes32[], bytes32[])` plus the adverse and discharge lists. |

## Determinism

Consensus only works if every honest node produces the same bytes, so:

- Both queries use `$order=document_id`, so nodes page the same rows.
- `canonicalDocs` sorts and dedupes; `buildReport` is independent of input order (tested).
- No clock, randomness or node-local state enters the result.

## Logs

| Log line | Meaning |
|---|---|
| `ACRIS docs=14 adverse=2026092900833001:LOCC` | 14 documents on the lot; one is adverse |
| `ACRIS docs=12 adverse=none` | Nothing adverse |
| `report written tx=0x…` | Delivered. A zero hash means a dry run (no `--broadcast`). |
| `ACRIS request failed: <status>` | An HTTP error: no report |
| `ACRIS response truncated at 5000 rows` | Possibly incomplete: no report |
| `no ACRIS documents for this BBL; refusing to report` | Empty: no report |

See also: [Configuration](configuration.md) · [Contract reference](contract.md)
