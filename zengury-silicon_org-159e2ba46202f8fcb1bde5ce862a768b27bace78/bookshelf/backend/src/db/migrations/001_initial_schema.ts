import type { Knex } from "knex";

export async function up(knex: Knex): Promise<void> {
  await knex.schema.raw('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

  await knex.schema.createTable("users", (t) => {
    t.uuid("id").primary().defaultTo(knex.raw("gen_random_uuid()"));
    t.text("email").notNullable().unique();
    t.text("password_hash");
    t.text("name").notNullable();
    t.text("oauth_provider").checkIn(["google", "apple"]);
    t.text("oauth_id");
    t.boolean("share_shelf").defaultTo(false);
    t.timestamps(true, true);
  });

  await knex.schema.createTable("shelves", (t) => {
    t.uuid("id").primary().defaultTo(knex.raw("gen_random_uuid()"));
    t.uuid("user_id").notNullable().references("id").inTable("users").onDelete("CASCADE");
    t.text("name").notNullable();
    t.integer("row_count").notNullable().checkBetween([1, 10]);
    t.integer("column_count").notNullable().checkBetween([1, 20]);
    t.timestamps(true, true);
    t.index("user_id");
  });

  await knex.schema.createTable("books", (t) => {
    t.uuid("id").primary().defaultTo(knex.raw("gen_random_uuid()"));
    t.uuid("shelf_id").notNullable().references("id").inTable("shelves").onDelete("CASCADE");
    t.text("title").notNullable();
    t.text("author").notNullable().defaultTo("Unknown");
    t.text("summary");
    t.text("isbn");
    t.text("cover_url");
    t.integer("position_row").notNullable();
    t.integer("position_col").notNullable();
    t.float("confidence").defaultTo(1.0);
    t.timestamp("created_at").defaultTo(knex.fn.now());
    t.index("shelf_id");
  });

  await knex.schema.raw(`
    CREATE INDEX idx_books_fts ON books
    USING GIN(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(author,'')))
  `);

  await knex.schema.createTable("recognition_jobs", (t) => {
    t.uuid("id").primary().defaultTo(knex.raw("gen_random_uuid()"));
    t.uuid("shelf_id").notNullable().references("id").inTable("shelves").onDelete("CASCADE");
    t.uuid("user_id").notNullable().references("id").inTable("users").onDelete("CASCADE");
    t.text("photo_key").notNullable();
    t.text("status").notNullable().defaultTo("pending");
    t.text("error_message");
    t.timestamps(true, true);
    t.index("shelf_id");
  });

  await knex.schema.createTable("subscriptions", (t) => {
    t.uuid("id").primary().defaultTo(knex.raw("gen_random_uuid()"));
    t.uuid("user_id").notNullable().unique().references("id").inTable("users").onDelete("CASCADE");
    t.text("status").notNullable().defaultTo("inactive");
    t.text("plan").notNullable().defaultTo("free");
    t.text("original_transaction_id");
    t.text("latest_receipt");
    t.timestamp("expires_at");
    t.boolean("will_renew").defaultTo(true);
    t.timestamps(true, true);
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists("subscriptions");
  await knex.schema.dropTableIfExists("recognition_jobs");
  await knex.schema.dropTableIfExists("books");
  await knex.schema.dropTableIfExists("shelves");
  await knex.schema.dropTableIfExists("users");
}
