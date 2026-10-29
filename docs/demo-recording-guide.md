# Liensight: live demo recording guide

Target length: **about 4 minutes**. Everything below was checked against the real project on Oct 28, 2026 (token still restricted, 18 contract tests and 17 workflow tests passing, issuer wallet has about 0.048 Sepolia ETH).

## The story in one line

> A lien gets recorded on a New York building. Liensight reads the public record, the Chainlink network agrees on it, and the token behind that building restricts its own transfers and cites the document.

---

## Before you press record

### Setup (10 minutes)

1. **Screen:** 1920x1080, browser zoom 110%, close every unrelated tab and notification. Use Windows Game Bar (`Win + G`) or OBS to record with your microphone on.
2. **Start the website** in a terminal (PowerShell), from the repo root, and leave it running:

```powershell
cd C:\dfol\legalhk; python -m http.server 5181 --directory site
```

3. **Open these browser tabs, in this order:**

| Tab | URL |
|---|---|
| 1 | http://localhost:5181/ |
| 2 | http://localhost:5181/check.html |
| 3 | http://localhost:5181/proof.html |
| 4 | https://sepolia.etherscan.io/tx/0xb27c9ed1891c763325412789f3d05e1d221584353186e80eb9ad31ea9769c4d9 (the deploy transaction) |
| 5 | https://sepolia.etherscan.io/tx/0xc0cc238205a36246731feddba275b3df50b4c781f3958b8d4cab8a862bda85ab |
| 6 | http://localhost:5181/security.html |

4. **Open a second PowerShell window** for the demo commands, in the repo root. Make the font large (Ctrl + mouse wheel).
5. **Check you're still logged in to CRE** (the login can expire):

```powershell
cre whoami
```

If it asks you to log in, run `cre login` now, not during the recording.

6. **Warm up once, off camera:** run the simulation command from Step 4 below one time, and load the Check page once. This makes the real run smooth and confirms nothing has changed.
7. **If the document count isn't 14,** ACRIS has recorded a new document on that lot since this was written. Just say the number you see. The lien should still be `2026092900833001`; if it isn't, tell me before you record.

### Never show on screen

- The `.env` file, or any private key.
- Your keystore password. (The demo commands below don't ask for it.)
- Your wallet address is public on Etherscan, so it's fine.

---

## Recording script

### Step 1: The idea (0:00 to 0:30) · Tab 1, landing page

**Show:** the hero, "A lien lands. Transfers stop." Scroll slowly to the dark evidence cards and drag the carousel once.

**Say:**
> "This is Liensight. A token that represents shares in a company that owns a New York building can keep trading even after a lien is recorded against that building. Liensight watches the public property record, and when a new lien appears, the token restricts itself and cites the document."

**Point out:** the live badge "Built on Chainlink CRE · live on Sepolia testnet".

---

### Step 2: The real data (0:30 to 1:20) · Tab 2, Check page

**Show:** the page loads with **2-5789-1022** already filled in and runs by itself.

**Say:**
> "This reads New York's ACRIS records live, in the browser. This Bronx lot has 14 recorded documents, and one of them is adverse."

**Do:**
1. Wait for the red result: **"Transfers would be restricted: 1 adverse filing."**
2. Point at the top row, type **LOCC**, document **2026092900833001**.
3. Click that document ID. The official ACRIS page opens in a new tab. Show it for 3 seconds, then close it.
4. Click **"Manhattan 1-905-1347 · clean"**.
5. Wait for the green result: **"No adverse filings: transfers stay open."**

**Say:**
> "Same check, different building: no tax lien, no federal lien, no judgment. Transfers would stay open."

**Honest note to say out loud:**
> "ACRIS records filings days after the event, so this is an early warning, not a title search."

---

### Step 3: The proof the code works (1:20 to 1:50) · PowerShell window

**Run:**

```powershell
cd C:\dfol\legalhk\contracts; forge test
```

**Show:** the list of passing tests, ending with `18 tests passed, 0 failed`.

**Say:**
> "Eighteen contract tests: access control, replays, a cleared lien never re-restricting, and stale clears reverting."

**Then run:**

```powershell
cd C:\dfol\legalhk\workflow; npm test
```

**Show:** `Tests 17 passed (17)`.

**Say:**
> "Seventeen more for the workflow: ordering, empty results, truncated responses, old document IDs."

---

### Step 4: The Chainlink workflow, live (1:50 to 2:50) · PowerShell window

This is the main moment. It takes about 15 to 20 seconds to run.

**Run:**

```powershell
cd C:\dfol\legalhk; $env:PATH="$PWD\workflow\node_modules\.bin;$env:PATH"; cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0 --broadcast
```

**Show:** the output as it appears. Pause on these lines:

```
✓ Workflow compiled
[USER LOG] ACRIS docs=14 adverse=2026092900833001:LOCC
[USER LOG] report written tx=0x...
✓ Workflow Simulation Result
```

**Say while it runs:**
> "This is the Chainlink CRE workflow. Every node fetches the ACRIS record on its own, and the network has to agree on the exact set of documents. It found 14 documents, flagged the lien we just saw, and sent a signed report to the token on Sepolia."

**Expect, and explain if you like:** this run sends one small real transaction (about 0.00002 ETH). The token already restricted itself on the first run, and the contract ignores a report for an unchanged document set. So the state won't change, but the transaction still succeeds.

> "Running it again changes nothing, because the document set is the same. That's deliberate."

**Do not** use `-T clean-settings` with `--broadcast`: that config doesn't point at the deployed token.

---

### Step 5: The result on-chain (2:50 to 3:40)

**5a. Tab 3, Proof page.** Scroll to the live table.

**Say:**
> "These values are read directly from the token on Sepolia every time this page loads. `restricted` is true."

**Point at:**
- `restricted()` → **true**
- `citedHash()` → `0xb87dc80e…49f4`

**Say:**
> "That hash is the keccak of the one lien's document ID. I computed it independently and it matches."

**5b. PowerShell window.** Prove the restriction really blocks transfers:

```powershell
cast call 0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE "transfer(address,uint256)(bool)" 0x000000000000000000000000000000000000dEaD 1 --from 0xd51E7130B55f10595939f274cCB8c00b52C915b4 --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

**Show:** `execution reverted ... 0xe827105e`

**Say:**
> "Even the issuer can't move tokens now. That error code is `TransferRestricted`."

**5c. Tab 5, the report transaction on Etherscan.** Point at **Status: Success**, then click the **Logs (2)** tab and show the event emitted by `0xf813…04aE` (our token).

**Say:**
> "The Chainlink forwarder delivered this report, so Etherscan lists the transaction under the forwarder. The token's own events are in the logs."

**Do not open the token's address page** on camera. Its "Transactions" tab only lists transactions sent directly to the token, and the report was sent to the forwarder, so that tab looks empty. The restriction shows under the address page's **Events** and **Internal Transactions** tabs, but they can load slowly, so use this transaction page instead.

**Tab 4 (optional):** the deploy transaction, to show the token was created on Sepolia.

---

### Step 6: It rejected the wrong thing too (3:40 to 4:00) · Tab 6, Security page

**Show:** scroll to the three receipts under "It said no."

**Say:**
> "Our first test token rejected a real report because the simulator used a different workflow owner than we'd allowed. The second token accepted it. The token only listens to the workflow it expects."

---

### Closing (4:00 to 4:20) · Tab 1 or the Roadmap page

**Say:**
> "To be clear about the limits: this runs on the Sepolia testnet through Chainlink's simulator, not a deployed network. ACRIS lags real events. And it covers federal liens, tax liens, common-charge liens and judgments, not lis pendens, which aren't in ACRIS. Liensight: the token finds out when the building does."

---

## If something goes wrong

| Problem | Fix |
|---|---|
| Check page shows an error or hangs | NYC's server is slow. Wait 10 seconds and press **Check** again. If it still fails, skip to Step 3 and say you'll show the stored result on the Proof page. |
| `cre` asks you to log in | Run `cre login` and finish in the browser, then start Step 4 again. |
| `cre` says `bun` is not found | You skipped the `$env:PATH` part of the command. Run it exactly as written. |
| Simulation fails with "insufficient funds" | The wallet in `.env` needs Sepolia ETH. It had about 0.048 ETH when this was written, so this shouldn't happen. |
| Proof page shows "read failed" | The public Sepolia endpoint is busy. Refresh once. Fallback: run `cast call ... "restricted()(bool)"` (command below) in PowerShell. |
| Anything in Step 4 is slow | Cut the video there and restart the step. It's a clean one-line command, so a retake is easy. |

Fallback command for `restricted()`:

```powershell
cast call 0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE "restricted()(bool)" --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

---

## Things not to claim

These aren't true yet, so don't say them in the video:

- **"It's deployed on a live Chainlink network."** It ran through the CRE simulator (one node) with a mock forwarder.
- **"The issuer can clear it"** as something you've shown. The function exists and is tested, but no clear has been run on Sepolia.
- **"It catches lis pendens or foreclosures."** ACRIS has no document type for them.
- **"It's production-ready" or "audited."** It's a testnet hackathon build.
- **"The Bronx lien is the building's real tax problem."** Say "a lien of common charges recorded on that lot." Don't guess more about the owner.

## Checklist right before recording

- [ ] `python -m http.server 5181 --directory site` is running
- [ ] Six browser tabs open, in order
- [ ] `cre whoami` works
- [ ] Warm-up run done once
- [ ] `.env` and password prompts are not visible
- [ ] Microphone checked
- [ ] Notifications off
