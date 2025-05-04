from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "Qwen/Qwen2.5-3B-Instruct"
# model_id = "Qwen/Qwen2.5-0.5B-Instruct"

print(f"Downloading Model: {model_id}\n")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32, trust_remote_code=True)

save_path = f"models/{model_id}"

print(f"\nSaving Model to Path: {save_path}\n")
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print("Sequence Completed")