CREATE TABLE "institution" (
	"id" uuid PRIMARY KEY NOT NULL,
	"label" text NOT NULL,
	"ico" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
