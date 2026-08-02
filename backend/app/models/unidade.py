from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.atendimento import Atendimento
    from app.models.escala import Escala
    from app.models.internacao import Internacao


class Unidade(Base):
    __tablename__ = "unidade"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ENFERMARIA', 'UTI', 'PRONTO_SOCORRO', 'AMBULATORIO')",
            name="ck_unidade_tipo",
        ),
        CheckConstraint("capacidade_leitos >= 0", name="ck_unidade_capacidade"),
    )

    id_unidade: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    capacidade_leitos: Mapped[int] = mapped_column(nullable=False)

    # raise: coleções potencialmente grandes (todo o histórico de atendimentos/internações
    # de uma unidade). Forçamos quem precisar delas a pedir explicitamente com
    # `selectinload(Unidade.atendimentos)` em vez de deixar a ORM disparar por acidente.
    atendimentos: Mapped[list["Atendimento"]] = relationship(
        back_populates="unidade", lazy="raise"
    )
    internacoes: Mapped[list["Internacao"]] = relationship(
        back_populates="unidade", lazy="raise"
    )
    # selectin: a grade de escalas de uma unidade é pequena (poucas dezenas de linhas) e é
    # exatamente o que a tela de escalas por unidade precisa exibir de cara.
    escalas: Mapped[list["Escala"]] = relationship(
        back_populates="unidade", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Unidade id_unidade={self.id_unidade} nome={self.nome!r}>"
