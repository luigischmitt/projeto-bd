from datetime import datetime

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


class PreceptorFlamenguistaResponse(BaseModel):
    """Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas
    (issue #10)."""

    preceptor: str

    model_config = ConfigDict(from_attributes=True)


class UltimoAtendimentoPacienteResponse(BaseModel):
    """Atendimento mais recente de cada paciente, com residente, preceptor e a lista de
    procedimentos realizados (issue #10)."""

    paciente: str
    data_hora: datetime
    residente: str
    preceptor: str
    procedimentos: list[str]

    model_config = ConfigDict(from_attributes=True)


class PercentualAltoRiscoResponse(BaseModel):
    """Percentual de procedimentos ALTO sobre o total realizado por cada residente
    (issue #10). Residentes sem nenhum procedimento realizado não aparecem — ver
    docstring de `percentual_alto_risco_por_residente`."""

    residente: str
    total_procedimentos: int
    total_alto_risco: int
    percentual_alto_risco: float

    model_config = ConfigDict(from_attributes=True)
