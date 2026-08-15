import Koa from "koa";
import cors from "@koa/cors";
import { koaBody } from "koa-body";
import { errorHandler } from "./middleware/errorHandler";
import { notFound } from "./middleware/notFound";
import { requestLogger } from "./middleware/requestLogger";
import router from "./routes";

const app = new Koa();

app.use(errorHandler);
app.use(requestLogger);
app.use(cors());
app.use(koaBody({
  multipart: true,
  formidable: {
    maxFileSize: 10 * 1024 * 1024,
  },
}));
app.use(router.routes());
app.use(router.allowedMethods());
app.use(notFound);

export default app;
