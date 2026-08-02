from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict


class PacienteInternadoResponse(BaseModel):
    """`vw_pacientes_internados` (db/04_views.sql, issue #6)."""

    id_internacao: int
    id_paciente: int
    nome_paciente: str
    id_unidade: int
    nome_unidade: str
    data_hora_entrada: datetime
    tempo_internado: timedelta

    model_config = ConfigDict(from_attributes=True)


class ResidenteSemSupervisorResponse(BaseModel):
    """`vw_residentes_sem_supervisor` (db/04_views.sql, issue #6)."""

    id_escala: int
    id_residente: int
    nome_residente: str
    id_unidade: int
    nome_unidade: str
    dia_semana: str
    turno: str
    id_preceptor: int
    nome_preceptor: str
    titulacao_preceptor: str

    model_config = ConfigDict(from_attributes=True)


class ProcedimentoFrequenteItem(BaseModel):
    procedimento: str
    quantidade: int


class EstatisticaMensalResponse(BaseModel):
    """`vw_estatisticas_atendimentos_mensal` (db/04_views.sql, issue #6)."""

    mes: datetime
    id_unidade: int
    nome_unidade: str
    total_atendimentos: int
    duracao_media_minutos: float
    procedimentos_mais_frequentes: list[ProcedimentoFrequenteItem]

    model_config = ConfigDict(from_attributes=True)
