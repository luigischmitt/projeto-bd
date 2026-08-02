from app.schemas.analytics import (
    PacienteSemRiscoAltoResponse,
    PercentualAltoRiscoResponse,
    PlantoesUnidadeResponse,
    PreceptorFlamenguistaResponse,
    PreceptorSupervisaoResponse,
    RankingResidentesResponse,
    TempoMedioEsperaResponse,
    UltimoAtendimentoPacienteResponse,
)
from app.schemas.atendimento import (
    AtendimentoCompletoCreate,
    AtendimentoCompletoResponse,
    AtendimentoCreate,
    AtendimentoDoPacienteResponse,
    AtendimentoListItem,
    AtendimentoProcedimentoResponse,
    AtendimentoResponse,
    ProcedimentoCompletoItem,
)
from app.schemas.auditoria import AuditoriaAtendimentoResponse
from app.schemas.common import PessoaFields, ProfissionalFields
from app.schemas.escala import EscalaReajusteRequest
from app.schemas.paciente import PacienteCreate, PacienteListItem, PacienteResponse, PacienteUpdate
from app.schemas.preceptor import PreceptorCreate, PreceptorListItem, PreceptorResponse, PreceptorUpdate
from app.schemas.residente import (
    ResidenteCreate,
    ResidenteListItem,
    ResidenteResponse,
    ResidenteTempoMedioResponse,
    ResidenteUpdate,
)
from app.schemas.unidade import UnidadeListItem
from app.schemas.views import (
    EstatisticaMensalResponse,
    PacienteInternadoResponse,
    ProcedimentoFrequenteItem,
    ResidenteSemSupervisorResponse,
)

__all__ = [
    "AtendimentoCompletoCreate",
    "AtendimentoCompletoResponse",
    "AtendimentoCreate",
    "AtendimentoDoPacienteResponse",
    "AtendimentoListItem",
    "AtendimentoProcedimentoResponse",
    "AtendimentoResponse",
    "AuditoriaAtendimentoResponse",
    "EscalaReajusteRequest",
    "EstatisticaMensalResponse",
    "PacienteCreate",
    "PacienteInternadoResponse",
    "PacienteListItem",
    "PacienteResponse",
    "PacienteSemRiscoAltoResponse",
    "PacienteUpdate",
    "PercentualAltoRiscoResponse",
    "PessoaFields",
    "PlantoesUnidadeResponse",
    "PreceptorCreate",
    "PreceptorFlamenguistaResponse",
    "PreceptorListItem",
    "PreceptorResponse",
    "PreceptorSupervisaoResponse",
    "PreceptorUpdate",
    "ProcedimentoCompletoItem",
    "ProcedimentoFrequenteItem",
    "ProfissionalFields",
    "RankingResidentesResponse",
    "ResidenteCreate",
    "ResidenteListItem",
    "ResidenteResponse",
    "ResidenteSemSupervisorResponse",
    "ResidenteTempoMedioResponse",
    "ResidenteUpdate",
    "TempoMedioEsperaResponse",
    "UltimoAtendimentoPacienteResponse",
    "UnidadeListItem",
]
