# Configuration

## Targets

[`workflow/workflow.yaml`](../workflow/workflow.yaml) defines two CRE targets. RPC endpoints per target live in [`project.yaml`](../project.yaml).

| Target | Workflow name | Config | Watches |
|---|---|---|---|
| `staging-settings` | `liensight-staging` | [`config.staging.json`](../workflow/config.staging.json) | Bronx `2-5789-1022` (has a lien), writes to the live token |
| `clean-settings` | `liensight-clean` | [`config.clean.json`](../workflow/config.clean.json) | Manhattan `1-905-1347` (clean), placeholder receiver, for comparison runs |

## Config keys

Validated at start-up by the Zod `configSchema` in `workflow.ts`.

| Key | Type | Example | Meaning |
|---|---|---|---|
| `schedule` | string | `"0 */10 * * * *"` | Cron with seconds; every 10 minutes |
| `bbl.borough` | int 1–5 | `2` | 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens, 5 Staten Island |
| `bbl.block` | int | `5789` | Tax block |
| `bbl.lot` | int | `1022` | Tax lot |
| `tokenAddress` | string | `0xf813…04aE` | Receiver contract |
| `chainSelectorName` | string | `ethereum-testnet-sepolia` | Target chain |
| `gasLimit` | string | `"10000000"` | Gas for the write |

## Watching a different property

1. Find the BBL by searching the address on [ACRIS](https://a836-acris.nyc.gov/).
2. Set `bbl` in the config.
3. Change the `BBL:` string in [`contracts/script/Deploy.s.sol`](../contracts/script/Deploy.s.sol) to match, for example `keccak256(bytes("BBL:3-1234-56"))`.
4. Deploy a new token ([Deployment](deployment.md)) and set `tokenAddress`.

The token rejects reports for any other property key (`WrongProperty`), so steps 2 and 3 must agree.

## The adverse map

[`workflow/src/codeMap.json`](../workflow/src/codeMap.json), version 1, verified against ACRIS Document Control Codes (dataset `7isb-wh4c`).

| List | Codes | Effect |
|---|---|---|
| `adverse` | `FL` federal lien (IRS), `FTL` federal lien (other), `NTXL` notice of estate tax lien, `TLS` tax lien sale certificate, `LOCC` lien of common charges, `JUDG` judgment | Restricts transfers |
| `discharge` | `RFL`, `RFTL`, `DTL`, `DPFTL`, `WFL`, `RTXL`, `TOLCC`, `PWFL`, `PRFL` | Emits `ClearSuggested`; never clears |

ACRIS has no type for lis pendens or foreclosure, so they are out of scope.

After changing the map, recompute its hash and deploy a token with it:

```bash
cd workflow
npx bun -e "import {codeMapHash} from './src/classify'; import m from './src/codeMap.json'; console.log(codeMapHash(m))"
# version 1: 0xf85b55218f5961096bde039896bb3b115179f44c76446ff88e22e3b94326faf3
```

## Secrets

Only broadcasting needs one: `CRE_ETH_PRIVATE_KEY` in a `.env` file at the repo root, read by the CRE CLI. `.env` is git-ignored. Never commit it, and use a dedicated testnet key.
