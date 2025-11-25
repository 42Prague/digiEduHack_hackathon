import json
import pandas as pd

from pymongo import MongoClient
from typing import List, Dict, Any
from chart_spec_agent import ChartSpecAgent


def make_mongo_query_tool():
    """
    Returns a function that can be used as the LLM tool.
    Executes a MongoDB query (string) with eval-safety and returns list of dict records.
    """

    def mongo_query(query: str) -> List[Dict[str, Any]]:
        """
        Run a MongoDB query. Accepts stringified JSON like:
        '{"training_type": "Leadership"}'
        """
        try:
            q = json.loads(query)
        except Exception:
            raise ValueError("Invalid query: must be valid JSON string")

        client = MongoClient("mongodb://localhost:27017/")
        db = client["data_quality_service"]
        collection = db["records"]
        cursor = collection.find(q)
        rows = [dict(x) for x in cursor]

        # Remove MongoDB ObjectId
        for r in rows:
            r.pop("_id", None)

        return rows

    return mongo_query



def make_dashboard_tool():
    """
    Returns a function that acts as a dashboard-generation tool.
    """

    agent = ChartSpecAgent()

    def call_dashboard_agent(instruction: str, mongo_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate dashboard: receives {'instruction': str, 'mongo_data': [...]}
        Returns final chart JSON.
        """
        df = pd.DataFrame(mongo_data)
        sample = df.head(20)

        chart_template = agent.generate_chart_code(sample, instruction)
        final_chart = agent.execute_chart_code(df, chart_template)

        return final_chart

    return call_dashboard_agent



def make_report_tool(llm_reporter=None):
    """
    Create a tool for generating long text reports.
    If llm_reporter is provided, use it; otherwise, fallback to template-based summary.
    """

    def create_text_report(instruction: str, mongo_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a long text report. Accepts:
        - instruction: str
        - mongo_data: list of dicts
        """
        if llm_reporter:
            return llm_reporter(instruction, mongo_data)

        # fallback simple report
        text = (
            f"Report based on instruction:\n{instruction}\n\n"
            f"Number of records: {len(mongo_data)}\n\n"
            "Data Sample:\n"
            f"{mongo_data[:5]}"
        )
        return {"report_text": text}

    return create_text_report