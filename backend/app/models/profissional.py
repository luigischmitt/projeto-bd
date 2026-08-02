"""`Profissional` — segunda especialização de `Pessoa` e, ao mesmo tempo, supertipo de
`Preceptor`/`Residente` (herança joined em dois níveis; ver `app/models/pessoa.py` para a
explicação completa do discriminador computado).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.pessoa import Pessoa


class Profissional(Pessoa):
    __tablename__ = "profissional"

    id_pessoa: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id_pessoa"), primary_key=True
    )
    crm: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    data_admissao: Mapped[date] = mapped_column(nullable=False)
    especialidade: Mapped[str] = mapped_column(String(80), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "profissional"}

    def __repr__(self) -> str:
        return f"<Profissional id_pessoa={self.id_pessoa} nome={self.nome!r}>"
