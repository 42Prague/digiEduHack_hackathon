// import * as z from 'zod';
// import { createAgent } from "langchain";
// import { geminiPro } from "../models/google/geminiModels.js";
// import { teacherProgramFeedbackSchema } from "../schemas/teacherProgramFeedbackSchema.js";
// import { type EduDocumentSchema, eduDocumentRecord } from "../schemas/eduDocumentSchema.js";
// import * as hub from "langchain/hub";
// import {connectToHackathlonDB, CLOUD_COLLECTION_NAME, closeMongo} from "@repo/mongo-connector";
// import type { AnyBulkWriteOperation } from "mongodb";
//
// const bulkWriteOps: AnyBulkWriteOperation<EduDocumentSchema>[] = [];
//
// const db = await connectToHackathlonDB();
// const collection = db?.collection<EduDocumentSchema>(CLOUD_COLLECTION_NAME);
// if (!db || !collection) throw new Error("Database failed");
//
// const sysPrompt = await hub.pull("edu-zmena-intervention-system-prompt");
// const textSysPrompt = await sysPrompt.invoke("");
//
// const agent = createAgent({
//   model: geminiPro,
//   systemPrompt: textSysPrompt.toString(),
//   responseFormat: teacherProgramFeedbackSchema,
// });
//
// const documents = collection.find({ rawData: { $exists: true } });
// const count = await documents.count();
// console.log(`Number of documents to process: ${count}`);
// if (!documents) {
//   await closeMongo();
//   console.log("No documents to process!");
//   process.exit(0);
// }
// for await (const doc of documents) {
//   const rawResult = await agent.invoke({
//     messages: [{ role: "user", content: doc.rawData!.toString() }],
//   });
//
//   const processedData = teacherProgramFeedbackSchema.safeParse(rawResult.structuredResponse);
//   if (!processedData.success) {
//     console.error("Failed to validate processed data:", processedData.error);
//     continue; // Skip this doc
//   } else {
//     console.log("Document validation has passed.");
//   }
//
//   bulkWriteOps.push({
//     updateOne: {
//       filter: { _id: doc._id },
//       //@ts-ignore
//       update: { $set: { processedData: processedData.data } },
//     },
//   });
// }
//
// if (bulkWriteOps.length > 0) {
//   console.log(`Writing the final batch of ${bulkWriteOps.length} records.`);
//   await collection.bulkWrite(bulkWriteOps);
// }
// await closeMongo();


import * as z from 'zod';
import { createAgent } from "langchain";
import { geminiPro } from "../models/google/geminiModels.js";
import { teacherProgramFeedbackSchema } from "../schemas/teacherProgramFeedbackSchema.js";
import { type EduDocumentSchema, eduDocumentRecord } from "../schemas/eduDocumentSchema.js";
import * as hub from "langchain/hub";
import {connectToHackathlonDB, CLOUD_COLLECTION_NAME, closeMongo} from "@repo/mongo-connector";
import type { AnyBulkWriteOperation, Db } from "mongodb";

/**
 * Runs the agent processing task.
 * Connects to the DB, fetches documents, processes them with an agent,
 * and writes the results back.
 */
export async function runDocumentProcessing() {
  const bulkWriteOps: AnyBulkWriteOperation<EduDocumentSchema>[] = [];
  let db: Db | undefined; // Declare db here to access in finally

  try {
    db = await connectToHackathlonDB();
    const collection = db?.collection<EduDocumentSchema>(CLOUD_COLLECTION_NAME);
    if (!db || !collection) {
      throw new Error("Database connection failed");
    }

    console.log("Setting up agent...");
    const sysPrompt = await hub.pull("edu-zmena-intervention-system-prompt");
    const textSysPrompt = await sysPrompt.invoke("");

    const agent = createAgent({
      model: geminiPro,
      systemPrompt: textSysPrompt.toString(),
      responseFormat: teacherProgramFeedbackSchema,
    });
    console.log("Agent setup complete.");

    const query = { rawData: { $exists: true }, processedData: { $exists: false } };
    const count = await collection.countDocuments(query);
    console.log(`Number of documents to process: ${count}`);

    if (count === 0) {
      console.log("No documents to process!");
      return; // Return early, don't use process.exit
    }

    const documents = collection.find(query);

    for await (const doc of documents) {
      try {
        console.log(`Processing document ${doc._id}...`);
        const rawResult = await agent.invoke({
          messages: [{ role: "user", content: doc.rawData!.toString() }],
        });

        const processedData = teacherProgramFeedbackSchema.safeParse(rawResult.structuredResponse);
        if (!processedData.success) {
          console.error(`Failed to validate processed data for doc ${doc._id}:`, processedData.error);
          continue; // Skip this doc, move to the next
        } else {
          console.log(`Document ${doc._id} validation has passed.`);
        }

        bulkWriteOps.push({
          updateOne: {
            filter: { _id: doc._id },
            //@ts-ignore
            update: { $set: { processedData: processedData.data } },
          },
        });

      } catch (docError) {
        console.error(`An error occurred processing document ${doc._id}:`, docError);
        // Continue to the next document
      }
    }

    if (bulkWriteOps.length > 0) {
      console.log(`Writing the final batch of ${bulkWriteOps.length} records.`);
      await collection.bulkWrite(bulkWriteOps);
    } else {
      console.log("No valid documents were processed to write.");
    }

    console.log("Processing finished successfully.");

  } catch (error) {
    console.error("A critical error occurred during the process:", error);
    // Depending on your needs, you might want to re-throw the error
    // throw error;
  } finally {
    // This block will run whether the try block succeeded or failed
    if (db) { // Only try to close if the connection was established
      // console.log("Closing database connection...");
      // // await closeMongo();
      // console.log("Database connection closed.");
    }
  }
}

// Example of how you might call this function from another file:
/*
  import { runDocumentProcessing } from './your-file-name.js';

  runDocumentProcessing()
    .then(() => console.log('All done!'))
    .catch((err) => console.error('Main process failed:', err));
*/
