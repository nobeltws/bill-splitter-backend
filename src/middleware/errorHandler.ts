import { Context, Next } from "koa";

export async function errorHandler(ctx: Context, next: Next): Promise<void> {
  try {
    await next();
  } catch (err: any) {
    const status = err.status || 500;
    const message = status === 500 ? "Internal Server Error" : err.message;
    ctx.status = status;
    ctx.body = { error: message };
  }
}
