# Glossary

| Term | Meaning |
|---|---|
| **ACRIS** | Automated City Register Information System: New York City’s public record of property documents (deeds, mortgages, liens, releases). |
| **Adverse filing** | A document type that signals a claim on the property: `FL`, `FTL`, `NTXL`, `TLS`, `LOCC`, `JUDG`. |
| **BBL** | Borough-block-lot: the city’s identifier for a tax lot, for example `2-5789-1022`. |
| **citedHash** | `keccak256(abi.encode(ids))` of the liens behind the current restriction. The issuer must name it to clear. |
| **Code map** | `workflow/src/codeMap.json`: which ACRIS document types are adverse or discharge. Its hash is stored on the token. |
| **Consensus (identical)** | CRE aggregation that requires every node to return the same result; otherwise there is no report. |
| **CRE** | Chainlink Runtime Environment: runs workflows across a decentralized oracle network. |
| **Discharge filing** | A release, discharge, withdrawal or termination of a lien. It only suggests a clear. |
| **docSetHash** | Hash of every `documentId:docType` on the lot. It changes whenever the record changes. |
| **DON** | Decentralized oracle network: the nodes that run the workflow. |
| **Fail closed** | On errors, truncation or empty data, write nothing rather than a possibly false answer. |
| **Forwarder** | The Chainlink contract that verifies a DON report and calls the receiver’s `onReport`. |
| **Issuer multisig** | The account that holds the supply and can clear restrictions and rotate the workflow owner. |
| **LOCC** | Lien of common charges: a condominium’s lien for unpaid charges. The demo filing. |
| **LSPV** | The demo token’s symbol (Liensight SPV). |
| **NYC Open Data** | The city’s open-data portal (Socrata API). It publishes ACRIS as datasets `8h5j-fqxa` (Legals) and `bnx9-e6tj` (Master). |
| **propertyKey** | `keccak256("BBL:<borough>-<block>-<lot>")`: binds a token to one property. |
| **RWA** | Real-world asset. |
| **SPV** | Special-purpose vehicle: the company that owns the building. The token represents its shares. |
| **Workflow owner** | The address that owns a CRE workflow. It appears in each report’s metadata and the token checks it. |
