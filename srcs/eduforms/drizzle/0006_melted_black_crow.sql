CREATE TYPE "public"."form_state" AS ENUM('todo', 'draft', 'submitted');--> statement-breakpoint
CREATE TABLE "field" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"description" text,
	"config" json
);
--> statement-breakpoint
CREATE TABLE "form" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"label" text NOT NULL,
	"description" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "form_field_data" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"form_id" uuid NOT NULL,
	"user_form_id" uuid,
	"state" "form_state"
);
--> statement-breakpoint
CREATE TABLE "user_form" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" text NOT NULL,
	"form_id" uuid NOT NULL,
	"submission_status" "form_state"
);
--> statement-breakpoint
ALTER TABLE "form_field_data" ADD CONSTRAINT "form_field_data_form_id_form_id_fk" FOREIGN KEY ("form_id") REFERENCES "public"."form"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "form_field_data" ADD CONSTRAINT "form_field_data_user_form_id_user_form_id_fk" FOREIGN KEY ("user_form_id") REFERENCES "public"."user_form"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "user_form" ADD CONSTRAINT "user_form_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "user_form" ADD CONSTRAINT "user_form_form_id_form_id_fk" FOREIGN KEY ("form_id") REFERENCES "public"."form"("id") ON DELETE no action ON UPDATE no action;