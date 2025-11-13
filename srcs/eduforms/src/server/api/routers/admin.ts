import { z } from "zod";
import { adminProcedure, createTRPCRouter } from "~/server/api/trpc";
import { user } from "~/server/db/schema";
import { eq } from "drizzle-orm";

/**
 * Admin router - all procedures here require admin role
 */
export const adminRouter = createTRPCRouter({
  // Example: Get all users (admin only)
  getAllUsers: adminProcedure.query(async ({ ctx }) => {
    const users = await ctx.db.select().from(user);
    return users;
  }),

  // Example: Update user role (admin only)
  updateUserRole: adminProcedure
    .input(
      z.object({
        userId: z.string(),
        role: z.string(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const updatedUser = await ctx.db
        .update(user)
        .set({ role: input.role })
        .where(eq(user.id, input.userId))
        .returning();

      return updatedUser[0];
    }),

  // Example: Ban user (admin only)
  banUser: adminProcedure
    .input(
      z.object({
        userId: z.string(),
        reason: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const bannedUser = await ctx.db
        .update(user)
        .set({
          banned: true,
          banReason: input.reason ?? "No reason provided",
        })
        .where(eq(user.id, input.userId))
        .returning();

      return bannedUser[0];
    }),

  // Example: Get admin stats (admin only)
  getStats: adminProcedure.query(async ({ ctx }) => {
    const allUsers = await ctx.db.select().from(user);
    
    return {
      totalUsers: allUsers.length,
      adminUsers: allUsers.filter(u => u.role === "admin").length,
      bannedUsers: allUsers.filter(u => u.banned).length,
      regularUsers: allUsers.filter(u => u.role !== "admin").length,
    };
  }),
});

