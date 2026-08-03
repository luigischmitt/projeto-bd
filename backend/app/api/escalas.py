from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.errors import RaiseException, UniqueViolation
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import escala as escala_repo
from app.schemas import EscalaCreateRequest, EscalaListItem, EscalaReajusteRequest

router = APIRouter(prefix="/escalas", tags=["Escalas"])


@router.get("", response_model=List[EscalaListItem], summary="Lista a grade semanal de escalas")
async def list_escalas(session: AsyncSession = Depends(get_session)):
    return await escala_repo.list_all(session)


@router.post(
    "",
    response_model=EscalaListItem,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma escala (dispara trg_check_sobreposicao_escala)",
)
async def create_escala(data: EscalaCreateRequest, session: AsyncSession = Depends(get_session)):
    try:
        return await escala_repo.create(session, data)
    except DBAPIError as err:
        if isinstance(err.orig, RaiseException):
            raise HTTPException(status_code=409, detail=err.orig.diag.message_primary)
        raise
    except IntegrityError as err:
        if isinstance(err.orig, UniqueViolation):
            raise HTTPException(
                status_code=409,
                detail="Residente já escalado nesta unidade, dia e turno (constraint UNIQUE).",
            )
        raise


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
