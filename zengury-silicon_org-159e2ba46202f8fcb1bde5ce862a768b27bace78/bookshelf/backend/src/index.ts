import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import { config } from "./config";
import { errorHandler, notFound } from "./middleware/errorHandler";
import authRouter from "./modules/auth/auth.router";
import shelvesRouter from "./modules/shelves/shelves.router";
import booksRouter from "./modules/books/books.router";
import recognitionRouter from "./modules/recognition/recognition.router";
import subscriptionsRouter from "./modules/subscriptions/subscriptions.router";

export function createApp() {
  const app = express();

  // Global middleware
  app.use(helmet());
  app.use(cors());
  app.use(morgan("short"));
  app.use(express.json());

  // Health check
  app.get("/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // API routes
  app.use("/api/v1/auth", authRouter);
  app.use("/api/v1/shelves", shelvesRouter);
  app.use("/api/v1/shelves", recognitionRouter); // /api/v1/shelves/:shelfId/recognize
  app.use("/api/v1/books", booksRouter);
  app.use("/api/v1/subscriptions", subscriptionsRouter);

  // 404 handler
  app.use(notFound);

  // Error handler
  app.use(errorHandler);

  return app;
}

// Start server if this is the main module
if (require.main === module) {
  const app = createApp();
  app.listen(config.port, () => {
    console.log(`📚 Bookshelf API listening on port ${config.port}`);
    console.log(`   Health: http://localhost:${config.port}/health`);
    console.log(`   Auth:   http://localhost:${config.port}/api/v1/auth`);
  });
}
