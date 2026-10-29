# Troubleshooting and FAQ

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `forge test` can’t find `@openzeppelin/...` or `forge-std` | Submodules not cloned | `git submodule update --init --recursive` |
| `cre workflow simulate` fails to build / can’t find `bun` | Bun not on `PATH` | `cd workflow && npm i`, then add `workflow/node_modules/.bin` to `PATH` |
| `cre` asks you to authenticate | Not logged in | `cre login` |
| `ACRIS request failed: <status>` | NYC Open Data unreachable or rate-limited | Retry later. No report is written, by design. |
| `ACRIS response truncated at 5000 rows` | Unusually large lot | By design nothing is written; narrow the query before production use |
| `no ACRIS documents for this BBL` | Wrong borough, block or lot | Check the BBL on [ACRIS](https://a836-acris.nyc.gov/) |
| `report written tx=0x000…000` | Dry run | Add `--broadcast` and set `CRE_ETH_PRIVATE_KEY` in `.env` |
| `writeReport failed` | Unfunded key, RPC error or gas | Fund the key with Sepolia ETH; check the RPC in `project.yaml` |
| Report written, token unchanged | Wrong property key, unexpected workflow owner, or the same `docSetHash` as last time | Match `bbl` with `Deploy.s.sol`; check `expectedWorkflowOwner`; a repeat is a no-op by design |
| Sepolia deploy out of gas | Sepolia prices contract code far above Foundry’s estimate | Keep `--gas-estimate-multiplier 800` |
| `clearRestriction` reverts `ReviewMismatch` | A new lien arrived since you read `citedHash` | Read `citedHash` again and review the new lien |
| The site’s Proof page says “read failed” | Public RPC busy | Refresh, or use the `cast call` commands in [Verification](verification.md) |
| Check page shows nothing | ACRIS slow or the BBL is empty | Retry; confirm the BBL |

## FAQ

**Does the token own the building?**
No. It represents shares in the company (SPV) that owns the building. The restriction comes from the issuer’s own rules, not from property law.

**Why not run one server that checks ACRIS?**
Then that server decides what the chain sees. With CRE, every node reads the record independently, and they must agree before anything is written.

**Can a lien be lifted automatically?**
No. A discharge filing emits `ClearSuggested`. Only the issuer clears, publicly, naming the liens it reviewed.

**What if ACRIS is down?**
The workflow fails closed and writes nothing, so the token keeps its last known state.

**Does it cover lis pendens or foreclosures?**
No. ACRIS has no document type for them (they are court and county-clerk filings).

**Does it work outside New York City?**
Not yet. Any county with open, queryable land records could be added the same way.

**Is personal data stored on-chain?**
No. Only document IDs, document types and hashes.

**Is this production-ready?**
No. It is a testnet build: reports came through the CRE simulator, and consensus ran in the local simulator. [Deployment](deployment.md#going-to-production) lists what production needs.

**Is this legal advice?**
No. It flags public filings early; it does not judge their legal effect.
