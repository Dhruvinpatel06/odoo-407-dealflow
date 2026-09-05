from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import DealFlowException

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DealFlowException)
async def dealflow_exception_handler(request: Request, exc: DealFlowException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "details": exc.details},
    )


@app.get("/health")
def health_check():
    """Liveness probe endpoint."""
    return {"status": "ok"}
