from services.llm_service import Service_LLM

class Agent_Orchestrator():

    def __init__(self, prompt_func):
        self.servie_llm = Service_LLM()
        self.prompt_func = prompt_func

    def run(self, user_query=None):
        context = self.prompt_func(user_input=user_query)
        response = self.servie_llm.call_inference(context)
        return response

