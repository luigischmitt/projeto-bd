from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.unidade import Unidade


class Internacao(Base):
    """Evento de internação com vigência (`data_hora_saida IS NULL` = em curso), acréscimo
    da Etapa 2 exigido por `vw_pacientes_internados` (issue #3, ver docs/modelagem.md
    seção 4.3)."""

    __tablename__ = "internacao"
    __table_args__ = (
        CheckConstraint(
            "data_hora_saida IS NULL OR data_hora_saida > data_hora_entrada",
            name="ck_internacao_saida",
        ),
    )

    id_internacao: Mapped[int] = mapped_column(primary_key=True)
    id_paciente: Mapped[int] = mapped_column(
        ForeignKey("paciente.id_pessoa"), nullable=False
    )
    id_unidade: Mapped[int] = mapped_column(
        ForeignKey("unidade.id_unidade"), nullable=False
    )
    data_hora_entrada: Mapped[datetime] = mapped_column(nullable=False)
    data_hora_saida: Mapped[datetime | None] = mapped_column()

    # joined: mesmo raciocínio de Atendimento/Escala — lado "N para 1", uma linha só.
    paciente: Mapped["Paciente"] = relationship(
        back_populates="internacoes", lazy="joined"
    )
    unidade: Mapped["Unidade"] = relationship(
        back_populates="internacoes", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Internacao id_internacao={self.id_internacao} id_paciente={self.id_paciente}>"
