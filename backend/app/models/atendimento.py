from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.preceptor import Preceptor
    from app.models.procedimento_realizado import ProcedimentoRealizado
    from app.models.residente import Residente
    from app.models.unidade import Unidade


class Atendimento(Base):
    __tablename__ = "atendimento"
    __table_args__ = (
        CheckConstraint("duracao_minutos > 0", name="ck_atendimento_duracao"),
    )

    id_atendimento: Mapped[int] = mapped_column(primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(nullable=False)
    duracao_minutos: Mapped[int] = mapped_column(nullable=False)
    # As FKs abaixo apontam para os SUBTIPOS (paciente/residente/preceptor), não para
    # pessoa/profissional — a integridade referencial já garante que quem recebe é um
    # paciente e quem executa/supervisiona é, respectivamente, residente e preceptor
    # (ver docs/modelagem.md, seção 4.1).
    id_paciente: Mapped[int] = mapped_column(
        ForeignKey("paciente.id_pessoa"), nullable=False
    )
    id_residente: Mapped[int] = mapped_column(
        ForeignKey("residente.id_profissional"), nullable=False
    )
    id_preceptor: Mapped[int] = mapped_column(
        ForeignKey("preceptor.id_profissional"), nullable=False
    )
    id_unidade: Mapped[int] = mapped_column(
        ForeignKey("unidade.id_unidade"), nullable=False
    )

    # joined: lado "N para 1" da relação — trazer paciente/residente/preceptor/unidade
    # junto na mesma consulta (um JOIN) é mais barato que uma consulta extra por
    # atendimento, já que cada um resolve para exatamente uma linha.
    paciente: Mapped["Paciente"] = relationship(
        back_populates="atendimentos", lazy="joined"
    )
    residente: Mapped["Residente"] = relationship(
        back_populates="atendimentos", lazy="joined"
    )
    preceptor: Mapped["Preceptor"] = relationship(
        back_populates="atendimentos_supervisionados", lazy="joined"
    )
    unidade: Mapped["Unidade"] = relationship(
        back_populates="atendimentos", lazy="joined"
    )
    # selectin: é exatamente o caso citado no design da Etapa 2 — listar os procedimentos
    # de um atendimento com uma segunda consulta em lote, evitando N+1 quando vários
    # atendimentos são listados de uma vez.
    procedimentos_realizados: Mapped[list["ProcedimentoRealizado"]] = relationship(
        back_populates="atendimento", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Atendimento id_atendimento={self.id_atendimento} data_hora={self.data_hora!r}>"
