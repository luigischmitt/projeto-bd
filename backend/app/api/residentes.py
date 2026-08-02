from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import handle_unique_violation
from app.db.session import get_session
from app.repositories import residente as residente_repo
from app.schemas import ResidenteCreate, ResidenteListItem, ResidenteResponse, ResidenteTempoMedioResponse, ResidenteUpdate

router = APIRouter(prefix="/residentes", tags=["Residentes"])


@router.get("/tempo-medio", response_model=List[ResidenteTempoMedioResponse], summary="Tempo médio de atendimentos por residente")
async def get_tempo_medio_residentes(session: AsyncSession = Depends(get_session)):
    return await residente_repo.tempo_medio(session)


@router.get("", response_model=List[ResidenteListItem], summary="Lista residentes cadastrados")
async def list_residentes(session: AsyncSession = Depends(get_session)):
    return await residente_repo.list_all(session)


@router.post("", response_model=ResidenteResponse, status_code=201, summary="Cadastra um novo residente")
async def create_residente(data: ResidenteCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await residente_repo.create(session, data)
    except IntegrityError as err:
        handle_unique_violation(err)


@router.put("/{id}", response_model=ResidenteResponse, summary="Atualiza dados de um residente")
async def update_residente(id: int, data: ResidenteUpdate, session: AsyncSession = Depends(get_session)):
    try:
        row = await residente_repo.update(session, id, data)
    except IntegrityError as err:
        handle_unique_violation(err)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Residente com ID {id} não encontrado.")
    return row
