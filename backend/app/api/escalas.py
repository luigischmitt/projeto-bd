from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import RaiseException
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import escala as escala_repo
from app.schemas import EscalaReajusteRequest

router = APIRouter(prefix="/escalas", tags=["Escalas"])


@router.post(
    "/reajustar",
    status_code=204,
    summary="Move as escalas de um residente do dia/turno de origem para o de destino",
)
async def post_reajustar_escala(
    data: EscalaReajusteRequest, session: AsyncSession = Depends(get_session)
):
    """Chama `sp_reajustar_escala` (PROCEDURE, invocada com `CALL`). Conflito de destino
    já ocupado vira `DBAPIError(orig=RaiseException)`; traduzimos para HTTP 409, já que é
    um conflito de estado (não um dado malformado, que seria 400)."""
    try:
        await escala_repo.reajustar(session, data)
    except DBAPIError as err:
        if not isinstance(err.orig, RaiseException):
            raise
        raise HTTPException(status_code=409, detail=err.orig.diag.message_primary)
