from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.escala import EscalaReajusteRequest


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
