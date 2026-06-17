import { z } from "zod";

export const createRecognitionSchema = z.object({
  // image comes as multipart file, validated in router
});
