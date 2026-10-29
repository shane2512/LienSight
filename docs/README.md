# Liensight documentation

Liensight restricts a real-estate token’s transfers when a lien is recorded against the building. A Chainlink CRE workflow reads New York City’s public land records (ACRIS), the nodes agree on what they say, and a signed report tells the token on-chain.

Start with the **[Quickstart](quickstart.md)**. It runs every test and a live workflow simulation in about ten minutes.

## Guides

| Page | Read it when you want to |
|---|---|
| [Quickstart](quickstart.md) | Install, test and simulate the workflow from a fresh clone |
| [Verifying the live deployment](verification.md) | Check the Sepolia token, report and restriction yourself, with or without tools |
| [Deployment](deployment.md) | Deploy your own token and point the workflow at it |
| [Configuration](configuration.md) | Watch a different property, change the schedule or the document-type map |
| [Testing](testing.md) | Know what each of the 35 tests proves and how to run them |
| [Troubleshooting and FAQ](troubleshooting.md) | Fix a failing step, or get a straight answer to a common question |

## Reference

| Page | What it covers |
|---|---|
| [Architecture](architecture.md) | Components, data flow, trust boundaries and design decisions |
| [Workflow reference](workflow.md) | `workflow.ts` step by step: trigger, HTTP fetch, consensus, report, write |
| [Contract reference](contract.md) | `LiensightToken`: state, functions, events, errors, report format |
| [Security model](security.md) | Threats, the checks that stop them, and what is out of scope |
| [Glossary](glossary.md) | BBL, ACRIS, DON, forwarder, docSetHash and other terms |

## Evidence and appendices

| Page | What it is |
|---|---|
| [Simulation log](simulation-log.md) | Raw CRE CLI output: two dry runs and the Sepolia broadcast |
| [Demo recording guide](demo-recording-guide.md) | How the demo video’s screen recordings were captured |

## At a glance

| | |
|---|---|
| **Chain** | Ethereum Sepolia (testnet) |
| **Token** | `LiensightToken` (LSPV), [`0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE`](https://sepolia.etherscan.io/address/0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE) |
| **Watched property** | Bronx BBL `2-5789-1022` |
| **Data source** | NYC Open Data: ACRIS Real Property Legals (`8h5j-fqxa`) and Master (`bnx9-e6tj`) |
| **Workflow** | TypeScript on `@chainlink/cre-sdk`, cron every 10 minutes |
| **Tests** | 18 Foundry + 17 Vitest |
| **Live site** | https://liensight.vercel.app |
| **Video** | https://youtu.be/HZOAwJRiEF8 |
