import { keccak256, toBytes } from "viem";
import type { AcrisDoc } from "./classify";

export type Bbl = { borough: 1 | 2 | 3 | 4 | 5; block: number; lot: number };

const BASE = "https://data.cityofnewyork.us/resource";

// encodeURIComponent (not URLSearchParams) so spaces are %20, not +
const query = (p: Record<string, string>) =>
  Object.entries(p).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");

export function legalsUrl(bbl: Bbl): string {
  const q = query({
    $select: "document_id",
    $where: `borough='${bbl.borough}' AND block='${bbl.block}' AND lot='${bbl.lot}'`,
    $limit: "5000",
  });
  return `${BASE}/8h5j-fqxa.json?${q}`;
}

export function masterUrl(ids: string[]): string {
  const q = query({
    $select: "document_id,doc_type",
    $where: `document_id in(${ids.map((i) => `'${i}'`).join(",")})`,
    $limit: "5000",
  });
  return `${BASE}/bnx9-e6tj.json?${q}`;
}

type LegalRow = { document_id: string };
type MasterRow = { document_id: string; doc_type: string };

/** Docs that appear in BOTH legals (for the BBL) and master (for the type). Sorted, deduped. */
export function canonicalDocs(legals: LegalRow[], master: MasterRow[]): AcrisDoc[] {
  const onLot = new Set(legals.map((l) => l.document_id));
  const byId = new Map<string, string>();
  for (const m of master) if (onLot.has(m.document_id)) byId.set(m.document_id, m.doc_type);
  return [...byId.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([documentId, docType]) => ({ documentId, docType }));
}

export function docSetHash(docs: AcrisDoc[]): `0x${string}` {
  return keccak256(toBytes(docs.map((d) => `${d.documentId}:${d.docType}`).join("\n")));
}

/** ACRIS document ids are 16-digit numbers; pad to bytes32 so they stay reversible on-chain. */
export function docIdToBytes32(documentId: string): `0x${string}` {
  return `0x${BigInt(documentId).toString(16).padStart(64, "0")}`;
}
