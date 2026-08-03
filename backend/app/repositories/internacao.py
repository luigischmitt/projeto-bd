from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.internacao import Internacao
from app.schemas.internacao import InternacaoAltaRequest, InternacaoCreate


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _internacao_em_curso(session: AsyncSession, id_paciente: int) -> Internacao | None:
    stmt = (
        select(Internacao)
        .where(Internacao.id_paciente == id_paciente)
        .order_by(Internacao.data_hora_entrada.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    ultima = result.scalar_one_or_none()
    if ultima is None or ultima.data_hora_saida is not None:
        return None
    return ultima


async def create(session: AsyncSession, data: InternacaoCreate) -> Internacao:
    async with session.begin():
        if await _internacao_em_curso(session, data.id_paciente) is not None:
            raise ValueError("paciente_ja_internado")
        internacao = Internacao(
            id_paciente=data.id_paciente,
            id_unidade=data.id_unidade,
            data_hora_entrada=data.data_hora_entrada or _now(),
        )
        session.add(internacao)
        await session.flush()
    return internacao


async def dar_alta(
    session: AsyncSession, id_internacao: int, data: InternacaoAltaRequest
) -> Internacao | None:
    async with session.begin():
        internacao = await session.get(Internacao, id_internacao)
        if internacao is None:
            return None
        if internacao.data_hora_saida is not None:
            raise ValueError("ja_com_alta")
        data_hora_saida = data.data_hora_saida or _now()
        if data_hora_saida <= internacao.data_hora_entrada:
            raise ValueError("saida_anterior_entrada")
        internacao.data_hora_saida = data_hora_saida
    return internacao
