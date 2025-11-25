import { auth } from "./config";
import { env } from "~/env";
import { db } from "~/server/db";
import { user } from "~/server/db/schema";
import { eq } from "drizzle-orm";

/**
 * Initializes the admin user on server startup.
 * Creates an admin user with credentials from environment variables if one doesn't exist.
 */
export async function initializeAdmin() {
  try {
    const adminEmail = env.ADMIN_NAME;
    const adminPassword = env.ADMIN_PASS;

    // Check if admin user already exists
    const existingAdmin = await db
      .select()
      .from(user)
      .where(eq(user.email, adminEmail))
      .limit(1);

    if (existingAdmin.length > 0) {
      console.log("✅ Admin user already exists");
      
      // Check if existing user has admin role
      if (existingAdmin[0]?.role !== "admin") {
        console.log("⚠️  Existing user doesn't have admin role, updating...");
        await db
          .update(user)
          .set({ role: "admin" })
          .where(eq(user.email, adminEmail));
        console.log("✅ Admin role assigned to existing user");
      }
      return;
    }

    // Create admin user using Better Auth API
    console.log("🔄 Creating admin user...");
    
    const newAdmin = await auth.api.signUpEmail({
      body: {
        email: adminEmail,
        password: adminPassword,
        name: "Administrator",
      },
    });

    // Set admin role
    if (newAdmin) {
      await db
        .update(user)
        .set({ role: "admin" })
        .where(eq(user.email, adminEmail));
      
      console.log("✅ Admin user created successfully");
    }
  } catch (error) {
    console.error("❌ Error initializing admin user:", error);
    // Don't throw - we don't want to prevent the server from starting
  }
}

