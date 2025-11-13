import * as dotenv from "dotenv";
dotenv.config();

import { connectToHackathlonDB, closeMongo, CLOUD_COLLECTION_NAME } from '@repo/mongo-connector';
import { Db } from "mongoDb";
import z from "zod";
import * as process from "node:process";
import * as console from "node:console";

const eduDocumentRecord = z.object({
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
        fileName: z.string(),
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

  processedData: z.object({
    attendanceRate: z.number(),
    averageScoreImprovement: z.number(),
    sentimentSummary: z.string(),
  }).optional().describe("Data as processed by ML Engine"),
});

type EduDocumentSchema = z.infer<typeof eduDocumentRecord>;

const db: Db | undefined = await connectToHackathlonDB();

if (!db) {
  console.error("Database not connected");
  process.exit(1);
}
const collection = db.collection<EduDocumentSchema>(CLOUD_COLLECTION_NAME);

const eduDocumentRecordExample: EduDocumentSchema = {
  schoolName: "Green Valley High School",
  regionName: "Central Bohemia",
  guideName: "Dr. Martina Nováková",
  interventionType: "STEM Mentorship Program",
  listOfParticipants: {
    schoolStaff: [
      { name: "Anna Horáková", age: 16, grade: "10A" },
      { name: "Petr Dvořák", age: 17, grade: "11B" }
    ],
    mentors: [
      { name: "Karel Veselý", subject: "Mathematics" }
    ]
  },
  listOfFiles: {
    reports: [
      { fileName: "progress_report_q1.pdf", uploadedAt: "2025-03-12" },
      { fileName: "summary_notes.docx", uploadedAt: "2025-04-05" }
    ]
  },
  listOfMultimedia: {
    multimedia: [
      { url: "https://example.com/photos/group1.jpg", description: "Team photo" }
    ],
  },
  processedData: {
    attendanceRate: 0.92,
    averageScoreImprovement: 12.5,
    sentimentSummary: "Positive engagement throughout the semester"
  }
};


async function insertJunk() {
  await collection.insertOne(eduDocumentRecordExample)
}
await insertJunk();
await closeMongo();


