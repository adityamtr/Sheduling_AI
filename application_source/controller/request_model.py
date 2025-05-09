from pydantic import BaseModel
from typing_extensions import List

class LlmBase(BaseModel):
    context : str