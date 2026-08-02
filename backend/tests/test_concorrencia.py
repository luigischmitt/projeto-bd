"""Teste da issue #11 (Req 6): duas transações async concorrentes disputando a mesma
vaga de escala (mesma unidade, dia, turno e residente) devem resultar em exatamente um
vencedor — o lock pessimista sobre a linha do residente (ver docstring de
`app/scripts/demo_concorrencia.py` para a explicação de por que a âncora precisa ser uma
linha que já existe) serializa a segunda transação até a primeira commitar, e a
revalidação pós-lock rejeita quem chegou depois.

Wrapper síncrono em torno de corrotinas (em vez de `pytest.mark.asyncio`), no mesmo
padrão de `test_orm_models.py`: o projeto não depende de `pytest-asyncio`.
"""

from __future__ import annotations

import asyncio

import psycopg
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_factory
from app.models.escala import Escala
from app.scripts.demo_concorrencia import executar_demonstracao


def _is_db_accessible() -> bool:
    try:
        with psycopg.connect(settings.DATABASE_URL):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _is_db_accessible(),
    reason="O banco de dados PostgreSQL local não está acessível no DATABASE_URL configurado.",
)

# Combinação livre no seed (db/05_seed.sql): residente 14 (Iris) não tem escala aos
# domingos em nenhuma unidade. Diferente da combinação usada por padrão no script de
# demonstração (residente 15, QUI/TARDE) para não colidir se os dois rodarem em paralelo.
_ID_UNIDADE = 2
_DIA_SEMANA = "DOM"
_TURNO = "MANHA"
_ID_RESIDENTE = 14
_ID_PRECEPTOR = 6


async def _limpar_escala_de_teste(session: AsyncSession) -> None:
    await session.execute(
        delete(Escala).where(
            Escala.id_unidade == _ID_UNIDADE,
            Escala.dia_semana == _DIA_SEMANA,
            Escala.turno == _TURNO,
            Escala.id_residente == _ID_RESIDENTE,
        )
    )
    await session.commit()


@pytest.fixture(autouse=True)
def _estado_limpo():
    async def limpar():
        async with async_session_factory() as session:
            await _limpar_escala_de_teste(session)

    asyncio.run(limpar())
    yield
    asyncio.run(limpar())


async def _rodar_disputa() -> tuple[bool, bool]:
    return await executar_demonstracao(
        id_unidade=_ID_UNIDADE,
        dia_semana=_DIA_SEMANA,
        turno=_TURNO,
        id_residente=_ID_RESIDENTE,
        id_preceptor=_ID_PRECEPTOR,
        # O próprio teste limpa via fixture; não depender da limpeza do script aqui
        # deixa a asserção sobre o estado do banco (abaixo) independente dessa mecânica.
        limpar_ao_final=False,
    )


def test_exatamente_uma_transacao_vence_a_disputa_pela_mesma_vaga():
    sucesso_a, sucesso_b = asyncio.run(_rodar_disputa())

    assert sucesso_a != sucesso_b, (
        "exatamente uma das duas transações concorrentes deveria ter sucesso, "
        f"mas sucesso_a={sucesso_a} e sucesso_b={sucesso_b}"
    )
    assert sucesso_a or sucesso_b


def test_apenas_uma_linha_de_escala_e_persistida_apos_a_disputa():
    asyncio.run(_rodar_disputa())

    with psycopg.connect(settings.DATABASE_URL) as conn:
        cur = conn.execute(
            "SELECT count(*) FROM escala WHERE id_unidade = %s AND dia_semana = %s "
            "AND turno = %s AND id_residente = %s",
            (_ID_UNIDADE, _DIA_SEMANA, _TURNO, _ID_RESIDENTE),
        )
        (total,) = cur.fetchone()

    assert total == 1
