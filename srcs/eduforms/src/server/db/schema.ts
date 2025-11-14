import { relations } from "drizzle-orm";
import {
  boolean,
  integer,
  json,
  pgEnum,
  pgTable,
  pgTableCreator,
  text,
  timestamp,
  uuid
} from "drizzle-orm/pg-core";

export const createTable = pgTableCreator((name) => `pg-drizzle_${name}`);


export const user = pgTable("user", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  emailVerified: boolean("email_verified").default(false).notNull(),
  image: text("image"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
  // Admin plugin fields
  role: text("role"),
  banned: boolean("banned"),
  banReason: text("ban_reason"),
  banExpires: timestamp("ban_expires"),
  institution: uuid().references(()=>institution.id, {onDelete:"cascade"}) // Maybe not cascade?
});


export const session = pgTable("session", {
  id: text("id").primaryKey(),
  expiresAt: timestamp("expires_at").notNull(),
  token: text("token").notNull().unique(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
  ipAddress: text("ip_address"),
  userAgent: text("user_agent"),
  userId: text("user_id")
    .notNull()
    .references(() => user.id, { onDelete: "cascade" }),
  // Admin plugin field
  impersonatedBy: text("impersonated_by"),
});

export const account = pgTable("account", {
  id: text("id").primaryKey(),
  accountId: text("account_id").notNull(),
  providerId: text("provider_id").notNull(),
  userId: text("user_id")
    .notNull()
    .references(() => user.id, { onDelete: "cascade" }),
  accessToken: text("access_token"),
  refreshToken: text("refresh_token"),
  idToken: text("id_token"),
  accessTokenExpiresAt: timestamp("access_token_expires_at"),
  refreshTokenExpiresAt: timestamp("refresh_token_expires_at"),
  scope: text("scope"),
  password: text("password"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
});

export const verification = pgTable("verification", {
  id: text("id").primaryKey(),
  identifier: text("identifier").notNull(),
  value: text("value").notNull(),
  expiresAt: timestamp("expires_at").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
});

export const userRelations = relations(user, ({ many, one }) => ({
  account: many(account),
  session: many(session),
  institutionRel: one(institution, {
    fields: [user.institution],
    references: [institution.id],
  }),
}));

export const accountRelations = relations(account, ({ one }) => ({
  user: one(user, { fields: [account.userId], references: [user.id] }),
}));

export const sessionRelations = relations(session, ({ one }) => ({
  user: one(user, { fields: [session.userId], references: [user.id] }),
}));


export const institution = pgTable("institution", {
  id: uuid("id").primaryKey().defaultRandom(),
  label: text("label").notNull(),
  ico: text("ico").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
});

export const institutionRelations = relations(institution, ({ many }) => ({
  users: many(user),
}));


export const form = pgTable("form", {
  id: uuid("id").primaryKey().defaultRandom(),
  label: text("label").notNull(),
  description: text(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
});

export const formState = pgEnum('form_state', ['todo', 'draft', 'submitted']);

export const user_form = pgTable("user_form", {
  id: uuid("id").primaryKey().defaultRandom(),
  user_id: text().references(()=>user.id).notNull(),
  form_id: uuid().references(()=>form.id).notNull(),
  submission_status: formState()
});

export type FieldConfigType = 
  | {
      type: 'text';
      label: string;
      required?: boolean;
      help?: string;
      placeholder?: string;
    }
  | {
      type: 'textarea';
      label: string;
      required?: boolean;
      help?: string;
      placeholder?: string;
      rows?: number;
    }
  | {
      type: 'date';
      label: string;
      required?: boolean;
      help?: string;
      defaultValue?: string;
    }
  | {
      type: 'number';
      label: string;
      required?: boolean;
      help?: string;
      minValue?: number;
      maxValue?: number;
      defaultValue?: number;
    }
  | {
      type: 'boolean';
      label: string;
      required?: boolean;
      help?: string;
      defaultValue?: boolean;
    }
  | {
      type: 'select';
      label: string;
      required?: boolean;
      help?: string;
      options: string[];
      defaultValue?: string;
    }
  | {
      type: 'radio';
      label: string;
      required?: boolean;
      help?: string;
      options: string[];
      defaultValue?: string;
    }
  | {
      type: 'multiselect';
      label: string;
      required?: boolean;
      help?: string;
      options: string[];
      maxSelections?: number;
    }
  | {
      type: 'slider';
      label: string;
      required?: boolean;
      help?: string;
      options: number[];
      defaultValue?: number;
    }| {
      type: 'discrete_range';
      label: string;
      required?: boolean;
      help?: string;
      options: {value: number, label:string}[];
    };

export const field = pgTable("field", {
  id: uuid().primaryKey().defaultRandom(),
  name: text().notNull(),
  description: text(),
  config: json().$type<FieldConfigType>()
})


export const form_field_data = pgTable("form_field_data", {
  id: uuid().primaryKey().defaultRandom(),
  form_id: uuid().references(()=>form.id).notNull(),
  user_form_id: uuid().references(()=>user_form.id),
  state: formState(),
  data: json().$type<Record<string, any>>(), // Stores field_id -> value mapping
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdate(() => /* @__PURE__ */ new Date())
    .notNull(),
})

export const form_field = pgTable("form_field", {
  form_id: uuid().references(()=>form.id).notNull(),
  field_id: uuid().references(()=>field.id).notNull(),
  order: integer()
})







