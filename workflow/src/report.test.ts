import { describe, it, expect } from "vitest";
import { decodeAbiParameters } from "viem";
import map from "./codeMap.json";
import legals from "../fixtures/acris-legals-2-5789-1022.json";
import masterRows from "../fixtures/acris-master-2-5789-1022.json";
import { canonicalDocs, docSetHash, docIdToBytes32 } from "./acris";
import { buildReport, propertyKey } from "./report";

const abi = [
  { type: "bytes32" },
  { type: "bytes32" },
  { type: "bytes32[]" },
  { type: "bytes32[]" },
] as const;

describe("buildReport", () => {
  const bbl = { borough: 2 as const, block: 5789, lot: 1022 };
  it("encodes key, docSetHash, adverse ids, discharge ids", () => {
    const docs = canonicalDocs(legals, masterRows);
    const r = buildReport(bbl, docs, map);
    const [key, setHash, adverse, discharge] = decodeAbiParameters(abi, r.payload);
    expect(key).toBe(propertyKey(bbl));
    expect(setHash).toBe(docSetHash(docs));
    const locc = docs.find((d) => d.docType === "LOCC")!;
    expect(adverse).toEqual([docIdToBytes32(locc.documentId)]);
    expect(discharge).toEqual([]);
  });
  it("empty doc list encodes empty arrays", () => {
    const r = buildReport(bbl, [], map);
    const [, , adverse, discharge] = decodeAbiParameters(abi, r.payload);
    expect(adverse).toEqual([]);
    expect(discharge).toEqual([]);
  });
  it("is identical regardless of input order (determinism for consensus)", () => {
    const a = buildReport(bbl, canonicalDocs(legals, masterRows), map).payload;
    const b = buildReport(bbl, canonicalDocs([...legals].reverse(), [...masterRows].reverse()), map).payload;
    expect(a).toBe(b);
  });
});
