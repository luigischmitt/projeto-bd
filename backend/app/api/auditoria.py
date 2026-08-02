from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import auditoria as auditoria_repo
from app.schemas import AuditoriaAtendimentoResponse

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get(
    "/atendimentos",
    response_model=List[AuditoriaAtendimentoResponse],
    summary="Histórico de auditoria de INSERT/UPDATE/DELETE em atendimento (trg_audita_atendimento)",
)
async def get_auditoria_atendimentos(
    id_atendimento: int | None = Query(
        None, description="Filtra pelo id_atendimento auditado"
    ),
    session: AsyncSession = Depends(get_session),
):
    return await auditoria_repo.list_atendimentos(session, id_atendimento)
