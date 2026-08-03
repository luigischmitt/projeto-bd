from pydantic import BaseModel, ConfigDict, Field

_DIAS = r"^(SEG|TER|QUA|QUI|SEX|SAB|DOM)$"
_TURNOS = r"^(MANHA|TARDE|NOITE)$"


class EscalaListItem(BaseModel):
    id_escala: int
    id_unidade: int
    nome_unidade: str
    dia_semana: str
    turno: str
    id_residente: int
    nome_residente: str
    id_preceptor: int
    nome_preceptor: str

    model_config = ConfigDict(from_attributes=True)


class EscalaReajusteRequest(BaseModel):
    """Corpo de `POST /escalas/reajustar`, repassado direto para `sp_reajustar_escala`
    (db/02_procedures.sql, issue #4)."""

    id_residente: int
    dia_origem: str = Field(..., pattern=_DIAS)
    turno_origem: str = Field(..., pattern=_TURNOS)
    dia_destino: str = Field(..., pattern=_DIAS)
    turno_destino: str = Field(..., pattern=_TURNOS)
