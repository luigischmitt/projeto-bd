from fastapi import HTTPException
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError


def handle_unique_violation(err: IntegrityError) -> None:
    """Recebe o `IntegrityError` que o SQLAlchemy usa para envelopar qualquer erro do
    driver (`err.orig` é o `psycopg.errors...` original). Só traduz violação de
    unicidade para 400 com mensagem amigável; qualquer outro `IntegrityError` (CHECK,
    FK, etc.) é relançado para não mascarar um bug com uma mensagem errada."""
    if not isinstance(err.orig, UniqueViolation):
        raise err
    constraint = err.orig.diag.constraint_name
    if constraint == "uq_pessoa_cpf":
        raise HTTPException(status_code=400, detail="CPF já cadastrado para outra pessoa.")
    if constraint == "uq_profissional_crm":
        raise HTTPException(status_code=400, detail="CRM já cadastrado para outro profissional.")
    if constraint == "uq_procedimento_codigo":
        raise HTTPException(status_code=400, detail="Código de procedimento já cadastrado.")
    raise HTTPException(status_code=400, detail="Registro duplicado violando uma restrição de unicidade.")
