ALTER TABLE "user_form" ADD COLUMN "assigned_at" timestamp DEFAULT now() NOT NULL;--> statement-breakpoint
ALTER TABLE "user_form" ADD COLUMN "assigned_by" text;