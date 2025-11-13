import { z } from "zod";
import { adminProcedure, createTRPCRouter, protectedProcedure } from "~/server/api/trpc";
import { institution } from "~/server/db/schema";
import { eq } from "drizzle-orm";

/**
 * Institutions router
 * - List: Available to all authenticated users
 * - Create/Update/Delete: Admin only
 */
export const institutionsRouter = createTRPCRouter({
  // List all institutions - available to all authenticated users
  list: protectedProcedure.query(async ({ ctx }) => {
    const institutions = await ctx.db.select().from(institution).orderBy(institution.label);
    return institutions;
  }),

  // Create a new institution - admin only
  create: adminProcedure
    .input(
      z.object({
        label: z.string().min(1, "Label is required"),
        ico: z.string().min(1, "ICO is required"),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const newInstitution = await ctx.db
        .insert(institution)
        .values({
          label: input.label,
          ico: input.ico,
        })
        .returning();

      return newInstitution[0];
    }),

  // Update an institution - admin only
  update: adminProcedure
    .input(
      z.object({
        id: z.string().uuid(),
        label: z.string().min(1, "Label is required").optional(),
        ico: z.string().min(1, "ICO is required").optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...updateData } = input;
      
      const updatedInstitution = await ctx.db
        .update(institution)
        .set(updateData)
        .where(eq(institution.id, id))
        .returning();

      if (!updatedInstitution[0]) {
        throw new Error("Institution not found");
      }

      return updatedInstitution[0];
    }),

  // Delete an institution - admin only
  delete: adminProcedure
    .input(
      z.object({
        id: z.string().uuid(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const deletedInstitution = await ctx.db
        .delete(institution)
        .where(eq(institution.id, input.id))
        .returning();

      if (!deletedInstitution[0]) {
        throw new Error("Institution not found");
      }

      return deletedInstitution[0];
    }),
});

