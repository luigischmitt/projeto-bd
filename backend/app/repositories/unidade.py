from psycopg import Connection
from psycopg.rows import dict_row


async def list_all(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id_unidade, nome, tipo, capacidade_leitos
            FROM unidade
            ORDER BY nome ASC
            """
        )
        return await cur.fetchall()
