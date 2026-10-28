import { describe, expect, it } from "vitest";
import { formatVnd, formatDate } from "./utils";

describe("formatVnd", () => {
  it("formats a number with dot thousands separators and the ₫ suffix", () => {
    expect(formatVnd(299000)).toBe("299.000₫");
  });

  it("accepts a string amount", () => {
    expect(formatVnd("2990000")).toBe("2.990.000₫");
  });
});

describe("formatDate", () => {
  it("formats an ISO timestamp as dd/MM/yyyy", () => {
    expect(formatDate("2026-11-27T10:10:56.362498Z")).toBe("27/11/2026");
  });
});
