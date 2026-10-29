# Security model

## Assets and roles

| Role | Can do | Cannot do |
|---|---|---|
| CRE workflow (via forwarder) | Restrict transfers by reporting a new adverse filing | Clear a restriction; report for another property |
| Issuer multisig | Clear a restriction it has reviewed; rotate the workflow owner | Clear without naming the current `citedHash`; stop a new lien from restricting |
| Holders | Transfer while unrestricted | Transfer while restricted |
| Anyone else | Read state | Call `onReport` or issuer functions |

## Threats and mitigations

| Threat | Mitigation | Tested by |
|---|---|---|
| Anyone calls `onReport` | Only `reportReceiver` (the forwarder) → `NotReceiver` | `test_onReportFromNonReceiverReverts` |
| Another workflow uses the shared forwarder | Owner in metadata must equal `expectedWorkflowOwner` → `WrongWorkflowOwner` | `test_reportFromWrongWorkflowOwnerReverts` |
| A report for a different building | `propertyKey` must match → `WrongProperty` | `test_reportForWrongPropertyReverts` |
| Malformed metadata | Under 62 bytes → `BadMetadata` | `test_shortMetadataReverts` |
| Replay of an old report | Same `docSetHash` is a no-op | `test_unchangedDocSetHashIsNoOp` |
| An outage reads as “clean” | Workflow fails closed on errors, truncation and zero documents | `assertComplete`, `assertNonEmpty` tests |
| One node lies or sees different data | Identical consensus: no agreement, no report | By construction (CRE) |
| Clearing a lien nobody reviewed | `clearRestriction` needs the current `citedHash` → `ReviewMismatch` | `test_clearWithStaleReviewedHashReverts` |
| A reviewed lien re-locks the token | `seenAdverse` | `test_clearedLienDoesNotRestrictAgainOnUnrelatedFiling` |
| Too many liens to process | Bounded loop, tested gas | `test_manyNewAdverseDocsFitInGasBudget` |
| Silent policy change | `codeMapHash` fixed in the token | Recompute: [Verification](verification.md) |

A pre-deployment security review found **1 critical and 5 important** issues. All were fixed before deployment and are covered by the tests above.

## Known limitations

- **Simulator trust.** The demo token accepts the CRE simulator’s public placeholder owner, so anyone using the simulator forwarder could report to it. Production rotates `expectedWorkflowOwner` to a deployed workflow’s owner and uses the production forwarder.
- **Single source.** Every node reads the same public API, so consensus protects against faulty nodes, not against wrong data at the source.
- **Issuer power.** The issuer can clear. That is deliberate (a lien may be paid or disputed) and constrained: the clear is public, names the reviewed liens, and states a reason.
- **Lag.** ACRIS records filings days after the event.

## Secrets

- No keys are in the repository. `.env` (which holds `CRE_ETH_PRIVATE_KEY` for broadcasting) is git-ignored.
- Deployment signs with an encrypted Foundry keystore (`--account`), never a raw key on the command line.
- Use testnet-only keys for this project.

## Privacy

Only document IDs, document types and hashes go on-chain or into fixtures. No party names or personal data.

## Reporting an issue

Open an issue on [GitHub](https://github.com/shane2512/LienSight/issues). For anything sensitive, contact the maintainer privately instead of posting details publicly.
