from sympy.codegen.cxxnodes import using
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from config.config import config
from services.singlton_arc import SingletonMeta
from services.gpt_service import GPTService
import torch
from pathlib import Path
import os
import requests
import json

device = "cuda" if torch.cuda.is_available() else "cpu"
# print(device)
root_path = Path(os.getcwd().split('application_source')[0] + 'application_source')
# print(root_path)



# class HostedLlm(metaclass=SingletonMeta):
#
#     def __init__(self):
#         self.host_link = config.get("llm", "host_link")
#         self.endpoint = "/call_qwen_llm"
#         self.path = f"{self.host_link}{self.endpoint}"
#
#     def forward(self, context):
#         request_data = {"context": json.dumps(context)}
#         response = requests.post(self.path, json=request_data, verify = False)
#         if response.status_code == 200:
#             pass
#         else:
#             print(f"Error: {response.status_code}, {response.text}")
#         return response.json()["response"]

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
                response_format = {"type": "json_schema", "json_schema": {"shema": is_json_response, "name": "format_schema", "strict": True}}

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
                print(usage)

        except Exception as e:
            print(e, code)
            raise e

        return answer


class Qwen_llm(metaclass=SingletonMeta):

    def __init__(self):
        model_id = Path.joinpath(root_path, "models/Qwen/Qwen2.5-3B-Instruct")

        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,  # <-- match input dtype
            bnb_4bit_use_double_quant=False,
            bnb_4bit_quant_type="nf4"  # or "fp4" if needed
        )

        model = AutoModelForCausalLM.from_pretrained(model_id,
                                                     quantization_config=bnb_config,
                                                     device_map="auto",
                                                     trust_remote_code=True)
        model.eval()

        self.tokenizer = tokenizer
        self.model = model

    def forward(self, context):
        text = self.tokenizer.apply_chat_template(
            context,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=8000,  # <-- use greedy decoding (not beam search)
            temperature=0.01,  # <-- has no effect if do_sample=False
            top_p=1.0,
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
