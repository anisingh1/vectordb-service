import sys, os
import json
import uuid
import argparse
import uvicorn

import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='TypedStorage is deprecated')


from vectordb import Memory
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from utils import LoggerInit, Logger
from moderator.exp_handler import unhandledExceptionHandler
from moderator.interface import (HealthResponse, InfoResponse, ErrorResponse)
from moderator import moderate, chat


# Setting Global variables
load_dotenv()
timeout_keep_alive = 5  # seconds
logger = Logger()
served_models = []
served_llm_model = None
served_detoxify_model = None
engine = None
environment = str(os.environ.get('ENVIRONMENT_NAME')).lower()
debug = os.environ.get('DEBUG')
if debug != None and (debug.lower() == 'true' or debug == '1'):
    debug = True
else:
    debug = False


# Reading Model Paths
if os.environ.get('PYTHON_APP_FOLDER') != None:
    model_path = os.path.join(os.environ.get('PYTHON_APP_FOLDER'), 'model')
    embeddings_model_path = os.path.join(os.environ.get('PYTHON_APP_FOLDER'), 'model', 'all-minilm-l6-v2')
else:
    if os.environ.get('MODEL_PATH') != None:
        model_path = os.environ.get('MODEL_PATH')
        served_models.append('llm')
    else:
        model_path = None
        logger.info("LLM model not found.")
    
    if os.environ.get('CACHE_MODEL_PATH') != None:
        embeddings_model_path = os.environ.get('CACHE_MODEL_PATH')
        served_models.append('cache')
    else:
        embeddings_model_path = None
        logger.info("Embeddings model not found. Cache will not be used.")

if len(served_models) == 0:
    raise Exception("No model found to serve.")


# Reading model versions
served_llm_model = None
if 'llm' in served_models:
    llm_model_config = os.path.join(model_path, 'config.json')
    max_model_len = 4096
    with open(llm_model_config) as f:
        conf = json.load(f)
        if conf['max_position_embeddings'] < 4096:
            max_model_len = conf['max_position_embeddings']
        served_llm_model = conf['_name_or_path']


# Initialize logger
LoggerInit()


# Setting configurable parameters
parser = argparse.ArgumentParser(description="vLLM RESTful API server.")

# uvicorn parameters
parser.add_argument("--host", type=str, default='0.0.0.0', help="Hostname")
parser.add_argument("--port", type=int, default=6006, help="Port")

# gunicorn parameters
parser.add_argument("--workers", type=int, default=1)
parser.add_argument("--bind", type=str, default="")
parser.add_argument("--timeout", type=int, default=2000)
parser.add_argument("--worker-class", type=str, default='uvicorn.workers.UvicornWorker')

# fastapi parameters
parser.add_argument("--allow-credentials",
                            action="store_true",
                            default=True,
                            help="allow credentials")
parser.add_argument("--allowed-origins",
                            type=json.loads,
                            default=["*"],
                            help="allowed origins")
parser.add_argument("--allowed-methods",
                            type=json.loads,
                            default=["*"],
                            help="allowed methods")
parser.add_argument("--allowed-headers",
                            type=json.loads,
                            default=["*"],
                            help="allowed headers")

# vllm parameters
sys.argv.extend(['--model', model_path])
sys.argv.extend(['--disable-log-requests'])
sys.argv.extend(['--disable-log-stats'])
sys.argv.extend(['--enforce-eager'])
sys.argv.extend(['--dtype', 'float16'])
sys.argv.extend(['--max-model-len', str(max_model_len)])

moderator = moderate(parser, served_llm_model)
chatbot = chat(parser, served_llm_model)

# Start Vector DB
if 'cache' in served_models:
    vector_store = Memory(embeddings=embeddings_model_path)
    vector_store.save("Hello World", {'category': ''})

# FastAPI app
app = FastAPI(title="Harm & Bias Service",
    summary="Content moderation service based on LLMs",
    version="0.1",
    openapi_tags=[
        {
            "name": "basic",
            "description": "Common API(s)",
        },
        {
            "name": "v1",
            "description": "Version 1 API(s)"
        },
    ],
    debug=debug
)
app.add_exception_handler(Exception, unhandledExceptionHandler)


# Get Health Check API
@app.get('/health')
async def health() -> Response:
    status = 'green'
    return JSONResponse(
        HealthResponse(
            env=environment, 
            status=status
        ).model_dump(), status_code=200)


# Get Models Info API
@app.get('/v1/info')
async def info() -> Response:
    model_paths = []
    if 'llm' in served_models:
        model_paths.append(os.path.basename(served_llm_model))
    if 'detoxify' in served_models:
        model_paths.append(os.path.basename(served_detoxify_model))
        
    return JSONResponse(
        InfoResponse(models=model_paths).model_dump(), status_code=200)


# Text Moderation API
@app.post('/v1/moderate')
async def safetyCheck(request: Request) -> Response:
    request_dict = await request.json()
    if 'request_id' in request_dict:
        id = str(request_dict.pop("request_id"))
    else:
        id = str(uuid.uuid4())
    try:
        models = []
        prompt = str(request_dict.pop("prompt"))
        if 'model' in request_dict:
            model = str(request_dict.pop("model"))
            if model == None:
                models = served_models
            elif model not in served_models:
                ret = ErrorResponse(request_id=id, code=str(422001), error="Requested model not found").model_dump()
                logger.error(e)
                return JSONResponse(ret, status_code=422)
            else:
                models.append(model)
        else:
            models = served_models
            
        region = None
        if "region" in request_dict:
            region = str(request_dict.pop("region"))
    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(422001), error="Required field `prompt` missing in request").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=422)

    try:
        try:
            prompt_words = prompt.split()
            filtered_prompt = [w for w in prompt_words if not w.lower() in stopwords]
            filtered_prompt = ' '.join(filtered_prompt)
            if 'cache' in models:
                cached_results = vector_store.search(filtered_prompt, 1)
                if len(cached_results) == 1 and cached_results[0]['distance'] == 0:
                    metadata = cached_results[0]['metadata']['category'].split(',')
                    safe = True
                    category = []
                    if len(metadata) > 0 and metadata[0] != '':
                        safe = False
                        category = metadata
                    ret = {
                        "request_id": id,
                        "model": "cache",
                        "input": prompt,
                        "safe": safe,
                        "category": category
                    }
                    return JSONResponse(ret)
        except Exception as e:
            ret = ErrorResponse(request_id=id, code=str(500), error="Something went wrong").model_dump()
            logger.error(ret)
            pass
        
        result = await moderator.run(prompt, request, id, models, region)
        if 'safe' in result:
            if 'cache' in models:
                vector_store.save(filtered_prompt, {'category': ','.join(result['category'])})
            return JSONResponse(result)
        elif 'error' in result:
            ret = ErrorResponse(request_id=id, code=str(500), error=result['error']).model_dump()
            logger.error(result['error'])
            return JSONResponse(ret, status_code=500)
        
    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(500), error="Something went wrong").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=500)


# Chat API
@app.post('/v1/chat')
async def chat(request: Request) -> Response:
    request_dict = await request.json()
    if 'request_id' in request_dict:
        id = str(request_dict.pop("request_id"))
    else:
        id = str(uuid.uuid4())
    try:
        tokens = 4096
        prompt = str(request_dict.pop("prompt"))
        if "tokens" in request_dict:
            tokens = request_dict.pop("tokens")
    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(422001), error="Required field `prompt` missing in request").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=422)

    try:
        result = await chatbot.run(prompt, request, id, tokens)
        if 'error' in result:
            ret = ErrorResponse(request_id=id, code=str(500), error=result['error']).model_dump()
            logger.error(result['error'])
            return JSONResponse(ErrorResponse(request_id=id, code=str(500), error="Something went wrong").model_dump(), status_code=500)
        else:
            return JSONResponse(result)

    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(500), error="Something went wrong").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=500)


args = parser.parse_args()
app.add_middleware(
    CORSMiddleware,
    allow_origins=args.allowed_origins,
    allow_credentials=args.allow_credentials,
    allow_methods=args.allowed_methods,
    allow_headers=args.allowed_headers,
)
logger.debug(f"args: {args}")


# Run Application
if __name__ == "__main__":

    # Uvicorn configuration
    uvicorn_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "loggers": {
            "uvicorn": {"level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO", "propagate": False},
        },
    }

    uvicorn.run(app, host=args.host, port=args.port, timeout_keep_alive=timeout_keep_alive, log_config=uvicorn_log_config)
