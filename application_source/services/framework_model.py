from config.config import config
from services.singlton_arc import SingletonMeta
from services.gpt_service import GPTService
from pathlib import Path
import os
import requests
import json

root_path = Path(os.getcwd().split('application_source')[0] + 'application_source')
# print(root_path)

class HostedLlm(metaclass=SingletonMeta):

    def __init__(self):
        self.service = config.get("llm", "use_service")
        self.model_name = config.get("llm", "model_name")
        if self.service == "openai":
            self.client = GPTService().get_client()
        else:
            pass

    def forward(self, context, is_json_response=False):

        client = self.client

        answer = ""
        code = ""

        response_format = {"type":"text"}

        if is_json_response:
            if isinstance(is_json_response, bool):
                response_format = {"type": "json_object"}
            else:
                response_format = {"type": "json_schema", "json_schema": {"schema": is_json_response, "name": "format_schema", "strict": True}}

        try:

            response = client.chat.completions.create(
                model = self.model_name,
                seed = 42,
                temperature = 0.01,
                messages = context,
                max_completion_tokens = 4096,
                response_format = response_format,
                stream = False
                )

            if len(response.choices) > 0:
                res = response.choices[0]
                if res.finish_reason:
                    code = res.finish_reason
                if res.message:
                    message = res.message
                    if message.content:
                        answer = message.content

                usage = response.usage
                # print(usage)

        except Exception as e:
            print(e, code)
            raise e

        return answer