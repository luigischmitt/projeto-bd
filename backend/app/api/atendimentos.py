from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation, RaiseException
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import atendimento as atendimento_repo
from app.schemas import (
    AtendimentoCompletoCreate,
    AtendimentoCompletoResponse,
    AtendimentoCreate,
    AtendimentoListItem,
    AtendimentoProcedimentoResponse,
    AtendimentoResponse,
)

router = APIRouter(prefix="/atendimentos", tags=["Atendimentos"])


@router.get("", response_model=List[AtendimentoListItem], summary="Lista atendimentos cadastrados")
async def list_atendimentos(session: AsyncSession = Depends(get_session)):
    return await atendimento_repo.list_all(session)


@router.post("", response_model=AtendimentoResponse, status_code=201, summary="Cria um novo atendimento")
async def create_atendimento(atendimento: AtendimentoCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await atendimento_repo.create(session, atendimento)
    except IntegrityError as err:
        if not isinstance(err.orig, ForeignKeyViolation):
            raise
        constraint = err.orig.diag.constraint_name
        if constraint == "fk_atendimento_paciente":
            raise HTTPException(status_code=400, detail=f"Paciente com id_pessoa {atendimento.id_paciente} não existe.")
        if constraint == "fk_atendimento_residente":
            raise HTTPException(status_code=400, detail=f"Residente com id_profissional {atendimento.id_residente} não existe.")
        if constraint == "fk_atendimento_preceptor":
            raise HTTPException(status_code=400, detail=f"Preceptor com id_profissional {atendimento.id_preceptor} não existe.")
        if constraint == "fk_atendimento_unidade":
            raise HTTPException(status_code=400, detail=f"Unidade com id_unidade {atendimento.id_unidade} não existe.")
        raise HTTPException(status_code=400, detail="Violação de chave estrangeira: paciente, residente, preceptor ou unidade inexistente.")


@router.post(
    "/completo",
    response_model=AtendimentoCompletoResponse,
    status_code=201,
    summary="Registra um atendimento e seus procedimentos realizados em uma única transação",
)
async def post_atendimento_completo(
    data: AtendimentoCompletoCreate, session: AsyncSession = Depends(get_session)
):
    """Chama `sp_registrar_atendimento_completo`. FK/CHECK inválidos no banco viram
    `DBAPIError(orig=RaiseException)`; traduzimos para 400 com a mensagem legível que a
    própria procedure já formata (ver `db/02_procedures.sql`), em vez de deixar subir
    como 500."""
    try:
        id_atendimento = await atendimento_repo.registrar_completo(session, data)
    except DBAPIError as err:
        if not isinstance(err.orig, RaiseException):
            raise
        raise HTTPException(status_code=400, detail=err.orig.diag.message_primary)
    return {"id_atendimento": id_atendimento}


@router.get(
    "/{id}/procedimentos",
    response_model=List[AtendimentoProcedimentoResponse],
    summary="Lista procedimentos realizados em um atendimento",
)
async def get_atendimento_procedimentos(id: int, session: AsyncSession = Depends(get_session)):
    rows = await atendimento_repo.list_procedimentos(session, id)
    if rows is None:
        raise HTTPException(status_code=404, detail=f"Atendimento com ID {id} não encontrado.")
    return rows


@router.delete(
    "/{id}/procedimentos/{cod}",
    status_code=204,
    summary="Remove a realização de um procedimento em um atendimento (se não faturado)",
)
async def delete_procedimento_realizado(id: int, cod: str, session: AsyncSession = Depends(get_session)):
    result = await atendimento_repo.delete_procedimento(session, id, cod)
    if result == "not_found":
        raise HTTPException(status_code=404, detail=f"Procedimento {cod} não encontrado no atendimento {id}.")
    if result == "faturado":
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível remover o procedimento {cod} do atendimento {id} pois ele já foi faturado.",
        )
