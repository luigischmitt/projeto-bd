"""`Paciente` — especialização joined de `Pessoa` (ver docstring de `app/models/pessoa.py`).

FK 1:1 com o supertipo: `paciente.id_pessoa` é ao mesmo tempo PK e FK para
`pessoa.id_pessoa`, exatamente como o schema já define.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.pessoa import Pessoa

if TYPE_CHECKING:
    from app.models.atendimento import Atendimento
    from app.models.internacao import Internacao


class Paciente(Pessoa):
    __tablename__ = "paciente"

    id_pessoa: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id_pessoa"), primary_key=True
    )
    num_convenio: Mapped[str | None] = mapped_column(String(40))
    alergias: Mapped[str | None] = mapped_column(Text)
    grupo_sanguineo: Mapped[str | None] = mapped_column(String(3))

    # selectin: listar o histórico de um paciente (atendimentos, internações) é o caso de
    # uso mais comum da tela de prontuário — carregar a coleção inteira em uma segunda
    # consulta batelada evita N+1 sem exigir join explícito toda vez.
    atendimentos: Mapped[list["Atendimento"]] = relationship(
        back_populates="paciente",
        lazy="selectin",
        order_by="Atendimento.data_hora.desc()",
    )
    internacoes: Mapped[list["Internacao"]] = relationship(
        back_populates="paciente",
        lazy="selectin",
        order_by="Internacao.data_hora_entrada.desc()",
    )

    __mapper_args__ = {"polymorphic_identity": "paciente"}

    def __repr__(self) -> str:
        return f"<Paciente id_pessoa={self.id_pessoa} nome={self.nome!r}>"
