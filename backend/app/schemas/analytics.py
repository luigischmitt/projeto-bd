from pydantic import BaseModel, ConfigDict


class RankingResidentesResponse(BaseModel):
    residente: str
    total_atendimentos: int

    model_config = ConfigDict(from_attributes=True)


class PreceptorSupervisaoResponse(BaseModel):
    preceptor: str
    total_supervisoes: int

    model_config = ConfigDict(from_attributes=True)


class PlantoesUnidadeResponse(BaseModel):
    unidade: str
    residente: str
    plantoes: int

    model_config = ConfigDict(from_attributes=True)


class PacienteSemRiscoAltoResponse(BaseModel):
    id_pessoa: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


class TempoMedioEsperaResponse(BaseModel):
    """Resultado de `sp_calcular_tempo_medio_espera` (db/02_procedures.sql, issue #4)."""

    id_unidade: int
    nome_unidade: str
    tempo_medio_espera_minutos: float

    model_config = ConfigDict(from_attributes=True)
