from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Engine assíncrona sobre o driver psycopg3 (`postgresql+psycopg://`), sem depender de
# asyncpg. A issue #9 migrou os últimos endpoints (analíticos) que ainda usavam o pool
# psycopg cru e removeu esse módulo por completo: esta é, desde então, a ÚNICA forma de
# acesso ao banco na aplicação. `echo` é controlado por `SQLALCHEMY_ECHO` em
# `config.py`, e não por um valor fixo aqui, para que o log de SQL possa ser ligado sem
# alterar código (útil para evidenciar o N+1 do lazy loading no vídeo da entrega).
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

    Usada por todos os endpoints da aplicação (issues #8 e #9 migraram o que faltava:
    pacientes, residentes, preceptores, atendimentos, unidades e, por fim, analíticos,
    procedures e views).
    """
    async with async_session_factory() as session:
        yield session
