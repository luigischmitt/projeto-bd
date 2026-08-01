from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AtendimentoCreate(BaseModel):
    data_hora: datetime
    duracao_minutos: int = Field(..., gt=0, description="Duração do atendimento deve ser maior que 0 minutos")
    id_paciente: int
    id_residente: int
    id_preceptor: int


class AtendimentoResponse(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    id_residente: int
    id_preceptor: int

    model_config = ConfigDict(from_attributes=True)


class AtendimentoDoPacienteResponse(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_residente: int
    id_preceptor: int
    nome_residente: str
    nome_preceptor: str

    model_config = ConfigDict(from_attributes=True)


class AtendimentoProcedimentoResponse(BaseModel):
    codigo: str
    nome_procedimento: str
    quantidade: int
    tempo_real_minutos: int
    faturado: bool

    model_config = ConfigDict(from_attributes=True)


class AtendimentoListItem(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    nome_paciente: str

    model_config = ConfigDict(from_attributes=True)
