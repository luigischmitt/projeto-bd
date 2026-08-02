"""Pool psycopg cru — sobrevive à issue #8 só por causa de `app/repositories/analytics.py`.

A issue #8 pedia para deletar este módulo junto com os repositories em SQL cru, mas
`app/repositories/analytics.py`/`app/api/analytics.py` são explicitamente escopo da
issue #9 (não desta), e ainda dependem de `get_db`/`AsyncConnectionPool`. Apagar o pool
agora quebraria os quatro endpoints de `/analytics` sem que a #9 tivesse chance de
migrá-los. Optamos por manter o módulo vivo, mas reduzido ao uso exclusivo dos
analíticos (nenhum repository migrado nesta issue o importa mais) — a #9 remove este
arquivo por completo quando terminar a migração.
"""

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
