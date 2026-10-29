# Deployment

Deploy your own `LiensightToken` on Sepolia, point the workflow at it, and send it a real report.

**You need:** the [Quickstart](quickstart.md) done, and a Sepolia account with test ETH.

## 1. Create a keystore account

Foundry stores the key encrypted, so it never appears on the command line:

```bash
cast wallet import liensight-deployer --interactive
```

## 2. Set the constructor inputs

```bash
cd contracts
export FORWARDER=0x15fC6ae953E024d975e77382eEeC56A9101f9F88       # CRE simulator forwarder (Sepolia)
export WORKFLOW_OWNER=0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa  # the simulator's placeholder owner
export CODEMAP_HASH=0xf85b55218f5961096bde039896bb3b115179f44c76446ff88e22e3b94326faf3
export ISSUER=<your address>                                       # receives supply, can clear
```

| Variable | Why this value |
|---|---|
| `FORWARDER` | `cre workflow simulate --broadcast` delivers through this forwarder. |
| `WORKFLOW_OWNER` | The simulator stamps reports with this public placeholder owner. |
| `CODEMAP_HASH` | Hash of `codeMap.json` v1 ([Configuration](configuration.md)). |
| `ISSUER` | Use a multisig in production. `msg.sender` in a Foundry script is not the broadcaster, so this is explicit. |

## 3. Deploy

Sepolia charges far more gas for contract code than Foundry’s local estimate, so keep the multiplier:

```bash
forge script script/Deploy.s.sol \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com \
  --account liensight-deployer --broadcast --gas-estimate-multiplier 800
# LiensightToken: 0x…
```

## 4. Point the workflow at it

Set `tokenAddress` in [`workflow/config.staging.json`](../workflow/config.staging.json) to the printed address.

## 5. Broadcast a report

Create `.env` at the repo root with a funded Sepolia key (git-ignored; never commit it):

```bash
CRE_ETH_PRIVATE_KEY=<hex private key of a testnet-only account>
```

Then:

```bash
export PATH="$PWD/workflow/node_modules/.bin:$PATH"
cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0 --broadcast
# [USER LOG] ACRIS docs=14 adverse=2026092900833001:LOCC
# [USER LOG] report written tx=0x…
```

## 6. Confirm

```bash
cast call <token> "restricted()(bool)" --rpc-url https://ethereum-sepolia-rpc.publicnode.com   # true
```

Open the transaction on Etherscan: status Success, and the token’s **Events** tab shows `Restricted` with the cited document.

## Clearing a restriction (issuer)

```bash
H=$(cast call <token> "citedHash()(bytes32)" --rpc-url $RPC)
cast send <token> "clearRestriction(bytes32,string)" $H "Paid; release recorded as <doc id>" \
  --account <issuer-keystore> --rpc-url $RPC
```

If a new lien arrived after you read `citedHash`, the call reverts with `ReviewMismatch()`. Read it again and review the new lien.

## Going to production

1. Deploy the workflow to a CRE DON (`cre account access` is required for deployment).
2. As the issuer, call `setExpectedWorkflowOwner(<deployed workflow owner>)`.
3. Deploy against the production forwarder, not the simulator’s.
