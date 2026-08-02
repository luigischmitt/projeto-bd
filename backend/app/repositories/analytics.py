"""Consultas analíticas da Etapa 1, reescritas com a DSL do SQLAlchemy (issue #9).

`tempo_medio_espera` é a única função deste módulo que não é DSL pura: ela invoca a
stored function `sp_calcular_tempo_medio_espera` (db/02_procedures.sql, issue #4) via
`session.execute(text("SELECT ..."))`, que é a forma idiomática de chamar uma rotina de
banco pela ORM — reescrevê-la em SQLAlchemy duplicaria, em Python, uma lógica que já mora
(e é testada) no banco.
"""

from calendar import monthrange
from datetime import datetime

from sqlalchemy import exists, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.atendimento import Atendimento
from app.models.escala import Escala
from app.models.paciente import Paciente
from app.models.preceptor import Preceptor
from app.models.procedimento import Procedimento
from app.models.procedimento_realizado import ProcedimentoRealizado
from app.models.residente import Residente
from app.models.unidade import Unidade


async def ranking_residentes(session: AsyncSession) -> list[dict]:
    total_col = func.count(Atendimento.id_atendimento).label("total_atendimentos")
    stmt = (
        select(Residente.nome.label("residente"), total_col)
        .join(Atendimento, Atendimento.id_residente == Residente.id_profissional)
        .group_by(Residente.id_profissional, Residente.nome)
        .order_by(total_col.desc(), Residente.nome.asc())
    )
    result = await session.execute(stmt)
    return [
        {"residente": row.residente, "total_atendimentos": row.total_atendimentos}
        for row in result
    ]


async def preceptores_supervisao(
    session: AsyncSession, data_inicio: datetime, data_fim: datetime
) -> list[dict]:
    total_col = func.count(Atendimento.id_atendimento).label("total_supervisoes")
    stmt = (
        select(Preceptor.nome.label("preceptor"), total_col)
        .join(Atendimento, Atendimento.id_preceptor == Preceptor.id_profissional)
        .where(Atendimento.data_hora >= data_inicio, Atendimento.data_hora <= data_fim)
        .group_by(Preceptor.id_profissional, Preceptor.nome)
        .having(total_col > 5)
        .order_by(total_col.desc(), Preceptor.nome.asc())
    )
    result = await session.execute(stmt)
    return [
        {"preceptor": row.preceptor, "total_supervisoes": row.total_supervisoes}
        for row in result
    ]


async def plantoes_por_unidade(session: AsyncSession) -> list[dict]:
    plantoes_col = func.count(Escala.id_escala).label("plantoes")
    stmt = (
        select(
            Unidade.nome.label("unidade"),
            Residente.nome.label("residente"),
            plantoes_col,
        )
        .select_from(Escala)
        .join(Unidade, Unidade.id_unidade == Escala.id_unidade)
        .join(Residente, Residente.id_profissional == Escala.id_residente)
        .group_by(Unidade.id_unidade, Unidade.nome, Escala.id_residente, Residente.nome)
        .order_by(Unidade.nome.asc(), plantoes_col.desc(), Residente.nome.asc())
    )
    result = await session.execute(stmt)
    return [
        {"unidade": row.unidade, "residente": row.residente, "plantoes": row.plantoes}
        for row in result
    ]


async def pacientes_sem_risco_alto(session: AsyncSession) -> list[dict]:
    tem_procedimento_alto_risco = exists(
        select(ProcedimentoRealizado.id_atendimento)
        .join(Atendimento, Atendimento.id_atendimento == ProcedimentoRealizado.id_atendimento)
        .join(Procedimento, Procedimento.id_procedimento == ProcedimentoRealizado.id_procedimento)
        .where(
            Atendimento.id_paciente == Paciente.id_pessoa,
            Procedimento.nivel_risco == "ALTO",
        )
    )
    stmt = (
        select(Paciente.id_pessoa, Paciente.nome)
        .where(~tem_procedimento_alto_risco)
        .order_by(Paciente.nome.asc())
    )
    result = await session.execute(stmt)
    return [{"id_pessoa": row.id_pessoa, "nome": row.nome} for row in result]


async def tempo_medio_espera(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT id_unidade, nome_unidade, tempo_medio_espera_minutos "
            "FROM sp_calcular_tempo_medio_espera()"
        )
    )
    return [
        {
            "id_unidade": row.id_unidade,
            "nome_unidade": row.nome_unidade,
            "tempo_medio_espera_minutos": float(row.tempo_medio_espera_minutos),
        }
        for row in result
    ]


def parse_mes(mes: str) -> tuple[datetime, datetime]:
    ano_str, mes_str = mes.split("-")
    ano, num_mes = int(ano_str), int(mes_str)
    if num_mes < 1 or num_mes > 12:
        raise ValueError
    data_inicio = datetime(ano, num_mes, 1, 0, 0, 0)
    _, ultimo_dia = monthrange(ano, num_mes)
    data_fim = datetime(ano, num_mes, ultimo_dia, 23, 59, 59, 999999)
    return data_inicio, data_fim
