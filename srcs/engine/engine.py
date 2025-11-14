from main_agent import MainAgent
from pprint import pprint


class EngineProcessor:
    def __init__(self):
        self.main_agent = MainAgent()

    def process(self, query: str):
        # Main agent processes the query
        response = self.main_agent.run(query)
        return response


if __name__ == "__main__":
    engine = EngineProcessor()
    # user_query = "Show a dashboard of sales trends by region for Q3 2023 and provide a summary report of total and average sales."
    user_query = "What is the result of 10 + 15?"

    engine_response = engine.process(user_query)
    print("RESPONSE:")
    pprint(engine_response)