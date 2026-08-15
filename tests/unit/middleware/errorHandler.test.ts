import Koa from "koa";
import request from "supertest";
import { errorHandler } from "../../../src/middleware/errorHandler";

function createTestApp(middleware: Koa.Middleware, routeHandler: Koa.Middleware): Koa {
  const app = new Koa();
  app.use(middleware);
  app.use(routeHandler);
  return app;
}

describe("errorHandler middleware", () => {
  it("returns 500 with JSON body for unhandled errors", async () => {
    const app = createTestApp(errorHandler, async () => {
      throw new Error("something broke");
    });

    const res = await request(app.callback()).get("/");

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ error: "Internal Server Error" });
  });

  it("returns custom status code when error has status property", async () => {
    const app = createTestApp(errorHandler, async () => {
      const err: any = new Error("bad input");
      err.status = 400;
      throw err;
    });

    const res = await request(app.callback()).get("/");

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ error: "bad input" });
  });
});
