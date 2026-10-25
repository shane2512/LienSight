import { encodeAbiParameters, keccak256, toBytes } from "viem";
import type { AcrisDoc, CodeMap } from "./classify";
import { classify } from "./classify";
import { docIdToBytes32, docSetHash, type Bbl } from "./acris";

export const propertyKey = (b: Bbl): `0x${string}` => keccak256(toBytes(`BBL:${b.borough}-${b.block}-${b.lot}`));

/** ABI payload for LiensightToken.onReport: (propertyKey, docSetHash, adverseIds[], dischargeIds[]). */
export function buildReport(bbl: Bbl, docs: AcrisDoc[], map: CodeMap) {
  const { adverse, discharge } = classify(docs, map);
  const payload = encodeAbiParameters(
    [{ type: "bytes32" }, { type: "bytes32" }, { type: "bytes32[]" }, { type: "bytes32[]" }],
    [propertyKey(bbl), docSetHash(docs), adverse.map((d) => docIdToBytes32(d.documentId)), discharge.map((d) => docIdToBytes32(d.documentId))],
  );
  return { payload, adverse, discharge };
}
