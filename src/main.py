from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import auth, health, metrics, orders, questions, titles
from src.lib.config import get_settings
from src.lib.problems import FieldError, pointer_from_loc, problem

load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


app = FastAPI(title="Spaceship", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    headers = {key: value for key, value in (exc.headers or {}).items()}
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return problem(exc.status_code, detail, request.url.path, headers=headers or None)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        FieldError(
            pointer=pointer_from_loc(err.get("loc", ())),
            detail=err.get("msg", "Invalid value"),
        )
        for err in exc.errors()
    ]
    return problem(
        422,
        "Request failed validation.",
        request.url.path,
        errors=errors,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    return problem(500, "The request could not be completed.", request.url.path)


app.include_router(health.router)
app.include_router(auth.router, prefix="/v1")
app.include_router(orders.router, prefix="/v1")
app.include_router(metrics.router, prefix="/v1")
app.include_router(questions.router, prefix="/v1")
app.include_router(titles.router, prefix="/v1")
