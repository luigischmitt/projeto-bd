import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Pool global inicializado no lifespan do FastAPI
_pool: AsyncConnectionPool | None = None

def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized.")
    return _pool

from fastapi import FastAPI

@asynccontextmanager
async def lifespan_db(app: FastAPI):
    global _pool
    # Inicializa o pool assíncrono do psycopg
    _pool = AsyncConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=2,
        max_size=10,
        open=False  # Não inicia imediatamente no construtor
    )
    await _pool.open()
    try:
        yield
    finally:
        await _pool.close()

async def get_db():
    """
    Dependência FastAPI que yielda uma conexão assíncrona do pool.
    Retorna a conexão ao pool automaticamente no final do escopo.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn
