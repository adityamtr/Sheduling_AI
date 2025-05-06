import json

from http import HTTPStatus
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from controller.request_model import LlmBase
from services.llm_service import Service_LLM


class HostController:

    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route("/", self.health_check, methods=["GET"])

        self.router.add_api_route(
            "/call_qwen_llm", self.qwen_llm, methods=["POST"]
        )

    def health_check(self):
        return JSONResponse(status_code=HTTPStatus.OK, content="Success")

    def qwen_llm(self, request: Request, query_request: LlmBase):

        headers = {"Content-Type": "application/json"}
        context = json.loads(query_request.context)

        try:
            response = Service_LLM().call_inference(context)
            response_json = jsonable_encoder({"response": response})
            query_response = JSONResponse(status_code=HTTPStatus.OK, content=response_json, headers=headers)
        except Exception as e:
            exception_dict = dict(err_stack=str(e))
            query_response =  JSONResponse(
                status_code=exception_dict.get("errCode", HTTPStatus.INTERNAL_SERVER_ERROR
            ),
            content=exception_dict,
            headers=headers
            )
        return query_response