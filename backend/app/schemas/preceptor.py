from typing import Literal

from pydantic import ConfigDict

from app.schemas.common import PessoaFields, ProfissionalFields

# Espelha o CHECK ck_preceptor_titulacao: erro de domínio vira 422 em vez de 500.
Titulacao = Literal["ESPECIALISTA", "MESTRE", "DOUTOR", "POS_DOUTOR"]


class PreceptorCreate(PessoaFields, ProfissionalFields):
    titulacao: Titulacao


class PreceptorUpdate(PessoaFields, ProfissionalFields):
    titulacao: Titulacao


class PreceptorListItem(PessoaFields, ProfissionalFields):
    id_profissional: int
    titulacao: Titulacao

    model_config = ConfigDict(from_attributes=True)


class PreceptorResponse(PreceptorListItem):
    model_config = ConfigDict(from_attributes=True)
