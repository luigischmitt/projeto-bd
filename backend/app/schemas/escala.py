from pydantic import BaseModel, Field

_DIAS = r"^(SEG|TER|QUA|QUI|SEX|SAB|DOM)$"
_TURNOS = r"^(MANHA|TARDE|NOITE)$"


class EscalaReajusteRequest(BaseModel):
    """Corpo de `POST /escalas/reajustar`, repassado direto para `sp_reajustar_escala`
    (db/02_procedures.sql, issue #4)."""

    id_residente: int
    dia_origem: str = Field(..., pattern=_DIAS)
    turno_origem: str = Field(..., pattern=_TURNOS)
    dia_destino: str = Field(..., pattern=_DIAS)
    turno_destino: str = Field(..., pattern=_TURNOS)
