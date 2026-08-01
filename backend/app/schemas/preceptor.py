from pydantic import ConfigDict, Field

from app.schemas.common import PessoaFields, ProfissionalFields


class PreceptorCreate(PessoaFields, ProfissionalFields):
    titulacao: str = Field(..., min_length=1, max_length=60)


class PreceptorUpdate(PessoaFields, ProfissionalFields):
    titulacao: str = Field(..., min_length=1, max_length=60)


class PreceptorListItem(PessoaFields, ProfissionalFields):
    id_profissional: int
    titulacao: str

    model_config = ConfigDict(from_attributes=True)


class PreceptorResponse(PreceptorListItem):
    model_config = ConfigDict(from_attributes=True)
