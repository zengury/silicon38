import { Router, Request, Response } from "express";
import { auth } from "../../middleware/auth";
import { createShelfSchema } from "./shelves.schema";
import * as shelvesService from "./shelves.service";

const router = Router();
router.use(auth);

router.get("/", async (req: Request, res: Response, next) => {
  try {
    const shelves = await shelvesService.listShelves(req.user!.sub);
    res.json({ data: { shelves }, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.post("/", async (req: Request, res: Response, next) => {
  try {
    const input = createShelfSchema.parse(req.body);
    const shelf = await shelvesService.createShelf(req.user!.sub, input);
    res.status(201).json({ data: shelf, meta: { requestId: req.headers["x-request-id"] as string || "", timestamp: new Date().toISOString() } });
  } catch (err) { next(err); }
});

router.delete("/:shelfId", async (req: Request, res: Response, next) => {
  try {
    await shelvesService.deleteShelf(req.user!.sub, req.params.shelfId as string);
    res.status(204).send();
  } catch (err) { next(err); }
});

export default router;
