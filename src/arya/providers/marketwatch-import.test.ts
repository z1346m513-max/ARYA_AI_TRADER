import { describe, expect, it } from "vitest";
import { candlesFromSnapshots, jalaliToGregorian, parseMarketWatch } from "./marketwatch-import";

const header = ["نماد", "نام", "تعداد", "حجم", "ارزش", "دیروز", "اولین", "a", "b", "c", "پایانی", "d", "e", "کمترین", "بیشترین"];
const row = (t: string, v: number, o: number, c: number, l: number, h: number) => [t, "", 1, v, 0, 0, o, 0, 0, 0, c, 0, 0, l, h];

describe("market watch import", () => {
  it("converts 1405/08/11 to 2 Nov 2026", () => {
    expect(jalaliToGregorian(1405, 8, 11)).toEqual([2026, 11, 2]);
  });
  it("reads the fold bar from the file layout", () => {
    const s = parseMarketWatch([["دیده بان بازار : 1405/08/11"], header, row("فولاد", 980, 4080, 4090, 4020, 4160)]);
    expect(s.t).toBe(Date.UTC(2026, 10, 2));
    expect(s.bars["فولاد"]).toEqual([4080, 4160, 4020, 4090, 980]);
  });
  it("skips untraded or inconsistent rows", () => {
    const s = parseMarketWatch([["1405/08/11"], header, row("الف", 0, 10, 10, 10, 10), row("ب", 5, 10, 12, 11, 11), row("فولاد", 1, 5, 5, 5, 5)]);
    expect(Object.keys(s.bars)).toEqual(["فولاد"]);
  });
  it("builds a sorted history across days", () => {
    const a = { jalali: "b", t: 2, bars: { X: [1, 2, 1, 2, 9] as [number, number, number, number, number] } };
    const b = { jalali: "a", t: 1, bars: { X: [1, 1, 1, 1, 9] as [number, number, number, number, number] } };
    expect(candlesFromSnapshots([a, b], "X").map((c) => c.t)).toEqual([1, 2]);
  });
});
