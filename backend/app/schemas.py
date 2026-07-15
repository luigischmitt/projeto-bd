from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- CRUD SCHEMAS ---

class PessoaFields(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    cpf: str = Field(..., min_length=11, max_length=11)
    data_nascimento: date
    is_flamengo: bool = False
    telefone: str = Field(..., min_length=1, max_length=20)

    @field_validator("cpf")
    @classmethod
    def cpf_digits_only(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch.isdigit())
        if len(cleaned) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos.")
        return cleaned


class ProfissionalFields(BaseModel):
    crm: str = Field(..., min_length=1, max_length=20)
    data_admissao: date
    especialidade: str = Field(..., min_length=1, max_length=80)


class PacienteCreate(PessoaFields):
    num_convenio: Optional[str] = Field(None, max_length=40)
    alergias: Optional[str] = None
    grupo_sanguineo: Optional[str] = Field(None, max_length=3)


class PacienteUpdate(PessoaFields):
    num_convenio: Optional[str] = Field(None, max_length=40)
    alergias: Optional[str] = None
    grupo_sanguineo: Optional[str] = Field(None, max_length=3)


class ResidenteCreate(PessoaFields, ProfissionalFields):
    ano_residencia: Literal["R1", "R2", "R3"]


class ResidenteUpdate(PessoaFields, ProfissionalFields):
    ano_residencia: Literal["R1", "R2", "R3"]


class PreceptorCreate(PessoaFields, ProfissionalFields):
    titulacao: str = Field(..., min_length=1, max_length=60)


class PreceptorUpdate(PessoaFields, ProfissionalFields):
    titulacao: str = Field(..., min_length=1, max_length=60)

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

class PacienteListItem(BaseModel):
    id_pessoa: int
    nome: str
    cpf: str
    data_nascimento: date
    is_flamengo: bool
    telefone: str
    num_convenio: Optional[str]
    alergias: Optional[str]
    grupo_sanguineo: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ResidenteListItem(BaseModel):
    id_profissional: int
    nome: str
    cpf: str
    data_nascimento: date
    is_flamengo: bool
    telefone: str
    crm: str
    data_admissao: date
    especialidade: str
    ano_residencia: str

    model_config = ConfigDict(from_attributes=True)

class PreceptorListItem(BaseModel):
    id_profissional: int
    nome: str
    cpf: str
    data_nascimento: date
    is_flamengo: bool
    telefone: str
    crm: str
    data_admissao: date
    especialidade: str
    titulacao: str

    model_config = ConfigDict(from_attributes=True)

class AtendimentoListItem(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    nome_paciente: str

    model_config = ConfigDict(from_attributes=True)

class PacienteResponse(PacienteListItem):
    model_config = ConfigDict(from_attributes=True)

class ResidenteResponse(ResidenteListItem):
    model_config = ConfigDict(from_attributes=True)

class PreceptorResponse(PreceptorListItem):
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
