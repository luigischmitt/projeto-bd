from psycopg import Connection
from psycopg.rows import dict_row

from app.schemas.paciente import PacienteCreate, PacienteUpdate

_SELECT = """
    SELECT pa.id_pessoa, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
           pa.num_convenio, pa.alergias, pa.grupo_sanguineo
    FROM paciente pa
    JOIN pessoa p ON p.id_pessoa = pa.id_pessoa
"""


async def list_all(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"{_SELECT} ORDER BY p.nome ASC")
        return await cur.fetchall()


async def fetch(cur, id_pessoa: int) -> dict | None:
    await cur.execute(f"{_SELECT} WHERE pa.id_pessoa = %s", (id_pessoa,))
    return await cur.fetchone()


async def exists(cur, id_pessoa: int) -> bool:
    await cur.execute("SELECT 1 FROM paciente WHERE id_pessoa = %s", (id_pessoa,))
    return await cur.fetchone() is not None


async def create(conn: Connection, data: PacienteCreate) -> dict:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_pessoa
            """,
            (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone),
        )
        id_pessoa = (await cur.fetchone())["id_pessoa"]
        await cur.execute(
            """
            INSERT INTO paciente (id_pessoa, num_convenio, alergias, grupo_sanguineo)
            VALUES (%s, %s, %s, %s)
            """,
            (id_pessoa, data.num_convenio, data.alergias, data.grupo_sanguineo),
        )
        row = await fetch(cur, id_pessoa)
        await conn.commit()
        return row


async def update(conn: Connection, id_pessoa: int, data: PacienteUpdate) -> dict | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        if not await exists(cur, id_pessoa):
            return None
        await cur.execute(
            """
            UPDATE pessoa
            SET nome = %s, cpf = %s, data_nascimento = %s, is_flamengo = %s, telefone = %s
            WHERE id_pessoa = %s
            """,
            (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone, id_pessoa),
        )
        await cur.execute(
            """
            UPDATE paciente
            SET num_convenio = %s, alergias = %s, grupo_sanguineo = %s
            WHERE id_pessoa = %s
            """,
            (data.num_convenio, data.alergias, data.grupo_sanguineo, id_pessoa),
        )
        row = await fetch(cur, id_pessoa)
        await conn.commit()
        return row
