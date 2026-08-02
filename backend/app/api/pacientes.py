from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import handle_unique_violation
from app.db.session import get_session
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
async def list_pacientes(session: AsyncSession = Depends(get_session)):
    return await paciente_repo.list_all(session)


@router.post("", response_model=PacienteResponse, status_code=201, summary="Cadastra um novo paciente")
async def create_paciente(data: PacienteCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await paciente_repo.create(session, data)
    except IntegrityError as err:
        handle_unique_violation(err)


@router.put("/{id}", response_model=PacienteResponse, summary="Atualiza dados de um paciente")
async def update_paciente(id: int, data: PacienteUpdate, session: AsyncSession = Depends(get_session)):
    try:
        row = await paciente_repo.update(session, id, data)
    except IntegrityError as err:
        handle_unique_violation(err)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Paciente com ID {id} não encontrado.")
    return row


@router.get(
    "/{id}/atendimentos",
    response_model=List[AtendimentoDoPacienteResponse],
    summary="Lista atendimentos de um paciente ordenados por data e hora",
)
async def get_paciente_atendimentos(id: int, session: AsyncSession = Depends(get_session)):
    rows = await atendimento_repo.list_by_paciente(session, id)
    if rows is None:
        raise HTTPException(status_code=404, detail=f"Paciente com ID {id} não encontrado.")
    return rows
