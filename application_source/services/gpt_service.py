import os
from pathlib import Path
from openai import OpenAI

from config.config import config
from services.singlton_arc import SingletonMeta

root_path = Path(os.getcwd().split('application_source')[0] + 'application_source')

class GPTService(metaclass=SingletonMeta):
    def __init__(self):

        with open(root_path / config.get("llm", "api_path"), 'r') as file:
            self.api_key = file.readline().strip()

    def get_client(self):

        client = OpenAI(api_key=self.api_key)
        return client