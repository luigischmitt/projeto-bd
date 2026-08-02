from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditoriaAtendimentoResponse(BaseModel):
    """Linha de `auditoria_atendimento`, gravada por `trg_audita_atendimento`
    (db/03_triggers.sql, issue #5) a cada INSERT/UPDATE/DELETE em `atendimento`."""

    id_auditoria: int
    id_atendimento: int
    operacao: str
    usuario: str
    data_hora: datetime
    dados_antigos: dict | None
    dados_novos: dict | None

    model_config = ConfigDict(from_attributes=True)
