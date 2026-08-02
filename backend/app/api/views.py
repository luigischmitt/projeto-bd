from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import views as views_repo
from app.schemas import (
    EstatisticaMensalResponse,
    PacienteInternadoResponse,
    ResidenteSemSupervisorResponse,
)

router = APIRouter(prefix="/views", tags=["Views"])


@router.get(
    "/pacientes-internados",
    response_model=List[PacienteInternadoResponse],
    summary="Pacientes cuja internação mais recente ainda está em curso (vw_pacientes_internados)",
)
async def get_pacientes_internados(session: AsyncSession = Depends(get_session)):
    return await views_repo.list_pacientes_internados(session)


@router.get(
    "/residentes-sem-supervisor",
    response_model=List[ResidenteSemSupervisorResponse],
    summary="Escalas de residentes sem supervisão de preceptor doutor (vw_residentes_sem_supervisor)",
)
async def get_residentes_sem_supervisor(session: AsyncSession = Depends(get_session)):
    return await views_repo.list_residentes_sem_supervisor(session)


@router.get(
    "/estatisticas-mensais",
    response_model=List[EstatisticaMensalResponse],
    summary="Estatísticas mensais de atendimentos por unidade (vw_estatisticas_atendimentos_mensal)",
)
async def get_estatisticas_mensais(session: AsyncSession = Depends(get_session)):
    return await views_repo.list_estatisticas_mensais(session)
