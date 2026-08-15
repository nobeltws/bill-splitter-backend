import Router from "@koa/router";
import { healthCheck } from "../controllers/health.controller";
import { parseReceipt } from "../controllers/receipt.controller";

const router = new Router();

router.get("/health", healthCheck);
router.post("/api/receipts/parse", parseReceipt);

export default router;
