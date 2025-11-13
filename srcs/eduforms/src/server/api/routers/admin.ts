import { z } from "zod";
import { adminProcedure, createTRPCRouter } from "~/server/api/trpc";
import { user } from "~/server/db/schema";
import { eq } from "drizzle-orm";
import { auth } from "~/server/better-auth";

/**
 * Admin router - all procedures here require admin role
 */
export const adminRouter = createTRPCRouter({
  // Get all users (admin only)
  getAllUsers: adminProcedure.query(async ({ ctx }) => {
    const users = await ctx.db.select().from(user);
    return users;
  }),

  // Get users by institution (admin only)
  getUsersByInstitution: adminProcedure
    .input(
      z.object({
        institutionId: z.string().uuid(),
      })
    )
    .query(async ({ ctx, input }) => {
      const users = await ctx.db
        .select()
        .from(user)
        .where(eq(user.institution, input.institutionId));
      return users;
    }),

  // Create a new user (admin only)
  createUser: adminProcedure
    .input(
      z.object({
        name: z.string().min(1, "Name is required"),
        email: z.string().email("Invalid email"),
        role: z.string().optional(),
        institutionId: z.string().uuid(),
        password: z.string().min(8, "Password must be at least 8 characters"),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Check if user with this email already exists
      const existingUser = await ctx.db
        .select()
        .from(user)
        .where(eq(user.email, input.email))
        .limit(1);

      if (existingUser.length > 0) {
        throw new Error("User with this email already exists");
      }

      // Create user using Better Auth API
      const newUser = await auth.api.signUpEmail({
        body: {
          email: input.email,
          password: input.password,
          name: input.name,
        },
      });

      if (!newUser) {
        throw new Error("Failed to create user");
      }

      // Update user with role and institution
      const updatedUser = await ctx.db
        .update(user)
        .set({
          role: input.role ?? "user",
          institution: input.institutionId,
        })
        .where(eq(user.email, input.email))
        .returning();

      return updatedUser[0];
    }),

  // Update user (admin only)
  updateUser: adminProcedure
    .input(
      z.object({
        userId: z.string(),
        name: z.string().min(1).optional(),
        email: z.string().email().optional(),
        role: z.string().optional(),
        institutionId: z.string().uuid().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { userId, ...updateData } = input;

      // If email is being updated, check it doesn't already exist
      if (updateData.email) {
        const existingUser = await ctx.db
          .select()
          .from(user)
          .where(eq(user.email, updateData.email))
          .limit(1);

        if (existingUser.length > 0 && existingUser[0]?.id !== userId) {
          throw new Error("User with this email already exists");
        }
      }

      const updatedUser = await ctx.db
        .update(user)
        .set({
          name: updateData.name,
          email: updateData.email,
          role: updateData.role,
          institution: updateData.institutionId,
        })
        .where(eq(user.id, userId))
        .returning();

      if (!updatedUser[0]) {
        throw new Error("User not found");
      }

      return updatedUser[0];
    }),

  // Delete user (admin only)
  deleteUser: adminProcedure
    .input(
      z.object({
        userId: z.string(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const deletedUser = await ctx.db
        .delete(user)
        .where(eq(user.id, input.userId))
        .returning();

      if (!deletedUser[0]) {
        throw new Error("User not found");
      }

      return deletedUser[0];
    }),

  // Update user role (admin only)
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

  // Ban user (admin only)
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

  // Get admin stats (admin only)
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

