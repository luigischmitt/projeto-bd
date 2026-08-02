from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.views import EstatisticaMensal, PacienteInternado, ResidenteSemSupervisor


async def list_pacientes_internados(session: AsyncSession) -> list[PacienteInternado]:
    stmt = select(PacienteInternado).order_by(PacienteInternado.nome_paciente.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_residentes_sem_supervisor(session: AsyncSession) -> list[ResidenteSemSupervisor]:
    stmt = select(ResidenteSemSupervisor).order_by(ResidenteSemSupervisor.id_escala.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_estatisticas_mensais(session: AsyncSession) -> list[EstatisticaMensal]:
    stmt = select(EstatisticaMensal).order_by(
        EstatisticaMensal.mes.asc(), EstatisticaMensal.id_unidade.asc()
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
