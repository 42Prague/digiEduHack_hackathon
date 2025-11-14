import z from "zod";

export const eduDocumentRecord = z.object({
  schoolName: z.string().describe("Name of the school"),
  regionName: z.string().describe("Name of the region the school is located"),
  guideName: z.string().describe("Name of the mentor in the"),
  interventionType: z.string().describe("Type of the intervention."),

  listOfParticipants: z.object({
    schoolStaff: z.array(
      z.object({
        name: z.string(),
        age: z.number(),
        grade: z.string(),
      })
    ),
    mentors: z.array(
      z.object({
        name: z.string(),
        subject: z.string(),
      })
    ),
  }).optional().describe("List of participants each as object."),

  listOfFiles: z.object({
    reports: z.array(
      z.object({
        processed: z.boolean,
        type: z.string(),
        fileName: z.string(),
        path: z.string(),
        uploadedAt: z.string(), // Or z.coerce.date()
      })
    ),
  }).optional().describe("List of files each as object."),

  listOfMultimedia: z.object({
    multimedia: z.array(
      z.object({
        url: z.string().url(),
        description: z.string(),
      })
    ),
  }).optional().describe("Multimedia files each as object."),
  rawData: z.string().optional().describe("Raw transcription text"),
  processedData: z.object().optional().describe("Data as processed by ML Engine"),
});

export type EduDocumentSchema = z.infer<typeof eduDocumentRecord>;