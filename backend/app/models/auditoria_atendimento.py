from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditoriaAtendimento(Base):
    """Log de auditoria gravado por `trg_audita_atendimento` (`db/03_triggers.sql`,
    issue #5) a cada INSERT/UPDATE/DELETE em `atendimento`.

    Não há `relationship()` para `Atendimento` nem `ForeignKey` em `id_atendimento` — é
    proposital e espelha o schema: o registro de auditoria precisa sobreviver ao `DELETE`
    do atendimento que ele documenta (ver comentário em `db/01_schema.sql`, linha da
    `CREATE INDEX ix_auditoria_atendimento`). Mapeá-la como referência lógica (só um
    `Integer`) em vez de FK/relationship evita que a ORM tente (ou permita) um
    `ON DELETE CASCADE`/`RESTRICT` que o schema não tem.
    """

    __tablename__ = "auditoria_atendimento"
    __table_args__ = (
        CheckConstraint(
            "operacao IN ('INSERT', 'UPDATE', 'DELETE')", name="ck_auditoria_operacao"
        ),
    )

    id_auditoria: Mapped[int] = mapped_column(primary_key=True)
    id_atendimento: Mapped[int] = mapped_column(nullable=False)
    operacao: Mapped[str] = mapped_column(String(6), nullable=False)
    usuario: Mapped[str] = mapped_column(String(80), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    dados_antigos: Mapped[dict | None] = mapped_column(JSONB)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return (
            f"<AuditoriaAtendimento id_auditoria={self.id_auditoria} "
            f"id_atendimento={self.id_atendimento} operacao={self.operacao!r}>"
        )
