import asyncio
import torch
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from utils import Logger
from moderator.models import detoxify, llm

logger = Logger()


class HealthResponse(BaseModel):
    env: str
    status: str


class InfoResponse(BaseModel):
    models: List[str]


class ErrorResponse(BaseModel):
    request_id: str
    code: str
    error: str


llm_obj = None
detoxify_obj = None
class base():
    def __init__(self, llm_args, llm_modelname, detox_args=None):
        global llm_obj
        global detoxify_obj
        if torch.cuda.is_available() == False and torch.backends.mps.is_available() == False:
            raise Exception("Supported GPU not available")
        elif torch.cuda.is_available() == True:
            gpus = torch.cuda.device_count()
            if gpus < 1:
                raise Exception("Supported GPU not available")
        
        if (detox_args != None and detoxify_obj == None):
            detoxify_obj = detoxify(detox_args)
        if (llm_obj == None):
            llm_obj = llm(llm_args, llm_modelname)


class moderate(base):
    def __init__(self, llm_args, llm_modelname, detox_args):
        super().__init__(llm_args, llm_modelname, detox_args)


    async def run(self, prompt, request, id, models, region=None):
        pending = []
        if 'detoxify' in models:
            detoxify_task = asyncio.create_task(detoxify_obj.check(prompt, id))
            pending.append(detoxify_task)
        if 'llm' in models:
            llama_task = asyncio.create_task(llm_obj.moderate(prompt, request, id, region))
            pending.append(llama_task)

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            result = done.pop().result()
            if 'safe' in result and result['safe'] == False:
                try:
                    while pending:
                        p = pending.pop()
                        p.cancel()
                    return result
                        
                except Exception as e:
                    logger.error(e)
        
        return result


class chat(base):
    def __init__(self, llm_args, llm_modelname):
        super().__init__(llm_args, llm_modelname)


    async def run(self, prompt, request, id, tokens=4096):
        result = await llm_obj.chat(prompt, request, id, tokens)
        return result