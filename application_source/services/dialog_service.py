from services.llm_service import Service_LLM

class Agent_Orchestrator():

    def __init__(self, prompt_func, is_json_response=False):
        self.servie_llm = Service_LLM()
        self.prompt_func = prompt_func
        self.is_json_response = is_json_response

    def run(self, user_query=None):
        context = self.prompt_func(user_input=user_query)
        response = self.servie_llm.call_inference(context, is_json_response = self.is_json_response)
        return response

