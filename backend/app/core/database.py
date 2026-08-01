from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from app.config import settings

_pool: AsyncConnectionPool | None = None


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized.")
    return _pool


@asynccontextmanager
async def lifespan_db(app: FastAPI):
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=2,
        max_size=10,
        open=False,
    )
    await _pool.open()
    try:
        yield
    finally:
        await _pool.close()


async def get_db():
    async with get_pool().connection() as conn:
        yield conn
