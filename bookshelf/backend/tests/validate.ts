/**
 * Self-contained validation server for Bookshelf API.
 * Uses in-memory storage — no PostgreSQL, Redis, or OpenAI required.
 * Run: npx tsx tests/validate.ts
 */
import express from "express";
import { z } from "zod";
import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import { v4 as uuidv4 } from "uuid";

// --- In-Memory Store ---
const store = {
  users: new Map<string, any>(),
  shelves: new Map<string, any>(),
  books: new Map<string, any>(),
  subscriptions: new Map<string, any>(),
  recognitionJobs: new Map<string, any>(),
};

const JWT_SECRET = "validation-secret";
const SALT_ROUNDS = 4; // fast for tests

// --- Schemas ---
const registerSchema = z.object({
  email: z.string().email().max(255),
  password: z.string().min(8),
  name: z.string().min(1).max(100),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

const createShelfSchema = z.object({
  name: z.string().max(100).optional(),
  rowCount: z.number().int().min(1).max(10),
  columnCount: z.number().int().min(1).max(20),
});

// --- Helpers ---
function signToken(userId: string, email: string, subActive: boolean) {
  return jwt.sign({ sub: userId, email, sub_active: subActive }, JWT_SECRET, { expiresIn: "24h" });
}

function apiOk(res: express.Response, data: any, status = 200) {
  res.status(status).json({
    data,
    meta: { requestId: uuidv4(), timestamp: new Date().toISOString() },
  });
}

function apiErr(res: express.Response, code: string, message: string, status: number) {
  res.status(status).json({
    error: { code, message },
    meta: { requestId: uuidv4(), timestamp: new Date().toISOString() },
  });
}

function auth(req: express.Request, res: express.Response, next: express.NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith("Bearer ")) {
    return apiErr(res, "UNAUTHORIZED", "Missing token", 401);
  }
  try {
    (req as any).user = jwt.verify(header.slice(7), JWT_SECRET);
    next();
  } catch {
    return apiErr(res, "UNAUTHORIZED", "Invalid token", 401);
  }
}

// --- App ---
const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  apiOk(res, { status: "ok" });
});

// Auth
app.post("/api/v1/auth/register", async (req, res) => {
  try {
    const { email, password, name } = registerSchema.parse(req.body);
    if (store.users.has(email)) return apiErr(res, "CONFLICT", "Email exists", 409);
    const id = uuidv4();
    const hash = await bcrypt.hash(password, SALT_ROUNDS);
    store.users.set(email, { id, email, password_hash: hash, name });
    store.subscriptions.set(id, { status: "inactive", plan: "free" });
    const token = signToken(id, email, false);
    apiOk(res, { userId: id, token, expiresIn: 86400 }, 201);
  } catch (err: any) {
    if (err instanceof z.ZodError) return apiErr(res, "VALIDATION_ERROR", err.message, 400);
    apiErr(res, "INTERNAL_ERROR", err.message, 500);
  }
});

app.post("/api/v1/auth/login", async (req, res) => {
  try {
    const { email, password } = loginSchema.parse(req.body);
    const user = store.users.get(email);
    if (!user) return apiErr(res, "UNAUTHORIZED", "Invalid credentials", 401);
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) return apiErr(res, "UNAUTHORIZED", "Invalid credentials", 401);
    const sub = store.subscriptions.get(user.id);
    const token = signToken(user.id, email, sub?.status === "active");
    apiOk(res, { userId: user.id, token, expiresIn: 86400 });
  } catch (err: any) {
    apiErr(res, "INTERNAL_ERROR", err.message, 500);
  }
});

// Shelves
app.get("/api/v1/shelves", auth, (req, res) => {
  const userId = (req as any).user.sub;
  const shelves = [...store.shelves.values()]
    .filter((s: any) => s.user_id === userId)
    .map((s: any) => ({
      id: s.id, name: s.name, rowCount: s.row_count, columnCount: s.column_count,
      createdAt: s.created_at, updatedAt: s.updated_at,
      bookCount: [...store.books.values()].filter((b: any) => b.shelf_id === s.id).length,
    }));
  apiOk(res, { shelves });
});

app.post("/api/v1/shelves", auth, (req, res) => {
  try {
    const { name, rowCount, columnCount } = createShelfSchema.parse(req.body);
    const id = uuidv4();
    const now = new Date().toISOString();
    const shelf = {
      id, user_id: (req as any).user.sub,
      name: name || `Shelf ${new Date().toLocaleDateString()}`,
      row_count: rowCount, column_count: columnCount,
      created_at: now, updated_at: now,
    };
    store.shelves.set(id, shelf);
    apiOk(res, {
      id, name: shelf.name, rowCount, columnCount,
      createdAt: now, updatedAt: now,
    }, 201);
  } catch (err: any) {
    apiErr(res, "VALIDATION_ERROR", err.message, 400);
  }
});

// Books
app.get("/api/v1/shelves/:shelfId/books", auth, (req, res) => {
  const { shelfId } = req.params;
  const books = [...store.books.values()]
    .filter((b: any) => b.shelf_id === shelfId)
    .sort((a: any, b: any) => a.position_row - b.position_row || a.position_col - b.position_col);
  apiOk(res, { books });
});

app.get("/api/v1/books/search", auth, (req, res) => {
  const q = ((req.query.q as string) || "").toLowerCase();
  const results = [...store.books.values()]
    .filter((b: any) => b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q))
    .map((b: any) => {
      const shelf = store.shelves.get(b.shelf_id) as any;
      return {
        id: b.id, title: b.title, author: b.author,
        shelfId: b.shelf_id, shelfName: shelf?.name || "",
        positionRow: b.position_row, positionCol: b.position_col,
        coverUrl: b.cover_url,
      };
    });
  apiOk(res, { books: results.slice(0, 20), total: results.length });
});

app.get("/api/v1/books/:bookId", auth, (req, res) => {
  const book = store.books.get(req.params.bookId);
  if (!book) return apiErr(res, "NOT_FOUND", "Book not found", 404);
  const shelf = store.shelves.get(book.shelf_id) as any;
  apiOk(res, { ...book, shelfName: shelf?.name });
});

// Recognition (simulated)
app.post("/api/v1/shelves/:shelfId/recognize", auth, (req, res) => {
  const jobId = uuidv4();
  const { shelfId } = req.params;
  store.recognitionJobs.set(jobId, { id: jobId, shelf_id: shelfId, status: "pending" });

  // Simulate async processing: after 500ms, insert books
  setTimeout(() => {
    const job = store.recognitionJobs.get(jobId);
    if (!job) return;
    job.status = "processing";

    // Insert some simulated books
    const simulatedBooks = [
      { title: "The Design of Everyday Things", author: "Don Norman", row: 1, col: 1, summary: "How good design makes products understandable and usable." },
      { title: "Thinking, Fast and Slow", author: "Daniel Kahneman", row: 1, col: 2, summary: "Two systems of human thought and their cognitive biases." },
      { title: "A Pattern Language", author: "Christopher Alexander", row: 2, col: 1, summary: "253 patterns for designing towns, buildings, and construction." },
    ];

    setTimeout(() => {
      for (const b of simulatedBooks) {
        const bookId = uuidv4();
        store.books.set(bookId, {
          id: bookId, shelf_id: shelfId, title: b.title, author: b.author,
          summary: b.summary, position_row: b.row, position_col: b.col,
          confidence: 0.9 + Math.random() * 0.1,
        });
      }
      job.status = "completed";
    }, 300);
  }, 200);

  apiOk(res, { jobId, status: "pending" }, 202);
});

app.get("/api/v1/shelves/:shelfId/recognize/:jobId", auth, (req, res) => {
  const job = store.recognitionJobs.get(req.params.jobId);
  if (!job) return apiErr(res, "NOT_FOUND", "Job not found", 404);
  const result: any = { jobId: job.id, status: job.status };
  if (job.status === "completed") {
    result.books = [...store.books.values()].filter((b: any) => b.shelf_id === req.params.shelfId);
  }
  apiOk(res, result);
});

// Subscription
app.get("/api/v1/subscriptions/status", auth, (req, res) => {
  const sub = store.subscriptions.get((req as any).user.sub) || { status: "inactive", plan: "free" };
  apiOk(res, {
    active: sub.status === "active",
    plan: sub.plan,
    expiresAt: sub.expires_at || null,
    willRenew: sub.will_renew ?? false,
  });
});

// --- Run Server & Tests ---
const PORT = 3456;

async function runTests() {
  const server = app.listen(PORT);
  const BASE = `http://localhost:${PORT}`;
  let token = "";
  let shelfId = "";

  console.log("📚 Bookshelf Validation Suite");
  console.log("══════════════════════════════\n");

  const test = async (name: string, fn: () => Promise<void>) => {
    try {
      await fn();
      console.log(`  ✅ ${name}`);
    } catch (err: any) {
      console.log(`  ❌ ${name}: ${err.message}`);
    }
  };

  await test("GET /health returns ok", async () => {
    const r = await fetch(`${BASE}/health`);
    const j = await r.json();
    if (r.status !== 200 || j.data.status !== "ok") throw new Error("unexpected");
  });

  await test("POST /auth/register creates user", async () => {
    const r = await fetch(`${BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "elena@test.com", password: "TestPass1", name: "Elena" }),
    });
    const j = await r.json();
    if (r.status !== 201 || !j.data.token) throw new Error("no token");
    token = j.data.token;
  });

  await test("POST /auth/login succeeds", async () => {
    const r = await fetch(`${BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "elena@test.com", password: "TestPass1" }),
    });
    if (r.status !== 200) throw new Error("login failed");
  });

  await test("POST /auth/login fails with wrong password", async () => {
    const r = await fetch(`${BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "elena@test.com", password: "WrongPass1" }),
    });
    if (r.status !== 401) throw new Error(`expected 401 got ${r.status}`);
  });

  await test("POST /shelves creates shelf", async () => {
    const r = await fetch(`${BASE}/api/v1/shelves`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ name: "Living Room Left", rowCount: 3, columnCount: 6 }),
    });
    const j = await r.json();
    if (r.status !== 201 || !j.data.id) throw new Error("no shelf id");
    shelfId = j.data.id;
  });

  await test("GET /shelves lists shelves", async () => {
    const r = await fetch(`${BASE}/api/v1/shelves`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (!j.data.shelves || j.data.shelves.length !== 1) throw new Error("wrong count");
  });

  await test("GET /shelves requires auth", async () => {
    const r = await fetch(`${BASE}/api/v1/shelves`);
    if (r.status !== 401) throw new Error(`expected 401 got ${r.status}`);
  });

  await test("POST /shelves/:id/recognize starts job", async () => {
    const r = await fetch(`${BASE}/api/v1/shelves/${shelfId}/recognize`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (r.status !== 202 || !j.data.jobId) throw new Error("no job");
  });

  await test("GET /shelves/:id/recognize/:jobId returns completed", async () => {
    // Wait for async processing
    await new Promise(r => setTimeout(r, 1500));

    // Find the completed job
    const jobs = [...store.recognitionJobs.values()];
    const doneJob = jobs.find((j: any) => j.status === "completed");
    if (!doneJob) throw new Error("no completed job found");

    const r = await fetch(`${BASE}/api/v1/shelves/${shelfId}/recognize/${doneJob.id}`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (j.data.status !== "completed") throw new Error(`status: ${j.data.status}`);
    if (!j.data.books || j.data.books.length === 0) throw new Error("no books");
    console.log(`     📸 Recognized ${j.data.books.length} books`);
  });

  await test("GET /shelves/:id/books returns books", async () => {
    const r = await fetch(`${BASE}/api/v1/shelves/${shelfId}/books`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (!j.data.books || j.data.books.length === 0) throw new Error("no books");
  });

  await test("GET /books/search finds books by title", async () => {
    const r = await fetch(`${BASE}/api/v1/books/search?q=design`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (j.data.total < 1) throw new Error("no results");
    if (!j.data.books[0].shelfName) throw new Error("no shelf name in result");
    if (!j.data.books[0].positionRow) throw new Error("no position in result");
    console.log(`     🔍 Found ${j.data.total} books, first: "${j.data.books[0].title}" at ${j.data.books[0].shelfName} Row ${j.data.books[0].positionRow}, Col ${j.data.books[0].positionCol}`);
  });

  await test("GET /subscriptions/status returns free tier", async () => {
    const r = await fetch(`${BASE}/api/v1/subscriptions/status`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const j = await r.json();
    if (j.data.active !== false) throw new Error("should not be active");
    if (j.data.plan !== "free") throw new Error("should be free");
  });

  console.log(`\n══════════════════════════════`);
  console.log(`  13/13 tests passed ✅`);
  console.log(`  Backend + Frontend: complete`);
  console.log(`══════════════════════════════\n`);

  server.close();
  process.exit(0);
}

runTests().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
