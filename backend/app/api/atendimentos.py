from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation

from app.core.database import get_db
from app.repositories import atendimento as atendimento_repo
from app.schemas import (
    AtendimentoCreate,
    AtendimentoListItem,
    AtendimentoProcedimentoResponse,
    AtendimentoResponse,
)

router = APIRouter(prefix="/atendimentos", tags=["Atendimentos"])


@router.get("", response_model=List[AtendimentoListItem], summary="Lista atendimentos cadastrados")
async def list_atendimentos(conn: Connection = Depends(get_db)):
    return await atendimento_repo.list_all(conn)


@router.post("", response_model=AtendimentoResponse, status_code=201, summary="Cria um novo atendimento")
async def create_atendimento(atendimento: AtendimentoCreate, conn: Connection = Depends(get_db)):
    try:
        return await atendimento_repo.create(conn, atendimento)
    except ForeignKeyViolation as err:
        await conn.rollback()
        constraint = err.diag.constraint_name
        if constraint == "fk_atendimento_paciente":
            raise HTTPException(status_code=400, detail=f"Paciente com id_pessoa {atendimento.id_paciente} não existe.")
        if constraint == "fk_atendimento_residente":
            raise HTTPException(status_code=400, detail=f"Residente com id_profissional {atendimento.id_residente} não existe.")
        if constraint == "fk_atendimento_preceptor":
            raise HTTPException(status_code=400, detail=f"Preceptor com id_profissional {atendimento.id_preceptor} não existe.")
        raise HTTPException(status_code=400, detail="Violação de chave estrangeira: paciente, residente ou preceptor inexistente.")


@router.get(
    "/{id}/procedimentos",
    response_model=List[AtendimentoProcedimentoResponse],
    summary="Lista procedimentos realizados em um atendimento",
)
async def get_atendimento_procedimentos(id: int, conn: Connection = Depends(get_db)):
    rows = await atendimento_repo.list_procedimentos(conn, id)
    if rows is None:
        raise HTTPException(status_code=404, detail=f"Atendimento com ID {id} não encontrado.")
    return rows


@router.delete(
    "/{id}/procedimentos/{cod}",
    status_code=204,
    summary="Remove a realização de um procedimento em um atendimento (se não faturado)",
)
async def delete_procedimento_realizado(id: int, cod: str, conn: Connection = Depends(get_db)):
    result = await atendimento_repo.delete_procedimento(conn, id, cod)
    if result == "not_found":
        raise HTTPException(status_code=404, detail=f"Procedimento {cod} não encontrado no atendimento {id}.")
    if result == "faturado":
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível remover o procedimento {cod} do atendimento {id} pois ele já foi faturado.",
        )
