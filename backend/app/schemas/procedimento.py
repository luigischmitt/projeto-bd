from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProcedimentoCatalogItem(BaseModel):
    id_procedimento: int
    codigo: str
    nome: str
    tempo_medio_minutos: int
    nivel_risco: str
    media_tempo_procedimento: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class ProcedimentoCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nome: str = Field(min_length=1, max_length=120)
    tempo_medio_minutos: int = Field(gt=0)
    nivel_risco: Literal["BAIXO", "MEDIO", "ALTO"]
