from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# --- CRUD SCHEMAS ---

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
    nome_procedimento: str
    quantidade: int
    tempo_real_minutos: int

    model_config = ConfigDict(from_attributes=True)

class PacienteUpdate(BaseModel):
    num_convenio: Optional[str] = Field(None, max_length=40)
    alergias: Optional[str] = None
    grupo_sanguineo: Optional[str] = Field(None, max_length=3)

class PacienteResponse(BaseModel):
    id_pessoa: int
    num_convenio: Optional[str]
    alergias: Optional[str]
    grupo_sanguineo: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ResidenteTempoMedioResponse(BaseModel):
    id_residente: int
    nome_residente: str
    tempo_medio_minutos: float

    model_config = ConfigDict(from_attributes=True)


# --- ANALYTICS SCHEMAS ---

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
