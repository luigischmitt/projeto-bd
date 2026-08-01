from typing import List

from fastapi import APIRouter, Depends
from psycopg import Connection

from app.core.database import get_db
from app.repositories import unidade as unidade_repo
from app.schemas import UnidadeListItem

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.get("", response_model=List[UnidadeListItem], summary="Lista unidades hospitalares")
async def list_unidades(conn: Connection = Depends(get_db)):
    return await unidade_repo.list_all(conn)
