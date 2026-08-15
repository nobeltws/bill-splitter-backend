import { Context, Next } from "koa";

export async function notFound(ctx: Context, next: Next): Promise<void> {
  await next();
  if (ctx.status === 404 && !ctx.body) {
    ctx.status = 404;
    ctx.body = { error: "Not Found" };
  }
}
