"""Testes das três consultas avançadas da issue #10 (`/analytics/preceptores-flamenguistas`,
`/analytics/ultimo-atendimento-por-paciente`, `/analytics/percentual-alto-risco`),
escritas exclusivamente com a DSL do SQLAlchemy.

Ordem alfabética de coleta do `pytest`: este arquivo roda depois de `test_api.py`, que já
mutou o banco (cria um atendimento novo para o paciente 1 em 2026-07-14, exclui o
procedimento PROC-01 do atendimento 1, e cria paciente/residente/preceptor extras sem
vínculo com atendimentos). As asserções abaixo refletem esse estado — não o seed "puro" —
e cada uma referencia explicitamente qual mutação de `test_api.py` está em jogo, para que
uma alteração de ordem de coleta ou de fixtures não deixe os números "certos por acaso".
"""

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/analytics/preceptores-flamenguistas",
        "/analytics/ultimo-atendimento-por-paciente",
        "/analytics/percentual-alto-risco",
    ],
)
def test_endpoints_respondem_200(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_preceptores_flamenguistas_usa_dois_passos_nao_so_o_atendimento_direto(client):
    response = client.get("/analytics/preceptores-flamenguistas")
    assert response.status_code == 200
    data = response.json()
    nomes = {item["preceptor"] for item in data}

    # Pacientes flamenguistas (is_flamengo=TRUE): Carlos (1) e Joao (3). Os residentes que
    # os atenderam em algum atendimento são Felipe (11, atds 1/5), Gabriela (12, atd 3) e
    # Iris (14, atd 7). Diego Preceptor (9) e Elena Preceptora (10) nunca supervisionaram
    # diretamente um atendimento a esses pacientes — mas supervisionaram Felipe/Gabriela em
    # *outros* atendimentos (9 e 10) — então só aparecem por causa da leitura em dois
    # passos do enunciado (residentes que atenderam flamenguistas -> preceptores desses
    # residentes), documentada em `preceptores_flamenguistas`.
    assert nomes == {
        "Ana Preceptora",
        "Bruno Preceptor",
        "Diego Preceptor",
        "Elena Preceptora",
    }
    # Clara Preceptora (8) e o "Preceptor Teste" (criado por test_api.py) não supervisionam
    # nenhum residente desse conjunto.
    assert "Clara Preceptora" not in nomes
    assert data == sorted(data, key=lambda item: item["preceptor"])


def test_ultimo_atendimento_por_paciente_traz_o_mais_recente_com_procedimentos(client):
    response = client.get("/analytics/ultimo-atendimento-por-paciente")
    assert response.status_code == 200
    data = response.json()
    por_paciente = {item["paciente"]: item for item in data}

    assert set(por_paciente) == {
        "Carlos Paciente",
        "Maria Paciente",
        "Joao Paciente",
        "Lucia Paciente",
        "Pedro SemRiscoAlto",
    }

    # test_create_atendimento_validation (test_api.py) cria um atendimento novo para Carlos
    # em 2026-07-14, mais recente que o atendimento 5 do seed (2026-06-06) — e sem nenhum
    # procedimento realizado associado.
    carlos = por_paciente["Carlos Paciente"]
    assert carlos["data_hora"] == "2026-07-14T10:00:00"
    assert carlos["residente"] == "Felipe Residente"
    assert carlos["preceptor"] == "Ana Preceptora"
    assert carlos["procedimentos"] == []

    # Maria: atendimento 6 do seed (2026-06-07), não afetado pelas mutações de test_api.py.
    maria = por_paciente["Maria Paciente"]
    assert maria["data_hora"] == "2026-06-07T15:00:00"
    assert maria["residente"] == "Hugo Residente"
    assert maria["preceptor"] == "Ana Preceptora"
    assert maria["procedimentos"] == ["Sutura simples"]

    # Joao: atendimento 7 do seed (2026-06-10), com procedimento de risco ALTO.
    joao = por_paciente["Joao Paciente"]
    assert joao["data_hora"] == "2026-06-10T08:30:00"
    assert joao["residente"] == "Iris Residente"
    assert joao["preceptor"] == "Bruno Preceptor"
    assert joao["procedimentos"] == ["Punção lombar"]

    # Pedro SemRiscoAlto: atendimento 10 do seed (2026-05-20), o mais recente dele.
    pedro = por_paciente["Pedro SemRiscoAlto"]
    assert pedro["data_hora"] == "2026-05-20T16:00:00"
    assert pedro["residente"] == "Gabriela Residente"
    assert pedro["preceptor"] == "Elena Preceptora"
    assert pedro["procedimentos"] == ["Sutura simples"]


def test_percentual_alto_risco_calcula_por_residente_e_exclui_quem_nao_tem_procedimento(
    client,
):
    response = client.get("/analytics/percentual-alto-risco")
    assert response.status_code == 200
    data = response.json()
    por_residente = {item["residente"]: item for item in data}

    # Jonas Residente (15) só tem o atendimento 8, que no seed não tem nenhuma linha em
    # procedimento_realizado (documentado em db/05_seed.sql) — decisão de design: ele fica
    # DE FORA do resultado em vez de aparecer com 0%, para não sugerir uma taxa que ele não
    # chegou a demonstrar. Ver docstring de `percentual_alto_risco_por_residente`.
    assert "Jonas Residente" not in por_residente

    # "Residente Teste" (criado por test_api.py) também não tem nenhum atendimento.
    assert "Residente Teste" not in por_residente

    # Iris (14): 1 procedimento realizado no atendimento 7, e é ALTO -> 100%.
    assert por_residente["Iris Residente"] == {
        "residente": "Iris Residente",
        "total_procedimentos": 1,
        "total_alto_risco": 1,
        "percentual_alto_risco": 100.0,
    }

    # Gabriela (12): atendimentos 3 (ALTO), 4 (ALTO) e 10 (MEDIO) -> 2/3.
    assert por_residente["Gabriela Residente"] == {
        "residente": "Gabriela Residente",
        "total_procedimentos": 3,
        "total_alto_risco": 2,
        "percentual_alto_risco": pytest.approx(66.6666667),
    }

    # Hugo (13): atendimentos 5 (BAIXO) e 6 (MEDIO) -> nenhum ALTO.
    assert por_residente["Hugo Residente"] == {
        "residente": "Hugo Residente",
        "total_procedimentos": 2,
        "total_alto_risco": 0,
        "percentual_alto_risco": 0.0,
    }

    # Felipe (11): test_delete_procedimento_realizado_validation (test_api.py) excluiu o
    # procedimento PROC-01 do atendimento 1, deixando só o PROC-03 (MEDIO) dele; somado ao
    # BAIXO do atendimento 2 e ao BAIXO do atendimento 9, e ao novo atendimento sem
    # procedimento criado por test_create_atendimento_validation -> total 3, nenhum ALTO.
    assert por_residente["Felipe Residente"] == {
        "residente": "Felipe Residente",
        "total_procedimentos": 3,
        "total_alto_risco": 0,
        "percentual_alto_risco": 0.0,
    }

    # Ordenado por percentual desc, nome asc.
    assert data == sorted(
        data, key=lambda item: (-item["percentual_alto_risco"], item["residente"])
    )
