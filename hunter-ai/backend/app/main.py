import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import dashboard, demo, offers, settings, sources, system
from app.core.config import APP_VERSION, get_settings
from app.core.logging import configure_logging

logger = logging.getLogger("hunter.http")


def create_app() -> FastAPI:
    cfg = get_settings()
    configure_logging(cfg.log_level)

    app = FastAPI(
        title="HUNTER AI API",
        version=APP_VERSION,
        description="API de veille commerciale et d'intelligence de marché (Phase 1 : socle).",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "requête",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
        response.headers["x-request-id"] = rid
        return response

    v1 = APIRouter(prefix="/api/v1")
    v1.include_router(system.router)
    v1.include_router(dashboard.router)
    v1.include_router(settings.router)
    v1.include_router(sources.router)
    v1.include_router(offers.router)
    v1.include_router(demo.router)
    app.include_router(v1)
    return app


app = create_app()
