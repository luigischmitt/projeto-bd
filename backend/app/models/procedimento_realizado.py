from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.atendimento import Atendimento
    from app.models.procedimento import Procedimento


class ProcedimentoRealizado(Base):
    """Tabela associativa N:N entre `Atendimento` e `Procedimento`, com atributos
    próprios — o relacionamento "realizado" do DER (`docs/modelagem.md`, seção 2.3)."""

    __tablename__ = "procedimento_realizado"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_pr_quantidade"),
        CheckConstraint("tempo_real_minutos > 0", name="ck_pr_tempo"),
    )

    id_atendimento: Mapped[int] = mapped_column(
        ForeignKey("atendimento.id_atendimento"), primary_key=True
    )
    id_procedimento: Mapped[int] = mapped_column(
        ForeignKey("procedimento.id_procedimento"), primary_key=True
    )
    quantidade: Mapped[int] = mapped_column(nullable=False)
    tempo_real_minutos: Mapped[int] = mapped_column(nullable=False)
    # Início da execução; com atendimento.data_hora (chegada) dá o tempo de espera do
    # paciente (usado por sp_calcular_tempo_medio_espera, issue #4).
    data_hora_inicio: Mapped[datetime | None] = mapped_column()
    observacao: Mapped[str | None] = mapped_column(Text)
    faturado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # joined: acessar o atendimento/procedimento a partir de uma linha de
    # procedimento_realizado é sempre "um para um" e barato via JOIN — é o padrão de uso
    # de telas que exibem "procedimento X, realizado no atendimento Y".
    atendimento: Mapped["Atendimento"] = relationship(
        back_populates="procedimentos_realizados", lazy="joined"
    )
    procedimento: Mapped["Procedimento"] = relationship(
        back_populates="realizacoes", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<ProcedimentoRealizado id_atendimento={self.id_atendimento} "
            f"id_procedimento={self.id_procedimento}>"
        )
