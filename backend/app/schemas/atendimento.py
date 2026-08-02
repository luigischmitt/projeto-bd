from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AtendimentoCreate(BaseModel):
    data_hora: datetime
    duracao_minutos: int = Field(..., gt=0, description="Duração do atendimento deve ser maior que 0 minutos")
    id_paciente: int
    id_residente: int
    id_preceptor: int
    id_unidade: int


class AtendimentoResponse(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    id_residente: int
    id_preceptor: int
    id_unidade: int

    model_config = ConfigDict(from_attributes=True)


class AtendimentoDoPacienteResponse(BaseModel):
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_residente: int
    id_preceptor: int
    nome_residente: str
    nome_preceptor: str
    nome_unidade: str

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
    id_unidade: int
    nome_unidade: str

    model_config = ConfigDict(from_attributes=True)


class ProcedimentoCompletoItem(BaseModel):
    """Um elemento do array `p_procedimentos` (JSONB) de `sp_registrar_atendimento_completo`
    (db/02_procedures.sql, issue #4).

    Propositalmente SEM `Field(gt=0)` em `quantidade`/`tempo_real_minutos`: essas regras
    já são impostas pelos CHECKs `ck_pr_quantidade`/`ck_pr_tempo` dentro da própria
    procedure, que é a fonte de verdade (outros clientes SQL do banco passam pelo mesmo
    CHECK). Deixar a validação de domínio para o banco — em vez de duplicá-la aqui — é o
    que permite a esta issue exercitar de ponta a ponta a tradução de `RAISE EXCEPTION`
    (violação de CHECK) em HTTP 400 (ver `app/api/atendimentos.py`)."""

    id_procedimento: int
    quantidade: int
    tempo_real_minutos: int
    data_hora_inicio: datetime | None = None
    observacao: str | None = None


class AtendimentoCompletoCreate(BaseModel):
    data_hora: datetime
    duracao_minutos: int = Field(..., gt=0, description="Duração do atendimento deve ser maior que 0 minutos")
    id_paciente: int
    id_residente: int
    id_preceptor: int
    id_unidade: int
    procedimentos: list[ProcedimentoCompletoItem] = Field(
        ..., min_length=1, description="Ao menos um procedimento realizado"
    )


class AtendimentoCompletoResponse(BaseModel):
    id_atendimento: int
