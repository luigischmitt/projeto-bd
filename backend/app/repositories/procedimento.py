from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.procedimento import ProcedimentoCreate

from app.models.procedimento import Procedimento


async def list_catalog(session: AsyncSession) -> list[dict]:
    stmt = select(Procedimento).order_by(Procedimento.codigo.asc())
    result = await session.execute(stmt)
    return [
        {
            "id_procedimento": p.id_procedimento,
            "codigo": p.codigo,
            "nome": p.nome,
            "tempo_medio_minutos": p.tempo_medio_minutos,
            "nivel_risco": p.nivel_risco,
            "media_tempo_procedimento": float(p.media_tempo_procedimento)
            if p.media_tempo_procedimento is not None
            else None,
        }
        for p in result.scalars().all()
    ]


async def create(session: AsyncSession, data: ProcedimentoCreate) -> dict:
    procedimento = Procedimento(**data.model_dump())
    async with session.begin():
        session.add(procedimento)
        await session.flush()
        id_procedimento = procedimento.id_procedimento
    result = await session.execute(
        select(Procedimento).where(Procedimento.id_procedimento == id_procedimento)
    )
    p = result.scalar_one()
    return {
        "id_procedimento": p.id_procedimento,
        "codigo": p.codigo,
        "nome": p.nome,
        "tempo_medio_minutos": p.tempo_medio_minutos,
        "nivel_risco": p.nivel_risco,
        "media_tempo_procedimento": None,
    }
