from openai import OpenAI
import os

class MainAgent:
    def __init__(self):
        self.llm = OpenAI(
            api_key=os.getenv("META_API_KEY"),
            base_url="https://api.featherless.ai/v1",
            # model="unsloth/Qwen3-4B-Instruct-2507",
        )
        self.prompt = (
            "You are a helpful AI assistant that can perform various tasks based on user queries."
        )
    
    def run(self, query: str):
        # Use agent_executor to process the query with LLM and tools
        response = self.llm.chat.completions.create(
            model='meta-llama/Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": query}
            ],
            temperature=0
        )
        return response.choices[0].message.content