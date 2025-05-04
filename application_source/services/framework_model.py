from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from pathlib import Path
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
# print(device)
root_path = Path(os.getcwd().split('application_source')[0] + 'application_source')
# print(root_path)

class Qwen_llm():

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
            temperature=0.001,  # <-- has no effect if do_sample=False
            top_p=1.0,
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
