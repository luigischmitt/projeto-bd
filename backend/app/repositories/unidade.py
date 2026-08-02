from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unidade import Unidade


async def list_all(session: AsyncSession) -> list[Unidade]:
    result = await session.execute(select(Unidade).order_by(Unidade.nome.asc()))
    return list(result.scalars().all())
