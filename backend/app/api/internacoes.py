from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import internacao as internacao_repo
from app.schemas import InternacaoAltaRequest, InternacaoCreate, InternacaoResponse

router = APIRouter(prefix="/internacoes", tags=["Internações"])


@router.post(
    "",
    response_model=InternacaoResponse,
    status_code=201,
    summary="Registra a internação de um paciente",
)
async def create_internacao(
    data: InternacaoCreate, session: AsyncSession = Depends(get_session)
):
    try:
        return await internacao_repo.create(session, data)
    except ValueError as err:
        if str(err) == "paciente_ja_internado":
            raise HTTPException(
                status_code=400,
                detail=f"Paciente {data.id_paciente} já possui internação em curso.",
            )
        raise
    except IntegrityError as err:
        if not isinstance(err.orig, ForeignKeyViolation):
            raise
        constraint = err.orig.diag.constraint_name
        if constraint == "fk_internacao_paciente":
            raise HTTPException(
                status_code=400,
                detail=f"Paciente com id_pessoa {data.id_paciente} não existe.",
            )
        if constraint == "fk_internacao_unidade":
            raise HTTPException(
                status_code=400,
                detail=f"Unidade com id_unidade {data.id_unidade} não existe.",
            )
        raise HTTPException(status_code=400, detail="Violação de chave estrangeira.")


@router.patch(
    "/{id}/alta",
    response_model=InternacaoResponse,
    summary="Encerra uma internação em curso (alta hospitalar)",
)
async def dar_alta_internacao(
    id: int, data: InternacaoAltaRequest, session: AsyncSession = Depends(get_session)
):
    try:
        row = await internacao_repo.dar_alta(session, id, data)
    except ValueError as err:
        if str(err) == "ja_com_alta":
            raise HTTPException(
                status_code=400,
                detail=f"Internação {id} já foi encerrada.",
            )
        if str(err) == "saida_anterior_entrada":
            raise HTTPException(
                status_code=400,
                detail="Data/hora de saída deve ser posterior à entrada.",
            )
        raise
    if row is None:
        raise HTTPException(status_code=404, detail=f"Internação com ID {id} não encontrada.")
    return row
