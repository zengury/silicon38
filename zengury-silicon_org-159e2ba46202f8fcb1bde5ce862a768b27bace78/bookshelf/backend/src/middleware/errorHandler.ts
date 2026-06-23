import { Request, Response, NextFunction } from "express";
import { ZodError } from "zod";

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
    public details?: Array<{ field: string; message: string }>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction): void {
  const requestId = (req.headers["x-request-id"] as string) || "";

  if (err instanceof ApiError) {
    res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, details: err.details },
      meta: { requestId, timestamp: new Date().toISOString() },
    });
    return;
  }

  if (err instanceof ZodError) {
    res.status(400).json({
      error: {
        code: "VALIDATION_ERROR",
        message: "Invalid request",
        details: err.errors.map((e) => ({ field: e.path.join("."), message: e.message })),
      },
      meta: { requestId, timestamp: new Date().toISOString() },
    });
    return;
  }

  console.error("Unhandled error:", err);
  res.status(500).json({
    error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" },
    meta: { requestId, timestamp: new Date().toISOString() },
  });
}

export function notFound(_req: Request, res: Response): void {
  res.status(404).json({
    error: { code: "NOT_FOUND", message: "Resource not found" },
    meta: { requestId: "", timestamp: new Date().toISOString() },
  });
}
