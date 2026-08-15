import Router from "@koa/router";
import { healthCheck } from "../controllers/health.controller";

const router = new Router();

router.get("/health", healthCheck);

export default router;
