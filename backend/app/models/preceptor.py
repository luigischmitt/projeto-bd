"""`Preceptor` — papel de `Profissional` (segundo nível da herança joined)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.profissional import Profissional

if TYPE_CHECKING:
    from app.models.atendimento import Atendimento
    from app.models.escala import Escala

TITULACOES_VALIDAS = ("ESPECIALISTA", "MESTRE", "DOUTOR", "POS_DOUTOR")


class Preceptor(Profissional):
    __tablename__ = "preceptor"
    # Espelha (não cria: o CHECK já existe em db/01_schema.sql) a restrição de domínio de
    # titulacao, para que fique documentada também no lado do modelo.
    __table_args__ = (
        CheckConstraint(
            "titulacao IN ('ESPECIALISTA', 'MESTRE', 'DOUTOR', 'POS_DOUTOR')",
            name="ck_preceptor_titulacao",
        ),
    )

    id_profissional: Mapped[int] = mapped_column(
        ForeignKey("profissional.id_pessoa"), primary_key=True
    )
    titulacao: Mapped[str] = mapped_column(String(20), nullable=False)

    # selectin: telas de preceptor (agenda, supervisão) sempre precisam da lista completa
    # de atendimentos/escalas supervisionados, não de um item isolado.
    atendimentos_supervisionados: Mapped[list["Atendimento"]] = relationship(
        back_populates="preceptor",
        lazy="selectin",
        order_by="Atendimento.data_hora.desc()",
    )
    escalas_supervisionadas: Mapped[list["Escala"]] = relationship(
        back_populates="preceptor",
        lazy="selectin",
    )

    __mapper_args__ = {"polymorphic_identity": "preceptor"}

    def __repr__(self) -> str:
        return f"<Preceptor id_profissional={self.id_profissional} nome={self.nome!r}>"
