from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InternacaoCreate(BaseModel):
    id_paciente: int
    id_unidade: int
    data_hora_entrada: datetime | None = Field(
        default=None,
        description="Se omitido, usa o momento atual no servidor.",
    )


class InternacaoAltaRequest(BaseModel):
    data_hora_saida: datetime | None = Field(
        default=None,
        description="Se omitido, usa o momento atual no servidor.",
    )


class InternacaoResponse(BaseModel):
    id_internacao: int
    id_paciente: int
    id_unidade: int
    data_hora_entrada: datetime
    data_hora_saida: datetime | None

    model_config = ConfigDict(from_attributes=True)
