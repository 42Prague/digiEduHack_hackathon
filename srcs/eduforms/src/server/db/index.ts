import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";

import { env } from "~/env";
import * as schema from "./schema";

/**
 * Cache the database connection in development. This avoids creating a new connection on every HMR
 * update.
 */
const globalForDb = globalThis as unknown as {
  conn: postgres.Sql | undefined;
};

const conn = globalForDb.conn ?? postgres(env.DATABASE_URL);
if (env.NODE_ENV !== "production") globalForDb.conn = conn;


export const db = drizzle(conn, { schema });

// Skip migrations during build process
if (process.env.SKIP_MIGRATIONS !== "true") {
  await migrate(db, {
      migrationsFolder: "drizzle",
  });
}