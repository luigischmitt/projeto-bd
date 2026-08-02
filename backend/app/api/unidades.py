from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import unidade as unidade_repo
from app.schemas import UnidadeListItem

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.get("", response_model=List[UnidadeListItem], summary="Lista unidades hospitalares")
async def list_unidades(session: AsyncSession = Depends(get_session)):
    return await unidade_repo.list_all(session)
