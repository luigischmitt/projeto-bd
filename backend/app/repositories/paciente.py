from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCreate, PacienteUpdate


async def list_all(session: AsyncSession) -> list[Paciente]:
    """`Paciente.nome` é herdado de `Pessoa` (herança joined) — `select(Paciente)` já
    resolve o `JOIN` com `pessoa` sozinho, sem precisarmos escrever `join()` à mão."""
    result = await session.execute(select(Paciente).order_by(Paciente.nome.asc()))
    return list(result.scalars().all())


async def fetch(session: AsyncSession, id_pessoa: int) -> Paciente | None:
    return await session.get(Paciente, id_pessoa)


async def exists(session: AsyncSession, id_pessoa: int) -> bool:
    return await fetch(session, id_pessoa) is not None


async def create(session: AsyncSession, data: PacienteCreate) -> Paciente:
    """`Paciente` estende `Pessoa` via herança joined: adicionar uma única instância à
    sessão faz o SQLAlchemy emitir os dois `INSERT`s (`pessoa`, depois `paciente`) que
    compartilham a mesma PK. `session.begin()` amarra os dois em uma única transação —
    se o segundo `INSERT` falhar (ex.: violação do CHECK de `grupo_sanguineo`), o
    primeiro é revertido também."""
    paciente = Paciente(**data.model_dump())
    async with session.begin():
        session.add(paciente)
        await session.flush()  # popula id_pessoa (gerado pela sequence) antes do commit
    return paciente


async def update(
    session: AsyncSession, id_pessoa: int, data: PacienteUpdate
) -> Paciente | None:
    async with session.begin():
        paciente = await session.get(Paciente, id_pessoa)
        if paciente is None:
            return None
        for field, value in data.model_dump().items():
            setattr(paciente, field, value)
    return paciente
