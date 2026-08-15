import Router from "@koa/router";
import { healthCheck } from "../controllers/health.controller";
import { parseReceipt } from "../controllers/receipt.controller";
import { createSessionHandler, getSessionHandler } from "../controllers/session.controller";

const router = new Router();

router.get("/health", healthCheck);
router.post("/api/receipts/parse", parseReceipt);
router.post("/api/sessions", createSessionHandler);
router.get("/api/sessions/:id", getSessionHandler);

export default router;
