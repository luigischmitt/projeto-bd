from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row
from typing import List

from app.db import get_db
from app.schemas import (
    AtendimentoCreate,
    AtendimentoResponse,
    AtendimentoDoPacienteResponse,
    AtendimentoProcedimentoResponse,
    AtendimentoListItem,
    PacienteListItem,
    PacienteCreate,
    PacienteUpdate,
    PacienteResponse,
    PreceptorCreate,
    PreceptorListItem,
    PreceptorResponse,
    PreceptorUpdate,
    ResidenteCreate,
    ResidenteListItem,
    ResidenteResponse,
    ResidenteUpdate,
    ResidenteTempoMedioResponse
)

router = APIRouter()


def _handle_unique_violation(err: UniqueViolation) -> None:
    constraint = err.diag.constraint_name
    if constraint == "uq_pessoa_cpf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado para outra pessoa."
        )
    if constraint == "uq_profissional_crm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CRM já cadastrado para outro profissional."
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Registro duplicado violando uma restrição de unicidade."
    )


async def _fetch_paciente(cur, id_pessoa: int) -> dict:
    await cur.execute(
        """
        SELECT pa.id_pessoa, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
               pa.num_convenio, pa.alergias, pa.grupo_sanguineo
        FROM paciente pa
        JOIN pessoa p ON p.id_pessoa = pa.id_pessoa
        WHERE pa.id_pessoa = %s
        """,
        (id_pessoa,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paciente com ID {id_pessoa} não encontrado.")
    return row


async def _fetch_residente(cur, id_profissional: int) -> dict:
    await cur.execute(
        """
        SELECT r.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
               pr.crm, pr.data_admissao, pr.especialidade, r.ano_residencia
        FROM residente r
        JOIN profissional pr ON pr.id_pessoa = r.id_profissional
        JOIN pessoa p ON p.id_pessoa = r.id_profissional
        WHERE r.id_profissional = %s
        """,
        (id_profissional,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Residente com ID {id_profissional} não encontrado.")
    return row


async def _fetch_preceptor(cur, id_profissional: int) -> dict:
    await cur.execute(
        """
        SELECT pr.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
               pf.crm, pf.data_admissao, pf.especialidade, pr.titulacao
        FROM preceptor pr
        JOIN profissional pf ON pf.id_pessoa = pr.id_profissional
        JOIN pessoa p ON p.id_pessoa = pr.id_profissional
        WHERE pr.id_profissional = %s
        """,
        (id_profissional,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Preceptor com ID {id_profissional} não encontrado.")
    return row

# --- Listagens para a interface ---

@router.get(
    "/pacientes",
    response_model=List[PacienteListItem],
    summary="Lista pacientes cadastrados"
)
async def list_pacientes(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT pa.id_pessoa, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
                   pa.num_convenio, pa.alergias, pa.grupo_sanguineo
            FROM paciente pa
            JOIN pessoa p ON p.id_pessoa = pa.id_pessoa
            ORDER BY p.nome ASC
            """
        )
        return await cur.fetchall()


@router.get(
    "/residentes",
    response_model=List[ResidenteListItem],
    summary="Lista residentes cadastrados"
)
async def list_residentes(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT r.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
                   pf.crm, pf.data_admissao, pf.especialidade, r.ano_residencia
            FROM residente r
            JOIN profissional pf ON pf.id_pessoa = r.id_profissional
            JOIN pessoa p ON p.id_pessoa = r.id_profissional
            ORDER BY p.nome ASC
            """
        )
        return await cur.fetchall()


@router.get(
    "/preceptores",
    response_model=List[PreceptorListItem],
    summary="Lista preceptores cadastrados"
)
async def list_preceptores(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT pr.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
                   pf.crm, pf.data_admissao, pf.especialidade, pr.titulacao
            FROM preceptor pr
            JOIN profissional pf ON pf.id_pessoa = pr.id_profissional
            JOIN pessoa p ON p.id_pessoa = pr.id_profissional
            ORDER BY p.nome ASC
            """
        )
        return await cur.fetchall()


@router.get(
    "/atendimentos",
    response_model=List[AtendimentoListItem],
    summary="Lista atendimentos cadastrados"
)
async def list_atendimentos(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT a.id_atendimento, a.data_hora, a.duracao_minutos, a.id_paciente, p.nome AS nome_paciente
            FROM atendimento a
            JOIN pessoa p ON p.id_pessoa = a.id_paciente
            ORDER BY a.data_hora DESC
            """
        )
        return await cur.fetchall()


@router.post(
    "/pacientes",
    response_model=PacienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo paciente"
)
async def create_paciente(data: PacienteCreate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        try:
            await cur.execute(
                """
                INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_pessoa
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone),
            )
            pessoa = await cur.fetchone()
            await cur.execute(
                """
                INSERT INTO paciente (id_pessoa, num_convenio, alergias, grupo_sanguineo)
                VALUES (%s, %s, %s, %s)
                """,
                (pessoa["id_pessoa"], data.num_convenio, data.alergias, data.grupo_sanguineo),
            )
            row = await _fetch_paciente(cur, pessoa["id_pessoa"])
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)


@router.post(
    "/residentes",
    response_model=ResidenteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo residente"
)
async def create_residente(data: ResidenteCreate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        try:
            await cur.execute(
                """
                INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_pessoa
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone),
            )
            pessoa = await cur.fetchone()
            id_pessoa = pessoa["id_pessoa"]
            await cur.execute(
                """
                INSERT INTO profissional (id_pessoa, crm, data_admissao, especialidade)
                VALUES (%s, %s, %s, %s)
                """,
                (id_pessoa, data.crm, data.data_admissao, data.especialidade),
            )
            await cur.execute(
                """
                INSERT INTO residente (id_profissional, ano_residencia)
                VALUES (%s, %s)
                """,
                (id_pessoa, data.ano_residencia),
            )
            row = await _fetch_residente(cur, id_pessoa)
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)


@router.post(
    "/preceptores",
    response_model=PreceptorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo preceptor"
)
async def create_preceptor(data: PreceptorCreate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        try:
            await cur.execute(
                """
                INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_pessoa
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone),
            )
            pessoa = await cur.fetchone()
            id_pessoa = pessoa["id_pessoa"]
            await cur.execute(
                """
                INSERT INTO profissional (id_pessoa, crm, data_admissao, especialidade)
                VALUES (%s, %s, %s, %s)
                """,
                (id_pessoa, data.crm, data.data_admissao, data.especialidade),
            )
            await cur.execute(
                """
                INSERT INTO preceptor (id_profissional, titulacao)
                VALUES (%s, %s)
                """,
                (id_pessoa, data.titulacao),
            )
            row = await _fetch_preceptor(cur, id_pessoa)
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)


# 1. POST /atendimentos - insere atendimento validando existência de paciente/residente/preceptor
@router.post(
    "/atendimentos",
    response_model=AtendimentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo atendimento"
)
async def create_atendimento(atendimento: AtendimentoCreate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        try:
            await cur.execute(
                """
                INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor
                """,
                (
                    atendimento.data_hora,
                    atendimento.duracao_minutos,
                    atendimento.id_paciente,
                    atendimento.id_residente,
                    atendimento.id_preceptor,
                )
            )
            row = await cur.fetchone()
            await conn.commit()
            return row
        except ForeignKeyViolation as err:
            await conn.rollback()
            # Identifica qual FK falhou com base no nome da constraint do schema
            constraint = err.diag.constraint_name
            if constraint == "fk_atendimento_paciente":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Paciente com id_pessoa {atendimento.id_paciente} não existe."
                )
            elif constraint == "fk_atendimento_residente":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Residente com id_profissional {atendimento.id_residente} não existe."
                )
            elif constraint == "fk_atendimento_preceptor":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Preceptor com id_profissional {atendimento.id_preceptor} não existe."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Violação de chave estrangeira: paciente, residente ou preceptor inexistente."
                )

# 2. GET /pacientes/{id}/atendimentos - atendimentos do paciente, ordenados por data_hora
@router.get(
    "/pacientes/{id}/atendimentos",
    response_model=List[AtendimentoDoPacienteResponse],
    summary="Lista atendimentos de um paciente ordenados por data e hora"
)
async def get_paciente_atendimentos(id: int, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        # Verifica se o paciente existe
        await cur.execute("SELECT 1 FROM paciente WHERE id_pessoa = %s", (id,))
        exists = await cur.fetchone()
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente com ID {id} não encontrado."
            )

        # Busca atendimentos
        await cur.execute(
            """
            SELECT a.id_atendimento, a.data_hora, a.duracao_minutos, a.id_residente, a.id_preceptor,
                   p_res.nome AS nome_residente, p_prec.nome AS nome_preceptor
            FROM atendimento a
            LEFT JOIN pessoa p_res ON p_res.id_pessoa = a.id_residente
            LEFT JOIN pessoa p_prec ON p_prec.id_pessoa = a.id_preceptor
            WHERE a.id_paciente = %s
            ORDER BY a.data_hora ASC
            """,
            (id,)
        )
        rows = await cur.fetchall()
        return rows

# 3. GET /atendimentos/{id}/procedimentos - nome do procedimento, quantidade, tempo real
@router.get(
    "/atendimentos/{id}/procedimentos",
    response_model=List[AtendimentoProcedimentoResponse],
    summary="Lista procedimentos realizados em um atendimento"
)
async def get_atendimento_procedimentos(id: int, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        # Verifica se o atendimento existe
        await cur.execute("SELECT 1 FROM atendimento WHERE id_atendimento = %s", (id,))
        exists = await cur.fetchone()
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Atendimento com ID {id} não encontrado."
            )

        # Busca os procedimentos realizados
        await cur.execute(
            """
            SELECT p.codigo, p.nome AS nome_procedimento, pr.quantidade, pr.tempo_real_minutos, pr.faturado
            FROM procedimento_realizado pr
            JOIN procedimento p ON p.id_procedimento = pr.id_procedimento
            WHERE pr.id_atendimento = %s
            ORDER BY p.nome ASC
            """,
            (id,)
        )
        rows = await cur.fetchall()
        return rows

# 4. PUT /pacientes/{id} - atualiza dados pessoais e clínicos do paciente
@router.put(
    "/pacientes/{id}",
    response_model=PacienteResponse,
    summary="Atualiza dados de um paciente"
)
async def update_paciente(id: int, data: PacienteUpdate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT 1 FROM paciente WHERE id_pessoa = %s", (id,))
        if not await cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente com ID {id} não encontrado."
            )

        try:
            await cur.execute(
                """
                UPDATE pessoa
                SET nome = %s, cpf = %s, data_nascimento = %s, is_flamengo = %s, telefone = %s
                WHERE id_pessoa = %s
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone, id),
            )
            await cur.execute(
                """
                UPDATE paciente
                SET num_convenio = %s, alergias = %s, grupo_sanguineo = %s
                WHERE id_pessoa = %s
                """,
                (data.num_convenio, data.alergias, data.grupo_sanguineo, id),
            )
            row = await _fetch_paciente(cur, id)
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)


@router.put(
    "/residentes/{id}",
    response_model=ResidenteResponse,
    summary="Atualiza dados de um residente"
)
async def update_residente(id: int, data: ResidenteUpdate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT 1 FROM residente WHERE id_profissional = %s", (id,))
        if not await cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Residente com ID {id} não encontrado."
            )

        try:
            await cur.execute(
                """
                UPDATE pessoa
                SET nome = %s, cpf = %s, data_nascimento = %s, is_flamengo = %s, telefone = %s
                WHERE id_pessoa = %s
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone, id),
            )
            await cur.execute(
                """
                UPDATE profissional
                SET crm = %s, data_admissao = %s, especialidade = %s
                WHERE id_pessoa = %s
                """,
                (data.crm, data.data_admissao, data.especialidade, id),
            )
            await cur.execute(
                """
                UPDATE residente
                SET ano_residencia = %s
                WHERE id_profissional = %s
                """,
                (data.ano_residencia, id),
            )
            row = await _fetch_residente(cur, id)
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)


@router.put(
    "/preceptores/{id}",
    response_model=PreceptorResponse,
    summary="Atualiza dados de um preceptor"
)
async def update_preceptor(id: int, data: PreceptorUpdate, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT 1 FROM preceptor WHERE id_profissional = %s", (id,))
        if not await cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preceptor com ID {id} não encontrado."
            )

        try:
            await cur.execute(
                """
                UPDATE pessoa
                SET nome = %s, cpf = %s, data_nascimento = %s, is_flamengo = %s, telefone = %s
                WHERE id_pessoa = %s
                """,
                (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone, id),
            )
            await cur.execute(
                """
                UPDATE profissional
                SET crm = %s, data_admissao = %s, especialidade = %s
                WHERE id_pessoa = %s
                """,
                (data.crm, data.data_admissao, data.especialidade, id),
            )
            await cur.execute(
                """
                UPDATE preceptor
                SET titulacao = %s
                WHERE id_profissional = %s
                """,
                (data.titulacao, id),
            )
            row = await _fetch_preceptor(cur, id)
            await conn.commit()
            return row
        except UniqueViolation as err:
            await conn.rollback()
            _handle_unique_violation(err)

# 5. DELETE /atendimentos/{id}/procedimentos/{cod} - remove só se faturado = FALSE
@router.delete(
    "/atendimentos/{id}/procedimentos/{cod}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a realização de um procedimento em um atendimento (se não faturado)"
)
async def delete_procedimento_realizado(id: int, cod: str, conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        # Verifica existência e status faturado do procedimento realizado
        await cur.execute(
            """
            SELECT pr.faturado, pr.id_procedimento
            FROM procedimento_realizado pr
            JOIN procedimento p ON p.id_procedimento = pr.id_procedimento
            WHERE pr.id_atendimento = %s AND p.codigo = %s
            """,
            (id, cod)
        )
        row = await cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Procedimento {cod} não encontrado no atendimento {id}."
            )

        if row["faturado"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é possível remover o procedimento {cod} do atendimento {id} pois ele já foi faturado."
            )

        # Remove o procedimento realizado
        await cur.execute(
            """
            DELETE FROM procedimento_realizado
            WHERE id_atendimento = %s AND id_procedimento = %s
            """,
            (id, row["id_procedimento"])
        )
        await conn.commit()
        return None

# 6. GET /residentes/tempo-medio - tempo médio de duração de atendimentos por residente
@router.get(
    "/residentes/tempo-medio",
    response_model=List[ResidenteTempoMedioResponse],
    summary="Retorna o tempo médio de duração dos atendimentos por residente"
)
async def get_tempo_medio_residentes(conn: Connection = Depends(get_db)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT r.id_profissional AS id_residente,
                   p.nome AS nome_residente,
                   COALESCE(AVG(a.duracao_minutos), 0.0) AS tempo_medio_minutos
            FROM residente r
            JOIN pessoa p ON p.id_pessoa = r.id_profissional
            LEFT JOIN atendimento a ON a.id_residente = r.id_profissional
            GROUP BY r.id_profissional, p.nome
            ORDER BY tempo_medio_minutos DESC, p.nome ASC
            """
        )
        rows = await cur.fetchall()
        # Converte o Decimal retornado pelo AVG para float compatível com o schema
        for row in rows:
            row["tempo_medio_minutos"] = float(row["tempo_medio_minutos"])
        return rows
