from services.framework_model import Qwen_llm, HostedLlm
from config.config import config

print(config.get("llm", "access_type"))
if config.get("llm", "access_type") == "hosted":
    llm = HostedLlm()
else:
    llm = Qwen_llm()

class Service_LLM():

    def __init__(self):
        self.llm = llm

    def call_inference(self, context):
        return self.llm.forward(context)