import { GoogleGenerativeAIEmbeddings } from "@langchain/google-genai";

import * as dotenv from "dotenv";
dotenv.config();

export const googleEmbeddingModel = new GoogleGenerativeAIEmbeddings({
  model: "embedding-001",
});
