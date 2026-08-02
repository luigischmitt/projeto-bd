"""Testes da infraestrutura ORM (issue #7).

Dois testes são exigidos pelo checklist da issue e são o cerne deste módulo:

1. `test_metadata_reflete_schema_real` — reflete o schema real do banco (via
   `sqlalchemy.inspect`) e compara, tabela a tabela e coluna a coluna, contra
   `Base.metadata` (os modelos declarados em `app/models/`). Não basta instanciar as
   classes: se um nome de coluna ou um tipo divergir do `db/01_schema.sql` real, este
   teste falha.
2. `test_heranca_joined_carrega_subtipo_correto` — carrega um `Residente` contra o banco
   de verdade e navega até os campos herdados de `Profissional` e `Pessoa`, provando que
   a herança joined (com o discriminador `CASE`/`EXISTS` de `app/models/pessoa.py`,
   sem coluna física) funciona ponta a ponta, não só em memória.
"""

from __future__ import annotations

import asyncio

import pytest
import psycopg
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.db.base import Base
from app.db.session import engine as async_engine
import app.models as models
from app.models.residente import Residente


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

# Tipos SQL cujo `python_type` diverge entre a coluna reflete (dialeto Postgres) e a
# declarada no modelo, mas que representam o mesmo domínio. Comparados por nome de classe
# em vez de por `python_type` (JSONB, por exemplo, não implementa `python_type`).
_TIPOS_SEM_PYTHON_TYPE = {"JSONB", "JSON"}


def _categoria_tipo(sa_type) -> str:
    """Agrupa tipos SQLAlchemy/Postgres equivalentes em uma categoria comparável,
    já que o tipo refletido do dialeto (ex.: `postgresql.VARCHAR`) não é a mesma classe
    Python do tipo declarado no modelo (ex.: `sqlalchemy.String`), mesmo representando a
    mesma coluna física."""
    name = type(sa_type).__name__.upper()
    if name in _TIPOS_SEM_PYTHON_TYPE:
        return "JSON"
    if "CHAR" in name or "TEXT" in name or "ENUM" in name:
        return "STRING"
    if "BOOL" in name:
        return "BOOLEAN"
    if "NUMERIC" in name or "DECIMAL" in name:
        return "NUMERIC"
    if "TIMESTAMP" in name or "DATETIME" in name:
        return "DATETIME"
    if name == "DATE":
        return "DATE"
    if "INT" in name:
        return "INTEGER"
    return name


def test_metadata_reflete_schema_real():
    """Compara `Base.metadata` (modelos declarados) contra o schema real do banco,
    obtido por reflexão (`sqlalchemy.inspect`). Cobre todas as 12 tabelas mapeadas."""
    sync_engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    try:
        inspector = inspect(sync_engine)
        tabelas_reais = set(inspector.get_table_names())

        tabelas_modelo = set(Base.metadata.tables.keys())
        assert tabelas_modelo == {
            "pessoa",
            "paciente",
            "profissional",
            "preceptor",
            "residente",
            "unidade",
            "procedimento",
            "atendimento",
            "procedimento_realizado",
            "escala",
            "internacao",
            "auditoria_atendimento",
        }
        faltando_no_banco = tabelas_modelo - tabelas_reais
        assert not faltando_no_banco, (
            f"Tabelas mapeadas nos modelos mas ausentes no banco real: {faltando_no_banco}"
        )

        for nome_tabela, tabela_modelo in Base.metadata.tables.items():
            colunas_reais = {
                col["name"]: col for col in inspector.get_columns(nome_tabela)
            }
            colunas_modelo = {col.name: col for col in tabela_modelo.columns}

            nomes_faltando = set(colunas_modelo) - set(colunas_reais)
            assert not nomes_faltando, (
                f"{nome_tabela}: colunas declaradas no modelo e ausentes no banco: "
                f"{nomes_faltando}"
            )
            nomes_a_mais = set(colunas_reais) - set(colunas_modelo)
            assert not nomes_a_mais, (
                f"{nome_tabela}: colunas reais que o modelo não mapeia: {nomes_a_mais}"
            )

            for nome_coluna, coluna_modelo in colunas_modelo.items():
                coluna_real = colunas_reais[nome_coluna]
                categoria_modelo = _categoria_tipo(coluna_modelo.type)
                categoria_real = _categoria_tipo(coluna_real["type"])
                assert categoria_modelo == categoria_real, (
                    f"{nome_tabela}.{nome_coluna}: tipo do modelo "
                    f"({coluna_modelo.type!r} -> {categoria_modelo}) não bate com o tipo "
                    f"real do banco ({coluna_real['type']!r} -> {categoria_real})"
                )
                # nullable é comparável diretamente: reflete exatamente a constraint NOT
                # NULL do schema.
                assert coluna_modelo.nullable == coluna_real["nullable"], (
                    f"{nome_tabela}.{nome_coluna}: nullable do modelo "
                    f"({coluna_modelo.nullable}) diverge do banco real "
                    f"({coluna_real['nullable']})"
                )
    finally:
        sync_engine.dispose()


def test_metadata_reflete_chaves_primarias():
    """Reforça a reflexão anterior conferindo especificamente as PKs — em especial as
    compostas (`procedimento_realizado`) e as PKs que também são FK do supertipo
    (herança joined: `paciente.id_pessoa`, `preceptor.id_profissional`, etc.)."""
    sync_engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    try:
        inspector = inspect(sync_engine)
        for nome_tabela, tabela_modelo in Base.metadata.tables.items():
            pk_modelo = {col.name for col in tabela_modelo.primary_key.columns}
            pk_real = set(inspector.get_pk_constraint(nome_tabela)["constrained_columns"])
            assert pk_modelo == pk_real, (
                f"{nome_tabela}: PK do modelo {pk_modelo} != PK real {pk_real}"
            )
    finally:
        sync_engine.dispose()


async def _carrega_residente_e_navega_heranca() -> Residente:
    async with AsyncSession(async_engine) as session:
        residente = await session.get(Residente, 11)

        assert residente is not None
        assert isinstance(residente, Residente)
        assert isinstance(residente, models.Profissional)
        assert isinstance(residente, models.Pessoa)

        # Atributos próprios de Residente.
        assert residente.ano_residencia == "R1"

        # Atributos herdados de Profissional (tabela `profissional`, joined).
        assert residente.crm == "CRM-PB-2001"
        assert residente.especialidade == "Clinica Medica"
        assert residente.data_admissao.isoformat() == "2023-02-01"

        # Atributos herdados de Pessoa (tabela `pessoa`, base da hierarquia).
        assert residente.nome == "Felipe Residente"
        assert residente.cpf == "12121212121"
        assert residente.is_flamengo is True
        assert residente.telefone == "83990000011"
        return residente


def test_heranca_joined_carrega_subtipo_correto():
    """Carrega Felipe Residente (id_pessoa=11, seed fixo) via `Session.get(Residente)` e
    navega pelos três níveis da hierarquia (Residente -> Profissional -> Pessoa), provando
    que a herança joined resolve o subtipo certo mesmo sem coluna discriminadora física.

    Wrapper síncrono em torno de uma corrotina (em vez de `pytest.mark.asyncio`) porque o
    projeto ainda não depende de `pytest-asyncio`; evita adicionar uma dependência nova só
    para este teste.
    """
    asyncio.run(_carrega_residente_e_navega_heranca())


async def _discrimina_pessoa_sem_papel_conhecido() -> dict[int, models.Pessoa]:
    async with AsyncSession(async_engine) as session:
        result = await session.execute(
            select(models.Pessoa).where(models.Pessoa.id_pessoa.in_([1, 6, 11]))
        )
        return {p.id_pessoa: p for p in result.scalars()}


def test_heranca_joined_discrimina_pessoa_sem_papel():
    """Complementa o teste anterior: uma consulta genérica a `Pessoa` também precisa
    resolver corretamente pacientes e preceptores (não só residentes), provando que o
    discriminador computado cobre os dois níveis da hierarquia (`pessoa` ->
    `paciente`/`profissional` -> `preceptor`/`residente`) em uma única consulta."""
    por_id = asyncio.run(_discrimina_pessoa_sem_papel_conhecido())

    assert isinstance(por_id[1], models.Paciente)
    assert isinstance(por_id[6], models.Preceptor)
    assert isinstance(por_id[11], Residente)
