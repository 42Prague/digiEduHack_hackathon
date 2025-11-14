import { z } from "zod";
import { adminProcedure, createTRPCRouter, protectedProcedure } from "~/server/api/trpc";
import { form, field, form_field, user_form, form_field_data } from "~/server/db/schema";
import type { FieldConfigType } from "~/server/db/schema";
import { eq, desc, and } from "drizzle-orm";

// Zod schema for FieldConfigType validation
const fieldConfigSchema: z.ZodType<FieldConfigType> = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("text"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    placeholder: z.string().optional(),
  }),
  z.object({
    type: z.literal("textarea"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    placeholder: z.string().optional(),
    rows: z.number().optional(),
  }),
  z.object({
    type: z.literal("date"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    defaultValue: z.string().optional(),
  }),
  z.object({
    type: z.literal("number"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    minValue: z.number().optional(),
    maxValue: z.number().optional(),
    defaultValue: z.number().optional(),
  }),
  z.object({
    type: z.literal("boolean"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    defaultValue: z.boolean().optional(),
  }),
  z.object({
    type: z.literal("select"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    options: z.array(z.string()),
    defaultValue: z.string().optional(),
  }),
  z.object({
    type: z.literal("radio"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    options: z.array(z.string()),
    defaultValue: z.string().optional(),
  }),
  z.object({
    type: z.literal("multiselect"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    options: z.array(z.string()),
    maxSelections: z.number().optional(),
  }),
  z.object({
    type: z.literal("slider"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    options: z.array(z.number()),
    defaultValue: z.number().optional(),
  }),
  z.object({
    type: z.literal("discrete_range"),
    label: z.string(),
    required: z.boolean().optional(),
    help: z.string().optional(),
    options: z.array(z.object({ value: z.number(), label: z.string() })),
  }),
]);

export const formsRouter = createTRPCRouter({
  // ============================================================
  // FORM MANAGEMENT
  // ============================================================

  // List all forms
  list: protectedProcedure.query(async ({ ctx }) => {
    const forms = await ctx.db
      .select()
      .from(form)
      .orderBy(desc(form.createdAt));
    return forms;
  }),

  // List all forms with user's submission status
  listWithStatus: protectedProcedure.query(async ({ ctx }) => {
    const forms = await ctx.db
      .select()
      .from(form)
      .orderBy(desc(form.createdAt));

    // Get all user's form submissions
    const userForms = await ctx.db
      .select()
      .from(user_form)
      .where(eq(user_form.user_id, ctx.session.user.id));

    // Map forms with their submission status
    return forms.map((formItem) => {
      const userFormEntry = userForms.find((uf) => uf.form_id === formItem.id);
      return {
        ...formItem,
        submissionStatus: userFormEntry?.submission_status || null,
      };
    });
  }),

  // Get a single form by ID
  get: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const formData = await ctx.db
        .select()
        .from(form)
        .where(eq(form.id, input.id))
        .limit(1);

      if (!formData[0]) {
        throw new Error("Form not found");
      }

      return formData[0];
    }),

  // Get form with its fields (ordered)
  getWithFields: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      // Get form
      const formData = await ctx.db
        .select()
        .from(form)
        .where(eq(form.id, input.id))
        .limit(1);

      if (!formData[0]) {
        throw new Error("Form not found");
      }

      // Get fields linked to this form
      const formFields = await ctx.db
        .select({
          field: field,
          order: form_field.order,
        })
        .from(form_field)
        .innerJoin(field, eq(form_field.field_id, field.id))
        .where(eq(form_field.form_id, input.id))
        .orderBy(form_field.order);

      return {
        ...formData[0],
        fields: formFields.map((f) => ({
          ...f.field,
          order: f.order,
        })),
      };
    }),

  // Create a new form (admin only)
  create: adminProcedure
    .input(
      z.object({
        label: z.string().min(1, "Label is required"),
        description: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const newForm = await ctx.db
        .insert(form)
        .values({
          label: input.label,
          description: input.description,
        })
        .returning();

      return newForm[0];
    }),

  // Update a form (admin only)
  update: adminProcedure
    .input(
      z.object({
        id: z.string().uuid(),
        label: z.string().min(1, "Label is required").optional(),
        description: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...updateData } = input;

      const updatedForm = await ctx.db
        .update(form)
        .set(updateData)
        .where(eq(form.id, id))
        .returning();

      if (!updatedForm[0]) {
        throw new Error("Form not found");
      }

      return updatedForm[0];
    }),

  // Delete a form (admin only)
  delete: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const deletedForm = await ctx.db
        .delete(form)
        .where(eq(form.id, input.id))
        .returning();

      if (!deletedForm[0]) {
        throw new Error("Form not found");
      }

      return deletedForm[0];
    }),

  // ============================================================
  // FIELD MANAGEMENT (Reusable fields)
  // ============================================================

  // List all available fields
  listFields: protectedProcedure.query(async ({ ctx }) => {
    const fields = await ctx.db.select().from(field);
    return fields;
  }),

  // Get a single field by ID
  getField: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const fieldData = await ctx.db
        .select()
        .from(field)
        .where(eq(field.id, input.id))
        .limit(1);

      if (!fieldData[0]) {
        throw new Error("Field not found");
      }

      return fieldData[0];
    }),

  // Create a new reusable field (admin only)
  createField: adminProcedure
    .input(
      z.object({
        name: z.string().min(1, "Name is required"),
        description: z.string().optional(),
        config: fieldConfigSchema,
      })
    )
    .mutation(async ({ ctx, input }) => {
      const newField = await ctx.db
        .insert(field)
        .values({
          name: input.name,
          description: input.description,
          config: input.config,
        })
        .returning();

      return newField[0];
    }),

  // Update a field (admin only)
  updateField: adminProcedure
    .input(
      z.object({
        id: z.string().uuid(),
        name: z.string().min(1, "Name is required").optional(),
        description: z.string().optional(),
        config: fieldConfigSchema.optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...updateData } = input;

      const updatedField = await ctx.db
        .update(field)
        .set(updateData)
        .where(eq(field.id, id))
        .returning();

      if (!updatedField[0]) {
        throw new Error("Field not found");
      }

      return updatedField[0];
    }),

  // Delete a field (admin only)
  deleteField: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const deletedField = await ctx.db
        .delete(field)
        .where(eq(field.id, input.id))
        .returning();

      if (!deletedField[0]) {
        throw new Error("Field not found");
      }

      return deletedField[0];
    }),

  // ============================================================
  // FORM-FIELD LINKING
  // ============================================================

  // Add a field to a form (admin only)
  addFieldToForm: adminProcedure
    .input(
      z.object({
        formId: z.string().uuid(),
        fieldId: z.string().uuid(),
        order: z.number().int().min(0),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Verify form exists
      const formExists = await ctx.db
        .select()
        .from(form)
        .where(eq(form.id, input.formId))
        .limit(1);

      if (!formExists[0]) {
        throw new Error("Form not found");
      }

      // Verify field exists
      const fieldExists = await ctx.db
        .select()
        .from(field)
        .where(eq(field.id, input.fieldId))
        .limit(1);

      if (!fieldExists[0]) {
        throw new Error("Field not found");
      }

      // Add field to form
      const newFormField = await ctx.db
        .insert(form_field)
        .values({
          form_id: input.formId,
          field_id: input.fieldId,
          order: input.order,
        })
        .returning();

      return newFormField[0];
    }),

  // Remove a field from a form (admin only)
  removeFieldFromForm: adminProcedure
    .input(
      z.object({
        formId: z.string().uuid(),
        fieldId: z.string().uuid(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const deletedFormField = await ctx.db
        .delete(form_field)
        .where(
          eq(form_field.form_id, input.formId) &&
            eq(form_field.field_id, input.fieldId)
        )
        .returning();

      if (!deletedFormField[0]) {
        throw new Error("Field not linked to form");
      }

      return deletedFormField[0];
    }),

  // Update field order in a form (admin only)
  updateFieldOrder: adminProcedure
    .input(
      z.object({
        formId: z.string().uuid(),
        fieldId: z.string().uuid(),
        order: z.number().int().min(0),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const updatedFormField = await ctx.db
        .update(form_field)
        .set({ order: input.order })
        .where(
          eq(form_field.form_id, input.formId) &&
            eq(form_field.field_id, input.fieldId)
        )
        .returning();

      if (!updatedFormField[0]) {
        throw new Error("Field not linked to form");
      }

      return updatedFormField[0];
    }),

  // ============================================================
  // FORM SUBMISSIONS (User)
  // ============================================================

  // Get user's submission for a form
  getUserSubmission: protectedProcedure
    .input(z.object({ formId: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      // Find user_form entry
      const userFormEntry = await ctx.db
        .select()
        .from(user_form)
        .where(
          and(
            eq(user_form.form_id, input.formId),
            eq(user_form.user_id, ctx.session.user.id)
          )
        )
        .limit(1);

      if (!userFormEntry[0]) {
        return null;
      }

      // Get the submission data
      const submissionData = await ctx.db
        .select()
        .from(form_field_data)
        .where(eq(form_field_data.user_form_id, userFormEntry[0].id))
        .limit(1);

      return {
        userForm: userFormEntry[0],
        submission: submissionData[0] || null,
      };
    }),

  // Save form as draft
  saveDraft: protectedProcedure
    .input(
      z.object({
        formId: z.string().uuid(),
        data: z.record(z.any()),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Find or create user_form entry
      let userFormEntry = await ctx.db
        .select()
        .from(user_form)
        .where(
          and(
            eq(user_form.form_id, input.formId),
            eq(user_form.user_id, ctx.session.user.id)
          )
        )
        .limit(1);

      if (!userFormEntry[0]) {
        // Create user_form entry
        const newUserForm = await ctx.db
          .insert(user_form)
          .values({
            form_id: input.formId,
            user_id: ctx.session.user.id,
            submission_status: "draft",
          })
          .returning();
        userFormEntry = newUserForm;
      }

      // Find existing submission data
      const existingData = await ctx.db
        .select()
        .from(form_field_data)
        .where(eq(form_field_data.user_form_id, userFormEntry[0]!.id))
        .limit(1);

      if (existingData[0]) {
        // Update existing
        const updated = await ctx.db
          .update(form_field_data)
          .set({
            data: input.data,
            state: "draft",
          })
          .where(eq(form_field_data.id, existingData[0].id))
          .returning();
        return updated[0];
      } else {
        // Create new
        const newData = await ctx.db
          .insert(form_field_data)
          .values({
            form_id: input.formId,
            user_form_id: userFormEntry[0]!.id,
            state: "draft",
            data: input.data,
          })
          .returning();
        return newData[0];
      }
    }),

  // Submit form
  submitForm: protectedProcedure
    .input(
      z.object({
        formId: z.string().uuid(),
        data: z.record(z.any()),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Find or create user_form entry
      let userFormEntry = await ctx.db
        .select()
        .from(user_form)
        .where(
          and(
            eq(user_form.form_id, input.formId),
            eq(user_form.user_id, ctx.session.user.id)
          )
        )
        .limit(1);

      if (!userFormEntry[0]) {
        // Create user_form entry
        const newUserForm = await ctx.db
          .insert(user_form)
          .values({
            form_id: input.formId,
            user_id: ctx.session.user.id,
            submission_status: "submitted",
          })
          .returning();
        userFormEntry = newUserForm;
      } else {
        // Update status to submitted
        await ctx.db
          .update(user_form)
          .set({ submission_status: "submitted" })
          .where(eq(user_form.id, userFormEntry[0].id));
      }

      // Find existing submission data
      const existingData = await ctx.db
        .select()
        .from(form_field_data)
        .where(eq(form_field_data.user_form_id, userFormEntry[0]!.id))
        .limit(1);

      if (existingData[0]) {
        // Update existing
        const updated = await ctx.db
          .update(form_field_data)
          .set({
            data: input.data,
            state: "submitted",
          })
          .where(eq(form_field_data.id, existingData[0].id))
          .returning();
        return updated[0];
      } else {
        // Create new
        const newData = await ctx.db
          .insert(form_field_data)
          .values({
            form_id: input.formId,
            user_form_id: userFormEntry[0]!.id,
            state: "submitted",
            data: input.data,
          })
          .returning();
        return newData[0];
      }
    }),
});
