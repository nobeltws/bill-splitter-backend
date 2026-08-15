import request from "supertest";
import app from "../../src/app";

jest.setTimeout(30000);

// Create a minimal valid PNG (1x1 pixel) for testing
const MINIMAL_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64"
);

describe("POST /api/receipts/parse", () => {
  it("returns 400 when no file is provided", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .send({});

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/image/i);
  });

  it("returns 400 for invalid file types", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .attach("image", Buffer.from("not an image"), {
        filename: "test.txt",
        contentType: "text/plain",
      });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/JPEG|PNG/i);
  });

  it("returns 200 with parsed data for a valid image", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .attach("image", MINIMAL_PNG, {
        filename: "receipt.png",
        contentType: "image/png",
      });

    // Minimal 1x1 PNG won't have meaningful OCR text, but the endpoint should succeed
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty("items");
    expect(res.body).toHaveProperty("tax");
    expect(res.body).toHaveProperty("serviceCharge");
    expect(res.body).toHaveProperty("rawText");
    expect(Array.isArray(res.body.items)).toBe(true);
  });
});
