import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.internal import router as internal_router
from app.api.users import router as users_router
from app.core.config import settings
from app.events.consumer import start_consuming, stop_consuming
from app.events.publisher import connect_rabbitmq, disconnect_rabbitmq

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_rabbitmq()
    await start_consuming()
    yield
    await stop_consuming()
    await disconnect_rabbitmq()


app = FastAPI(
    title="TransFans Auth Service",
    description="Authentication and user management microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(internal_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
