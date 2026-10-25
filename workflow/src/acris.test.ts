import { describe, it, expect } from "vitest";
import legals from "../fixtures/acris-legals-2-5789-1022.json";
import master from "../fixtures/acris-master-2-5789-1022.json";
import { canonicalDocs, docSetHash, docIdToBytes32, legalsUrl, masterUrl, assertComplete, assertNonEmpty, LIMIT } from "./acris";

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
  it("docIdToBytes32 handles legacy non-numeric ids (FT_, BK_) without throwing", () => {
    const a = docIdToBytes32("FT_2300000813130");
    expect(a).toMatch(/^0x[0-9a-f]{64}$/);
    expect(docIdToBytes32("FT_2300000813130")).toBe(a);
    expect(docIdToBytes32("BK_2300000813130")).not.toBe(a);
  });
  it("queries are ordered so every node pages the same rows", () => {
    expect(decodeURIComponent(legalsUrl({ borough: 2, block: 5789, lot: 1022 }))).toContain("$order=document_id");
    expect(decodeURIComponent(masterUrl(["A"]))).toContain("$order=document_id");
  });
  it("assertComplete fails static when a response hit the row limit", () => {
    expect(() => assertComplete(new Array(LIMIT).fill({}))).toThrow(/truncat/i);
    expect(() => assertComplete(new Array(LIMIT - 1).fill({}))).not.toThrow();
  });
  it("assertNonEmpty refuses to report a property with zero documents", () => {
    expect(() => assertNonEmpty([])).toThrow(/no ACRIS documents/i);
    expect(() => assertNonEmpty([{ documentId: "1", docType: "DEED" }])).not.toThrow();
  });
});
