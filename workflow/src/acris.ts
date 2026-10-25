import { keccak256, toBytes } from "viem";
import type { AcrisDoc } from "./classify";

export type Bbl = { borough: 1 | 2 | 3 | 4 | 5; block: number; lot: number };

export const LIMIT = 5000;
const BASE = "https://data.cityofnewyork.us/resource";

// encodeURIComponent (not URLSearchParams) so spaces are %20, not +
const query = (p: Record<string, string>) =>
  Object.entries(p).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");

export function legalsUrl(bbl: Bbl): string {
  const q = query({
    $select: "document_id",
    $where: `borough='${bbl.borough}' AND block='${bbl.block}' AND lot='${bbl.lot}'`,
    $order: "document_id",
    $limit: String(LIMIT),
  });
  return `${BASE}/8h5j-fqxa.json?${q}`;
}

export function masterUrl(ids: string[]): string {
  const q = query({
    $select: "document_id,doc_type",
    $where: `document_id in(${ids.map((i) => `'${i}'`).join(",")})`,
    $order: "document_id",
    $limit: String(LIMIT),
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
  // legacy pre-2003 ids look like "FT_2300000813130"; hash those instead of throwing
  if (!/^\d+$/.test(documentId)) return keccak256(toBytes(documentId));
  return `0x${BigInt(documentId).toString(16).padStart(64, "0")}`;
}

/** A response that hit the row limit may be incomplete: refuse to report (fail static). */
export function assertComplete(rows: unknown[]): void {
  if (rows.length >= LIMIT) throw new Error(`ACRIS response truncated at ${LIMIT} rows`);
}

/** A 200 with zero documents is more likely an outage or wrong BBL than a clean lot. */
export function assertNonEmpty(docs: AcrisDoc[]): void {
  if (docs.length === 0) throw new Error("no ACRIS documents for this BBL; refusing to report");
}
