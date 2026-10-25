# Liensight pitch

**One line:** An early-warning transfer restriction when a public lien filing hits the property behind your token.

**Problem:** Tokenized property shares can trade while a tax lien, federal lien or judgment sits on the property. The party who would flag it (issuer, transfer agent) is slow or conflicted.

**Solution:** A CRE workflow where every node reads NYC ACRIS and the DON agrees on the exact filing set. A new adverse filing restricts secondary transfers and cites the document IDs. Only the issuer multisig can clear.

**Why different from the other submitted builds (16 at time of writing):** the chain acts on a government record, not on an AI's own output.

**Why a DON for one API:** no single server decides what the chain sees; anyone can verify the cited IDs on ACRIS. The issuer can still clear, but only for the exact set of liens it reviewed.

**Honest framing:** token = SPV equity, not title; restriction = issuer-governed per operating agreement, not a statutory duty; ACRIS lags; no lis pendens in ACRIS.

**Demo (90s):** 1) open demo page, check 2-5789-1022: restricted, 1 LOCC, link to ACRIS. 2) check 1-905-1347: open. 3) show `docs/simulation-log.md` and `forge test` 16/16.
