export interface ParsedItem {
  name: string;
  quantity: number;
  unitPrice: number;
}

export interface ParsedReceipt {
  items: ParsedItem[];
  tax: number;
  serviceCharge: number;
}

const BLACKLIST = [
  "total", "subtotal", "sub-total", "cash", "change",
  "visa", "mastercard", "amex", "nets", "balance",
  "thank you", "receipt", "invoice",
];

const ITEM_REGEX = /^(?:(\d+)\s*[xX]\s+)?(.+?)\s{2,}(\d+\.\d{2})$/;
const TAX_REGEX = /(gst|tax|vat)\s*[:]?\s*(\d+\.\d{2})/i;
const SERVICE_CHARGE_REGEX = /(service\s*charge|serv\.?\s*chg|svc)\s*[:]?\s*(\d+\.\d{2})/i;

function isBlacklisted(line: string): boolean {
  const lower = line.toLowerCase();
  return BLACKLIST.some((word) => lower.includes(word));
}

export function parseReceiptText(rawText: string): ParsedReceipt {
  const lines = rawText.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);

  let tax = 0;
  let serviceCharge = 0;
  const items: ParsedItem[] = [];

  for (const line of lines) {
    const taxMatch = line.match(TAX_REGEX);
    if (taxMatch) {
      tax = parseFloat(taxMatch[2]);
      continue;
    }

    const scMatch = line.match(SERVICE_CHARGE_REGEX);
    if (scMatch) {
      serviceCharge = parseFloat(scMatch[2]);
      continue;
    }

    if (isBlacklisted(line)) {
      continue;
    }

    const itemMatch = line.match(ITEM_REGEX);
    if (itemMatch) {
      const quantity = itemMatch[1] ? parseInt(itemMatch[1], 10) : 1;
      const totalPrice = parseFloat(itemMatch[3]);
      items.push({
        name: itemMatch[2].trim(),
        quantity,
        unitPrice: Math.round((totalPrice / quantity) * 100) / 100,
      });
    }
  }

  return { items, tax, serviceCharge };
}
