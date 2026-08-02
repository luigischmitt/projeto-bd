from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Engine assíncrona sobre o driver psycopg3 (`postgresql+psycopg://`), sem depender de
# asyncpg. Ainda convive com o pool psycopg cru de `app.core.database` (issue #9 remove
# o pool por completo): a issue #8 migrou pacientes/residentes/preceptores/atendimentos/
# unidades para esta engine, mas `app/repositories/analytics.py` é escopo da #9 e segue
# no pool cru até lá. `echo` é controlado por `SQLALCHEMY_ECHO` em `config.py`, e não por
# um valor fixo aqui, para que o log de SQL possa ser ligado sem alterar código (útil
# para evidenciar o N+1 do lazy loading no vídeo da entrega).
engine: AsyncEngine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI que entrega uma `AsyncSession` por request.

    Usada por todos os endpoints migrados na issue #8 (pacientes, residentes,
    preceptores, atendimentos, unidades). Os endpoints de `/analytics` continuam com
    `get_db`/pool psycopg até a issue #9.
    """
    async with async_session_factory() as session:
        yield session
