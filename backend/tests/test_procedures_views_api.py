"""Testes dos endpoints novos da issue #9: as três procedures (`POST
/atendimentos/completo`, `POST /escalas/reajustar`) e as três views + auditoria (`GET
/views/...`, `GET /auditoria/atendimentos`), todos expostos pela API.

Diferente de `test_procedures.py`/`test_views.py` (que chamam banco direto via psycopg
e nunca commitam), estes testes passam pela API real e COMMITAM no banco — cada teste
que muda estado deixa a base como encontrou (reverte a escala movida, ou usa uma
data/unidade fora do que `test_views.py` verifica com igualdade exata), para não quebrar
os testes de outros arquivos que rodam depois na mesma sessão do pytest.
"""

import psycopg
import pytest

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


# ---------------------------------------------------------------------------
# POST /atendimentos/completo -> sp_registrar_atendimento_completo
# ---------------------------------------------------------------------------


def _payload_atendimento_completo(**overrides):
    payload = {
        "data_hora": "2026-07-20T09:00:00",
        "duracao_minutos": 30,
        "id_paciente": 2,
        "id_residente": 12,
        "id_preceptor": 7,
        "id_unidade": 2,
        "procedimentos": [
            {
                "id_procedimento": 1,
                "quantidade": 1,
                "tempo_real_minutos": 10,
                "data_hora_inicio": "2026-07-20T09:05:00",
                "observacao": None,
            },
            {
                "id_procedimento": 2,
                "quantidade": 2,
                "tempo_real_minutos": 15,
                "data_hora_inicio": "2026-07-20T09:20:00",
                "observacao": "teste automatizado",
            },
        ],
    }
    payload.update(overrides)
    return payload


def test_atendimento_completo_cria_atendimento_e_procedimentos(client):
    response = client.post("/atendimentos/completo", json=_payload_atendimento_completo())
    assert response.status_code == 201
    id_atendimento = response.json()["id_atendimento"]
    assert isinstance(id_atendimento, int)

    procedimentos = client.get(f"/atendimentos/{id_atendimento}/procedimentos")
    assert procedimentos.status_code == 200
    codigos = {item["codigo"] for item in procedimentos.json()}
    assert codigos == {"PROC-01", "PROC-02"}


def test_atendimento_completo_fk_invalida_retorna_400_e_nao_cria_nada(client):
    total_antes = len(client.get("/atendimentos").json())

    payload = _payload_atendimento_completo(
        data_hora="2026-07-21T09:00:00",
        procedimentos=[
            {
                "id_procedimento": 9999,
                "quantidade": 1,
                "tempo_real_minutos": 10,
                "data_hora_inicio": "2026-07-21T09:05:00",
                "observacao": None,
            }
        ],
    )
    response = client.post("/atendimentos/completo", json=payload)
    assert response.status_code == 400
    assert "Referência inválida" in response.json()["detail"]

    total_depois = len(client.get("/atendimentos").json())
    assert total_depois == total_antes


def test_atendimento_completo_check_invalido_retorna_400_e_nao_cria_nada(client):
    total_antes = len(client.get("/atendimentos").json())

    payload = _payload_atendimento_completo(
        data_hora="2026-07-22T09:00:00",
        procedimentos=[
            {
                "id_procedimento": 1,
                "quantidade": 0,  # viola ck_pr_quantidade
                "tempo_real_minutos": 10,
                "data_hora_inicio": "2026-07-22T09:05:00",
                "observacao": None,
            }
        ],
    )
    response = client.post("/atendimentos/completo", json=payload)
    assert response.status_code == 400
    assert "Dado inválido" in response.json()["detail"]

    total_depois = len(client.get("/atendimentos").json())
    assert total_depois == total_antes


# ---------------------------------------------------------------------------
# POST /escalas/reajustar -> sp_reajustar_escala
# ---------------------------------------------------------------------------


def test_reajustar_escala_move_e_reverte_sem_deixar_residuo(client):
    # Residente 11 (Felipe) tem escala em SEG/MANHA (id_escala=1) no seed.
    ida = client.post(
        "/escalas/reajustar",
        json={
            "id_residente": 11,
            "dia_origem": "SEG",
            "turno_origem": "MANHA",
            "dia_destino": "QUI",
            "turno_destino": "TARDE",
        },
    )
    assert ida.status_code == 204

    plantoes = client.get("/analytics/plantoes-por-unidade").json()
    felipe_enfermaria = [
        item
        for item in plantoes
        if item["residente"] == "Felipe Residente" and item["unidade"] == "Enfermaria Norte"
    ]
    # A escala mudou de dia/turno, mas continua na mesma unidade — a contagem de
    # plantões (que não distingue dia/turno) permanece 2.
    assert felipe_enfermaria == [
        {"unidade": "Enfermaria Norte", "residente": "Felipe Residente", "plantoes": 2}
    ]

    # Reverte para não afetar os demais testes da suíte (test_triggers.py, test_views.py)
    # que assumem o seed original.
    volta = client.post(
        "/escalas/reajustar",
        json={
            "id_residente": 11,
            "dia_origem": "QUI",
            "turno_origem": "TARDE",
            "dia_destino": "SEG",
            "turno_destino": "MANHA",
        },
    )
    assert volta.status_code == 204


def test_reajustar_escala_conflito_retorna_409_e_nao_altera_nada(client):
    # Residente 11 já está em TER/MANHA (id_escala=3) e em SEX/NOITE (id_escala=7):
    # mover SEX/NOITE -> TER/MANHA colide com uma escala já existente do mesmo residente.
    response = client.post(
        "/escalas/reajustar",
        json={
            "id_residente": 11,
            "dia_origem": "SEX",
            "turno_origem": "NOITE",
            "dia_destino": "TER",
            "turno_destino": "MANHA",
        },
    )
    assert response.status_code == 409
    assert "já possui escala" in response.json()["detail"]

    plantoes = client.get("/analytics/plantoes-por-unidade").json()
    felipe_pronto_socorro = [
        item
        for item in plantoes
        if item["residente"] == "Felipe Residente" and item["unidade"] == "Pronto-Socorro"
    ]
    # Nada mudou: a escala SEX/NOITE (Pronto-Socorro) continua existindo.
    assert felipe_pronto_socorro == [
        {"unidade": "Pronto-Socorro", "residente": "Felipe Residente", "plantoes": 1}
    ]


def test_reajustar_escala_validacao_rejeita_dia_turno_invalido(client):
    response = client.post(
        "/escalas/reajustar",
        json={
            "id_residente": 11,
            "dia_origem": "SEGUNDA",
            "turno_origem": "MANHA",
            "dia_destino": "QUI",
            "turno_destino": "TARDE",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /views/pacientes-internados -> vw_pacientes_internados
# ---------------------------------------------------------------------------


def test_get_pacientes_internados(client):
    response = client.get("/views/pacientes-internados")
    assert response.status_code == 200
    data = response.json()

    por_paciente = {item["id_paciente"]: item for item in data}
    assert set(por_paciente) == {1, 2, 3}
    # Paciente 1: internação 1 encerrada, depois internação 6 em curso — a mais
    # recente decide.
    assert por_paciente[1]["id_internacao"] == 6
    assert por_paciente[1]["id_unidade"] == 2
    assert por_paciente[1]["nome_paciente"] == "Carlos Paciente"
    # tempo_internado vem como duração ISO 8601 (timedelta serializado pelo Pydantic).
    assert por_paciente[1]["tempo_internado"].startswith("P")


# ---------------------------------------------------------------------------
# GET /views/residentes-sem-supervisor -> vw_residentes_sem_supervisor
# ---------------------------------------------------------------------------


def test_get_residentes_sem_supervisor(client):
    response = client.get("/views/residentes-sem-supervisor")
    assert response.status_code == 200
    data = response.json()

    assert [item["id_escala"] for item in data] == [3, 5, 6]
    assert all(item["titulacao_preceptor"] not in ("DOUTOR", "POS_DOUTOR") for item in data)
    assert data[0] == {
        "id_escala": 3,
        "id_residente": 11,
        "nome_residente": "Felipe Residente",
        "id_unidade": 1,
        "nome_unidade": "Enfermaria Norte",
        "dia_semana": "TER",
        "turno": "MANHA",
        "id_preceptor": 7,
        "nome_preceptor": "Bruno Preceptor",
        "titulacao_preceptor": "MESTRE",
    }


# ---------------------------------------------------------------------------
# GET /views/estatisticas-mensais -> vw_estatisticas_atendimentos_mensal
# ---------------------------------------------------------------------------


def test_get_estatisticas_mensais(client):
    response = client.get("/views/estatisticas-mensais")
    assert response.status_code == 200
    data = response.json()

    chaves = {(item["mes"][:7], item["id_unidade"]) for item in data}
    assert {("2026-05", 1), ("2026-05", 3), ("2026-06", 1), ("2026-06", 2)}.issubset(chaves)

    unidade1_junho = next(
        item for item in data if item["id_unidade"] == 1 and item["mes"].startswith("2026-06")
    )
    assert unidade1_junho["total_atendimentos"] == 4
    assert unidade1_junho["duracao_media_minutos"] == pytest.approx(42.5)
    assert unidade1_junho["procedimentos_mais_frequentes"][0] == {
        "procedimento": "Aplicacao de medicacao",
        "quantidade": 2,
    }


# ---------------------------------------------------------------------------
# GET /auditoria/atendimentos -> auditoria_atendimento
# ---------------------------------------------------------------------------


def test_get_auditoria_atendimentos_lista_e_filtra_por_atendimento(client):
    response = client.get("/auditoria/atendimentos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert {"id_auditoria", "id_atendimento", "operacao", "usuario", "data_hora"} <= data[0].keys()
    assert all(item["operacao"] in ("INSERT", "UPDATE", "DELETE") for item in data)

    id_atendimento = data[0]["id_atendimento"]
    filtrado = client.get(f"/auditoria/atendimentos?id_atendimento={id_atendimento}")
    assert filtrado.status_code == 200
    assert all(item["id_atendimento"] == id_atendimento for item in filtrado.json())
