# Quickstart

From a fresh clone to a passing test suite and a live workflow simulation against real NYC records. About ten minutes, most of it installing tools.

You don’t need a wallet or any keys for this page. Writing to Sepolia is covered in [Deployment](deployment.md).

## 1. Install the tools

| Tool | Version used | Install |
|---|---|---|
| Git | any | https://git-scm.com |
| Foundry (`forge`, `cast`) | 1.5.1 | https://getfoundry.sh, then `foundryup` |
| Node.js and npm | 20 or newer | https://nodejs.org |
| Chainlink CRE CLI (`cre`) | v1.2.0 | https://docs.chain.link/cre |

Check them:

```bash
git --version && forge --version && node --version && cre version
```

## 2. Clone

The contracts depend on OpenZeppelin (and, through it, `forge-std`) as git submodules, so clone recursively:

```bash
git clone --recursive https://github.com/shane2512/LienSight.git liensight
cd liensight
```

If you already cloned without `--recursive`, run `git submodule update --init --recursive`.

## 3. Install the workflow’s packages

```bash
cd workflow && npm i && cd ..
```

This also installs Bun locally, which the CRE CLI uses to build the TypeScript workflow.

## 4. Run the tests

```bash
cd contracts && forge test && cd ..
cd workflow && npm test && cd ..
```

Expected:

```
Ran 1 test suite ...: 18 tests passed, 0 failed, 0 skipped (18 total tests)
 Test Files  3 passed (3)
      Tests  17 passed (17)
```

[Testing](testing.md) lists what each test proves.

## 5. Simulate the workflow against live ACRIS

Log in once, put the local Bun on your `PATH`, then simulate both configured properties:

```bash
cre login
export PATH="$PWD/workflow/node_modules/.bin:$PATH"

# Bronx 2-5789-1022: has a recorded lien of common charges
cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0

# Manhattan 1-905-1347: nothing adverse
cre workflow simulate ./workflow -T clean-settings --non-interactive --trigger-index 0
```

On Windows PowerShell, set the path with `$env:Path = "$PWD\workflow\node_modules\.bin;$env:Path"`.

Expected log lines (timestamps will differ; document counts can grow as the city records new filings):

```
✓ Workflow compiled
[USER LOG] ACRIS docs=14 adverse=2026092900833001:LOCC
...
[USER LOG] ACRIS docs=12 adverse=none
```

Without `--broadcast` the write is a dry run and logs a zero transaction hash. That’s expected. [`demo/replay.sh`](../demo/replay.sh) runs both simulations in one go.

## 6. Look at the result on-chain

The same workflow, run with `--broadcast`, already restricted the demo token on Sepolia. Read it:

```bash
cast call 0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE "restricted()(bool)" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# true
```

## 7. Try the website (optional)

```bash
python -m http.server 5181 --directory site
# open http://localhost:5181/check.html
```

Or use the live copy at https://liensight.vercel.app/check.html. Pick a lot, press **Check**, and the page reads ACRIS in your browser using the same adverse-type map as the workflow.

## Next steps

- [Verifying the live deployment](verification.md): check every claim about the Sepolia token yourself.
- [Deployment](deployment.md): deploy your own token and send it a real report.
- [Configuration](configuration.md): watch a different building.
- [Architecture](architecture.md): how the pieces fit.
