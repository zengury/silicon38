import { z } from "zod";

export const createShelfSchema = z.object({
  name: z.string().max(100).optional(),
  rowCount: z.number().int().min(1).max(10),
  columnCount: z.number().int().min(1).max(20),
});

export type CreateShelfInput = z.infer<typeof createShelfSchema>;
