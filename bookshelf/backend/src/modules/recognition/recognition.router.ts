import { Router, Request, Response } from "express";
import multer from "multer";
import { auth } from "../../middleware/auth";
import * as recognitionService from "./recognition.service";

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 20 * 1024 * 1024 } });
const router = Router();
router.use(auth);

router.post("/:shelfId/recognize", upload.single("image"), async (req: Request, res: Response, next) => {
  try {
    if (!req.file) {
      res.status(400).json({
        error: { code: "VALIDATION_ERROR", message: "Image file is required" },
        meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() },
      });
      return;
    }

    // In production: upload to S3 and get the key. For dev, use a temp key.
    const photoKey = `shelves/${req.user!.sub}/${req.params.shelfId}/${Date.now()}.jpg`;
    const job = await recognitionService.createRecognitionJob(req.user!.sub, req.params.shelfId as string, photoKey);

    res.status(202).json({
      data: { jobId: job.id, status: job.status },
      meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() },
    });
  } catch (err) { next(err); }
});

router.get("/:shelfId/recognize/:jobId", async (req: Request, res: Response, next) => {
  try {
    const job = await recognitionService.getRecognitionJob(req.user!.sub, req.params.shelfId as string, req.params.jobId as string);

    const result: any = { jobId: job.id, status: job.status };
    if (job.status === "completed") {
      const books = await import("../books/books.service").then(m =>
        m.getShelfBooks(req.user!.sub, req.params.shelfId as string)
      );
      result.books = books;
    }
    if (job.status === "failed") {
      result.error = job.error_message;
    }

    res.json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

export default router;
