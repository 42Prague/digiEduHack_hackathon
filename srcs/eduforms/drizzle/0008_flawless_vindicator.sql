ALTER TABLE "form_field_data" ADD COLUMN "data" json;--> statement-breakpoint
ALTER TABLE "form_field_data" ADD COLUMN "created_at" timestamp DEFAULT now() NOT NULL;--> statement-breakpoint
ALTER TABLE "form_field_data" ADD COLUMN "updated_at" timestamp DEFAULT now() NOT NULL;