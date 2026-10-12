from fastapi import FastAPI

from src.transcriber.utils.logging import setup_logging
from src.transcriber.api.routes import router
from src.transcriber.config.settings import settings

setup_logging()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }