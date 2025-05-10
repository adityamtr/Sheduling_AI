from services.dialog_service import Agent_Orchestrator
from services.agentic import Agent_Generate_Summary, AgentGenerateKPIs
from services.db_controller import DBController
from optimization_algorithm.run_priority_model_v2 import PriorityModel
from services.singlton_arc import SingletonMeta
import pandas as pd
from pathlib import Path
import json
import ast


class Agent_Controller(metaclass=SingletonMeta):

    def __init__(self):
        self.db = DBController()
        self.model = PriorityModel()
        self.products_markdown = self.db.get_products_table()

    def information_extract(self, transcript_data):

        summary  = ""
        generated_kpis = ""
        query = str(transcript_data)

        print("Running Summarization agent")
        orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Summary().prompt_func)
        summary = orchestrator.run(query)

        query = f"""
        Products table:

        {self.products_markdown}

        """

        query += str(transcript_data)

        print("Running KPI agent")
        orchestrator = Agent_Orchestrator(prompt_func=AgentGenerateKPIs().prompt_func,
                                          is_json_response=AgentGenerateKPIs().prompt_response_schema())
        res = orchestrator.run(query)
        try:
            generated_kpis = json.loads(res)
        except:
            generated_kpis = ast.literal_eval(res)

        return summary, generated_kpis

    def priority_results_generation(self, seller_id):

        analysis = self.model.run(seller_id)
        return analysis