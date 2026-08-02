"""Modelos ORM read-only para as views da Etapa 2 (issues #6 e #9).

Usam uma `DeclarativeBase` própria (`ViewBase`), separada de `app.db.base.Base`, por um
motivo concreto: `backend/tests/test_orm_models.py::test_metadata_reflete_schema_real`
(issue #7) compara `Base.metadata.tables.keys()` contra o conjunto EXATO das 12 tabelas
físicas do schema (`assert tabelas_modelo == {...}`). Se as views compartilhassem
`Base.metadata`, esse teste passaria a falhar por um motivo que não tem nada a ver com o
que ele verifica (reflexão de tabela real via `inspector.get_table_names()`, que nem
sequer lista views). Uma base separada mantém os dois testes ortogonais.

Views do Postgres não têm PK física. Cada classe abaixo declara como `primary_key` a(s)
coluna(s) que já são únicas por linha na definição da view (`db/04_views.sql`) só para
satisfazer a exigência do mapeador ORM de ter uma chave identificadora — isso não cria
nenhuma constraint nova no banco, e nenhuma dessas classes é usada para INSERT/UPDATE/
DELETE (os repositories em `app/repositories/views.py` só fazem `select()`).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ViewBase(DeclarativeBase):
    pass


class PacienteInternado(ViewBase):
    """`vw_pacientes_internados`: uma linha por paciente cuja internação mais recente
    ainda está em curso. `id_internacao` é único por linha (é a PK real da tabela
    `internacao` de onde a view seleciona), então serve de chave para o mapeador."""

    __tablename__ = "vw_pacientes_internados"

    id_internacao: Mapped[int] = mapped_column(primary_key=True)
    id_paciente: Mapped[int] = mapped_column()
    nome_paciente: Mapped[str] = mapped_column(String(120))
    id_unidade: Mapped[int] = mapped_column()
    nome_unidade: Mapped[str] = mapped_column(String(80))
    data_hora_entrada: Mapped[datetime] = mapped_column()
    tempo_internado: Mapped[timedelta] = mapped_column()

    def __repr__(self) -> str:
        return f"<PacienteInternado id_internacao={self.id_internacao} id_paciente={self.id_paciente}>"


class ResidenteSemSupervisor(ViewBase):
    """`vw_residentes_sem_supervisor`: uma linha por escala ativa sem supervisão de
    preceptor doutor. `id_escala` é único por linha, mesma lógica de `PacienteInternado`."""

    __tablename__ = "vw_residentes_sem_supervisor"

    id_escala: Mapped[int] = mapped_column(primary_key=True)
    id_residente: Mapped[int] = mapped_column()
    nome_residente: Mapped[str] = mapped_column(String(120))
    id_unidade: Mapped[int] = mapped_column()
    nome_unidade: Mapped[str] = mapped_column(String(80))
    dia_semana: Mapped[str] = mapped_column(String(3))
    turno: Mapped[str] = mapped_column(String(5))
    id_preceptor: Mapped[int] = mapped_column()
    nome_preceptor: Mapped[str] = mapped_column(String(120))
    titulacao_preceptor: Mapped[str] = mapped_column(String(20))

    def __repr__(self) -> str:
        return f"<ResidenteSemSupervisor id_escala={self.id_escala} id_residente={self.id_residente}>"


class EstatisticaMensal(ViewBase):
    """`vw_estatisticas_atendimentos_mensal`: uma linha por (mês, unidade). A combinação
    `(mes, id_unidade)` é a chave natural da view (é o `GROUP BY` da definição), então
    usamos os dois como PK composta em vez de inventar uma coluna sintética."""

    __tablename__ = "vw_estatisticas_atendimentos_mensal"

    mes: Mapped[datetime] = mapped_column(primary_key=True)
    id_unidade: Mapped[int] = mapped_column(primary_key=True)
    nome_unidade: Mapped[str] = mapped_column(String(80))
    total_atendimentos: Mapped[int] = mapped_column(Integer)
    # asdecimal=False: AVG(integer) do Postgres volta como NUMERIC/Decimal por padrão no
    # driver; convertendo aqui, o valor já chega em `float` no objeto Python, sem exigir
    # cast manual no repository (mesma ideia de `residente_repo.tempo_medio`).
    duracao_media_minutos: Mapped[float] = mapped_column(Numeric(asdecimal=False))
    procedimentos_mais_frequentes: Mapped[list] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<EstatisticaMensal mes={self.mes!r} id_unidade={self.id_unidade}>"
