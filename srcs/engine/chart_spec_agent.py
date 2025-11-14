import pandas as pd
import numpy as np
from openai import OpenAI, InternalServerError
import os
import json


class ChartSpecAgent:
    ALLOWED_CHART_TYPES = ["bar", "line", "scatter", "pie", "boxplot", "histogram"]

    chart_spec_template = {
        "name": "build_chart_spec",
        "description": "Create a chart specification based on data and instruction.",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ALLOWED_CHART_TYPES,
                },
                "title": {"type": "string"},
                "x": {"type": "string"},
                "y": {"type": "string"},
                "group_by": {"type": "string"},
                "data": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["chart_type", "data"],
        },
    }

    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=os.getenv("META_API_KEY"),
        )

    def call_agent(self, prompt: str, text: str):
        response = self.client.chat.completions.create(
            model='meta-llama/Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        return response.choices[0].message

    # def generate_chart_spec(self, df: pd.DataFrame, instruction: str) -> dict:
        """
        Input:
            df — DataFrame
            instruction — string describing what to do

        Output:
            JSON with chart specification (chart_type, data, title, x, y, group…)
        """
        df_json = df.to_dict(orient="records")

        system_prompt = (
            """
            You are an analytical agent for preparing data for visualization.
            You receive:
            1) a data table (DataFrame),
            2) a textual task/instruction.
            You MUST return ONLY a valid JSON object that matches the build_chart_spec schema.
            Do not add explanations, text, comments, or formatting.
            Return ONLY JSON, nothing else.

            Your job:
            - Analyze the meaning of the instruction.
            - Determine which columns of the dataset are relevant.
            - Select the appropriate chart type ONLY from the list:
            ["bar", "line", "scatter", "pie", "boxplot", "histogram"].
            - Perform any required aggregations or filtering of the data.
            - Prepare the data structure required to render the chart.
            - Return ONLY the JSON that matches the build_chart_spec function schema.

            Rules:
            - Do NOT generate an actual visualization — only the data specification.
            - Always choose the chart type based on the instruction's intent.
            - Always prepare preprocessed data (aggregated when necessary).
            - Use only the provided dataset.
            - If grouping or aggregation is needed, specify it explicitly.
            - Do NOT invent columns that do not exist in the dataset.
            - If the data is insufficient for a more complex chart, choose the most informative option (usually bar/histogram).

            The JSON MUST have:
            - "chart_type" (one of: ["bar","line","scatter","pie","boxplot","histogram"])
            - "data": array of objects (preprocessed data)

            Optional fields:
            - "title"
            - "x"
            - "y"
            - "group_by"
            """
        )

        user_text = (
            f"""
            Below you have the dataset and the instruction.
            Analyze the data structure, choose an appropriate chart type,
            and prepare a JSON specification for the visualization.

            Below is the dataset and the instruction.

            Dataset (first rows):
            {df.head(20).to_dict()}

            Instruction:
            {instruction}

            Remember:
            - Use only the allowed chart types.
            - Prepare the data so that the chart can be rendered immediately.
            - Return ONLY the JSON arguments for build_chart_spec.
            - Do NOT add any explanations.
            """
        )

        print("Calling agent with prompt: \n", user_text)
        msg = self.call_agent(system_prompt, user_text)
        print("Response received from agent.")

        # print("\n\nAgent response:", msg.content)

        # The model returns plain text JSON, so just parse it
        content = msg.content.strip("```json")

        # print("\n\nContent to parse:", content)

        try:
            print("Loading JSON content.")
            spec = json.loads(content)
            # save json for debugging
            with open(f"0{instruction[0]}_debug_chart_spec.json", "w") as f:
                print("Saving json data")
                json.dump(spec, f, indent=4)

        except json.JSONDecodeError:
            print("LLM output:", content)
            raise RuntimeError("Model did not return valid JSON.")

        # allow placeholder
        if spec.get("data") == "USE_FULL_DATASET":
            spec["data"] = df_json

        return spec

    def generate_chart_code(self, df_sample: pd.DataFrame, instruction: str) -> dict:
        """
        Generates:
        1) JSON template with placeholders
        2) Python code that aggregates/transforms the full dataset to fill the template
        """
        df_json = df_sample.to_dict(orient="records")

        system_prompt = f"""
        You are an analytical agent that generates Python code for data transformations.
        Input:
        1) A sample dataset (few rows)
        2) A textual instruction for a chart

        Output:
        1) A JSON chart template with placeholders (use "FILL_WITH_AGGREGATED_DATA" in 'data')
        2) Python code that, when run on the full dataset (variable 'df'), performs all necessary aggregations/filters and fills the 'data' field in the template

        Rules:
        - Only use allowed chart types: {self.ALLOWED_CHART_TYPES}
        - Do not process the full dataset in your reasoning; use only the sample to infer logic
        - The code must be directly executable on the full dataset
        - Return ONLY JSON and code (no explanations)
        - Do NOT include any hardcoded dataset in your code.
        - Assume the variable 'df' contains the full dataset.
        - Generate only the logic to filter, aggregate, or transform df.
        - Fill the 'data' field of the given chart template.
        - Do not generate sample rows.
        """

        user_text = f"""
        Sample dataset (few rows):
        {df_sample.head(20).to_dict()}

        Instruction:
        {instruction}

        Chart template:
        {self.chart_spec_template}
        """

        print(f"Calling agent to generate chart code...\n{user_text}")
        msg = self.call_agent(system_prompt, user_text)
        
        content = msg.content
        print(f"\n\nResponse received from agent.\n{content}")

        # Split code and template JSON if LLM returns both
        try:
            parts = content.split("```python")
            for i in range(len(parts)):
                parts[i] = parts[i].replace("```python", "").replace("```json", "").replace("```", "")

            template_json_text = parts[0]
            if len(parts) > 1:
                code_text = parts[1]
            else:
                code_text = ""

            print(f"\n\nTemplate JSON to parse:\n{template_json_text}\n")
            print(f"\n\nGenerated code:\n{code_text}\n")

            chart_template = json.loads(template_json_text)
            chart_template['instruction'] = instruction  # optional, keep track

            # Save code for later execution
            chart_template['generated_code'] = code_text

            with open(f"debug_generated_code.py", "w") as f:
                print("Saving generated code")
                f.write(code_text) 

        except Exception as e:
            print("LLM output:", content)
            raise RuntimeError("Failed to parse LLM output:", e)

        return chart_template
    
    def execute_chart_code(self, df: pd.DataFrame, chart_spec: dict) -> dict:
        """
        Execute the LLM-generated code and replace 'data' with the transformed dataset.
        If an error occurs, return a dict with an error message and no dashboard info.
        """
        print("\n\nDataFrame before executing generated code:")
        print(df.head(10))
        print(f"DataFrame columns: {df.columns.tolist()}\n\n")
        local_vars = {"df": df.copy()}  # copy to avoid SettingWithCopyWarning
        try:
            exec(chart_spec['generated_code'], {}, local_vars)
            if 'data' in local_vars:
                data = local_vars['data']
                # Convert any pandas Timestamps to ISO strings
                for row in data:
                    for k, v in row.items():
                        if isinstance(v, pd.Timestamp):
                            row[k] = v.isoformat()
                chart_spec['data'] = data
            else:
                print("Warning: LLM code did not produce variable 'data'.")
            chart_spec.pop('generated_code', None)
            return chart_spec
        except Exception as e:
            print("Error executing generated code:", e)
            return {"error": f"Dashboard generation failed: {e}"}


if __name__ == "__main__":
    agent = ChartSpecAgent()

    np.random.seed(42)

    df = pd.DataFrame({
        "school": np.random.choice(["Alpha", "Beta", "Gamma", "Delta"], size=200),
        "city": np.random.choice(["Prague", "Brno", "Ostrava"], size=200),
        "trainer": np.random.choice(["John", "Maria", "Lee", "Anna"], size=200),
        "training_type": np.random.choice(["Soft Skills", "Leadership", "IT Basics", "AI Intro"], size=200),
        "students": np.random.randint(10, 40, size=200),
        "avg_score_before": np.round(np.random.uniform(2.0, 4.5, size=200), 2),
        "avg_score_after": np.round(np.random.uniform(3.0, 5.0, size=200), 2),
        "satisfaction": np.round(np.random.uniform(3.0, 5.0, size=200), 2),
        "date": pd.date_range(start="2024-01-01", periods=200, freq="D")
    })

    df["score_improvement"] = df["avg_score_after"] - df["avg_score_before"]

    instructions = [
        "1. Plot the mean score improvement for each training type.",
        "2. Show the average satisfaction for each school, grouped by city.",
        "3. Show daily score_improvement for Leadership training only.",
        "4. Compare satisfaction variability by city.",
        "5. Compare the correlation between satisfaction and score_improvement.",
        "6. Compare average avg_score_after for trainers who taught at least 10 sessions."
    ]

    for i, instruction in enumerate(instructions):
        try:
            print(f"\n\n=== Processing Instruction {i+1}: {instruction} ===")

            # Generate template + code
            chart_spec = agent.generate_chart_code(df.sample(20), instruction)

            # Execute LLM code on full dataset and fill actual 'data'
            final_chart = agent.execute_chart_code(df, chart_spec)

            print("\n=== Final Chart Spec ===")
            print(json.dumps(final_chart, indent=4))

            # Optional: save
            if not os.path.exists("output"):
                os.makedirs("output")
            with open(f"output/0{i}_filled_chart_spec.json", "w") as f:
                json.dump(final_chart, f, indent=4)
        except InternalServerError as e:
            print("Internal Server Error from LLM API:", e)
            continue