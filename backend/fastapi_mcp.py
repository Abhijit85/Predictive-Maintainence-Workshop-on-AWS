"""
FastAPI-based Server for Predictions Module
"""

import asyncio
import os
import sys
import logging
from fastmcp import FastMCP
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from bson.json_util import dumps
import uvicorn
import certifi

sys.path.append(str(Path(__file__).parent))

from config.config_loader import FastAPIConfig, ModelsConfig
from core.services import PredictionService
from api.models import PredictionRequest, PredictionResponse, ModelListResponse, SensorListResponse, DiagnosisResponse, TextGenerationResponse, HealthResponse

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

# Create our own config instances to avoid logging conflicts
fastapi_config = FastAPIConfig()
models_config = ModelsConfig()

# ==================== Global Variables ====================

# ==================== Configuration Variables ====================

MONGO_CONN = fastapi_config.MONGO_CONN
MONGO_DB_NAME = fastapi_config.OUTPUT_DB
PREDICTION_DB_INPUT = fastapi_config.INPUT_DB
MONGO_CHUNKS_COL = fastapi_config.CHUNKS_COL
EMBEDDINGS_MODEL = fastapi_config.EMBEDDING_MODEL
RERANKER_MODEL = fastapi_config.RERANKER_MODEL
GUARDRAIL_ID = fastapi_config.BEDROCK_GUARDRAIL_ID
GUARDRAIL_VERSION = fastapi_config.BEDROCK_GUARDRAIL_VERSION
MODELS_FOLDER = Path(models_config.MODEL_FOLDER)


# Global variables for database and service
client = None
prediction_service = None

# ==================== Lifespan Management ====================

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """FastAPI lifespan for startup and shutdown"""
    global client, prediction_service

    logging.info("Starting up the Predictive Maintenance FastAPI app...")

    try:
        fastapi_config.log_configuration()
    except Exception as e:
        logging.error("Failed to log configuration: %s", e)

    try:
        client = MongoClient(MONGO_CONN, server_api=ServerApi('1'), tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where())
        client.admin.command('ping')
        logging.info("Connected to MongoDB.")

        logging.info(f"Using database (env PREDICTION_MONGODB_NAME): {MONGO_DB_NAME}")
        logging.info(f"Using input database (env PREDICTION_DB_INPUT): {PREDICTION_DB_INPUT}")
        logging.info(f"Using chunks collection (env PREDICTION_CHUNKS_COL): {MONGO_CHUNKS_COL}")
        logging.info(f"Using embeddings model (env EMBEDDING_MODEL): {EMBEDDINGS_MODEL}")
        logging.info(f"Using reranker model: {RERANKER_MODEL}")

        # Initialize prediction service
        input_db = client[PREDICTION_DB_INPUT]
        output_db = client[MONGO_DB_NAME]
        chunks_col = input_db[MONGO_CHUNKS_COL]
        info_col = input_db[fastapi_config.INFO_COL]

        prediction_service = PredictionService(
            client=client,
            input_db=input_db,
            output_db=output_db,
            chunks_col=chunks_col,
            info_col=info_col,
            embedding_model=EMBEDDINGS_MODEL,
            reranker_model=RERANKER_MODEL,
            guardrail_id=GUARDRAIL_ID,
            guardrail_version=GUARDRAIL_VERSION
        )

    except Exception as e:
        logging.error("MongoDB connection failed: %s", e)
        raise

    os.makedirs(MODELS_FOLDER, exist_ok=True)

    yield

    logging.info("Shutting down the Predictive Maintenance FastAPI app...")
    if client:
        client.close()

# ==================== API Endpoints ====================

# ==================== FastAPI App Creation ====================

app = FastAPI(
    title="Predictive Maintenance API",
    version="1.0.0",
    lifespan=app_lifespan
)

# ==================== Regular API Endpoints ====================

@app.post('/api/predict', operation_id="make_prediction", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Endpoint for model prediction

    Expected JSON format:
    {
        "independent_variables": [[1.2, 3.4, 5.6, ...]] or [1.2, 3.4, 5.6, ...],
        "dependent_variables": [0, 1, 0, ...] (optional),
        "model_identifier": "model_name"
    }
    """
    try:
        data = request.model_dump()

        if data is None:
            raise HTTPException(status_code=400, detail='No JSON data provided')

        independent_variables = data['independent_variables']
        dependent_variables = data.get('dependent_variables', None)
        model_identifier = data['model_identifier']

        return prediction_service.make_prediction(independent_variables, model_identifier, dependent_variables)

    except Exception as e:
        logging.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Prediction failed: {str(e)}')

@app.get('/api/models', operation_id="list_available_models", response_model=ModelListResponse)
async def list_models():
    """List available models in the models directory"""
    return prediction_service.list_models()

@app.get("/api/diagnose", operation_id="diagnose_technical_issue", response_model=DiagnosisResponse)
async def diagnose(
    issue: str = Query(..., description="Issue description"),
    model: str = Query("", description="Completion model"),
    embeddings_model: str = Query(EMBEDDINGS_MODEL, description="Embeddings model"),
    reranker: str = Query(RERANKER_MODEL, description="Reranker model")
):
    """Diagnose technical issues using AI with hybrid search and reranking."""
    return prediction_service.diagnose_issue(issue, model, embeddings_model, reranker)

@app.get("/api/monitoring", operation_id="get_sensor_monitoring_data")
async def monitoring(
    sensor: str = Query(..., description="Sensor name"),
    excludeId: str = Query(None, description="Exclude document ID"),
    limit: int = Query(10, description="Number of records to return")
):
    """Get monitoring data for a specific sensor."""
    response = prediction_service.get_monitoring_data(sensor, limit, excludeId)

    if limit == 1 and isinstance(response, dict):
        return response
    return Response(content=dumps(response), media_type="application/json")

@app.get("/api/text_gen", operation_id="generate_text_with_ai", response_model=TextGenerationResponse)
async def text_gen(
    model: str = Query("", description="AI model to use"),
    text: str = Query(..., description="Input text prompt")
):
    """Generate text using AI models."""
    return prediction_service.generate_text(text, model)

@app.get("/api/sensors", operation_id="list_sensor_collections", response_model=SensorListResponse)
async def list_sensor_collections():
    """
    List all sensor collections (MongoDB collections) in the predictions database.
    """
    return prediction_service.list_sensor_collections()

# ==================== Health Check ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "predictive_maintenance"}

# ==================== Main Execution ====================

async def start_servers():
    """Start FastAPI server with MCP mounted for HTTP/SSE transport"""
    logging.info(f"Starting Predictive Maintenance Server on {fastapi_config.HOST}:{fastapi_config.PORT}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create MCP from existing FastAPI app
    mcp = FastMCP.from_fastapi(
        app=app,
        name="Predictive Maintenance MCP"
    )

    # Create MCP HTTP app
    mcp_app = mcp.http_app(path='/')

    # Combine lifespans
    @asynccontextmanager
    async def combined_lifespan(fastapi_app: FastAPI):
        async with app_lifespan(fastapi_app):
            async with mcp_app.lifespan(fastapi_app):
                yield

    # Update the existing app's lifespan
    app.router.lifespan_context = combined_lifespan

    # Mount MCP into the existing app
    app.mount("/mcp/", mcp_app)

    # Log endpoints
    logging.info("Server ready:")
    logging.info("  - REST API: http://%s:%d/api/*", fastapi_config.HOST, fastapi_config.PORT)
    logging.info("  - MCP HTTP: http://%s:%d/mcp/", fastapi_config.HOST, fastapi_config.PORT)

    # Console-only logging configuration for uvicorn (CloudWatch compatible)
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(asctime)s [%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    # Create and run uvicorn server
    config = uvicorn.Config(
        app,
        host=fastapi_config.HOST,
        port=fastapi_config.PORT,
        reload=fastapi_config.RELOAD,
        log_level="info",
        access_log=True,
        log_config=log_config
    )

    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_servers())
