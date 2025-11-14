CREATE TABLE "form_field" (
	"form_id" uuid NOT NULL,
	"field_id" uuid NOT NULL,
	"order" integer
);
--> statement-breakpoint
ALTER TABLE "form_field" ADD CONSTRAINT "form_field_form_id_form_id_fk" FOREIGN KEY ("form_id") REFERENCES "public"."form"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "form_field" ADD CONSTRAINT "form_field_field_id_field_id_fk" FOREIGN KEY ("field_id") REFERENCES "public"."field"("id") ON DELETE no action ON UPDATE no action;