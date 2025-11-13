import { geminiFlash} from "../models/google/geminiModels.js";
import { createAgent, tool} from "langchain";
import * as readline from "node:readline";
import { MemorySaver } from "@langchain/langgraph";
import * as z from 'zod';



const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
})

// const search = tool( async ({query}) => {
//   return await jobSearch(query)}, {
//   name: "jobSearch",
//   description: "Search for job information.",
//   schema: z.object({query: z.string().describe("The search query. Be very specific as the fields accepts sematic meaning.")})
// })

const agent = createAgent({
  model: geminiFlash,
  systemPrompt: "You are a joker, you always make fun from the user question and somehow you twist it and make fun of it.",
  checkpointer: new MemorySaver(),
  tools: [],
})

const config = {
  configurable: { thread_id: 1},
  context: { user_id: "1"},
}


function prompt() {
  rl.question("Enter your question: ", async (input) => {
    if (input.trim().toUpperCase() === "/Q") {
      console.log("Quitting!");
      rl.close();
      return;
    }
    const aiOutput = await agent.invoke({
      messages: [{role: "user", content: input}]
    }, config)
    console.log(aiOutput.messages);
    prompt();
  });
}


prompt();
