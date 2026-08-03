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
from app.schemas.escala import EscalaCreateRequest, EscalaListItem, EscalaReajusteRequest
from app.schemas.internacao import InternacaoAltaRequest, InternacaoCreate, InternacaoResponse
from app.schemas.paciente import PacienteCreate, PacienteListItem, PacienteResponse, PacienteUpdate
from app.schemas.preceptor import PreceptorCreate, PreceptorListItem, PreceptorResponse, PreceptorUpdate
from app.schemas.procedimento import ProcedimentoCatalogItem, ProcedimentoCreate
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
    "EscalaCreateRequest",
    "EscalaListItem",
    "EscalaReajusteRequest",
    "EstatisticaMensalResponse",
    "InternacaoAltaRequest",
    "InternacaoCreate",
    "InternacaoResponse",
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
    "ProcedimentoCatalogItem",
    "ProcedimentoCreate",
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
