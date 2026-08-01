from psycopg import Connection
from psycopg.rows import dict_row

from app.repositories import paciente as paciente_repo
from app.schemas.atendimento import AtendimentoCreate


async def list_all(conn: Connection) -> list[dict]:
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


async def create(conn: Connection, data: AtendimentoCreate) -> dict:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor
            """,
            (data.data_hora, data.duracao_minutos, data.id_paciente, data.id_residente, data.id_preceptor),
        )
        row = await cur.fetchone()
        await conn.commit()
        return row


async def list_by_paciente(conn: Connection, id_paciente: int) -> list[dict] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        if not await paciente_repo.exists(cur, id_paciente):
            return None
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
            (id_paciente,),
        )
        return await cur.fetchall()


async def list_procedimentos(conn: Connection, id_atendimento: int) -> list[dict] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT 1 FROM atendimento WHERE id_atendimento = %s", (id_atendimento,))
        if not await cur.fetchone():
            return None
        await cur.execute(
            """
            SELECT p.codigo, p.nome AS nome_procedimento, pr.quantidade, pr.tempo_real_minutos, pr.faturado
            FROM procedimento_realizado pr
            JOIN procedimento p ON p.id_procedimento = pr.id_procedimento
            WHERE pr.id_atendimento = %s
            ORDER BY p.nome ASC
            """,
            (id_atendimento,),
        )
        return await cur.fetchall()


async def delete_procedimento(conn: Connection, id_atendimento: int, cod: str) -> str | None:
    """Returns None on success, 'not_found', or 'faturado'."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT pr.faturado, pr.id_procedimento
            FROM procedimento_realizado pr
            JOIN procedimento p ON p.id_procedimento = pr.id_procedimento
            WHERE pr.id_atendimento = %s AND p.codigo = %s
            """,
            (id_atendimento, cod),
        )
        row = await cur.fetchone()
        if not row:
            return "not_found"
        if row["faturado"]:
            return "faturado"
        await cur.execute(
            "DELETE FROM procedimento_realizado WHERE id_atendimento = %s AND id_procedimento = %s",
            (id_atendimento, row["id_procedimento"]),
        )
        await conn.commit()
        return None
