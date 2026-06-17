import db from "../../db/knex";
import { ApiError } from "../../middleware/errorHandler";
import type { SearchBooksInput } from "./books.schema";

export async function getShelfBooks(userId: string, shelfId: string) {
  const shelf = await db("shelves").where({ id: shelfId, user_id: userId }).first();
  if (!shelf) throw new ApiError(404, "NOT_FOUND", "Shelf not found");

  return db("books")
    .where({ shelf_id: shelfId })
    .orderBy("position_row", "asc")
    .orderBy("position_col", "asc");
}

export async function getBook(userId: string, bookId: string) {
  const book = await db("books")
    .join("shelves", "books.shelf_id", "shelves.id")
    .where("shelves.user_id", userId)
    .where("books.id", bookId)
    .select("books.*", "shelves.name as shelf_name")
    .first();
  if (!book) throw new ApiError(404, "NOT_FOUND", "Book not found");
  return book;
}

export async function searchBooks(userId: string, input: SearchBooksInput) {
  const query = input.q.trim().replace(/[^a-zA-Z0-9\s]/g, "");

  const [{ count }] = await db("books")
    .join("shelves", "books.shelf_id", "shelves.id")
    .where("shelves.user_id", userId)
    .whereRaw(
      `to_tsvector('english', coalesce(books.title,'') || ' ' || coalesce(books.author,'')) @@ plainto_tsquery('english', ?)`,
      [query]
    )
    .count("* as count");

  const books = await db("books")
    .join("shelves", "books.shelf_id", "shelves.id")
    .where("shelves.user_id", userId)
    .whereRaw(
      `to_tsvector('english', coalesce(books.title,'') || ' ' || coalesce(books.author,'')) @@ plainto_tsquery('english', ?)`,
      [query]
    )
    .select(
      "books.id",
      "books.title",
      "books.author",
      "books.shelf_id",
      "shelves.name as shelf_name",
      "books.position_row",
      "books.position_col",
      "books.cover_url"
    )
    .orderByRaw(`ts_rank(to_tsvector('english', coalesce(books.title,'') || ' ' || coalesce(books.author,'')), plainto_tsquery('english', ?)) DESC`, [query])
    .limit(input.limit)
    .offset(input.offset);

  return { books, total: parseInt(count as string, 10) };
}
