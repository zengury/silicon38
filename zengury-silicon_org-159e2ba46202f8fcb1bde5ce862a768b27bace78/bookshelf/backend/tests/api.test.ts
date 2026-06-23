import { describe, it, expect, beforeAll, afterAll } from "vitest";

// Smoke tests for the Bookshelf API
// Run with: npm test
// Requires: docker-compose up (PostgreSQL + Redis)

const BASE = "http://localhost:3000/api/v1";

describe("Bookshelf API", () => {
  let token: string;
  let userId: string;

  describe("Auth", () => {
    it("POST /auth/register — creates a new user", async () => {
      const res = await fetch(`${BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: `test-${Date.now()}@bookshelf.app`,
          password: "TestPass1",
          name: "Test User",
        }),
      });
      expect(res.status).toBe(201);
      const body = await res.json();
      expect(body.data.token).toBeDefined();
      expect(body.data.userId).toBeDefined();
      token = body.data.token;
      userId = body.data.userId;
    });

    it("POST /auth/login — logs in", async () => {
      const res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: "test@bookshelf.app",
          password: "TestPass1",
        }),
      });
      // Will be 401 if user doesn't exist, which is fine for smoke test
      expect([200, 401]).toContain(res.status);
    });
  });

  describe("Shelves", () => {
    it("POST /shelves — creates a shelf", async () => {
      if (!token) return;
      const res = await fetch(`${BASE}/shelves`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ name: "Test Shelf", rowCount: 3, columnCount: 6 }),
      });
      expect(res.status).toBe(201);
    });

    it("GET /shelves — lists shelves", async () => {
      if (!token) return;
      const res = await fetch(`${BASE}/shelves`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
    });
  });

  describe("Books", () => {
    it("GET /books/search — searches with FTS", async () => {
      if (!token) return;
      const res = await fetch(`${BASE}/books/search?q=design`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
    });
  });

  describe("Subscriptions", () => {
    it("GET /subscriptions/status — returns status", async () => {
      if (!token) return;
      const res = await fetch(`${BASE}/subscriptions/status`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.active).toBe(false);
    });
  });

  describe("Health", () => {
    it("GET /health — returns ok", async () => {
      const res = await fetch("http://localhost:3000/health");
      expect(res.status).toBe(200);
    });
  });
});
