import { describe, it, expect } from "vitest";
import map from "./codeMap.json";
import { classify, codeMapHash } from "./classify";

const d = (documentId: string, docType: string) => ({ documentId, docType });

describe("classify", () => {
  it("classifies federal lien and judgment as adverse", () => {
    const r = classify([d("A", "FL"), d("B", "JUDG")], map);
    expect(r.adverse.map((x) => x.documentId)).toEqual(["A", "B"]);
  });
  it("classifies release of federal lien as discharge", () => {
    const r = classify([d("C", "RFL")], map);
    expect(r.discharge).toEqual([d("C", "RFL")]);
    expect(r.adverse).toEqual([]);
  });
  it("unknown or ordinary code goes to other", () => {
    const r = classify([d("E", "DEED"), d("F", "ZZZZ")], map);
    expect(r.other).toHaveLength(2);
    expect(r.adverse).toHaveLength(0);
  });
  it("codeMapHash is stable under key reorder", () => {
    const reordered = { discharge: map.discharge, adverse: map.adverse, source: map.source, version: map.version };
    expect(codeMapHash(reordered)).toBe(codeMapHash(map));
    expect(codeMapHash(map)).toMatch(/^0x[0-9a-f]{64}$/);
  });
});
