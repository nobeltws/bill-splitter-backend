import { Context } from "koa";
import { validateCreateSessionInput } from "../services/session.service";
import { createSession, findSessionById } from "../repos/session.repo";

export async function createSessionHandler(ctx: Context): Promise<void> {
  const input = ctx.request.body as any;

  const error = validateCreateSessionInput(input);
  if (error) {
    ctx.status = 400;
    ctx.body = { error };
    return;
  }

  const session = await createSession({
    hostPaynowId: input.hostPaynowId,
    tax: input.tax ?? 0,
    serviceCharge: input.serviceCharge ?? 0,
    discount: input.discount ?? 0,
    items: input.items,
  });

  ctx.status = 201;
  ctx.body = {
    sessionId: session.id,
    createdAt: session.createdAt,
  };
}

export async function getSessionHandler(ctx: Context): Promise<void> {
  const { id } = ctx.params;

  const session = await findSessionById(id);
  if (!session) {
    ctx.status = 404;
    ctx.body = { error: "Session not found" };
    return;
  }

  ctx.status = 200;
  ctx.body = {
    sessionId: session.id,
    hostPaynowId: session.hostPaynowId,
    items: session.items.map((item) => ({
      id: item.id,
      name: item.name,
      quantity: item.quantity,
      unitPrice: Number(item.unitPrice),
    })),
    tax: Number(session.tax),
    serviceCharge: Number(session.serviceCharge),
    discount: Number(session.discount),
    claims: [],
    payments: [],
    createdAt: session.createdAt,
  };
}
