# CRE simulation log (cre-cli v1.2.0, 2026-10-25, dry-run: no --broadcast)

## Run 1: BBL 2-5789-1022 (property with a recorded LOCC)
```
✓ Workflow compiled
2026-10-25T14:40:28Z [SIMULATION] Simulator Initialized
2026-10-25T14:40:28Z [SIMULATION] Running trigger trigger=cron-trigger@1.0.0
2026-10-25T14:40:36Z [USER LOG] ACRIS docs=14 adverse=2026092900833001:LOCC
2026-10-25T14:40:36Z [USER LOG] report written tx=0x0000000000000000000000000000000000000000000000000000000000000000
✓ Workflow Simulation Result:
2026-10-25T14:40:36Z [SIMULATION] Execution finished signal received
2026-10-25T14:40:36Z [SIMULATION] Skipping WorkflowEngineV2
```

## Run 2: BBL 1-905-1347 (no adverse documents)
```
✓ Workflow compiled
2026-10-25T14:41:33Z [SIMULATION] Simulator Initialized
2026-10-25T14:41:33Z [SIMULATION] Running trigger trigger=cron-trigger@1.0.0
2026-10-25T14:41:35Z [USER LOG] ACRIS docs=12 adverse=none
2026-10-25T14:41:36Z [USER LOG] report written tx=0x0000000000000000000000000000000000000000000000000000000000000000
✓ Workflow Simulation Result:
2026-10-25T14:41:36Z [SIMULATION] Execution finished signal received
2026-10-25T14:41:36Z [SIMULATION] Skipping WorkflowEngineV2
```

Notes: the report write is a dry run (zero tx hash). Each run fetched live NYC ACRIS data through the DON HTTP capability with identical-consensus aggregation. Contract-side restrict/clear behavior is covered by 11 forge tests.


## Run 3: live broadcast to Sepolia (cre simulate --broadcast, mock forwarder)
- Token: `0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE` (Sepolia), deploy tx `0xb27c9ed1891c763325412789f3d05e1d221584353186e80eb9ad31ea9769c4d9`
- Report tx: `0xc0cc238205a36246731feddba275b3df50b4c781f3958b8d4cab8a862bda85ab` (status success, forwarder ReportProcessed = true)
- Workflow log: `ACRIS docs=14 adverse=2026092900833001:LOCC`, report written.
- Verified on-chain afterwards (cast): `restricted() = true`; `citedHash() = 0xb87dc80e...49f4`, equal to keccak256(abi.encode([2026092900833001])) computed independently; issuer `transfer` call reverts with `TransferRestricted()` (0xe827105e).
- Note: the simulator stamps reports with a placeholder workflow owner (`0xaaaa...aaaa`), so the token was deployed expecting that owner. Earlier attempts: a first token expecting the deployer as owner correctly ignored the simulator report (forwarder logged success=false).
