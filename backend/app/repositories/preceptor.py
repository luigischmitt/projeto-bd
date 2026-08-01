from psycopg import Connection
from psycopg.rows import dict_row

from app.schemas.preceptor import PreceptorCreate, PreceptorUpdate

_SELECT = """
    SELECT pr.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
           pf.crm, pf.data_admissao, pf.especialidade, pr.titulacao
    FROM preceptor pr
    JOIN profissional pf ON pf.id_pessoa = pr.id_profissional
    JOIN pessoa p ON p.id_pessoa = pr.id_profissional
"""


async def list_all(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"{_SELECT} ORDER BY p.nome ASC")
        return await cur.fetchall()


async def fetch(cur, id_profissional: int) -> dict | None:
    await cur.execute(f"{_SELECT} WHERE pr.id_profissional = %s", (id_profissional,))
    return await cur.fetchone()


async def exists(cur, id_profissional: int) -> bool:
    await cur.execute("SELECT 1 FROM preceptor WHERE id_profissional = %s", (id_profissional,))
    return await cur.fetchone() is not None


async def create(conn: Connection, data: PreceptorCreate) -> dict:
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
            INSERT INTO profissional (id_pessoa, crm, data_admissao, especialidade)
            VALUES (%s, %s, %s, %s)
            """,
            (id_pessoa, data.crm, data.data_admissao, data.especialidade),
        )
        await cur.execute(
            "INSERT INTO preceptor (id_profissional, titulacao) VALUES (%s, %s)",
            (id_pessoa, data.titulacao),
        )
        row = await fetch(cur, id_pessoa)
        await conn.commit()
        return row


async def update(conn: Connection, id_profissional: int, data: PreceptorUpdate) -> dict | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        if not await exists(cur, id_profissional):
            return None
        await cur.execute(
            """
            UPDATE pessoa
            SET nome = %s, cpf = %s, data_nascimento = %s, is_flamengo = %s, telefone = %s
            WHERE id_pessoa = %s
            """,
            (data.nome, data.cpf, data.data_nascimento, data.is_flamengo, data.telefone, id_profissional),
        )
        await cur.execute(
            """
            UPDATE profissional
            SET crm = %s, data_admissao = %s, especialidade = %s
            WHERE id_pessoa = %s
            """,
            (data.crm, data.data_admissao, data.especialidade, id_profissional),
        )
        await cur.execute(
            "UPDATE preceptor SET titulacao = %s WHERE id_profissional = %s",
            (data.titulacao, id_profissional),
        )
        row = await fetch(cur, id_profissional)
        await conn.commit()
        return row
