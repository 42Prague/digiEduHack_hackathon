// Replace your original file content with this updated version

import {MongoClient, Db} from "mongodb";
import * as console from "node:console";

// --- Extract variables from environment ---
// Next.js automatically loads these from .env.local
const CLOUD_URI = process.env.MONGODB_CLOUD_URI;
const CLOUD_DB_NAME = process.env.MONGODB_CLOUD_DB_NAME;
// ------------------------------------------

// Add a check to ensure the variables are set (Server-side safety)
if (!CLOUD_URI || !CLOUD_DB_NAME) {
  throw new Error("Missing MONGODB_CLOUD_URI or MONGODB_CLOUD_DB_NAME environment variables.");
}

export const CLOUD_COLLECTION_NAME = "edu-change";

let cloudDb: Db | null = null; // Use Db | null for better typing

const cloudClient = new MongoClient(CLOUD_URI); // Use the variable

// ... (rest of your connection logic remains the same)

async function connectToMongo() {
  try {
    await cloudClient.connect();
    console.log("Connected to MongoDB.");
  } catch (e) {
    console.log("Failed to connect to MongoDB instance", e);
    process.exit(1);
  }
}

export async function closeMongo() {
  try {
    await cloudClient.close();
    console.log("MongoDB closed.");
  } catch (e) {
    console.log("Failed to close MongoDB instance", e);
  }
}

// Update the type signature for cloudDb check
export async function connectToHackathlonDB(): Promise<Db | undefined>{
  try {
    if (!cloudDb) {
      await connectToMongo();
      // Ensure cloudClient.db is called with the variable
      cloudDb = cloudClient.db(CLOUD_DB_NAME); 
    }
    console.log("Connected to Hackathlon DB.");
    return cloudDb;
  } catch (e) {
    console.error("Failed to connect to Hackathlon DB", e);
  }
}