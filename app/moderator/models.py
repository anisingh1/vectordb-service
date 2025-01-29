import os
import time
from vllm import SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from detoxify import Detoxify

from prompt import getModerationPrompt, getPrompt, parseModerationResponse
from utils import Logger, Prefs

logger = Logger()


class detoxify():
    def __init__(self, path):
        self.detox = Detoxify('unbiased', 
            checkpoint=os.path.join(path, "toxic_debiased-c7548aa0.ckpt"), 
            device='cuda', 
            huggingface_config_path=path)
        self.threshold = Prefs().getFloatPref('detoxifythreshold')


    async def check(self, text, request_id):
        try:
            start = time.time()
            response = self.detox.predict(text)
            result = True
            categories = []

            if response['toxicity'] >= self.threshold or \
                response['severe_toxicity'] >= self.threshold or \
                response['identity_attack'] >= self.threshold or \
                response['insult'] >= self.threshold or \
                response['threat'] >= self.threshold:
                categories.append('Offensive')
                result = False
            if response['sexual_explicit'] >= self.threshold or \
                response['threat'] >= self.threshold or \
                response['sexual_explicit'] >= self.threshold or \
                response['obscene'] >= self.threshold:
                categories.append('Sexual')
                result = False

            ret = {
                "request_id": request_id,
                "model": "detoxify",
                "input": text,
                "safe": result,
                "category": categories
            }
            end = time.time()
            logger.debug(f"Detoxify : {result}, Time: {int((end - start) * 1000)}ms")
            return ret
        
        except Exception as e:
            logger.error(e)
            ret = {
                "request_id": request_id,
                "model": "detoxify",
                "input": text,
                "safe": "error"
            }
            return ret


class llm():
    def __init__(self, llm_args, llm_modelname):
        pargs = AsyncEngineArgs.add_cli_args(llm_args).parse_args()
        engine_args = AsyncEngineArgs.from_cli_args(pargs)
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        self.model = os.path.basename(engine_args.model)
        self.modelname = llm_modelname


    async def moderate(self, text, request, request_id, region):
        try:
            start = time.time()
            finalprompt = getModerationPrompt(text, self.modelname, region)
            sampling_params = SamplingParams(temperature=0, top_p=1, max_tokens=40)

            results_generator = self.engine.generate(finalprompt, sampling_params, request_id)
            final_output = None
            async for request_output in results_generator:
                if await request.is_disconnected():
                    # Abort the request if the client disconnects.
                    await self.engine.abort(request_id)
                    return {}
                final_output = request_output

            assert final_output is not None
            text_outputs = final_output.outputs[0].text

            response = parseModerationResponse(text_outputs, self.modelname)
            if 'safe' in response:
                ret = {
                    "request_id": request_id,
                    "model": self.modelname,
                    "input": text,
                    "safe": response['safe'],
                    "category": response['category']
                }
            else:
                ret = {
                    "request_id": request_id,
                    "model": self.modelname,
                    "input": text,
                    "error": response['error']
                }
            end = time.time()
            logger.debug(f"{self.modelname} : {ret['safe']}, Time: {int((end - start) * 1000)}ms")
            return ret
        
        except Exception as e:
            logger.error(e)
            ret = {
                "request_id": request_id,
                "model": self.modelname,
                "input": text,
                "error": e
            }
            return ret
    

    async def chat(self, text, request, request_id, tokens=4096):
        try:
            start = time.time()
            finalprompt = getPrompt(text, self.modelname)
            sampling_params = SamplingParams(temperature=0, top_p=1, max_tokens=tokens)

            results_generator = self.engine.generate(finalprompt, sampling_params, request_id)
            final_output = None
            async for request_output in results_generator:
                if await request.is_disconnected():
                    # Abort the request if the client disconnects.
                    await self.engine.abort(request_id)
                    return {}
                final_output = request_output

            assert final_output is not None
            finalprompt = final_output.prompt
            text_outputs = final_output.outputs[0].text
            ret = {
                "request_id": request_id,
                "model": self.modelname,
                "response": text_outputs
            }
            end = time.time()
            logger.debug(f"{self.modelname} : {text_outputs}, Time: {int((end - start) * 1000)}ms")
            return ret
        
        except Exception as e:
            logger.error(e)
            ret = {
                "request_id": request_id,
                "model": self.modelname,
                "error": e
            }
            return ret