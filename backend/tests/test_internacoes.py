def test_create_internacao(client):
    response = client.post(
        "/internacoes",
        json={"id_paciente": 5, "id_unidade": 1},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id_paciente"] == 5
    assert data["id_unidade"] == 1
    assert data["data_hora_saida"] is None

    views = client.get("/views/pacientes-internados")
    assert views.status_code == 200
    assert any(row["id_paciente"] == 5 for row in views.json())


def test_create_internacao_paciente_ja_internado(client):
    response = client.post(
        "/internacoes",
        json={"id_paciente": 2, "id_unidade": 1},
    )
    assert response.status_code == 400
    assert "internação em curso" in response.json()["detail"]


def test_create_internacao_paciente_inexistente(client):
    response = client.post(
        "/internacoes",
        json={"id_paciente": 9999, "id_unidade": 1},
    )
    assert response.status_code == 400


def test_dar_alta_internacao(client):
    response = client.patch("/internacoes/3/alta", json={})
    assert response.status_code == 200
    assert response.json()["data_hora_saida"] is not None

    views = client.get("/views/pacientes-internados")
    assert not any(row["id_paciente"] == 3 for row in views.json())


def test_dar_alta_internacao_ja_encerrada(client):
    response = client.patch("/internacoes/1/alta", json={})
    assert response.status_code == 400
    assert "encerrada" in response.json()["detail"]


def test_dar_alta_internacao_inexistente(client):
    response = client.patch("/internacoes/9999/alta", json={})
    assert response.status_code == 404
