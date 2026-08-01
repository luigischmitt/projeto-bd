from datetime import date

from pydantic import BaseModel, Field, field_validator


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
