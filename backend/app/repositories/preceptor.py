from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preceptor import Preceptor
from app.schemas.preceptor import PreceptorCreate, PreceptorUpdate


async def list_all(session: AsyncSession) -> list[Preceptor]:
    result = await session.execute(select(Preceptor).order_by(Preceptor.nome.asc()))
    return list(result.scalars().all())


async def fetch(session: AsyncSession, id_profissional: int) -> Preceptor | None:
    return await session.get(Preceptor, id_profissional)


async def exists(session: AsyncSession, id_profissional: int) -> bool:
    return await fetch(session, id_profissional) is not None


async def create(session: AsyncSession, data: PreceptorCreate) -> Preceptor:
    """Mesmo caso de `residente_repo.create`: `Preceptor` também fecha os três níveis da
    herança joined (`pessoa` -> `profissional` -> `preceptor`), e `session.begin()` garante
    que os três `INSERT`s (um por tabela) sejam atômicos."""
    preceptor = Preceptor(**data.model_dump())
    async with session.begin():
        session.add(preceptor)
        await session.flush()
    return preceptor


async def update(
    session: AsyncSession, id_profissional: int, data: PreceptorUpdate
) -> Preceptor | None:
    async with session.begin():
        preceptor = await session.get(Preceptor, id_profissional)
        if preceptor is None:
            return None
        for field, value in data.model_dump().items():
            setattr(preceptor, field, value)
    return preceptor
