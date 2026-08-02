"""`Residente` — papel de `Profissional` (segundo nível da herança joined)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.profissional import Profissional

if TYPE_CHECKING:
    from app.models.atendimento import Atendimento
    from app.models.escala import Escala

ANOS_RESIDENCIA_VALIDOS = ("R1", "R2", "R3")


class Residente(Profissional):
    __tablename__ = "residente"
    __table_args__ = (
        CheckConstraint(
            "ano_residencia IN ('R1', 'R2', 'R3')",
            name="ck_residente_ano",
        ),
    )

    id_profissional: Mapped[int] = mapped_column(
        ForeignKey("profissional.id_pessoa"), primary_key=True
    )
    ano_residencia: Mapped[str] = mapped_column(String(2), nullable=False)

    # selectin pelo mesmo motivo de Preceptor: a agenda do residente é sempre consultada
    # como lista.
    atendimentos: Mapped[list["Atendimento"]] = relationship(
        back_populates="residente",
        lazy="selectin",
        order_by="Atendimento.data_hora.desc()",
    )
    escalas: Mapped[list["Escala"]] = relationship(
        back_populates="residente",
        lazy="selectin",
    )

    __mapper_args__ = {"polymorphic_identity": "residente"}

    def __repr__(self) -> str:
        return f"<Residente id_profissional={self.id_profissional} nome={self.nome!r}>"
