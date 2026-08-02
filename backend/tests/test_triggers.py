"""Testes das triggers da Etapa 2 (issue #5), direto contra o banco via psycopg.

Não passam pela API: escrevem SQL diretamente para exercitar as triggers de
db/03_triggers.sql. Reaproveita os dados do seed (db/05_seed.sql) e usa
`conn.transaction()` como savepoint em torno das operações que devem ser
rejeitadas, para que o restante do teste continue com a conexão utilizável.
Nada é commitado: o fixture `conn` sempre faz rollback no final.
"""

import psycopg
import pytest

from app.config import settings


@pytest.fixture
def conn():
    connection = psycopg.connect(settings.DATABASE_URL)
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# trg_check_sobreposicao_escala
# ---------------------------------------------------------------------------
# Residente 11 (Felipe), no seed, já está em SEG/MANHA na unidade 1.


def test_escala_outra_unidade_mesmo_dia_turno_e_rejeitada(conn):
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute(
                "INSERT INTO escala (id_unidade, dia_semana, turno, id_residente, id_preceptor) "
                "VALUES (2, 'SEG', 'MANHA', 11, 8)"
            )

    cur = conn.execute(
        "SELECT count(*) FROM escala WHERE id_residente = 11 AND id_unidade = 2 "
        "AND dia_semana = 'SEG' AND turno = 'MANHA'"
    )
    assert cur.fetchone()[0] == 0


def test_escala_mesma_unidade_e_bloqueada_pela_unique_nao_pela_trigger(conn):
    # Mesma tripla (unidade, dia, turno) e mesmo residente do seed: quem rejeita
    # aqui é uq_escala_unidade_dia_turno_residente, não fn_check_sobreposicao_escala.
    # É o escopo que a trigger deliberadamente NÃO reimplementa.
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():
            conn.execute(
                "INSERT INTO escala (id_unidade, dia_semana, turno, id_residente, id_preceptor) "
                "VALUES (1, 'SEG', 'MANHA', 11, 7)"
            )


def test_escala_dia_turno_livre_e_aceita(conn):
    cur = conn.execute(
        "INSERT INTO escala (id_unidade, dia_semana, turno, id_residente, id_preceptor) "
        "VALUES (2, 'QUI', 'MANHA', 11, 6) RETURNING id_escala"
    )
    assert cur.fetchone() is not None


def test_escala_update_sem_mudar_dia_turno_nao_se_autorejeita(conn):
    # Regressão do cuidado citado na issue: a trigger precisa excluir a própria
    # linha (id_escala <> NEW.id_escala) para não se autorejeitar num UPDATE
    # que não toca dia_semana/turno.
    conn.execute("UPDATE escala SET id_preceptor = 7 WHERE id_escala = 1")
    cur = conn.execute("SELECT id_preceptor FROM escala WHERE id_escala = 1")
    assert cur.fetchone()[0] == 7


def test_escala_update_para_conflito_em_outra_unidade_e_rejeitado(conn):
    # Residente 14 já está em u2/QUA/MANHA (seed). Cria uma escala livre para
    # ele e tenta movê-la, via UPDATE, para o mesmo dia/turno em outra unidade.
    conn.execute(
        "INSERT INTO escala (id_unidade, dia_semana, turno, id_residente, id_preceptor) "
        "VALUES (3, 'DOM', 'NOITE', 14, 6)"
    )

    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute(
                "UPDATE escala SET dia_semana = 'QUA', turno = 'MANHA' "
                "WHERE id_unidade = 3 AND dia_semana = 'DOM' AND turno = 'NOITE' AND id_residente = 14"
            )


# ---------------------------------------------------------------------------
# trg_audita_atendimento
# ---------------------------------------------------------------------------


def test_insert_update_delete_em_atendimento_grava_auditoria(conn):
    cur = conn.execute(
        "INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor, id_unidade) "
        "VALUES ('2026-07-01 10:00:00', 20, 1, 11, 6, 1) RETURNING id_atendimento"
    )
    id_atendimento = cur.fetchone()[0]

    conn.execute(
        "UPDATE atendimento SET duracao_minutos = 25 WHERE id_atendimento = %s",
        (id_atendimento,),
    )
    conn.execute("DELETE FROM atendimento WHERE id_atendimento = %s", (id_atendimento,))

    cur = conn.execute(
        "SELECT operacao, usuario, dados_antigos, dados_novos FROM auditoria_atendimento "
        "WHERE id_atendimento = %s ORDER BY id_auditoria",
        (id_atendimento,),
    )
    linhas = cur.fetchall()

    assert [linha[0] for linha in linhas] == ["INSERT", "UPDATE", "DELETE"]
    assert all(linha[1] for linha in linhas)  # usuario preenchido nas três

    _, _, antigos_insert, novos_insert = linhas[0]
    assert antigos_insert is None
    assert novos_insert["id_atendimento"] == id_atendimento
    assert novos_insert["duracao_minutos"] == 20

    _, _, antigos_update, novos_update = linhas[1]
    assert antigos_update["duracao_minutos"] == 20
    assert novos_update["duracao_minutos"] == 25

    _, _, antigos_delete, novos_delete = linhas[2]
    assert antigos_delete["duracao_minutos"] == 25
    assert novos_delete is None


# ---------------------------------------------------------------------------
# trg_atualiza_media_procedimentos
# ---------------------------------------------------------------------------


def test_media_do_procedimento_e_recalculada_apos_insercao(conn):
    cur = conn.execute(
        "SELECT media_tempo_procedimento FROM procedimento WHERE id_procedimento = 1"
    )
    media_antes = cur.fetchone()[0]

    cur = conn.execute(
        "INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor, id_unidade) "
        "VALUES ('2026-07-02 09:00:00', 15, 2, 12, 6, 1) RETURNING id_atendimento"
    )
    id_atendimento = cur.fetchone()[0]

    conn.execute(
        "INSERT INTO procedimento_realizado "
        "(id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) "
        "VALUES (%s, 1, 1, 13, '2026-07-02 09:10:00')",
        (id_atendimento,),
    )

    cur = conn.execute(
        "SELECT media_tempo_procedimento FROM procedimento WHERE id_procedimento = 1"
    )
    media_depois = cur.fetchone()[0]

    cur = conn.execute(
        "SELECT ROUND(AVG(tempo_real_minutos), 2) FROM procedimento_realizado WHERE id_procedimento = 1"
    )
    media_esperada = cur.fetchone()[0]

    assert media_depois != media_antes
    assert media_depois == media_esperada
