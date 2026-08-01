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
