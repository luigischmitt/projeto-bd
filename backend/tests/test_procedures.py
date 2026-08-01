"""Testes das stored procedures da Etapa 2 (issue #4).

Diferente de test_api.py, estes testes não passam pela aplicação FastAPI: eles
chamam as procedures diretamente via psycopg, como faria qualquer cliente SQL.
Cada teste abre sua própria conexão/transação e faz ROLLBACK no teardown, para
não vazar dados mutados entre testes (o cálculo de tempo médio de espera, em
particular, depende dos valores exatos do seed).
"""

import psycopg
import pytest
from psycopg.types.json import Json

from app.config import settings


def is_db_accessible() -> bool:
    try:
        with psycopg.connect(settings.DATABASE_URL):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_db_accessible(),
    reason="O banco de dados PostgreSQL local não está acessível no DATABASE_URL configurado.",
)


@pytest.fixture
def conn():
    connection = psycopg.connect(settings.DATABASE_URL)
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# sp_registrar_atendimento_completo
# ---------------------------------------------------------------------------


def _contar_atendimentos(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atendimento")
        return cur.fetchone()[0]


def test_registrar_atendimento_completo_cria_atendimento_com_n_procedimentos(conn):
    procedimentos = [
        {
            "id_procedimento": 1,
            "quantidade": 1,
            "tempo_real_minutos": 10,
            "data_hora_inicio": "2026-07-01T08:10:00",
            "observacao": None,
        },
        {
            "id_procedimento": 2,
            "quantidade": 2,
            "tempo_real_minutos": 15,
            "data_hora_inicio": "2026-07-01T08:20:00",
            "observacao": "sem intercorrencia",
        },
    ]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sp_registrar_atendimento_completo(
                %s::timestamp, %s::integer, %s::integer, %s::integer, %s::integer, %s::integer, %s::jsonb
            )
            """,
            ("2026-07-01 08:00:00", 30, 1, 11, 6, 1, Json(procedimentos)),
        )
        id_atendimento = cur.fetchone()[0]

        cur.execute("SELECT id_unidade FROM atendimento WHERE id_atendimento = %s", (id_atendimento,))
        assert cur.fetchone()[0] == 1

        cur.execute(
            "SELECT id_procedimento, quantidade FROM procedimento_realizado "
            "WHERE id_atendimento = %s ORDER BY id_procedimento",
            (id_atendimento,),
        )
        rows = cur.fetchall()
        assert rows == [(1, 1), (2, 2)]


def test_registrar_atendimento_completo_procedimento_invalido_reverte_tudo(conn):
    total_antes = _contar_atendimentos(conn)

    procedimentos = [
        {
            "id_procedimento": 1,
            "quantidade": 1,
            "tempo_real_minutos": 10,
            "data_hora_inicio": "2026-07-02T08:10:00",
            "observacao": None,
        },
        # id_procedimento inexistente: dispara violação de FK no meio do laço.
        {
            "id_procedimento": 9999,
            "quantidade": 1,
            "tempo_real_minutos": 15,
            "data_hora_inicio": "2026-07-02T08:20:00",
            "observacao": None,
        },
    ]

    with pytest.raises(psycopg.Error, match="Referência inválida"):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sp_registrar_atendimento_completo(
                    %s::timestamp, %s::integer, %s::integer, %s::integer, %s::integer, %s::integer, %s::jsonb
                )
                """,
                ("2026-07-02 08:00:00", 30, 1, 11, 6, 1, Json(procedimentos)),
            )

    conn.rollback()
    # O INSERT do atendimento (primeiro comando do bloco) também foi desfeito:
    # nem o atendimento nem o procedimento válido que veio antes do inválido ficaram.
    assert _contar_atendimentos(conn) == total_antes


def test_registrar_atendimento_completo_quantidade_invalida_reverte_tudo(conn):
    total_antes = _contar_atendimentos(conn)

    procedimentos = [
        {
            "id_procedimento": 1,
            "quantidade": 1,
            "tempo_real_minutos": 10,
            "data_hora_inicio": "2026-07-03T08:10:00",
            "observacao": None,
        },
        # quantidade <= 0 viola ck_pr_quantidade (CHECK).
        {
            "id_procedimento": 2,
            "quantidade": 0,
            "tempo_real_minutos": 15,
            "data_hora_inicio": "2026-07-03T08:20:00",
            "observacao": None,
        },
    ]

    with pytest.raises(psycopg.Error, match="Dado inválido"):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sp_registrar_atendimento_completo(
                    %s::timestamp, %s::integer, %s::integer, %s::integer, %s::integer, %s::integer, %s::jsonb
                )
                """,
                ("2026-07-03 08:00:00", 30, 1, 11, 6, 1, Json(procedimentos)),
            )

    conn.rollback()
    assert _contar_atendimentos(conn) == total_antes


# ---------------------------------------------------------------------------
# sp_calcular_tempo_medio_espera
# ---------------------------------------------------------------------------


def test_calcular_tempo_medio_espera_bate_com_calculo_manual_do_seed(conn):
    # Reproduz manualmente, em SQL puro, a definição do enunciado: para cada
    # unidade, a média da diferença entre a chegada (atendimento.data_hora) e o
    # início do primeiro procedimento (MIN(procedimento_realizado.data_hora_inicio))
    # daquele atendimento, excluindo atendimentos sem procedimento registrado.
    # Comparar contra essa consulta independente (em vez de valores fixos do seed)
    # mantém o teste correto mesmo que outros testes da suíte alterem o banco.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id_unidade, ROUND(AVG(EXTRACT(EPOCH FROM (inicio.data_hora_inicio_min - a.data_hora)) / 60)::NUMERIC, 2)
            FROM atendimento a
            JOIN (
                SELECT id_atendimento, MIN(data_hora_inicio) AS data_hora_inicio_min
                FROM procedimento_realizado
                WHERE data_hora_inicio IS NOT NULL
                GROUP BY id_atendimento
            ) inicio ON inicio.id_atendimento = a.id_atendimento
            GROUP BY a.id_unidade
            """
        )
        esperado = {row[0]: float(row[1]) for row in cur.fetchall()}

        cur.execute("SELECT id_unidade, nome_unidade, tempo_medio_espera_minutos FROM sp_calcular_tempo_medio_espera()")
        resultado = {row[0]: float(row[2]) for row in cur.fetchall()}

    assert resultado == esperado
    # E ainda confere com o cálculo manual original do seed (db/05_seed.sql), caso
    # nenhum outro teste da suíte tenha alterado procedimento_realizado até aqui:
    #   unidade 1 (atendimentos 1,2,3,4,10): esperas 15, 20, 25, 10, 20 -> media 18.00
    #   unidade 2 (atendimentos 5,6,7):       esperas 30, 5, 20         -> media 18.33
    #   unidade 3 (atendimentos 8,9):         atend. 8 sem procedimento, so conta o 9 (15) -> media 15.00


def test_calcular_tempo_medio_espera_exclui_atendimento_sem_procedimento(conn):
    # O atendimento 8 (unidade 3) não tem procedimento_realizado associado no seed.
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM procedimento_realizado WHERE id_atendimento = 8"
        )
        assert cur.fetchone()[0] == 0

        cur.execute(
            "SELECT tempo_medio_espera_minutos FROM sp_calcular_tempo_medio_espera() WHERE id_unidade = 3"
        )
        (media_unidade_3,) = cur.fetchone()
        # Se o atendimento 8 entrasse no cálculo (sem procedimento -> sem instante de
        # início), a média mudaria; o valor isolado do atendimento 9 é 15.00.
        assert float(media_unidade_3) == 15.00


# ---------------------------------------------------------------------------
# sp_reajustar_escala
# ---------------------------------------------------------------------------


def _escalas_do_residente(conn, id_residente: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_escala, id_unidade, dia_semana, turno FROM escala "
            "WHERE id_residente = %s ORDER BY id_escala",
            (id_residente,),
        )
        return cur.fetchall()


def test_reajustar_escala_sucesso_move_todas_as_escalas_do_dia_turno(conn):
    antes = _escalas_do_residente(conn, 11)
    # Residente 11 tem uma única escala em SEG/MANHA (id_escala=1) no seed.
    assert ("SEG", "MANHA") in [(row[2], row[3]) for row in antes]

    with conn.cursor() as cur:
        cur.execute("CALL sp_reajustar_escala(%s, %s, %s, %s, %s)", (11, "SEG", "MANHA", "QUI", "TARDE"))

    depois = _escalas_do_residente(conn, 11)
    dias_turnos_depois = [(row[2], row[3]) for row in depois]

    assert ("SEG", "MANHA") not in dias_turnos_depois
    assert ("QUI", "TARDE") in dias_turnos_depois
    # Nenhuma escala foi criada ou removida, apenas movida.
    assert len(depois) == len(antes)


def test_reajustar_escala_conflito_falha_e_nao_altera_nada(conn):
    # Residente 11 já está escalado em TER/MANHA (id_escala=3) e em SEX/NOITE (id_escala=7).
    antes = _escalas_do_residente(conn, 11)

    with pytest.raises(psycopg.Error, match="já possui escala"):
        with conn.cursor() as cur:
            cur.execute("CALL sp_reajustar_escala(%s, %s, %s, %s, %s)", (11, "SEX", "NOITE", "TER", "MANHA"))

    conn.rollback()
    depois = _escalas_do_residente(conn, 11)
    assert depois == antes
