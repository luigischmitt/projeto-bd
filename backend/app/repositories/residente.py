from psycopg import Connection
from psycopg.rows import dict_row

from app.schemas.residente import ResidenteCreate, ResidenteUpdate

_SELECT = """
    SELECT r.id_profissional, p.nome, p.cpf, p.data_nascimento, p.is_flamengo, p.telefone,
           pf.crm, pf.data_admissao, pf.especialidade, r.ano_residencia
    FROM residente r
    JOIN profissional pf ON pf.id_pessoa = r.id_profissional
    JOIN pessoa p ON p.id_pessoa = r.id_profissional
"""


async def list_all(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"{_SELECT} ORDER BY p.nome ASC")
        return await cur.fetchall()


async def fetch(cur, id_profissional: int) -> dict | None:
    await cur.execute(f"{_SELECT} WHERE r.id_profissional = %s", (id_profissional,))
    return await cur.fetchone()


async def exists(cur, id_profissional: int) -> bool:
    await cur.execute("SELECT 1 FROM residente WHERE id_profissional = %s", (id_profissional,))
    return await cur.fetchone() is not None


async def create(conn: Connection, data: ResidenteCreate) -> dict:
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
            "INSERT INTO residente (id_profissional, ano_residencia) VALUES (%s, %s)",
            (id_pessoa, data.ano_residencia),
        )
        row = await fetch(cur, id_pessoa)
        await conn.commit()
        return row


async def update(conn: Connection, id_profissional: int, data: ResidenteUpdate) -> dict | None:
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
            "UPDATE residente SET ano_residencia = %s WHERE id_profissional = %s",
            (data.ano_residencia, id_profissional),
        )
        row = await fetch(cur, id_profissional)
        await conn.commit()
        return row


async def tempo_medio(conn: Connection) -> list[dict]:
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
        for row in rows:
            row["tempo_medio_minutos"] = float(row["tempo_medio_minutos"])
        return rows
