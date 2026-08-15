import { parseReceiptText, ParsedReceipt } from "../../../src/services/receipt-parser.service";
import * as fs from "fs";
import * as path from "path";

const sampleReceipt = fs.readFileSync(
  path.join(__dirname, "../../fixtures/sample-receipt.txt"),
  "utf-8"
);

describe("receipt-parser.service", () => {
  describe("parseReceiptText", () => {
    let result: ParsedReceipt;

    beforeAll(() => {
      result = parseReceiptText(sampleReceipt);
    });

    it("extracts line items with quantity and price", () => {
      expect(result.items).toEqual(
        expect.arrayContaining([
          { name: "Chicken Rice", quantity: 2, unitPrice: 6.50 },
          { name: "Laksa", quantity: 1, unitPrice: 8.50 },
          { name: "Fish & Chips", quantity: 1, unitPrice: 15.00 },
          { name: "Iced Tea", quantity: 3, unitPrice: 3.00 },
        ])
      );
    });

    it("extracts tax/GST amount", () => {
      expect(result.tax).toBe(3.64);
    });

    it("extracts service charge", () => {
      expect(result.serviceCharge).toBe(4.55);
    });

    it("filters out blacklisted lines (total, visa, etc.)", () => {
      const itemNames = result.items.map((i) => i.name.toLowerCase());
      expect(itemNames).not.toContain("total");
      expect(itemNames).not.toContain("subtotal");
      expect(itemNames).not.toContain("visa");
    });

    it("returns 0 for tax when not present", () => {
      const noTaxReceipt = "1x Coffee  5.00\nSubtotal  5.00\nTotal  5.00";
      const parsed = parseReceiptText(noTaxReceipt);
      expect(parsed.tax).toBe(0);
    });

    it("returns 0 for service charge when not present", () => {
      const noScReceipt = "1x Coffee  5.00\nSubtotal  5.00\nTotal  5.00";
      const parsed = parseReceiptText(noScReceipt);
      expect(parsed.serviceCharge).toBe(0);
    });

    it("handles items without explicit quantity prefix", () => {
      const text = "Fish & Chips  15.00";
      const parsed = parseReceiptText(text);
      expect(parsed.items[0]).toEqual({
        name: "Fish & Chips",
        quantity: 1,
        unitPrice: 15.00,
      });
    });
  });
});
