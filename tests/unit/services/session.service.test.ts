import { validateCreateSessionInput } from "../../../src/services/session.service";

describe("session.service", () => {
  describe("validateCreateSessionInput", () => {
    const validInput = {
      hostPaynowId: "+6591234567",
      items: [{ name: "Chicken Rice", quantity: 2, unitPrice: 6.50 }],
      tax: 1.20,
      serviceCharge: 2.00,
      discount: 0,
    };

    it("returns null for valid input", () => {
      const error = validateCreateSessionInput(validInput);
      expect(error).toBeNull();
    });

    it("returns error when hostPaynowId is missing", () => {
      const error = validateCreateSessionInput({ ...validInput, hostPaynowId: "" });
      expect(error).toMatch(/hostPaynowId/i);
    });

    it("returns error when items array is empty", () => {
      const error = validateCreateSessionInput({ ...validInput, items: [] });
      expect(error).toMatch(/items/i);
    });

    it("returns error when item name is empty", () => {
      const error = validateCreateSessionInput({
        ...validInput,
        items: [{ name: "", quantity: 1, unitPrice: 5.00 }],
      });
      expect(error).toMatch(/name/i);
    });

    it("returns error when item quantity is 0 or negative", () => {
      const error = validateCreateSessionInput({
        ...validInput,
        items: [{ name: "Item", quantity: 0, unitPrice: 5.00 }],
      });
      expect(error).toMatch(/quantity/i);
    });

    it("returns error when item unitPrice is 0 or negative", () => {
      const error = validateCreateSessionInput({
        ...validInput,
        items: [{ name: "Item", quantity: 1, unitPrice: -1 }],
      });
      expect(error).toMatch(/unitPrice/i);
    });

    it("returns error when tax is negative", () => {
      const error = validateCreateSessionInput({ ...validInput, tax: -1 });
      expect(error).toMatch(/tax/i);
    });

    it("returns error when serviceCharge is negative", () => {
      const error = validateCreateSessionInput({ ...validInput, serviceCharge: -1 });
      expect(error).toMatch(/serviceCharge/i);
    });

    it("returns error when discount is negative", () => {
      const error = validateCreateSessionInput({ ...validInput, discount: -1 });
      expect(error).toMatch(/discount/i);
    });
  });
});
