from datetime import datetime
from calendar import monthrange

from psycopg import Connection
from psycopg.rows import dict_row


async def ranking_residentes(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.nome AS residente, COUNT(a.id_atendimento) AS total_atendimentos
            FROM residente r
            JOIN pessoa p ON p.id_pessoa = r.id_profissional
            JOIN atendimento a ON a.id_residente = r.id_profissional
            GROUP BY r.id_profissional, p.nome
            ORDER BY total_atendimentos DESC, p.nome ASC
            """
        )
        return await cur.fetchall()


async def preceptores_supervisao(conn: Connection, data_inicio: datetime, data_fim: datetime) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.nome AS preceptor, COUNT(a.id_atendimento) AS total_supervisoes
            FROM preceptor pr
            JOIN pessoa p ON p.id_pessoa = pr.id_profissional
            JOIN atendimento a ON a.id_preceptor = pr.id_profissional
            WHERE a.data_hora >= %s AND a.data_hora <= %s
            GROUP BY pr.id_profissional, p.nome
            HAVING COUNT(a.id_atendimento) > 5
            ORDER BY total_supervisoes DESC, p.nome ASC
            """,
            (data_inicio, data_fim),
        )
        return await cur.fetchall()


async def plantoes_por_unidade(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT u.nome AS unidade, p.nome AS residente, COUNT(e.id_escala) AS plantoes
            FROM escala e
            JOIN unidade u ON u.id_unidade = e.id_unidade
            JOIN pessoa p ON p.id_pessoa = e.id_residente
            GROUP BY u.id_unidade, u.nome, e.id_residente, p.nome
            ORDER BY u.nome ASC, plantoes DESC, p.nome ASC
            """
        )
        return await cur.fetchall()


async def pacientes_sem_risco_alto(conn: Connection) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.id_pessoa, p.nome
            FROM paciente pac
            JOIN pessoa p ON p.id_pessoa = pac.id_pessoa
            WHERE NOT EXISTS (
                SELECT 1
                FROM atendimento a
                JOIN procedimento_realizado pr ON pr.id_atendimento = a.id_atendimento
                JOIN procedimento proc ON proc.id_procedimento = pr.id_procedimento
                WHERE a.id_paciente = pac.id_pessoa
                  AND proc.nivel_risco = 'ALTO'
            )
            ORDER BY p.nome ASC
            """
        )
        return await cur.fetchall()


def parse_mes(mes: str) -> tuple[datetime, datetime]:
    ano_str, mes_str = mes.split("-")
    ano, num_mes = int(ano_str), int(mes_str)
    if num_mes < 1 or num_mes > 12:
        raise ValueError
    data_inicio = datetime(ano, num_mes, 1, 0, 0, 0)
    _, ultimo_dia = monthrange(ano, num_mes)
    data_fim = datetime(ano, num_mes, ultimo_dia, 23, 59, 59, 999999)
    return data_inicio, data_fim
