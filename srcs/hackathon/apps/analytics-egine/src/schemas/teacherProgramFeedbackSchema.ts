import { z } from "zod";

export const teacherProgramFeedbackSchema = z.object({
  overall_sentiment: z.object({
    polarity: z.enum(["positive", "neutral", "negative", "mixed"]),
    confidence: z.number().min(0).max(1),
    emotional_tone: z.array(z.enum(["enthusiasm", "frustration", "hope", "uncertainty"])).optional(),
  }),
  sentiment_by_aspect: z.array(z.object({
    aspect: z.string(),
    sentiment: z.enum(["positive", "neutral", "negative"]),
  })).optional(),
  theme_extraction: z.object({
    primary_themes: z.array(z.object({
      theme: z.string(),
      frequency: z.enum(["high", "medium", "low"]),
      sentiment: z.enum(["positive", "neutral", "negative"]).optional(),
      key_phrases: z.array(z.string()).optional(),
    })).optional(),
    pedagogical_concepts: z.array(z.string()).optional(),
    challenges_mentioned: z.array(z.string()).optional(),
  }).optional(),
  impact_assessment: z.object({
    on_students: z.object({
      mentioned: z.boolean(),
      type: z.enum(["behavioral", "academic", "motivational", "social"]).optional(),
      direction: z.enum(["positive", "negative", "neutral", "mixed"]).optional(),
      examples: z.array(z.string()).optional(),
    }),
    on_teacher: z.object({
      professional_growth: z.enum(["significant", "moderate", "minimal"]).optional(),
      confidence_level: z.enum(["increased", "decreased", "unchanged"]).optional(),
      self_awareness: z.array(z.string()).optional(),
    }),
    on_school_culture: z.object({
      mentioned: z.boolean(),
      scope: z.enum(["individual_classroom", "team", "whole_school"]).optional(),
      changes: z.array(z.string()).optional(),
    }),
  }).optional(),
  barrier_enabler_analysis: z.object({
    barriers: z.array(z.object({
      type: z.enum(["time", "resources", "support", "skills", "systemic"]),
      severity: z.enum(["critical", "significant", "moderate", "minor"]).optional(),
      description: z.string(),
    })).optional(),
    enablers: z.array(z.object({
      type: z.enum(["time", "resources", "support", "skills", "systemic"]),
      impact: z.enum(["high", "medium", "low"]).optional(),
      description: z.string(),
    })).optional(),
  }).optional(),
});

export type TeacherProgramFeedback = z.infer<typeof teacherProgramFeedbackSchema>;