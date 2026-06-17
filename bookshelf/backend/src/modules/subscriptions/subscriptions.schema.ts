import { z } from "zod";

export const verifyReceiptSchema = z.object({
  receiptData: z.string().min(1),
});

export type VerifyReceiptInput = z.infer<typeof verifyReceiptSchema>;
