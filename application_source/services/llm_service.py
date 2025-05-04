from services.framework_model import Qwen_llm

llm = Qwen_llm()

class Service_LLM():

    def __init__(self):
        self.llm = llm

    def call_inference(self, context):
        return self.llm.forward(context)