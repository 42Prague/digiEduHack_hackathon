import os

from openai import OpenAI

API_KEY = os.getenv("POETRY_META_API_KEY")

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=API_KEY,
)

prompt = """
<prompt>
  <role>
    You are an analytical assistant specializing in education policy and school systems.
  </role>
  <task>
    Read the provided text and extract all information related to schools, schooling, and the education system, including any reforms, trends, policies, funding changes, quality indicators, and learning outcomes.
  </task>
  <analysis>
    Focus only on content directly connected to education and schools, and determine for each described change whether it represents an improvement or a deterioration, and for which groups (students, teachers, parents, schools, or regions).
  </analysis>
  <output_requirements>
    Write a concise summary of the situation and its evolution in exactly 5–6 sentences, clearly describing the main changes, their direction (better or worse), and their key causes or consequences.
    Do not use bullet points, quotes, or formatting; write in clear, neutral, and accessible language that a non-expert can understand.
  </output_requirements>
</prompt>
"""


def call_agent(prompt: str, text: str) -> str:
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content
