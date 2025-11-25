/**
 * This file is run once when the Next.js server starts.
 * It's used to initialize server-side resources and perform startup tasks.
 * 
 * @see https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    // Only run on server startup, not on edge runtime
    const { initializeAdmin } = await import("./server/better-auth/init-admin");
    await initializeAdmin();
  }
}

