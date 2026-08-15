import { Controller, Post, Route, Response, UploadedFile, SuccessResponse } from "tsoa";
import { extractTextFromImage } from "../services/ocr.service";
import { parseReceiptText } from "../services/receipt-parser.service";
import { ErrorResponse } from "../types/api";

interface ParsedItemOutput {
  name: string;
  quantity: number;
  unitPrice: number;
}

interface ParseReceiptResponse {
  items: ParsedItemOutput[];
  tax: number;
  serviceCharge: number;
  rawText: string;
}

const ALLOWED_TYPES = ["image/jpeg", "image/png"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

@Route("api/receipts")
export class ReceiptController extends Controller {
  /**
   * Parse a receipt image via OCR and return structured item data.
   * Accepts JPEG or PNG images up to 10MB.
   */
  @SuccessResponse("200", "Successfully parsed")
  @Response<ErrorResponse>(400, "Invalid file")
  @Response<ErrorResponse>(413, "File too large")
  @Post("parse")
  public async parseReceipt(
    @UploadedFile() image: Express.Multer.File
  ): Promise<ParseReceiptResponse> {
    if (!image) {
      this.setStatus(400);
      return { error: "A single image file is required in the 'image' field" } as any;
    }

    if (!ALLOWED_TYPES.includes(image.mimetype || "")) {
      this.setStatus(400);
      return { error: "Only JPEG and PNG files are accepted" } as any;
    }

    if (image.size > MAX_FILE_SIZE) {
      this.setStatus(413);
      return { error: "File size exceeds 10MB limit" } as any;
    }

    const rawText = await extractTextFromImage(image.buffer);
    const parsed = parseReceiptText(rawText);

    return {
      items: parsed.items,
      tax: parsed.tax,
      serviceCharge: parsed.serviceCharge,
      rawText,
    };
  }
}
