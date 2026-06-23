import { Request, Response, NextFunction } from "express";

export function requireSubscription(req: Request, res: Response, next: NextFunction): void {
  if (!req.user?.sub_active) {
    res.status(403).json({
      error: { code: "FORBIDDEN", message: "Subscription required for this feature" },
      meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() },
    });
    return;
  }
  next();
}

export function softSubscriptionGate(req: Request, res: Response, next: NextFunction): void {
  // soft gate: allow but limited — actual limits checked per-endpoint
  next();
}
