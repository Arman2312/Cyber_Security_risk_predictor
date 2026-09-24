"""
FastAPI Application Initialization & Lifespan Management
AuthRisk-LR System (SRS 4.1, NFR-REL-2, NFR-SEC-3)
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.config import settings
from api.routes import router
from model.predictor import RiskPredictor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("authrisk-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    REQ-INF-1 & NFR-REL-2: Deserialize model artifact once at application startup.
    Fails closed if the artifact is missing, corrupted, or invalid.
    """
    logger.info("Initializing AuthRisk-LR inference service...")
    try:
        predictor = RiskPredictor(model_path=settings.MODEL_PATH)
        app.state.predictor = predictor
        logger.info("Model artifact successfully deserialized and verified.")
    except Exception as e:
        logger.critical(f"FATAL: Model initialization failed: {e}")
        # NFR-REL-2 Fail-Closed principle
        raise SystemExit(1) from e

    yield

    logger.info("Shutting down AuthRisk-LR inference service...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AuthRisk-LR Real-Time Cyber Authentication Risk Engine",
        version="1.0.0",
        description="Low-latency microservice for gating authentication using calibrated Logistic Regression.",
        lifespan=lifespan,
    )

    # NFR-SEC-3: Do not leak stack traces or internal server paths in error responses
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Internal error processing request {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred while processing the request."},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": "Input validation error", "errors": exc.errors()},
        )

    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=settings.HOST, port=settings.PORT, workers=settings.WORKERS)
