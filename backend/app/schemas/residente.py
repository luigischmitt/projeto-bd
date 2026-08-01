from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PessoaFields, ProfissionalFields


class ResidenteCreate(PessoaFields, ProfissionalFields):
    ano_residencia: Literal["R1", "R2", "R3"]


class ResidenteUpdate(PessoaFields, ProfissionalFields):
    ano_residencia: Literal["R1", "R2", "R3"]


class ResidenteListItem(PessoaFields, ProfissionalFields):
    id_profissional: int
    ano_residencia: str

    model_config = ConfigDict(from_attributes=True)


class ResidenteResponse(ResidenteListItem):
    model_config = ConfigDict(from_attributes=True)


class ResidenteTempoMedioResponse(BaseModel):
    id_residente: int
    nome_residente: str
    tempo_medio_minutos: float

    model_config = ConfigDict(from_attributes=True)
