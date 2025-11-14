import {MongoClient, Db} from "mongodb";
import * as console from "node:console";
import { envs } from "@repo/env-loader";

const CLOUD_URI = envs.DATABASE_URL;
const CLOUD_DB_NAME = "hackathlon";

export const CLOUD_COLLECTION_NAME = "edu-change";

let cloudDb: any = null;

const cloudClient = new MongoClient(CLOUD_URI);


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

export async function connectToHackathlonDB(): Promise<Db | undefined>{
  try {
    if (!cloudDb) {
      await connectToMongo();
      cloudDb = cloudClient.db(CLOUD_DB_NAME);
    }
    console.log("Connected to Hackathlon DB.");
    return cloudDb;
  } catch (e) {
    console.error("Failed to connect to Hackathlon DB", e);
  }
}
