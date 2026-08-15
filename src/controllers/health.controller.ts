import { Controller, Get, Route } from "tsoa";

@Route("health")
export class HealthController extends Controller {
  @Get()
  public async healthCheck(): Promise<{ status: string }> {
    return { status: "ok" };
  }
}
