from pydantic import BaseModel, ConfigDict


class UnidadeListItem(BaseModel):
    id_unidade: int
    nome: str
    tipo: str
    capacidade_leitos: int

    model_config = ConfigDict(from_attributes=True)
