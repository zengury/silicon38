import { Router, Request, Response } from "express";
import { auth } from "../../middleware/auth";
import { verifyReceiptSchema } from "./subscriptions.schema";
import * as subscriptionsService from "./subscriptions.service";

const router = Router();
router.use(auth);

router.get("/status", async (req: Request, res: Response, next) => {
  try {
    const status = await subscriptionsService.getSubscriptionStatus(req.user!.sub);
    res.json({ data: status, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.post("/verify", async (req: Request, res: Response, next) => {
  try {
    const input = verifyReceiptSchema.parse(req.body);
    const result = await subscriptionsService.verifyReceipt(req.user!.sub, input);
    res.json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

export default router;
