from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.api.helpers import handle_unique_violation
from app.core.database import get_db
from app.repositories import residente as residente_repo
from app.schemas import ResidenteCreate, ResidenteListItem, ResidenteResponse, ResidenteTempoMedioResponse, ResidenteUpdate

router = APIRouter(prefix="/residentes", tags=["Residentes"])


@router.get("/tempo-medio", response_model=List[ResidenteTempoMedioResponse], summary="Tempo médio de atendimentos por residente")
async def get_tempo_medio_residentes(conn: Connection = Depends(get_db)):
    return await residente_repo.tempo_medio(conn)


@router.get("", response_model=List[ResidenteListItem], summary="Lista residentes cadastrados")
async def list_residentes(conn: Connection = Depends(get_db)):
    return await residente_repo.list_all(conn)


@router.post("", response_model=ResidenteResponse, status_code=201, summary="Cadastra um novo residente")
async def create_residente(data: ResidenteCreate, conn: Connection = Depends(get_db)):
    try:
        return await residente_repo.create(conn, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)


@router.put("/{id}", response_model=ResidenteResponse, summary="Atualiza dados de um residente")
async def update_residente(id: int, data: ResidenteUpdate, conn: Connection = Depends(get_db)):
    try:
        row = await residente_repo.update(conn, id, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Residente com ID {id} não encontrado.")
    return row
