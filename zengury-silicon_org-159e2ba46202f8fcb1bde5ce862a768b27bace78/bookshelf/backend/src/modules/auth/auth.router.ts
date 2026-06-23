import { Router, Request, Response } from "express";
import { registerSchema, loginSchema, oauthSchema } from "./auth.schema";
import * as authService from "./auth.service";

const router = Router();

router.post("/register", async (req: Request, res: Response, next) => {
  try {
    const input = registerSchema.parse(req.body);
    const result = await authService.register(input);
    res.status(201).json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.post("/login", async (req: Request, res: Response, next) => {
  try {
    const input = loginSchema.parse(req.body);
    const result = await authService.login(input);
    res.json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.post("/oauth", async (req: Request, res: Response, next) => {
  try {
    const input = oauthSchema.parse(req.body);
    const result = await authService.oauthLogin(input);
    res.json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.post("/logout", (_req: Request, res: Response) => {
  res.status(204).send();
});

export default router;
