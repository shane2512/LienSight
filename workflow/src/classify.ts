import { keccak256, toBytes } from "viem";

export type AcrisDoc = { documentId: string; docType: string };
export type CodeMap = { version: number; adverse: string[]; discharge: string[]; [k: string]: unknown };

export function classify(docs: AcrisDoc[], map: CodeMap) {
  const adverse: AcrisDoc[] = [];
  const discharge: AcrisDoc[] = [];
  const other: AcrisDoc[] = [];
  for (const doc of docs) {
    if (map.adverse.includes(doc.docType)) adverse.push(doc);
    else if (map.discharge.includes(doc.docType)) discharge.push(doc);
    else other.push(doc);
  }
  return { adverse, discharge, other };
}

function canonical(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(canonical).join(",")}]`;
  if (v && typeof v === "object")
    return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canonical((v as Record<string, unknown>)[k])}`).join(",")}}`;
  return JSON.stringify(v);
}

export function codeMapHash(map: CodeMap): `0x${string}` {
  return keccak256(toBytes(canonical(map)));
}
