from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field

from app.schemas.common import PessoaFields


class PacienteCreate(PessoaFields):
    num_convenio: Optional[str] = Field(None, max_length=40)
    alergias: Optional[str] = None
    grupo_sanguineo: Optional[str] = Field(None, max_length=3)


class PacienteUpdate(PessoaFields):
    num_convenio: Optional[str] = Field(None, max_length=40)
    alergias: Optional[str] = None
    grupo_sanguineo: Optional[str] = Field(None, max_length=3)


class PacienteListItem(PessoaFields):
    id_pessoa: int
    num_convenio: Optional[str]
    alergias: Optional[str]
    grupo_sanguineo: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PacienteResponse(PacienteListItem):
    model_config = ConfigDict(from_attributes=True)
