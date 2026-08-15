import Koa from "koa";
import cors from "@koa/cors";
import { koaBody } from "koa-body";
import Router from "@koa/router";
import { errorHandler } from "./middleware/errorHandler";
import { notFound } from "./middleware/notFound";
import { requestLogger } from "./middleware/requestLogger";
import { RegisterRoutes } from "./generated/routes";

const app = new Koa();

app.use(errorHandler);
app.use(requestLogger);
app.use(cors());
app.use(koaBody({
  multipart: false,
}));

const router = new Router();
RegisterRoutes(router);
app.use(router.routes());
app.use(router.allowedMethods());
app.use(notFound);

export default app;
