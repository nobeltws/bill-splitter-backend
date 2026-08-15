import { Body, Controller, Get, Path, Post, Route, Response, SuccessResponse } from "tsoa";
import { validateCreateSessionInput } from "../services/session.service";
import { createSession, findSessionById } from "../repos/session.repo";
import { ErrorResponse } from "../types/api";

interface ItemInput {
  name: string;
  /** @minimum 1 */
  quantity: number;
  /** @minimum 0.01 */
  unitPrice: number;
}

interface CreateSessionRequest {
  hostPaynowId: string;
  /** @minItems 1 */
  items: ItemInput[];
  tax?: number;
  serviceCharge?: number;
  discount?: number;
}

interface CreateSessionResponse {
  sessionId: string;
  createdAt: Date;
}

interface ItemOutput {
  id: string;
  name: string;
  quantity: number;
  unitPrice: number;
}

interface SessionResponse {
  sessionId: string;
  hostPaynowId: string;
  items: ItemOutput[];
  tax: number;
  serviceCharge: number;
  discount: number;
  claims: Record<string, any>[];
  payments: Record<string, any>[];
  createdAt: Date;
}

@Route("api/sessions")
export class SessionController extends Controller {
  @SuccessResponse("201", "Created")
  @Response<ErrorResponse>(400, "Validation error")
  @Post()
  public async createSession(@Body() body: CreateSessionRequest): Promise<CreateSessionResponse> {
    const error = validateCreateSessionInput({
      hostPaynowId: body.hostPaynowId,
      items: body.items,
      tax: body.tax ?? 0,
      serviceCharge: body.serviceCharge ?? 0,
      discount: body.discount ?? 0,
    });

    if (error) {
      this.setStatus(400);
      return { error } as any;
    }

    const session = await createSession({
      hostPaynowId: body.hostPaynowId,
      tax: body.tax ?? 0,
      serviceCharge: body.serviceCharge ?? 0,
      discount: body.discount ?? 0,
      items: body.items,
    });

    this.setStatus(201);
    return {
      sessionId: session.id,
      createdAt: session.createdAt,
    };
  }

  @Response<ErrorResponse>(404, "Session not found")
  @Get("{id}")
  public async getSession(@Path() id: string): Promise<SessionResponse> {
    const session = await findSessionById(id);

    if (!session) {
      this.setStatus(404);
      return { error: "Session not found" } as any;
    }

    return {
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
}
