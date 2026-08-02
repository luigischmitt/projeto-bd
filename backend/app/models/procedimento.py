from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.procedimento_realizado import ProcedimentoRealizado


class Procedimento(Base):
    __tablename__ = "procedimento"
    __table_args__ = (
        CheckConstraint("tempo_medio_minutos > 0", name="ck_procedimento_tempo"),
        CheckConstraint(
            "nivel_risco IN ('BAIXO', 'MEDIO', 'ALTO')", name="ck_procedimento_risco"
        ),
    )

    id_procedimento: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tempo_medio_minutos: Mapped[int] = mapped_column(nullable=False)
    nivel_risco: Mapped[str] = mapped_column(String(5), nullable=False)
    # Mantida por trg_atualiza_media_procedimentos (03_triggers.sql); nula até o primeiro
    # procedimento_realizado ser inserido. Nunca é escrita pela aplicação.
    media_tempo_procedimento: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    # raise: `procedimento` é um catálogo pequeno consultado por si só na maioria das
    # telas; a lista de todas as realizações de um procedimento (potencialmente grande)
    # só deve ser carregada quando alguém pedir explicitamente.
    realizacoes: Mapped[list["ProcedimentoRealizado"]] = relationship(
        back_populates="procedimento", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Procedimento id_procedimento={self.id_procedimento} codigo={self.codigo!r}>"
