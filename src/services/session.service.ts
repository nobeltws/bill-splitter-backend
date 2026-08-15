export interface CreateSessionInput {
  hostPaynowId: string;
  items: { name: string; quantity: number; unitPrice: number }[];
  tax: number;
  serviceCharge: number;
  discount: number;
}

export function validateCreateSessionInput(input: CreateSessionInput): string | null {
  if (!input.hostPaynowId || input.hostPaynowId.trim() === "") {
    return "hostPaynowId is required";
  }

  if (!input.items || input.items.length === 0) {
    return "At least one item is required in items";
  }

  for (let i = 0; i < input.items.length; i++) {
    const item = input.items[i];
    if (!item.name || item.name.trim() === "") {
      return `Item ${i + 1}: name is required`;
    }
    if (!item.quantity || item.quantity <= 0) {
      return `Item ${i + 1}: quantity must be greater than 0`;
    }
    if (item.unitPrice === undefined || item.unitPrice <= 0) {
      return `Item ${i + 1}: unitPrice must be greater than 0`;
    }
  }

  if (input.tax < 0) {
    return "tax cannot be negative";
  }

  if (input.serviceCharge < 0) {
    return "serviceCharge cannot be negative";
  }

  if (input.discount < 0) {
    return "discount cannot be negative";
  }

  return null;
}
