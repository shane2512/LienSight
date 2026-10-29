# Verifying the live deployment

Every claim about the Sepolia token can be checked independently. Steps 1–3 need only a browser.

## In a browser

1. **The lien in the public record.** Open https://liensight.vercel.app/check.html and click **Bronx 2-5789-1022 · has a lien**. The page reads ACRIS live and shows one adverse filing: `LOCC 2026092900833001`, recorded 2026-09-30. Cross-check on [ACRIS](https://a836-acris.nyc.gov/) by searching that document ID.
2. **The report on-chain.** Open the [token’s events](https://sepolia.etherscan.io/address/0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE#events). The `report(...)` call carries the document-set hash the nodes agreed on (`0xde6f…3948`).
3. **The restriction.** Open https://liensight.vercel.app/proof.html, which reads `restricted()` from Sepolia in your browser.

## From a terminal (Foundry)

```bash
RPC=https://ethereum-sepolia-rpc.publicnode.com
TOKEN=0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE

cast call $TOKEN "restricted()(bool)" --rpc-url $RPC              # true
cast call $TOKEN "citedHash()(bytes32)" --rpc-url $RPC            # 0xb87dc80e…49f4
cast call $TOKEN "reportReceiver()(address)" --rpc-url $RPC       # 0x15fC6ae9…9F88 (CRE forwarder)
cast call $TOKEN "codeMapHash()(bytes32)" --rpc-url $RPC          # 0xf85b5521…4326faf3

# even the issuer cannot move shares: reverts with TransferRestricted() (0xe827105e)
cast call $TOKEN "transfer(address,uint256)(bool)" 0x000000000000000000000000000000000000dEaD 1 \
  --from 0xd51E7130B55f10595939f274cCB8c00b52C915b4 --rpc-url $RPC
```

## Tie the restriction to the ACRIS document

`citedHash` is `keccak256(abi.encode(bytes32[]))` of the cited IDs. Recompute it for the one cited document:

```bash
cast keccak $(cast abi-encode "f(bytes32[])" "[$(cast to-uint256 2026092900833001 | cast to-bytes32)]")
# matches citedHash(): 0xb87dc80ef6af1d3f62a75f819a8065410a69b6bd888cd54d725b6d0cab6d49f4
```

## Tie the token to the published policy

The adverse map’s hash is fixed in the token. Recompute it from the repo:

```bash
cd workflow
npx bun -e "import {codeMapHash} from './src/classify'; import m from './src/codeMap.json'; console.log(codeMapHash(m))"
# 0xf85b55218f5961096bde039896bb3b115179f44c76446ff88e22e3b94326faf3 == codeMapHash()
```

## Deployment record

| Item | Value |
|---|---|
| Token | `0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE` |
| Deploy tx | [`0xb27c9ed1…69c4d9`](https://sepolia.etherscan.io/tx/0xb27c9ed1891c763325412789f3d05e1d221584353186e80eb9ad31ea9769c4d9) |
| First restricting report | [`0xc0cc2382…bda85ab`](https://sepolia.etherscan.io/tx/0xc0cc238205a36246731feddba275b3df50b4c781f3958b8d4cab8a862bda85ab) |
| Report in the demo video | [`0x5e301044…160d94`](https://sepolia.etherscan.io/tx/0x5e301044fbb77ae37e096d0752208fa19f6e0d23f8292a2bbc45217aff160d94) |
| Forwarder | `0x15fC6ae953E024d975e77382eEeC56A9101f9F88` (CRE simulator) |
| Expected workflow owner | `0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa` (simulator placeholder) |
| Issuer | `0xd51E7130B55f10595939f274cCB8c00b52C915b4` |
| Property key | `keccak256("BBL:2-5789-1022")` |

Raw CLI output: [simulation-log.md](simulation-log.md).
