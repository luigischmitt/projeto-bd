from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escala import Escala
from app.schemas.escala import EscalaReajusteRequest


async def list_all(session: AsyncSession) -> list[dict]:
    """Unidade, residente e preceptor já vêm eager (lazy="joined" em `Escala`), então
    um único `SELECT` com JOINs basta — sem N+1 nem `selectinload` explícito."""
    stmt = select(Escala).order_by(Escala.id_escala.asc())
    result = await session.execute(stmt)
    escalas = result.unique().scalars().all()
    return [
        {
            "id_escala": e.id_escala,
            "id_unidade": e.id_unidade,
            "nome_unidade": e.unidade.nome,
            "dia_semana": e.dia_semana,
            "turno": e.turno,
            "id_residente": e.id_residente,
            "nome_residente": e.residente.nome,
            "id_preceptor": e.id_preceptor,
            "nome_preceptor": e.preceptor.nome,
        }
        for e in escalas
    ]


async def reajustar(session: AsyncSession, data: EscalaReajusteRequest) -> None:
    """Invoca `sp_reajustar_escala` (db/02_procedures.sql, issue #4). É uma PROCEDURE,
    não uma FUNCTION — chamada com `CALL`, não `SELECT`. O conflito de destino ocupado
    é sinalizado pelo banco com `RAISE EXCEPTION`, que sobe como `sqlalchemy.exc.DBAPIError`
    (a tradução para HTTP 409 é feita em `app/api/escalas.py`, não aqui)."""
    async with session.begin():
        await session.execute(
            text(
                "CALL sp_reajustar_escala("
                ":id_residente, :dia_origem, :turno_origem, :dia_destino, :turno_destino)"
            ),
            data.model_dump(),
        )
