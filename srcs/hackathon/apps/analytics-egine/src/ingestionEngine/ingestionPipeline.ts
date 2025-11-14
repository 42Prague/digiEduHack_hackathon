import * as z from 'zod';
import { createAgent } from "langchain";
import { geminiPro } from "../models/google/geminiModels.js";
import { teacherProgramFeedbackSchema } from "../schemas/teacherProgramFeedbackSchema.js";
import { type EduDocumentSchema, eduDocumentRecord } from "../schemas/eduDocumentSchema.js";
import * as hub from "langchain/hub";
import {connectToHackathlonDB, CLOUD_COLLECTION_NAME, closeMongo} from "@repo/mongo-connector";
import type { AnyBulkWriteOperation } from "mongodb";

const bulkWriteOps: AnyBulkWriteOperation<EduDocumentSchema>[] = [];

const db = await connectToHackathlonDB();
const collection = db?.collection<EduDocumentSchema>(CLOUD_COLLECTION_NAME);
if (!db || !collection) throw new Error("Database failed");

const sysPrompt = await hub.pull("edu-zmena-intervention-system-prompt");
const textSysPrompt = await sysPrompt.invoke("");

const agent = createAgent({
  model: geminiPro,
  systemPrompt: textSysPrompt.toString(),
  responseFormat: teacherProgramFeedbackSchema,
});

const documents = collection.find({ rawData: { $exists: true } });
const count = await documents.count();
console.log(`Number of documents to process: ${count}`);
if (!documents) {
  await closeMongo();
  console.log("No documents to process!");
  process.exit(0);
}
for await (const doc of documents) {
  const rawResult = await agent.invoke({
    messages: [{ role: "user", content: doc.rawData!.toString() }],
  });

  const processedData = teacherProgramFeedbackSchema.safeParse(rawResult.structuredResponse);
  if (!processedData.success) {
    console.error("Failed to validate processed data:", processedData.error);
    continue; // Skip this doc
  } else {
    console.log("Document validation has passed.");
  }

  bulkWriteOps.push({
    updateOne: {
      filter: { _id: doc._id },
      //@ts-ignore
      update: { $set: { processedData: processedData.data } },
    },
  });
}

if (bulkWriteOps.length > 0) {
  console.log(`Writing the final batch of ${bulkWriteOps.length} records.`);
  await collection.bulkWrite(bulkWriteOps);
}
await closeMongo();