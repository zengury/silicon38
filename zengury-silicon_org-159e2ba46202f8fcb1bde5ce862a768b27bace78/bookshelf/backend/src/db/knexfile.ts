import type { Knex } from "knex";
import type { Knex as KnexType } from "knex";

const knexConfig: KnexType.Config = {
  client: "pg",
  connection: {
    host: process.env.DB_HOST || "localhost",
    port: parseInt(process.env.DB_PORT || "5432"),
    user: process.env.DB_USER || "bookshelf",
    password: process.env.DB_PASSWORD || "bookshelf",
    database: process.env.DB_NAME || "bookshelf",
  },
  migrations: {
    directory: "./src/db/migrations",
    extension: "ts",
  },
};

export default knexConfig;
