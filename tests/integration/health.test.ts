import request from "supertest";
import app from "../../src/app";

describe("GET /health", () => {
  it("returns 200 with status ok", async () => {
    const res = await request(app.callback()).get("/health");

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: "ok" });
  });
});

describe("Unknown routes", () => {
  it("returns 404 with JSON error for unknown paths", async () => {
    const res = await request(app.callback()).get("/unknown");

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ error: "Not Found" });
  });
});
