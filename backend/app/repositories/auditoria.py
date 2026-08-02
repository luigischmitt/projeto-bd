from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auditoria_atendimento import AuditoriaAtendimento


async def list_atendimentos(
    session: AsyncSession, id_atendimento: int | None = None
) -> list[AuditoriaAtendimento]:
    stmt = select(AuditoriaAtendimento).order_by(AuditoriaAtendimento.data_hora.desc())
    if id_atendimento is not None:
        stmt = stmt.where(AuditoriaAtendimento.id_atendimento == id_atendimento)
    result = await session.execute(stmt)
    return list(result.scalars().all())
