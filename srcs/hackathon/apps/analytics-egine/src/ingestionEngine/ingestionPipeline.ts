import * as z from 'zod';
import { createAgent, tool } from "langchain";
import { geminiFlash, geminiPro } from "../models/google/geminiModels.js";
import {teacherProgramFeedbackSchema} from "../schemas/teacherProgramFeedbackSchema.js";
import * as hub from "langchain/hub";
import {connectToHackathlonDB, CLOUD_COLLECTION_NAME } from "@repo/mongo-connector";



const sysPrompt = await hub.pull("edu-zmena-intervention-system-prompt")
const textSysPrompt = await sysPrompt.invoke("");

const agent = createAgent({
  model: geminiPro,
  systemPrompt: textSysPrompt.toString(),
  responseFormat: teacherProgramFeedbackSchema,
});

const result = await agent.invoke({
  messages: [
    {
      role: "user",
      content: "some content",
    },
  ],
});

console.log(result.structuredResponse);

