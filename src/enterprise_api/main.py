"""FastAPI application factory, lifespan management, and global exception handlers."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from enterprise_api.api.v1.api import api_router
from enterprise_api.core.config import settings
from enterprise_api.core.database import AsyncSessionLocal, engine
from enterprise_api.core.exceptions import AppException
from enterprise_api.core.logging import logger
from enterprise_api.core.security import hash_password
from enterprise_api.middleware.correlation import CorrelationAndTimingMiddleware
from enterprise_api.models import Base
from enterprise_api.models.enums import UserRole
from enterprise_api.models.user import User
from enterprise_api.repositories.user_repository import UserRepository


async def seed_initial_admin() -> None:
    """Ensure the initial system administrator account exists."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        existing_admin = await user_repo.get_by_email(settings.FIRST_ADMIN_EMAIL)
        if not existing_admin:
            admin_user = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name=settings.FIRST_ADMIN_FULL_NAME,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Default admin initialized: {settings.FIRST_ADMIN_EMAIL}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management for database migration and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' mode...")

    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema synchronized.")

    # Seed initial superuser
    await seed_initial_admin()

    yield

    logger.info("Shutting down database connection pool...")
    await engine.dispose()
    logger.info("Application stopped cleanly.")


def create_application() -> FastAPI:
    """Build and configure the main FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Enterprise Task & Project Orchestration REST API built with Clean Architecture, "
            "FastAPI, SQLAlchemy 2.0, and Pydantic V2."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Performance & Correlation Middleware
    app.add_middleware(CorrelationAndTimingMiddleware)

    # 3. Exception Handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        formatted_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            formatted_errors.append({"field": loc, "issue": err.get("msg")})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "Input validation failed. Please review the provided fields.",
                "details": formatted_errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(f"Unhandled server error: {exc} [request_id={request_id}]")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact system support.",
                "request_id": request_id,
            },
        )

    # 4. Include Routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
