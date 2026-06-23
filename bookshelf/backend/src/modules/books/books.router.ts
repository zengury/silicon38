import { Router, Request, Response } from "express";
import { auth } from "../../middleware/auth";
import { searchBooksSchema } from "./books.schema";
import * as booksService from "./books.service";

const router = Router();
router.use(auth);

router.get("/search", async (req: Request, res: Response, next) => {
  try {
    const input = searchBooksSchema.parse(req.query);
    const result = await booksService.searchBooks(req.user!.sub, input);
    res.json({ data: result, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.get("/:bookId", async (req: Request, res: Response, next) => {
  try {
    const book = await booksService.getBook(req.user!.sub, req.params.bookId as string);
    res.json({ data: book, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

export default router;
