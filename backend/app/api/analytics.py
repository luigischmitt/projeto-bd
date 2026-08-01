from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.core.database import get_db
from app.repositories import analytics as analytics_repo
from app.schemas import (
    PacienteSemRiscoAltoResponse,
    PlantoesUnidadeResponse,
    PreceptorSupervisaoResponse,
    RankingResidentesResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/ranking-residentes",
    response_model=List[RankingResidentesResponse],
    summary="Ranking dos residentes por número de atendimentos",
)
async def get_ranking_residentes(conn: Connection = Depends(get_db)):
    return await analytics_repo.ranking_residentes(conn)


@router.get(
    "/preceptores-supervisao",
    response_model=List[PreceptorSupervisaoResponse],
    summary="Preceptores com mais de 5 atendimentos supervisionados em um determinado mês",
)
async def get_preceptores_supervisao(
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Formato YYYY-MM"),
    conn: Connection = Depends(get_db),
):
    try:
        data_inicio, data_fim = analytics_repo.parse_mes(mes)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de mês inválido. Use YYYY-MM com ano e mês válidos.")
    return await analytics_repo.preceptores_supervisao(conn, data_inicio, data_fim)


@router.get(
    "/plantoes-por-unidade",
    response_model=List[PlantoesUnidadeResponse],
    summary="Quantidade de plantões escalados por residente em cada unidade (escalas vigentes)",
)
async def get_plantoes_por_unidade(conn: Connection = Depends(get_db)):
    return await analytics_repo.plantoes_por_unidade(conn)


@router.get(
    "/pacientes-sem-risco-alto",
    response_model=List[PacienteSemRiscoAltoResponse],
    summary="Pacientes que nunca realizaram nenhum procedimento classificado com nível de risco ALTO",
)
async def get_pacientes_sem_risco_alto(conn: Connection = Depends(get_db)):
    return await analytics_repo.pacientes_sem_risco_alto(conn)
