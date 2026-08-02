"""Modelos ORM (SQLAlchemy 2.0), um módulo por agregado.

A ordem de importação abaixo é significativa: cada classe filha da hierarquia de
`Pessoa` precisa que sua tabela pai já esteja registrada em `Base.metadata` quando o
`ForeignKey`/`__mapper_args__` dela é resolvido. Importar este pacote (em vez dos módulos
individuais) garante que `Base.metadata` enxergue todas as tabelas — é o que
`Base.metadata.create_all()` e os testes de reflexão de schema precisam.
"""

from app.models.pessoa import Pessoa
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.models.preceptor import Preceptor
from app.models.residente import Residente
from app.models.unidade import Unidade
from app.models.procedimento import Procedimento
from app.models.atendimento import Atendimento
from app.models.procedimento_realizado import ProcedimentoRealizado
from app.models.escala import Escala
from app.models.internacao import Internacao
from app.models.auditoria_atendimento import AuditoriaAtendimento

__all__ = [
    "Pessoa",
    "Paciente",
    "Profissional",
    "Preceptor",
    "Residente",
    "Unidade",
    "Procedimento",
    "Atendimento",
    "ProcedimentoRealizado",
    "Escala",
    "Internacao",
    "AuditoriaAtendimento",
]
