from services.dialog_service import Agent_Orchestrator
from services.agentic import Agent_Generate_Summary, AgentGenerateKPIs, Agent_Generate_Priority_Reasoning, Agent_Formatter
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

    def valdiate_response(self, data):

        if "properties" in data[0].keys():
            final = []
            for element in data:
                final.append(element["properties"])
            return final
        return data


    def priority_results_generation(self, seller_id):

        analysis, analysis_expanded = self.model.run(seller_id)

        query = ""

        priority_order = analysis_expanded['priority_order']

        for name, data in analysis_expanded.items():
            if name != "priority_order":
                customer_name = name
                priority = priority_order.index(customer_name) + 1
                score = data['score']

                query += f"""
                
                ### --------- ###
                
                customer_name: {customer_name}
                priority: {priority}
                priority_score : {score}
                days_since_last_meeting: {data['days_since_last_meeting']}
                days_since_last_purchase: {data['days_since_last_purchase']}
                avg_annual_sales: {data['avg_annual_sales']}
                purchase_freq_per_qtr: {data['purchase_freq_per_qtr']}
                sentiment_score: {data['sentiment_score']}
                
                """

                customer_id = data['customer_id']
                kpi_data = self.db.get_reasoning_requirements(seller_id=seller_id, customer_id=customer_id)

                for index, row in kpi_data.iterrows():
                    summary = row['summary']
                    sentiment = row['sentiment']
                    products_marketed_list = row['products_marketed_list']
                    products_interested_list = row['products_interested_list']

                    query += f"\nMeeting {index+1}:\n"
                    query += f"""
                    
                    1. Summary: {summary}
                    
                    2. Sentiment: {sentiment}
                    
                    3. Products marked list: {products_marketed_list}
                    
                    4. Products interested list: {products_interested_list}
                    
                    """

        print("Running Reasoning and Results agent")
        orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Priority_Reasoning().prompt_func,
                                          is_json_response=Agent_Generate_Priority_Reasoning().prompt_response_schema())
        res = orchestrator.run(query)
        try:
            res = json.loads(res)
        except:
            res = ast.literal_eval(res)
        cutomer_visits_highlights = self.valdiate_response(res)

        print("Running Formatting agent")
        for data in cutomer_visits_highlights:
            query = str(data)
            orchestrator = Agent_Orchestrator(prompt_func=Agent_Formatter().prompt_func,
                                              is_json_response=Agent_Formatter().prompt_response_schema())
            res = orchestrator.run(query)
            analysis[data['customer_name']]['summary'] = res


        return analysis

