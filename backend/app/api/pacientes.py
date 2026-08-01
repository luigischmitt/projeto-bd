from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.api.helpers import handle_unique_violation
from app.core.database import get_db
from app.repositories import atendimento as atendimento_repo
from app.repositories import paciente as paciente_repo
from app.schemas import (
    AtendimentoDoPacienteResponse,
    PacienteCreate,
    PacienteListItem,
    PacienteResponse,
    PacienteUpdate,
)

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.get("", response_model=List[PacienteListItem], summary="Lista pacientes cadastrados")
async def list_pacientes(conn: Connection = Depends(get_db)):
    return await paciente_repo.list_all(conn)


@router.post("", response_model=PacienteResponse, status_code=201, summary="Cadastra um novo paciente")
async def create_paciente(data: PacienteCreate, conn: Connection = Depends(get_db)):
    try:
        return await paciente_repo.create(conn, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)


@router.put("/{id}", response_model=PacienteResponse, summary="Atualiza dados de um paciente")
async def update_paciente(id: int, data: PacienteUpdate, conn: Connection = Depends(get_db)):
    try:
        row = await paciente_repo.update(conn, id, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Paciente com ID {id} não encontrado.")
    return row


@router.get(
    "/{id}/atendimentos",
    response_model=List[AtendimentoDoPacienteResponse],
    summary="Lista atendimentos de um paciente ordenados por data e hora",
)
async def get_paciente_atendimentos(id: int, conn: Connection = Depends(get_db)):
    rows = await atendimento_repo.list_by_paciente(conn, id)
    if rows is None:
        raise HTTPException(status_code=404, detail=f"Paciente com ID {id} não encontrado.")
    return rows
