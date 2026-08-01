"""Testes das views da Etapa 2 (issue #6), validadas diretamente contra o banco.

As views ainda não são expostas por endpoint (isso é escopo da issue #9), então os
testes aqui rodam SQL cru com psycopg e conferem linhas específicas do seed, não
apenas "retornou alguma coisa".
"""

import psycopg
import pytest

from app.config import settings
from conftest import is_db_accessible

pytestmark = pytest.mark.skipif(
    not is_db_accessible(),
    reason="O banco de dados PostgreSQL local não está acessível no DATABASE_URL configurado.",
)


@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(settings.DATABASE_URL) as connection:
        yield connection


def rows(conn, query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


class TestVwPacientesInternados:
    def test_apenas_pacientes_cuja_internacao_mais_recente_segue_sem_alta(self, conn):
        data = rows(
            conn,
            "SELECT id_paciente, nome_paciente, id_unidade FROM vw_pacientes_internados "
            "ORDER BY id_paciente",
        )
        assert [row["id_paciente"] for row in data] == [1, 2, 3]

    def test_paciente_com_alta_seguida_de_nova_internacao_aparece(self, conn):
        """Paciente 1: internação 1 encerrada, depois internação 6 em curso. A mais
        recente decide, então ele deve aparecer com os dados da internação 6."""
        data = rows(
            conn,
            "SELECT id_internacao, id_unidade FROM vw_pacientes_internados "
            "WHERE id_paciente = 1",
        )
        assert len(data) == 1
        assert data[0]["id_internacao"] == 6
        assert data[0]["id_unidade"] == 2

    def test_paciente_so_com_internacao_encerrada_nao_aparece(self, conn):
        """Paciente 5 só tem a internação 5, já com alta."""
        data = rows(
            conn, "SELECT 1 FROM vw_pacientes_internados WHERE id_paciente = 5"
        )
        assert data == []

    def test_internacao_em_curso_no_meio_do_historico_nao_conta_se_ha_alta_mais_recente(
        self, conn
    ):
        """Paciente 4: internação 4 encerrada, depois 7 em curso, depois 8 encerrada.
        A internação 7 (sem alta) não deveria "vazar" para a view: a mais recente
        de todas (8) já tem alta, então o paciente 4 não aparece."""
        data = rows(
            conn, "SELECT 1 FROM vw_pacientes_internados WHERE id_paciente = 4"
        )
        assert data == []

    def test_expoe_nome_e_tempo_internado(self, conn):
        data = rows(
            conn,
            "SELECT nome_paciente, nome_unidade, tempo_internado "
            "FROM vw_pacientes_internados WHERE id_paciente = 2",
        )
        assert data[0]["nome_paciente"] == "Maria Paciente"
        assert data[0]["nome_unidade"] == "UTI Central"
        assert data[0]["tempo_internado"].total_seconds() > 0


class TestVwResidentesSemSupervisor:
    def test_exclui_escalas_supervisionadas_por_doutor_ou_pos_doutor(self, conn):
        data = rows(
            conn,
            "SELECT titulacao_preceptor FROM vw_residentes_sem_supervisor",
        )
        assert all(
            row["titulacao_preceptor"] not in ("DOUTOR", "POS_DOUTOR") for row in data
        )

    def test_retorna_exatamente_as_escalas_esperadas(self, conn):
        data = rows(
            conn,
            "SELECT id_escala, nome_residente, dia_semana, turno, titulacao_preceptor "
            "FROM vw_residentes_sem_supervisor ORDER BY id_escala",
        )
        assert [row["id_escala"] for row in data] == [3, 5, 6]
        assert data[0] == {
            "id_escala": 3,
            "nome_residente": "Felipe Residente",
            "dia_semana": "TER",
            "turno": "MANHA",
            "titulacao_preceptor": "MESTRE",
        }

    def test_mesmo_residente_pode_aparecer_com_e_sem_supervisor_doutor(self, conn):
        """Felipe Residente (id 11) está nas escalas 1 (preceptor DOUTOR) e 3
        (preceptor MESTRE). Só a 3 deve aparecer na view."""
        data = rows(
            conn,
            "SELECT id_escala FROM vw_residentes_sem_supervisor WHERE id_residente = 11",
        )
        assert [row["id_escala"] for row in data] == [3]


class TestVwEstatisticasAtendimentosMensal:
    def test_agrega_por_mes_e_unidade(self, conn):
        # Outros testes da suíte (ex.: test_api.py, via TestClient) criam atendimentos
        # reais e comitados fora do escopo deste arquivo, então a asserção verifica que
        # as combinações mês/unidade esperadas do seed estão presentes, sem exigir que
        # sejam as únicas.
        data = rows(
            conn,
            "SELECT mes, id_unidade, nome_unidade, total_atendimentos, "
            "duracao_media_minutos FROM vw_estatisticas_atendimentos_mensal "
            "ORDER BY mes, id_unidade",
        )
        chaves = {(row["mes"].strftime("%Y-%m"), row["id_unidade"]) for row in data}
        assert {
            ("2026-05", 1),
            ("2026-05", 3),
            ("2026-06", 1),
            ("2026-06", 2),
        }.issubset(chaves)

    def test_totais_e_media_de_duracao_unidade1_junho(self, conn):
        """Unidade 1 em 2026-06: atendimentos 1,2,3,4 (durações 40,35,50,45)."""
        data = rows(
            conn,
            "SELECT total_atendimentos, duracao_media_minutos "
            "FROM vw_estatisticas_atendimentos_mensal "
            "WHERE id_unidade = 1 AND mes = '2026-06-01'",
        )
        assert data[0]["total_atendimentos"] == 4
        assert data[0]["duracao_media_minutos"] == pytest.approx(42.5)

    def test_procedimentos_mais_frequentes_unidade1_junho(self, conn):
        """Aplicacao de medicacao tem quantidade 2 (atendimento 2) e é o mais
        frequente da unidade 1 em junho/2026."""
        data = rows(
            conn,
            "SELECT procedimentos_mais_frequentes "
            "FROM vw_estatisticas_atendimentos_mensal "
            "WHERE id_unidade = 1 AND mes = '2026-06-01'",
        )
        procedimentos = data[0]["procedimentos_mais_frequentes"]
        assert len(procedimentos) == 3
        assert procedimentos[0] == {
            "procedimento": "Aplicacao de medicacao",
            "quantidade": 2,
        }

    def test_atendimento_sem_procedimento_nao_quebra_a_agregacao(self, conn):
        """O atendimento 8 (unidade 3, maio/2026) não tem procedimento_realizado, mas
        ainda deve contar para o total de atendimentos da unidade/mês."""
        data = rows(
            conn,
            "SELECT total_atendimentos, procedimentos_mais_frequentes "
            "FROM vw_estatisticas_atendimentos_mensal "
            "WHERE id_unidade = 3 AND mes = '2026-05-01'",
        )
        assert data[0]["total_atendimentos"] == 2
        assert data[0]["procedimentos_mais_frequentes"] == [
            {"procedimento": "Coleta de sangue", "quantidade": 1}
        ]
