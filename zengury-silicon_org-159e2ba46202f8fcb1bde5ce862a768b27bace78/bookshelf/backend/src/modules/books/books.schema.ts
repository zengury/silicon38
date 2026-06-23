import { z } from "zod";

export const searchBooksSchema = z.object({
  q: z.string().min(1).max(200),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
});

export type SearchBooksInput = z.infer<typeof searchBooksSchema>;
