import db from "../../db/knex";
import { ApiError } from "../../middleware/errorHandler";
import type { CreateShelfInput } from "./shelves.schema";

export async function listShelves(userId: string) {
  return db("shelves")
    .where({ user_id: userId })
    .leftJoin(
      db("books").select("shelf_id").count("* as book_count").groupBy("shelf_id").as("bc"),
      "shelves.id",
      "bc.shelf_id"
    )
    .select("shelves.*", db.raw("COALESCE(bc.book_count, 0)::int as book_count"))
    .orderBy("created_at", "desc");
}

export async function createShelf(userId: string, input: CreateShelfInput) {
  const name = input.name || `Shelf ${new Date().toLocaleDateString()}`;
  const [shelf] = await db("shelves")
    .insert({ user_id: userId, name, row_count: input.rowCount, column_count: input.columnCount })
    .returning("*");
  return shelf;
}

export async function deleteShelf(userId: string, shelfId: string) {
  const shelf = await db("shelves").where({ id: shelfId, user_id: userId }).first();
  if (!shelf) throw new ApiError(404, "NOT_FOUND", "Shelf not found");
  await db("shelves").where({ id: shelfId }).del();
}
