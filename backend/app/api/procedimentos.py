from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import handle_unique_violation
from app.db.session import get_session
from app.repositories import procedimento as procedimento_repo
from app.schemas.procedimento import ProcedimentoCatalogItem, ProcedimentoCreate

router = APIRouter(prefix="/procedimentos", tags=["Procedimentos"])


@router.get(
    "",
    response_model=List[ProcedimentoCatalogItem],
    summary="Catálogo de procedimentos com media_tempo_procedimento (trg_atualiza_media_procedimentos)",
)
async def list_procedimentos(session: AsyncSession = Depends(get_session)):
    return await procedimento_repo.list_catalog(session)


@router.post(
    "",
    response_model=ProcedimentoCatalogItem,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um procedimento no catálogo (codigo, nome, tempo e nivel_risco)",
)
async def create_procedimento(data: ProcedimentoCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await procedimento_repo.create(session, data)
    except IntegrityError as err:
        handle_unique_violation(err)
