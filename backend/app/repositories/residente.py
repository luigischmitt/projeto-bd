from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.atendimento import Atendimento
from app.models.residente import Residente
from app.schemas.residente import ResidenteCreate, ResidenteUpdate


async def list_all(session: AsyncSession) -> list[Residente]:
    result = await session.execute(select(Residente).order_by(Residente.nome.asc()))
    return list(result.scalars().all())


async def fetch(session: AsyncSession, id_profissional: int) -> Residente | None:
    return await session.get(Residente, id_profissional)


async def exists(session: AsyncSession, id_profissional: int) -> bool:
    return await fetch(session, id_profissional) is not None


async def create(session: AsyncSession, data: ResidenteCreate) -> Residente:
    """Exemplo principal de transação de múltiplas etapas exigido pela issue: `Residente`
    fecha os três níveis da herança joined (`pessoa` -> `profissional` -> `residente`), então
    uma única `Residente(**dados)` adicionada à sessão faz o SQLAlchemy emitir três `INSERT`s
    em sequência dentro da MESMA transação (`session.begin()`). Se o terceiro falhar (ex.:
    CHECK de `ano_residencia`), os dois primeiros são revertidos pelo ROLLBACK automático do
    context manager — não existe estado parcial (pessoa/profissional órfãos) possível.
    """
    residente = Residente(**data.model_dump())
    async with session.begin():
        session.add(residente)
        await session.flush()
    return residente


async def update(
    session: AsyncSession, id_profissional: int, data: ResidenteUpdate
) -> Residente | None:
    async with session.begin():
        residente = await session.get(Residente, id_profissional)
        if residente is None:
            return None
        for field, value in data.model_dump().items():
            setattr(residente, field, value)
    return residente


async def tempo_medio(session: AsyncSession) -> list[dict]:
    tempo_medio_col = func.coalesce(func.avg(Atendimento.duracao_minutos), 0.0).label(
        "tempo_medio_minutos"
    )
    stmt = (
        select(
            Residente.id_profissional.label("id_residente"),
            Residente.nome.label("nome_residente"),
            tempo_medio_col,
        )
        .outerjoin(Atendimento, Atendimento.id_residente == Residente.id_profissional)
        .group_by(Residente.id_profissional, Residente.nome)
        .order_by(tempo_medio_col.desc(), Residente.nome.asc())
    )
    result = await session.execute(stmt)
    return [
        {
            "id_residente": row.id_residente,
            "nome_residente": row.nome_residente,
            "tempo_medio_minutos": float(row.tempo_medio_minutos),
        }
        for row in result
    ]
