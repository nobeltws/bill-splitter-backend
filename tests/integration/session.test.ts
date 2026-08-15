import request from "supertest";
import app from "../../src/app";
import { AppDataSource } from "../../src/db/data-source";

beforeAll(async () => {
  await AppDataSource.initialize();
  await AppDataSource.runMigrations();
});

afterAll(async () => {
  await AppDataSource.destroy();
});

describe("POST /api/sessions", () => {
  const validBody = {
    hostPaynowId: "+6591234567",
    items: [
      { name: "Chicken Rice", quantity: 2, unitPrice: 6.5 },
      { name: "Laksa", quantity: 1, unitPrice: 8.5 },
    ],
    tax: 1.2,
    serviceCharge: 2.0,
    discount: 0,
  };

  it("creates a session and returns 201 with sessionId", async () => {
    const res = await request(app.callback())
      .post("/api/sessions")
      .send(validBody);

    expect(res.status).toBe(201);
    expect(res.body.sessionId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    );
    expect(res.body.createdAt).toBeDefined();
  });

  it("returns 400 when hostPaynowId is missing", async () => {
    const res = await request(app.callback())
      .post("/api/sessions")
      .send({ ...validBody, hostPaynowId: "" });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/hostPaynowId/i);
  });

  it("returns 400 when items is empty", async () => {
    const res = await request(app.callback())
      .post("/api/sessions")
      .send({ ...validBody, items: [] });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/items/i);
  });

  it("returns 400 when item has invalid quantity", async () => {
    const res = await request(app.callback())
      .post("/api/sessions")
      .send({
        ...validBody,
        items: [{ name: "Bad", quantity: 0, unitPrice: 5 }],
      });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/quantity/i);
  });
});

describe("GET /api/sessions/:id", () => {
  let sessionId: string;

  beforeAll(async () => {
    const res = await request(app.callback())
      .post("/api/sessions")
      .send({
        hostPaynowId: "+6591234567",
        items: [{ name: "Test Item", quantity: 1, unitPrice: 10.0 }],
        tax: 0.7,
        serviceCharge: 1.0,
        discount: 0,
      });
    sessionId = res.body.sessionId;
  });

  it("returns 200 with full session state", async () => {
    const res = await request(app.callback()).get(
      `/api/sessions/${sessionId}`
    );

    expect(res.status).toBe(200);
    expect(res.body.sessionId).toBe(sessionId);
    expect(res.body.hostPaynowId).toBe("+6591234567");
    expect(res.body.items).toHaveLength(1);
    expect(res.body.items[0].name).toBe("Test Item");
    expect(res.body.items[0].quantity).toBe(1);
    expect(res.body.items[0].unitPrice).toBe(10.0);
    expect(res.body.tax).toBe(0.7);
    expect(res.body.serviceCharge).toBe(1.0);
    expect(res.body.discount).toBe(0);
    expect(res.body.claims).toEqual([]);
    expect(res.body.payments).toEqual([]);
    expect(res.body.createdAt).toBeDefined();
  });

  it("returns 404 for non-existent session", async () => {
    const res = await request(app.callback()).get(
      "/api/sessions/00000000-0000-0000-0000-000000000000"
    );

    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });
});
