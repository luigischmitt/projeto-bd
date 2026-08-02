"""Consultas analíticas da Etapa 1, reescritas com a DSL do SQLAlchemy (issue #9).

`tempo_medio_espera` é a única função deste módulo que não é DSL pura: ela invoca a
stored function `sp_calcular_tempo_medio_espera` (db/02_procedures.sql, issue #4) via
`session.execute(text("SELECT ..."))`, que é a forma idiomática de chamar uma rotina de
banco pela ORM — reescrevê-la em SQLAlchemy duplicaria, em Python, uma lógica que já mora
(e é testada) no banco.
"""

from calendar import monthrange
from datetime import datetime

from sqlalchemy import case, exists, func, select, text
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


async def preceptores_flamenguistas(session: AsyncSession) -> list[dict]:
    """Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas
    (issue #10, consulta 1).

    O enunciado descreve dois passos, não um único filtro: (1) os residentes que
    atenderam ao menos um paciente `is_flamengo = TRUE`, em qualquer atendimento; (2) os
    preceptores que supervisionaram esses residentes, em qualquer atendimento — não
    necessariamente no mesmo atendimento do paciente flamenguista. Um único JOIN
    atendimento-paciente-preceptor responderia uma pergunta mais restrita ("preceptor
    supervisionou pessoalmente o atendimento a um flamenguista"), que no seed devolve só
    Ana Preceptora e Bruno Preceptor; a subquery com `id_residente.in_(...)` abaixo segue
    a leitura literal do enunciado e traz também Diego Preceptor e Elena Preceptora, que
    supervisionaram Felipe/Gabriela/Hugo/Iris em *outros* atendimentos.
    """
    residentes_de_flamenguistas = (
        select(Atendimento.id_residente)
        .join(Paciente, Paciente.id_pessoa == Atendimento.id_paciente)
        .where(Paciente.is_flamengo.is_(True))
        .distinct()
    )
    stmt = (
        select(Preceptor.nome.label("preceptor"))
        .join(Atendimento, Atendimento.id_preceptor == Preceptor.id_profissional)
        .where(Atendimento.id_residente.in_(residentes_de_flamenguistas))
        .distinct()
        .order_by(Preceptor.nome.asc())
    )
    result = await session.execute(stmt)
    return [{"preceptor": row.preceptor} for row in result]


async def ultimo_atendimento_por_paciente(session: AsyncSession) -> list[dict]:
    """Para cada paciente, o atendimento mais recente com residente, preceptor e a lista
    de procedimentos realizados (issue #10, consulta 2).

    Usa `row_number()` particionado por paciente e ordenado por `data_hora` decrescente
    (função de janela da DSL) para identificar, em uma única consulta, o id do atendimento
    mais recente de cada paciente — a alternativa seria uma subquery correlacionada com
    `MAX(data_hora)` por paciente, também disponível na DSL, mas a janela evita repetir o
    agrupamento. A partir desses ids, a segunda consulta carrega as entidades `Atendimento`
    já com paciente/residente/preceptor (relationships `lazy="joined"`) e a lista de
    procedimentos (`lazy="selectin"`), reaproveitando o mapeamento ORM em vez de montar o
    JOIN à mão outra vez.
    """
    rn_col = (
        func.row_number()
        .over(partition_by=Atendimento.id_paciente, order_by=Atendimento.data_hora.desc())
        .label("rn")
    )
    ultimos = select(Atendimento.id_atendimento, rn_col).subquery()
    ids_ultimos = select(ultimos.c.id_atendimento).where(ultimos.c.rn == 1)

    stmt = (
        select(Atendimento)
        .join(Atendimento.paciente)
        .where(Atendimento.id_atendimento.in_(ids_ultimos))
        .order_by(Paciente.nome.asc())
    )
    result = await session.execute(stmt)
    atendimentos = result.scalars().unique().all()
    return [
        {
            "paciente": atendimento.paciente.nome,
            "data_hora": atendimento.data_hora,
            "residente": atendimento.residente.nome,
            "preceptor": atendimento.preceptor.nome,
            "procedimentos": sorted(
                realizado.procedimento.nome
                for realizado in atendimento.procedimentos_realizados
            ),
        }
        for atendimento in atendimentos
    ]


async def percentual_alto_risco_por_residente(session: AsyncSession) -> list[dict]:
    """Percentual de procedimentos com `nivel_risco = 'ALTO'` sobre o total realizado por
    cada residente (issue #10, consulta 3).

    Decisão de design — divisão por zero: um residente sem nenhum procedimento realizado
    (no seed, Jonas Residente id=15, cujo único atendimento não tem linha em
    `procedimento_realizado`) fica DE FORA do resultado, em vez de aparecer com 0%. Os
    quatro JOINs abaixo são todos INNER: um residente só entra no agrupamento se existir ao
    menos uma linha de `procedimento_realizado` associada a um dos seus atendimentos, então
    o denominador (`total_procedimentos`) nunca é zero nas linhas retornadas — a divisão por
    zero é evitada por construção da consulta, não por um `CASE`/`NULLIF` no cálculo do
    percentual. A alternativa (incluir com 0%, via LEFT JOIN) atribuiria a esse residente
    uma taxa "sem risco" que ele não chegou a demonstrar, por falta de qualquer
    procedimento — optamos por omitir em vez de sugerir um dado que não existe.
    """
    total_col = func.count(ProcedimentoRealizado.id_procedimento).label(
        "total_procedimentos"
    )
    alto_col = func.sum(case((Procedimento.nivel_risco == "ALTO", 1), else_=0)).label(
        "total_alto_risco"
    )
    percentual_col = (alto_col * 100.0 / total_col).label("percentual_alto_risco")
    stmt = (
        select(
            Residente.nome.label("residente"),
            total_col,
            alto_col,
            percentual_col,
        )
        .select_from(Residente)
        .join(Atendimento, Atendimento.id_residente == Residente.id_profissional)
        .join(
            ProcedimentoRealizado,
            ProcedimentoRealizado.id_atendimento == Atendimento.id_atendimento,
        )
        .join(
            Procedimento,
            Procedimento.id_procedimento == ProcedimentoRealizado.id_procedimento,
        )
        .group_by(Residente.id_profissional, Residente.nome)
        .order_by(percentual_col.desc(), Residente.nome.asc())
    )
    result = await session.execute(stmt)
    return [
        {
            "residente": row.residente,
            "total_procedimentos": row.total_procedimentos,
            "total_alto_risco": row.total_alto_risco,
            "percentual_alto_risco": float(row.percentual_alto_risco),
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
