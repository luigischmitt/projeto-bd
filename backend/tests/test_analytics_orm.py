"""Testes dos quatro analíticos da Etapa 1 reescritos com a DSL do SQLAlchemy, e do
analítico novo `tempo-medio-espera` (issue #9).

Este arquivo é colecionado antes de `test_api.py` (ordem alfabética de `pytest`), então
roda contra o banco ainda intocado pelo seed — os valores exatos abaixo espelham os
mesmos usados nos testes originais da Etapa 1 (agora migrados daqui) e no docstring de
`test_calcular_tempo_medio_espera_bate_com_calculo_manual_do_seed`
(`backend/tests/test_procedures.py`), então uma regressão na migração da DSL (paths e
contratos de resposta inalterados) fica visível aqui sem depender de mutações de outros
arquivos de teste.
"""

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/analytics/ranking-residentes",
        "/analytics/preceptores-supervisao?mes=2026-06",
        "/analytics/plantoes-por-unidade",
        "/analytics/pacientes-sem-risco-alto",
        "/analytics/tempo-medio-espera",
    ],
)
def test_endpoints_respondem_200(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ranking_residentes_conta_atendimentos_por_residente(client):
    response = client.get("/analytics/ranking-residentes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert {"residente", "total_atendimentos"} <= data[0].keys()

    por_residente = {item["residente"]: item["total_atendimentos"] for item in data}
    # Felipe Residente (id 11) aparece nos atendimentos 1, 2 e 9 do seed.
    assert por_residente["Felipe Residente"] == 3
    # Ordenado por total desc, nome asc — ninguém com total maior que o primeiro.
    assert data == sorted(data, key=lambda i: (-i["total_atendimentos"], i["residente"]))


def test_preceptores_supervisao_filtra_por_mes_e_aplica_having(client):
    response = client.get("/analytics/preceptores-supervisao?mes=2026-06")
    assert response.status_code == 200
    data = response.json()
    # Ana Preceptora (id 6) supervisiona os atendimentos 1-6 de junho/2026: 6 > 5.
    assert len(data) == 1
    assert data[0] == {"preceptor": "Ana Preceptora", "total_supervisoes": 6}

    response = client.get("/analytics/preceptores-supervisao?mes=2026-05")
    assert response.status_code == 200
    # Nenhum preceptor supervisiona mais de 5 atendimentos em maio/2026 no seed.
    assert response.json() == []

    response = client.get("/analytics/preceptores-supervisao?mes=2026-13")
    assert response.status_code == 400


def test_plantoes_por_unidade_agrega_escalas_vigentes(client):
    response = client.get("/analytics/plantoes-por-unidade")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert {"unidade", "residente", "plantoes"} <= data[0].keys()
    # Felipe Residente tem 2 escalas na Enfermaria Norte (SEG/MANHA e TER/MANHA).
    linha_felipe_enfermaria = [
        item
        for item in data
        if item["residente"] == "Felipe Residente" and item["unidade"] == "Enfermaria Norte"
    ]
    assert linha_felipe_enfermaria == [
        {"unidade": "Enfermaria Norte", "residente": "Felipe Residente", "plantoes": 2}
    ]


def test_pacientes_sem_risco_alto_exclui_quem_tem_procedimento_alto(client):
    response = client.get("/analytics/pacientes-sem-risco-alto")
    assert response.status_code == 200
    data = response.json()
    nomes = {item["nome"] for item in data}
    # Pedro SemRiscoAlto (id 5) só tem procedimentos BAIXO/MEDIO no seed.
    assert "Pedro SemRiscoAlto" in nomes
    # Joao Paciente (id 3) tem o procedimento PROC-04 (ALTO) no atendimento 3.
    assert "Joao Paciente" not in nomes


def test_tempo_medio_espera_bate_com_o_calculo_documentado_do_seed(client):
    response = client.get("/analytics/tempo-medio-espera")
    assert response.status_code == 200
    data = response.json()
    por_unidade = {item["id_unidade"]: item["tempo_medio_espera_minutos"] for item in data}
    assert por_unidade == {1: 18.0, 2: pytest.approx(18.33), 3: 15.0}
