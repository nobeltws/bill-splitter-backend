import { Context } from "koa";
import { extractTextFromImage } from "../services/ocr.service";
import { parseReceiptText } from "../services/receipt-parser.service";

const ALLOWED_TYPES = ["image/jpeg", "image/png"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export async function parseReceipt(ctx: Context): Promise<void> {
  const file = ctx.request.files?.image;

  if (!file || Array.isArray(file)) {
    ctx.status = 400;
    ctx.body = { error: "A single image file is required in the 'image' field" };
    return;
  }

  if (!ALLOWED_TYPES.includes(file.mimetype || "")) {
    ctx.status = 400;
    ctx.body = { error: "Only JPEG and PNG files are accepted" };
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    ctx.status = 413;
    ctx.body = { error: "File size exceeds 10MB limit" };
    return;
  }

  const fs = await import("fs/promises");
  const imageBuffer = await fs.readFile(file.filepath);

  const rawText = await extractTextFromImage(imageBuffer);
  const parsed = parseReceiptText(rawText);

  ctx.status = 200;
  ctx.body = {
    items: parsed.items,
    tax: parsed.tax,
    serviceCharge: parsed.serviceCharge,
    rawText,
  };
}
