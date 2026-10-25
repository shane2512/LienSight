import { describe, it, expect } from "vitest";
import legals from "../fixtures/acris-legals-2-5789-1022.json";
import master from "../fixtures/acris-master-2-5789-1022.json";
import { canonicalDocs, docSetHash, docIdToBytes32, legalsUrl, masterUrl } from "./acris";

describe("acris", () => {
  it("canonicalDocs sorts and dedupes", () => {
    const docs = canonicalDocs(legals, [...master, ...master].reverse());
    expect(docs).toHaveLength(14);
    const ids = docs.map((d) => d.documentId);
    expect(ids).toEqual([...ids].sort());
    expect(docs.some((d) => d.docType === "LOCC")).toBe(true);
  });
  it("canonicalDocs returns [] for zero rows", () => {
    expect(canonicalDocs([], [])).toEqual([]);
    expect(canonicalDocs(legals, [])).toEqual([]);
  });
  it("same docs in different order give same docSetHash", () => {
    const a = canonicalDocs(legals, master);
    const b = canonicalDocs([...legals].reverse(), [...master].reverse());
    expect(docSetHash(a)).toBe(docSetHash(b));
    expect(docSetHash(a)).toMatch(/^0x[0-9a-f]{64}$/);
    expect(docSetHash([])).toMatch(/^0x[0-9a-f]{64}$/);
  });
  it("legalsUrl encodes borough/block/lot", () => {
    const u = decodeURIComponent(legalsUrl({ borough: 2, block: 5789, lot: 1022 }));
    expect(u).toContain("8h5j-fqxa");
    expect(u).toContain("borough='2'");
    expect(u).toContain("block='5789'");
    expect(u).toContain("lot='1022'");
  });
  it("masterUrl lists document ids", () => {
    const u = decodeURIComponent(masterUrl(["A1", "B2"]));
    expect(u).toContain("bnx9-e6tj");
    expect(u).toContain("document_id in('A1','B2')");
  });
  it("docIdToBytes32 is reversible numeric padding", () => {
    expect(docIdToBytes32("2026092900833001")).toBe(
      "0x" + BigInt("2026092900833001").toString(16).padStart(64, "0"),
    );
  });
});
