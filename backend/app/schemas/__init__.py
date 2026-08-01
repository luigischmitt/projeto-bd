from app.schemas.analytics import (
    PacienteSemRiscoAltoResponse,
    PlantoesUnidadeResponse,
    PreceptorSupervisaoResponse,
    RankingResidentesResponse,
)
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoDoPacienteResponse,
    AtendimentoListItem,
    AtendimentoProcedimentoResponse,
    AtendimentoResponse,
)
from app.schemas.common import PessoaFields, ProfissionalFields
from app.schemas.paciente import PacienteCreate, PacienteListItem, PacienteResponse, PacienteUpdate
from app.schemas.preceptor import PreceptorCreate, PreceptorListItem, PreceptorResponse, PreceptorUpdate
from app.schemas.residente import (
    ResidenteCreate,
    ResidenteListItem,
    ResidenteResponse,
    ResidenteTempoMedioResponse,
    ResidenteUpdate,
)

__all__ = [
    "AtendimentoCreate",
    "AtendimentoDoPacienteResponse",
    "AtendimentoListItem",
    "AtendimentoProcedimentoResponse",
    "AtendimentoResponse",
    "PacienteCreate",
    "PacienteListItem",
    "PacienteResponse",
    "PacienteSemRiscoAltoResponse",
    "PacienteUpdate",
    "PessoaFields",
    "PlantoesUnidadeResponse",
    "PreceptorCreate",
    "PreceptorListItem",
    "PreceptorResponse",
    "PreceptorSupervisaoResponse",
    "PreceptorUpdate",
    "ProfissionalFields",
    "RankingResidentesResponse",
    "ResidenteCreate",
    "ResidenteListItem",
    "ResidenteResponse",
    "ResidenteTempoMedioResponse",
    "ResidenteUpdate",
]
