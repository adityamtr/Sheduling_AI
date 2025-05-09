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
        self.remove_elements = ["```json", "```python", "```"]

    def cleanup(self, data):

        for element in self.remove_elements:
            data = data.replace(element, "")
        return data

    def call_inference(self, context):
        res = self.llm.forward(context)
        cleaned_res = self.cleanup(res)
        return cleaned_res