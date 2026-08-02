from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import analytics as analytics_repo
from app.schemas import (
    PacienteSemRiscoAltoResponse,
    PlantoesUnidadeResponse,
    PreceptorSupervisaoResponse,
    RankingResidentesResponse,
    TempoMedioEsperaResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/ranking-residentes",
    response_model=List[RankingResidentesResponse],
    summary="Ranking dos residentes por número de atendimentos",
)
async def get_ranking_residentes(session: AsyncSession = Depends(get_session)):
    return await analytics_repo.ranking_residentes(session)


@router.get(
    "/preceptores-supervisao",
    response_model=List[PreceptorSupervisaoResponse],
    summary="Preceptores com mais de 5 atendimentos supervisionados em um determinado mês",
)
async def get_preceptores_supervisao(
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Formato YYYY-MM"),
    session: AsyncSession = Depends(get_session),
):
    try:
        data_inicio, data_fim = analytics_repo.parse_mes(mes)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de mês inválido. Use YYYY-MM com ano e mês válidos.")
    return await analytics_repo.preceptores_supervisao(session, data_inicio, data_fim)


@router.get(
    "/plantoes-por-unidade",
    response_model=List[PlantoesUnidadeResponse],
    summary="Quantidade de plantões escalados por residente em cada unidade (escalas vigentes)",
)
async def get_plantoes_por_unidade(session: AsyncSession = Depends(get_session)):
    return await analytics_repo.plantoes_por_unidade(session)


@router.get(
    "/pacientes-sem-risco-alto",
    response_model=List[PacienteSemRiscoAltoResponse],
    summary="Pacientes que nunca realizaram nenhum procedimento classificado com nível de risco ALTO",
)
async def get_pacientes_sem_risco_alto(session: AsyncSession = Depends(get_session)):
    return await analytics_repo.pacientes_sem_risco_alto(session)


@router.get(
    "/tempo-medio-espera",
    response_model=List[TempoMedioEsperaResponse],
    summary="Tempo médio de espera dos pacientes por unidade (sp_calcular_tempo_medio_espera)",
)
async def get_tempo_medio_espera(session: AsyncSession = Depends(get_session)):
    return await analytics_repo.tempo_medio_espera(session)
