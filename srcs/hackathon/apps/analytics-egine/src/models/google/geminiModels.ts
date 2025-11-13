import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { InMemoryCache } from "@langchain/core/caches";

const GEM_MODELS_FLASH_LITE = "gemini-2.5-flash-lite";
const GEM_MODELS_FLASH = "gemini-2.5-flash";
const GEM_MODELS_PRO = "gemini-2.5-pro";

import * as dotenv from "dotenv";

dotenv.config();

export const geminiFlashLite = new ChatGoogleGenerativeAI({
  model: GEM_MODELS_FLASH_LITE,
  temperature: 0,
  maxRetries: 3,
  cache: new InMemoryCache(),
});

export const geminiFlash = new ChatGoogleGenerativeAI({
  model: GEM_MODELS_FLASH,
  temperature: 0,
  maxRetries: 3,
  cache: new InMemoryCache(),
});

export const geminiPro = new ChatGoogleGenerativeAI({
  model: GEM_MODELS_PRO,
  temperature: 0,
  maxRetries: 3,
  cache: new InMemoryCache(),
});
