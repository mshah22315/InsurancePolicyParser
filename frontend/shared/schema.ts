import { pgTable, text, serial, integer, boolean, timestamp, jsonb, real, varchar, uuid } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  email: text("email"),
  fullName: text("full_name"),
  role: text("role").default("agent"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const policies = pgTable("policies", {
  id: serial("id").primaryKey(),
  policyNumber: text("policy_number").notNull().unique(),
  insurerName: text("insurer_name").notNull(),
  policyholderName: text("policyholder_name").notNull(),
  propertyAddress: text("property_address").notNull(),
  totalPremium: real("total_premium"),
  effectiveDate: timestamp("effective_date"),
  expirationDate: timestamp("expiration_date"),
  coverageDetails: jsonb("coverage_details").$type<Array<{
    coverageType: string;
    limit: number;
    deductible: number;
    premium: number;
  }>>(),
  deductibles: jsonb("deductibles").$type<Array<{
    coverageType: string;
    amount: number;
    type: string;
  }>>(),
  documentSourceFilename: text("document_source_filename"),
  processingStatus: text("processing_status").default("pending"),
  processedAt: timestamp("processed_at"),
  // Proactive fields
  roofAgeYears: integer("roof_age_years"),
  propertyFeatures: jsonb("property_features").$type<string[]>(),
  renewalDate: timestamp("renewal_date"),
  lastProactiveAnalysis: timestamp("last_proactive_analysis"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const policyChunks = pgTable("policy_chunks", {
  id: serial("id").primaryKey(),
  policyId: integer("policy_id").references(() => policies.id),
  documentSourceFilename: text("document_source_filename"),
  sectionType: text("section_type"),
  chunkText: text("chunk_text").notNull(),
  embedding: jsonb("embedding").$type<number[]>(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const propertyFeatures = pgTable("property_features", {
  id: serial("id").primaryKey(),
  policyId: integer("policy_id").references(() => policies.id),
  featureName: text("feature_name").notNull(),
  featureDescription: text("feature_description"),
  discountPercentage: real("discount_percentage"),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
});

export const processingTasks = pgTable("processing_tasks", {
  id: serial("id").primaryKey(),
  taskId: uuid("task_id").notNull().unique(),
  taskType: text("task_type").notNull(), // 'policy_processing', etc.
  status: text("status").default("pending"), // 'pending', 'processing', 'completed', 'failed'
  filename: text("filename"),
  progress: integer("progress").default(0),
  errorMessage: text("error_message"),
  result: jsonb("result"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Relations
export const policiesRelations = relations(policies, ({ many }) => ({
  chunks: many(policyChunks),
  propertyFeatures: many(propertyFeatures),
}));

export const policyChunksRelations = relations(policyChunks, ({ one }) => ({
  policy: one(policies, {
    fields: [policyChunks.policyId],
    references: [policies.id],
  }),
}));

export const propertyFeaturesRelations = relations(propertyFeatures, ({ one }) => ({
  policy: one(policies, {
    fields: [propertyFeatures.policyId],
    references: [policies.id],
  }),
}));

// Insert schemas
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
  email: true,
  fullName: true,
  role: true,
});

export const insertPolicySchema = createInsertSchema(policies).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertPolicyChunkSchema = createInsertSchema(policyChunks).omit({
  id: true,
  createdAt: true,
});

export const insertPropertyFeatureSchema = createInsertSchema(propertyFeatures).omit({
  id: true,
  createdAt: true,
});

export const insertProcessingTaskSchema = createInsertSchema(processingTasks).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

// Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Policy = typeof policies.$inferSelect;
export type InsertPolicy = z.infer<typeof insertPolicySchema>;

export type PolicyChunk = typeof policyChunks.$inferSelect;
export type InsertPolicyChunk = z.infer<typeof insertPolicyChunkSchema>;

export type PropertyFeature = typeof propertyFeatures.$inferSelect;
export type InsertPropertyFeature = z.infer<typeof insertPropertyFeatureSchema>;

export type ProcessingTask = typeof processingTasks.$inferSelect;
export type InsertProcessingTask = z.infer<typeof insertProcessingTaskSchema>;
