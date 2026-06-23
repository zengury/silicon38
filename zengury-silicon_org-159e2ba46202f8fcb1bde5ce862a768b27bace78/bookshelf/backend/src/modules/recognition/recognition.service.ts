import { Queue, Worker, Job } from "bullmq";
import { config } from "../../config";
import db from "../../db/knex";
import { ApiError } from "../../middleware/errorHandler";

const connection = { host: config.redis.host, port: config.redis.port };

export const recognitionQueue = new Queue("recognition", { connection });

export async function createRecognitionJob(userId: string, shelfId: string, photoKey: string) {
  const shelf = await db("shelves").where({ id: shelfId, user_id: userId }).first();
  if (!shelf) throw new ApiError(404, "NOT_FOUND", "Shelf not found");

  const [job] = await db("recognition_jobs")
    .insert({ shelf_id: shelfId, user_id: userId, photo_key: photoKey, status: "pending" })
    .returning("*");

  await recognitionQueue.add("recognize", {
    jobId: job.id,
    shelfId,
    userId,
    photoKey,
    rowCount: shelf.row_count,
    columnCount: shelf.column_count,
  });

  return job;
}

export async function getRecognitionJob(userId: string, shelfId: string, jobId: string) {
  const job = await db("recognition_jobs").where({ id: jobId, shelf_id: shelfId, user_id: userId }).first();
  if (!job) throw new ApiError(404, "NOT_FOUND", "Recognition job not found");
  return job;
}

// --- Worker: processes recognition jobs ---

interface RecognitionJobData {
  jobId: string;
  shelfId: string;
  userId: string;
  photoKey: string;
  rowCount: number;
  columnCount: number;
}

const worker = new Worker<RecognitionJobData>(
  "recognition",
  async (job: Job<RecognitionJobData>) => {
    const { jobId, shelfId, userId, photoKey } = job.data;

    await db("recognition_jobs").where({ id: jobId }).update({ status: "processing", updated_at: db.fn.now() });
    await job.updateProgress(10);

    try {
      // Step 1: Build prompt for GPT-4o Vision
      const prompt = buildRecognitionPrompt(job.data);

      // Step 2: Call GPT-4o Vision API
      const books = await callGpt4oVision(photoKey, prompt);
      await job.updateProgress(50);

      // Step 3: Store recognized books
      if (books.length === 0) {
        await db("recognition_jobs").where({ id: jobId }).update({
          status: "completed",
          error_message: "No books recognized in this photo",
          updated_at: db.fn.now(),
        });
        return;
      }

      await db.transaction(async (trx) => {
        for (const book of books) {
          await trx("books").insert({
            shelf_id: shelfId,
            title: book.title,
            author: book.author || "Unknown",
            summary: book.summary || "",
            position_row: Math.min(book.row, job.data.rowCount),
            position_col: Math.min(book.column, job.data.columnCount),
            confidence: book.confidence || 1.0,
          });
        }
      });

      await job.updateProgress(100);
      await db("recognition_jobs").where({ id: jobId }).update({ status: "completed", updated_at: db.fn.now() });
    } catch (err: any) {
      await db("recognition_jobs").where({ id: jobId }).update({
        status: "failed",
        error_message: err.message || "Recognition failed",
        updated_at: db.fn.now(),
      });
      throw err;
    }
  },
  { connection, concurrency: 3 }
);

worker.on("completed", (job) => {
  console.log(`[recognition] job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`[recognition] job ${job?.id} failed:`, err.message);
});

// --- GPT-4o Vision Client ---

interface RecognizedBook {
  title: string;
  author: string;
  summary: string;
  row: number;
  column: number;
  confidence?: number;
}

function buildRecognitionPrompt(data: RecognitionJobData): string {
  return `Identify every book in this bookshelf photo. The shelf has ${data.rowCount} rows and ${data.columnCount} columns.

For each book, return:
- title: the exact title
- author: the author's name
- row: the row number (1 = top, ${data.rowCount} = bottom)
- column: the column number (1 = left, ${data.columnCount} = right)
- summary: a 2-3 sentence summary of the book's content
- confidence: a number 0.0-1.0 indicating your confidence in the recognition (1.0 = certain)

Return ONLY a JSON object with a "books" array. Do not include any other text.`;
}

async function callGpt4oVision(photoKey: string, prompt: string): Promise<RecognizedBook[]> {
  if (!config.openai.apiKey) {
    // Dev mode: return simulated books for testing
    console.warn("[recognition] No OPENAI_API_KEY — returning simulated results");
    return getSimulatedBooks();
  }

  const photoUrl = `${config.s3.endpoint}/${config.s3.bucket}/${photoKey}`;

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${config.openai.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: config.openai.model,
      messages: [{
        role: "user",
        content: [
          { type: "text", text: prompt },
          { type: "image_url", image_url: { url: photoUrl, detail: "high" } },
        ],
      }],
      response_format: { type: "json_object" },
      max_tokens: 4096,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`GPT-4o API error: ${response.status} ${err}`);
  }

  const data = await response.json() as any;
  const content = data.choices?.[0]?.message?.content;
  if (!content) throw new Error("GPT-4o returned empty response");

  const parsed = JSON.parse(content);
  return parsed.books || [];
}

function getSimulatedBooks(): RecognizedBook[] {
  return [
    { title: "The Design of Everyday Things", author: "Don Norman", summary: "Explores how good design makes products understandable and usable, introducing concepts like affordances, signifiers, and the gulfs of execution and evaluation.", row: 1, column: 1, confidence: 0.95 },
    { title: "Thinking, Fast and Slow", author: "Daniel Kahneman", summary: "Examines the two systems of human thought: the fast, intuitive System 1 and the slow, deliberate System 2, revealing cognitive biases that affect decision-making.", row: 1, column: 2, confidence: 0.92 },
    { title: "A Pattern Language", author: "Christopher Alexander", summary: "Presents 253 patterns for designing towns, buildings, and construction, emphasizing human-centered design that creates spaces where people feel alive and connected.", row: 2, column: 1, confidence: 0.88 },
    { title: "The Timeless Way of Building", author: "Christopher Alexander", summary: "Introduces the concept of a 'quality without a name' that makes buildings and spaces feel alive, arguing that this quality emerges from pattern languages rather than imposed design.", row: 2, column: 2, confidence: 0.87 },
    { title: "High Output Management", author: "Andrew S. Grove", summary: "A practical guide to management from Intel's former CEO, covering managerial leverage, meetings, decision-making, motivation, and performance appraisal.", row: 3, column: 1, confidence: 0.93 },
  ];
}
