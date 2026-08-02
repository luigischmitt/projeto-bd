from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.preceptor import Preceptor
    from app.models.residente import Residente
    from app.models.unidade import Unidade


class Escala(Base):
    __tablename__ = "escala"
    __table_args__ = (
        CheckConstraint(
            "dia_semana IN ('SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM')",
            name="ck_escala_dia",
        ),
        CheckConstraint("turno IN ('MANHA', 'TARDE', 'NOITE')", name="ck_escala_turno"),
        UniqueConstraint(
            "id_unidade",
            "dia_semana",
            "turno",
            "id_residente",
            name="uq_escala_unidade_dia_turno_residente",
        ),
    )

    id_escala: Mapped[int] = mapped_column(primary_key=True)
    id_unidade: Mapped[int] = mapped_column(
        ForeignKey("unidade.id_unidade"), nullable=False
    )
    dia_semana: Mapped[str] = mapped_column(String(3), nullable=False)
    turno: Mapped[str] = mapped_column(String(5), nullable=False)
    id_residente: Mapped[int] = mapped_column(
        ForeignKey("residente.id_profissional"), nullable=False
    )
    id_preceptor: Mapped[int] = mapped_column(
        ForeignKey("preceptor.id_profissional"), nullable=False
    )

    # joined: cada linha de escala resolve para exatamente uma unidade/residente/preceptor
    # — o mesmo raciocínio de Atendimento (lado "N para 1", barato via JOIN).
    unidade: Mapped["Unidade"] = relationship(back_populates="escalas", lazy="joined")
    residente: Mapped["Residente"] = relationship(back_populates="escalas", lazy="joined")
    preceptor: Mapped["Preceptor"] = relationship(
        back_populates="escalas_supervisionadas", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<Escala id_escala={self.id_escala} dia_semana={self.dia_semana!r} "
            f"turno={self.turno!r}>"
        )
