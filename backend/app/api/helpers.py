from fastapi import HTTPException
from psycopg.errors import UniqueViolation


def handle_unique_violation(err: UniqueViolation) -> None:
    constraint = err.diag.constraint_name
    if constraint == "uq_pessoa_cpf":
        raise HTTPException(status_code=400, detail="CPF já cadastrado para outra pessoa.")
    if constraint == "uq_profissional_crm":
        raise HTTPException(status_code=400, detail="CRM já cadastrado para outro profissional.")
    raise HTTPException(status_code=400, detail="Registro duplicado violando uma restrição de unicidade.")
