import os, sys
import json
import uuid
import argparse
import uvicorn

import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='TypedStorage is deprecated')

from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from utils import LoggerInit, Logger
from utils.interface import (HealthResponse, InfoResponse, ErrorResponse)
from vectordb import Memory



# Setting Global variables
load_dotenv()
timeout_keep_alive = 5  # seconds
logger = Logger()
environment = str(os.environ.get('ENVIRONMENT_NAME')).lower()
debug = os.environ.get('DEBUG')
if debug != None and (debug.lower() == 'true' or debug == '1'):
    debug = True
else:
    debug = False


# Reading Model Paths
if os.environ.get('PYTHON_APP_FOLDER') != None:
    model_path = os.path.join(os.environ.get('PYTHON_APP_FOLDER'), 'model')
else:
    if os.environ.get('MODEL_PATH') != None:
        model_path = os.environ.get('MODEL_PATH')

if not os.path.exists(os.path.join(model_path, "config.json")):
    raise Exception("Model not found.")


# Reading model versions
model_config = os.path.join(model_path, 'config.json')
with open(model_config) as f:
    conf = json.load(f)
    served_model = conf['_name_or_path']


# Initialize logger
LoggerInit()


# Exception Handler
async def unhandledExceptionHandler(request: Request, exc: Exception) -> JSONResponse:
    """
    This middleware will log all unhandled exceptions.
    Unhandled exceptions are all exceptions that are not HTTPExceptions or RequestValidationErrors.
    """
    id = str(uuid.uuid4())
    exception_type, exception_value, exception_traceback = sys.exc_info()
    exception_name = getattr(exception_type, "__name__", None)
    response = ErrorResponse(request_id=id, code=str(500000), error=str(exception_name)).model_dump()
    logger.error(response)
    return JSONResponse(response, status_code=500)


# Setting configurable parameters
parser = argparse.ArgumentParser(description="RESTful API server.")

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


# Start Vector DB
vector_store = Memory(model=model_path)
vector_store.save("Hello World", 'World')

# FastAPI app
app = FastAPI(title="VectorDB Service",
    summary="Vector Cache service to store and search embeddings",
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
    return JSONResponse(
        InfoResponse(models=[model_path]).model_dump(), status_code=200)



@app.post('/v1/add')
async def add(request: Request) -> Response:
    # Reading input request data
    request_dict = await request.json()
    if 'request_id' in request_dict:
        id = str(request_dict.pop("request_id"))
    else:
        id = str(uuid.uuid4())

    if 'text' in request_dict:
        text = str(request_dict.pop("text"))
    else:
        ret = ErrorResponse(request_id=id, code=str(422001), error="Required field `text` missing in request").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=422)

    if 'metadata' in request_dict:
        metadata = request_dict.pop("metadata")
    else:
        metadata = ''

    try:
        vector_store.save(text=text, metadata=metadata)
        ret = {
            "request_id": id
        }
        return JSONResponse(ret)
        
    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(500), error="Something went wrong: " + str(e)).model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=500)


@app.post('/v1/search')
async def add(request: Request) -> Response:
    # Reading input request data
    request_dict = await request.json()
    if 'request_id' in request_dict:
        id = str(request_dict.pop("request_id"))
    else:
        id = str(uuid.uuid4())

    if 'text' in request_dict:
        text = str(request_dict.pop("text"))
    else:
        ret = ErrorResponse(request_id=id, code=str(422001), error="Required field `text` missing in request").model_dump()
        logger.error(e)
        return JSONResponse(ret, status_code=422)

    if 'top_n' in request_dict:
        top_n = request_dict.pop("top_n")
    else:
        top_n = 3

    try:
        cached_results = vector_store.search(query=text, top_n=1)
        if len(cached_results) == 1 and cached_results[0]['distance'] == 0:
            results = []
            for i in cached_results:
                results.append({
                    "text": i['chunk'],
                    "metadata": i['metadata']
                })
            ret = {
                "request_id": id,
                "results": results
            }
        else:
            ret = {
                "request_id": id,
                "results": []
            }
        return JSONResponse(ret)
        
    except Exception as e:
        ret = ErrorResponse(request_id=id, code=str(500), error="Something went wrong: " + str(e)).model_dump()
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
