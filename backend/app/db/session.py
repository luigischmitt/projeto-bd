from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Engine assíncrona sobre o driver psycopg3 (`postgresql+psycopg://`), sem depender de
# asyncpg. Convive de propósito com o pool psycopg cru de `app.core.database` durante as
# issues #7/#8/#9: o pool só é removido quando o último repository em SQL cru for
# migrado (issue #8). `echo` é controlado por `SQLALCHEMY_ECHO` em `config.py`, e não por
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

    Ainda não é usada por nenhum endpoint nesta issue (#7) — os repositories em SQL cru
    continuam usando `get_db`/pool psycopg até serem migrados nas issues #8 e #9.
    """
    async with async_session_factory() as session:
        yield session
