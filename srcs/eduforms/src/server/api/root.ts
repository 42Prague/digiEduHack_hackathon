// import { postRouter } from "~/server/api/routers/post";
import { adminRouter } from "~/server/api/routers/admin";
import { institutionsRouter } from "~/server/api/routers/institutions";
import { formsRouter } from "~/server/api/routers/forms";
import { createCallerFactory, createTRPCRouter } from "~/server/api/trpc";

/**
 * This is the primary router for your server.
 *
 * All routers added in /api/routers should be manually added here.
 */
export const appRouter = createTRPCRouter({
  // post: postRouter,
  admin: adminRouter,
  institutions: institutionsRouter,
  forms: formsRouter,
});

// export type definition of API
export type AppRouter = typeof appRouter;

/**
 * Create a server-side caller for the tRPC API.
 * @example
 * const trpc = createCaller(createContext);
 * const res = await trpc.post.all();
 *       ^? Post[]
 */
export const createCaller = createCallerFactory(appRouter);
