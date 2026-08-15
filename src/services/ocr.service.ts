import { createWorker } from "tesseract.js";

export async function extractTextFromImage(imageBuffer: Buffer): Promise<string> {
  const worker = await createWorker("eng");
  try {
    const { data } = await worker.recognize(imageBuffer);
    return data.text;
  } finally {
    await worker.terminate();
  }
}
