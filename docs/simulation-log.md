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
