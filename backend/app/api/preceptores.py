from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.api.helpers import handle_unique_violation
from app.core.database import get_db
from app.repositories import preceptor as preceptor_repo
from app.schemas import PreceptorCreate, PreceptorListItem, PreceptorResponse, PreceptorUpdate

router = APIRouter(prefix="/preceptores", tags=["Preceptores"])


@router.get("", response_model=List[PreceptorListItem], summary="Lista preceptores cadastrados")
async def list_preceptores(conn: Connection = Depends(get_db)):
    return await preceptor_repo.list_all(conn)


@router.post("", response_model=PreceptorResponse, status_code=201, summary="Cadastra um novo preceptor")
async def create_preceptor(data: PreceptorCreate, conn: Connection = Depends(get_db)):
    try:
        return await preceptor_repo.create(conn, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)


@router.put("/{id}", response_model=PreceptorResponse, summary="Atualiza dados de um preceptor")
async def update_preceptor(id: int, data: PreceptorUpdate, conn: Connection = Depends(get_db)):
    try:
        row = await preceptor_repo.update(conn, id, data)
    except UniqueViolation as err:
        await conn.rollback()
        handle_unique_violation(err)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Preceptor com ID {id} não encontrado.")
    return row
