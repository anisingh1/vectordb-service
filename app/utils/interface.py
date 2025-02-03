from pydantic import BaseModel
from typing import List
from utils import Logger

logger = Logger()


class HealthResponse(BaseModel):
    env: str
    status: str


class InfoResponse(BaseModel):
    models: List[str]
    dbs: List[dict]


class ErrorResponse(BaseModel):
    request_id: str
    code: str
    error: str