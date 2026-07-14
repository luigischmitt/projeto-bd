from datetime import datetime, date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from psycopg.rows import dict_row
from typing import List

from app.db import get_db
from app.schemas import (
    RankingResidentesResponse,
    PreceptorSupervisaoResponse,
    PlantoesUnidadeResponse,
    PacienteSemRiscoAltoResponse
)

router = APIRouter(prefix="/analytics")

# 1. GET /analytics/ranking-residentes - ranking dos residentes por total de atendimentos
@router.get(
    "/ranking-residentes",
    response_model=List[RankingResidentesResponse],
    summary="Ranking dos residentes por número de atendimentos"
)
async def get_ranking_residentes(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.nome AS residente, COUNT(a.id_atendimento) AS total_atendimentos
            FROM residente r
            JOIN pessoa p ON p.id_pessoa = r.id_profissional
            JOIN atendimento a ON a.id_residente = r.id_profissional
            GROUP BY r.id_profissional, p.nome
            ORDER BY total_atendimentos DESC, p.nome ASC;
            """
        )
        rows = await cur.fetchall()
        return rows

# 2. GET /analytics/preceptores-supervisao?mes=YYYY-MM - preceptores com > 5 atendimentos supervisionados no mês
@router.get(
    "/preceptores-supervisao",
    response_model=List[PreceptorSupervisaoResponse],
    summary="Preceptores com mais de 5 atendimentos supervisionados em um determinado mês"
)
async def get_preceptores_supervisao(
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Formato YYYY-MM"),
    conn: Connection = Depends(get_db)
):
    try:
        ano_str, mes_str = mes.split("-")
        ano = int(ano_str)
        num_mes = int(mes_str)
        if num_mes < 1 or num_mes > 12:
            raise ValueError
        
        # Limites do mês
        data_inicio = datetime(ano, num_mes, 1, 0, 0, 0)
        # Calcula último dia do mês
        _, ultimo_dia = monthrange(ano, num_mes)
        data_fim = datetime(ano, num_mes, ultimo_dia, 23, 59, 59, 999999)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de mês inválido. Use YYYY-MM com ano e mês válidos."
        )

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.nome AS preceptor, COUNT(a.id_atendimento) AS total_supervisoes
            FROM preceptor pr
            JOIN pessoa p ON p.id_pessoa = pr.id_profissional
            JOIN atendimento a ON a.id_preceptor = pr.id_profissional
            WHERE a.data_hora >= %s AND a.data_hora <= %s
            GROUP BY pr.id_profissional, p.nome
            HAVING COUNT(a.id_atendimento) > 5
            ORDER BY total_supervisoes DESC, p.nome ASC;
            """,
            (data_inicio, data_fim)
        )
        rows = await cur.fetchall()
        return rows

# 3. GET /analytics/plantoes-por-unidade - quantidade de plantões escalados por residente
@router.get(
    "/plantoes-por-unidade",
    response_model=List[PlantoesUnidadeResponse],
    summary="Quantidade de plantões escalados por residente em cada unidade (escalas vigentes)"
)
async def get_plantoes_por_unidade(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT u.nome AS unidade,
                   p.nome AS residente,
                   COUNT(e.id_escala) AS plantoes
            FROM escala e
            JOIN unidade u ON u.id_unidade = e.id_unidade
            JOIN pessoa p ON p.id_pessoa = e.id_residente
            GROUP BY u.id_unidade, u.nome, e.id_residente, p.nome
            ORDER BY u.nome ASC, plantoes DESC, p.nome ASC;
            """
        )
        rows = await cur.fetchall()
        return rows

# 4. GET /analytics/pacientes-sem-risco-alto - pacientes que nunca realizaram procedimento de nivel_risco ALTO
@router.get(
    "/pacientes-sem-risco-alto",
    response_model=List[PacienteSemRiscoAltoResponse],
    summary="Pacientes que nunca realizaram nenhum procedimento classificado com nível de risco ALTO"
)
async def get_pacientes_sem_risco_alto(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.id_pessoa, p.nome
            FROM paciente pac
            JOIN pessoa p ON p.id_pessoa = pac.id_pessoa
            WHERE NOT EXISTS (
                SELECT 1
                FROM atendimento a
                JOIN procedimento_realizado pr ON pr.id_atendimento = a.id_atendimento
                JOIN procedimento proc ON proc.id_procedimento = pr.id_procedimento
                WHERE a.id_paciente = pac.id_pessoa
                  AND proc.nivel_risco = 'ALTO'
            )
            ORDER BY p.nome ASC;
            """
        )
        rows = await cur.fetchall()
        return rows
