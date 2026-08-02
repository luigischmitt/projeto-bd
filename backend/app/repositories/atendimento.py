import json

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, lazyload, selectinload

from app.models.atendimento import Atendimento
from app.models.procedimento import Procedimento
from app.models.procedimento_realizado import ProcedimentoRealizado
from app.repositories import paciente as paciente_repo
from app.schemas.atendimento import AtendimentoCompletoCreate, AtendimentoCreate


async def list_all(session: AsyncSession) -> list[dict]:
    """Eager loading explícito (DSL): `joinedload` para `paciente`/`unidade` traz tudo em
    uma única consulta com `JOIN`. É redundante com o `lazy="joined"` já configurado em
    `app/models/atendimento.py`, mas deixamos explícito aqui para documentar a estratégia
    no ponto de uso, em contraste direto com `list_by_paciente` abaixo (lazy de
    propósito)."""
    stmt = (
        select(Atendimento)
        .options(joinedload(Atendimento.paciente), joinedload(Atendimento.unidade))
        .order_by(Atendimento.data_hora.desc())
    )
    result = await session.execute(stmt)
    atendimentos = result.unique().scalars().all()
    return [
        {
            "id_atendimento": a.id_atendimento,
            "data_hora": a.data_hora,
            "duracao_minutos": a.duracao_minutos,
            "id_paciente": a.id_paciente,
            "nome_paciente": a.paciente.nome,
            "id_unidade": a.id_unidade,
            "nome_unidade": a.unidade.nome,
        }
        for a in atendimentos
    ]


async def create(session: AsyncSession, data: AtendimentoCreate) -> Atendimento:
    atendimento = Atendimento(**data.model_dump())
    async with session.begin():
        session.add(atendimento)
        await session.flush()
    return atendimento


async def registrar_completo(session: AsyncSession, data: AtendimentoCompletoCreate) -> int:
    """Invoca `sp_registrar_atendimento_completo` (db/02_procedures.sql, issue #4), uma
    FUNCTION chamada com `SELECT`. Falha de FK (referência inexistente) ou de CHECK
    (ex.: `quantidade` <= 0) no meio do laço de procedimentos faz o banco desfazer TUDO,
    incluindo o `INSERT` do atendimento — a procedure já garante essa atomicidade via
    savepoint implícito (ver comentário em `db/02_procedures.sql`); aqui só propagamos o
    `RAISE EXCEPTION` como `sqlalchemy.exc.DBAPIError` para `app/api/atendimentos.py`
    traduzir em HTTP 400."""
    procedimentos_json = json.dumps(
        [item.model_dump(mode="json") for item in data.procedimentos]
    )
    async with session.begin():
        result = await session.execute(
            text(
                "SELECT sp_registrar_atendimento_completo("
                ":data_hora, :duracao_minutos, :id_paciente, :id_residente, "
                ":id_preceptor, :id_unidade, CAST(:procedimentos AS JSONB))"
            ),
            {
                "data_hora": data.data_hora,
                "duracao_minutos": data.duracao_minutos,
                "id_paciente": data.id_paciente,
                "id_residente": data.id_residente,
                "id_preceptor": data.id_preceptor,
                "id_unidade": data.id_unidade,
                "procedimentos": procedimentos_json,
            },
        )
        return result.scalar_one()


async def list_by_paciente(session: AsyncSession, id_paciente: int) -> list[dict] | None:
    """Endpoint mantido **lazy de propósito** (contrariando o `lazy="joined"` padrão do
    modelo) para servir de material do vídeo da entrega: `lazyload()` abaixo desliga o
    eager loading de `residente`/`preceptor`/`unidade` para ESTA consulta específica, então
    o `await a.awaitable_attrs.residente` (etc.) dentro do loop dispara uma consulta extra
    POR atendimento — o N+1 clássico, visível no log de SQL com `SQLALCHEMY_ECHO=1`.
    Comparar com `list_all`/`list_procedimentos`, que carregam eager de propósito."""
    if not await paciente_repo.exists(session, id_paciente):
        return None

    stmt = (
        select(Atendimento)
        .where(Atendimento.id_paciente == id_paciente)
        .options(
            lazyload(Atendimento.residente),
            lazyload(Atendimento.preceptor),
            lazyload(Atendimento.unidade),
        )
        .order_by(Atendimento.data_hora.asc())
    )
    result = await session.execute(stmt)
    atendimentos = result.scalars().all()

    rows = []
    for a in atendimentos:
        # Cada await abaixo é uma consulta lazy separada (N+1 intencional; ver docstring).
        residente = await a.awaitable_attrs.residente
        preceptor = await a.awaitable_attrs.preceptor
        unidade = await a.awaitable_attrs.unidade
        rows.append(
            {
                "id_atendimento": a.id_atendimento,
                "data_hora": a.data_hora,
                "duracao_minutos": a.duracao_minutos,
                "id_residente": a.id_residente,
                "id_preceptor": a.id_preceptor,
                "nome_residente": residente.nome,
                "nome_preceptor": preceptor.nome,
                "nome_unidade": unidade.nome,
            }
        )
    return rows


async def list_procedimentos(session: AsyncSession, id_atendimento: int) -> list[dict] | None:
    """`selectinload` explícito para `procedimentos_realizados`: uma segunda consulta em
    lote (`WHERE id_atendimento IN (...)`) traz todas as realizações de uma vez, em vez de
    uma consulta por procedimento — é o caso pedido pela issue como demonstração de eager
    loading via `selectinload`. `ProcedimentoRealizado.procedimento` já é `lazy="joined"`
    no modelo, então o `nome`/`codigo` do procedimento vem junto na mesma consulta
    selectin, sem N+1 adicional."""
    stmt = (
        select(Atendimento)
        .where(Atendimento.id_atendimento == id_atendimento)
        .options(selectinload(Atendimento.procedimentos_realizados))
    )
    result = await session.execute(stmt)
    atendimento = result.scalar_one_or_none()
    if atendimento is None:
        return None

    realizados = sorted(
        atendimento.procedimentos_realizados, key=lambda pr: pr.procedimento.nome
    )
    return [
        {
            "codigo": pr.procedimento.codigo,
            "nome_procedimento": pr.procedimento.nome,
            "quantidade": pr.quantidade,
            "tempo_real_minutos": pr.tempo_real_minutos,
            "faturado": pr.faturado,
        }
        for pr in realizados
    ]


async def delete_procedimento(
    session: AsyncSession, id_atendimento: int, cod: str
) -> str | None:
    """Returns None on success, 'not_found', or 'faturado'."""
    async with session.begin():
        stmt = (
            select(ProcedimentoRealizado)
            .join(
                Procedimento,
                Procedimento.id_procedimento == ProcedimentoRealizado.id_procedimento,
            )
            .where(
                ProcedimentoRealizado.id_atendimento == id_atendimento,
                Procedimento.codigo == cod,
            )
        )
        result = await session.execute(stmt)
        procedimento_realizado = result.scalar_one_or_none()
        if procedimento_realizado is None:
            return "not_found"
        if procedimento_realizado.faturado:
            return "faturado"
        await session.delete(procedimento_realizado)
    return None
