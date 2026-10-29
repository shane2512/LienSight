# Contract reference: `LiensightToken`

[`contracts/src/LiensightToken.sol`](../contracts/src/LiensightToken.sol): an OpenZeppelin v5.1 ERC-20 (Solidity 0.8.24) for shares in the company (SPV) that owns the building. It is **not** title to the property. A CRE workflow reports ACRIS document sets; adverse filings restrict transfers until the issuer clears.

Deployed on Sepolia at [`0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE`](https://sepolia.etherscan.io/address/0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE).

## Constructor

```solidity
constructor(
  string name_, string symbol_,
  address issuerMultisig_,          // receives 1,000,000 tokens; can clear and rotate the owner
  address reportReceiver_,          // the Chainlink forwarder allowed to call onReport
  bytes32 codeMapHash_,             // hash of workflow/src/codeMap.json
  address expectedWorkflowOwner_,   // only this workflow owner's reports are accepted
  bytes32 propertyKey_              // keccak256("BBL:<borough>-<block>-<lot>")
)
```

## Functions

| Function | Caller | Behavior |
|---|---|---|
| `onReport(bytes metadata, bytes report)` | Forwarder only | See [onReport](#onreport) below. |
| `clearRestriction(bytes32 reviewedCitedHash, string reason)` | Issuer only | Reverts `ReviewMismatch` unless `reviewedCitedHash == citedHash`. Sets `restricted = false`, resets `citedHash`, emits `Cleared(reason)`. |
| `setExpectedWorkflowOwner(address newOwner)` | Issuer only | Rotates the accepted workflow owner, for example from the simulator to a deployed workflow. |
| `supportsInterface(bytes4 id)` | Anyone | True for `0x805f2132` (CRE `IReceiver`) and `0x01ffc9a7` (ERC-165). |
| ERC-20 `transfer`, `transferFrom` | Holders | Revert `TransferRestricted` while `restricted` (minting excepted, via `_update`). |

### onReport

1. `msg.sender` must equal `reportReceiver`, otherwise `NotReceiver`.
2. `metadata` must be at least 62 bytes (`workflowId (32) | workflowName (10) | workflowOwner (20)`), otherwise `BadMetadata`.
3. The owner in bytes 42–62 must equal `expectedWorkflowOwner`, otherwise `WrongWorkflowOwner`.
4. Decode `(bytes32 key, bytes32 docSetHash, bytes32[] adverse, bytes32[] discharge)`; `key` must equal `propertyKey`, otherwise `WrongProperty`.
5. If `docSetHash == lastDocSetHash`, return: nothing changed.
6. Record `lastDocSetHash`. For each adverse ID not yet in `seenAdverse`, mark it seen and collect it.
7. If any were new: `restricted = true`, `citedHash = keccak256(abi.encode(newIds))`, emit `Restricted(docSetHash, newIds)`.
8. If `discharge` is non-empty, emit `ClearSuggested(discharge)`. It does **not** clear.

## State

| Variable | Type | Meaning |
|---|---|---|
| `restricted` | `bool` | Transfers blocked |
| `citedHash` | `bytes32` | Hash of the liens behind the current restriction (full list in the `Restricted` event) |
| `lastDocSetHash` | `bytes32` | Last processed document set |
| `seenAdverse` | `mapping(bytes32 => bool)` | Every adverse document ever reported |
| `expectedWorkflowOwner` | `address` | The accepted workflow owner |
| `issuerMultisig`, `reportReceiver`, `codeMapHash`, `propertyKey` | immutable | Set at deploy |

## Events

| Event | When |
|---|---|
| `Restricted(bytes32 docSetHash, bytes32[] docIds)` | A report brought at least one new adverse document |
| `Cleared(string reason)` | The issuer cleared the restriction |
| `ClearSuggested(bytes32[] dischargeDocIds)` | A report contained discharge filings |

## Errors

| Error | Selector meaning |
|---|---|
| `TransferRestricted()` | A transfer while restricted (`0xe827105e`) |
| `NotReceiver()` | `onReport` not called by the forwarder |
| `NotIssuer()` | An issuer-only function called by someone else |
| `BadMetadata()` | Metadata shorter than 62 bytes |
| `WrongWorkflowOwner()` | Report from an unexpected workflow owner |
| `WrongProperty()` | Report for a different property key |
| `ReviewMismatch()` | `clearRestriction` named a stale `citedHash` |

## Reading the live token

```bash
RPC=https://ethereum-sepolia-rpc.publicnode.com
TOKEN=0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE
cast call $TOKEN "restricted()(bool)" --rpc-url $RPC
cast call $TOKEN "citedHash()(bytes32)" --rpc-url $RPC
cast call $TOKEN "expectedWorkflowOwner()(address)" --rpc-url $RPC
cast call $TOKEN "codeMapHash()(bytes32)" --rpc-url $RPC
```

See also: [Security model](security.md) · [Deployment](deployment.md)
