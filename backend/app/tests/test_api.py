import pytest
from fastapi.testclient import TestClient
from app.main import app
import psycopg

# Função auxiliar para verificar se o banco de dados está online e respondendo
def is_db_accessible():
    from app.db import settings
    try:
        with psycopg.connect(settings.DATABASE_URL) as conn:
            return True
    except Exception:
        return False

# Pula todos os testes de integração se o banco de dados não estiver online
pytestmark = pytest.mark.skipif(
    not is_db_accessible(),
    reason="O banco de dados PostgreSQL local não está acessível no DATABASE_URL configurado."
)

@pytest.fixture(scope="module")
def client():
    # O uso do gerenciador de contexto 'with' garante a execução do lifespan do FastAPI
    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Bem-vindo" in response.json()["message"]

# --- TESTES DE ANÁLISE (REQUISITO 4) ---

def test_analytics_ranking_residentes(client):
    response = client.get("/analytics/ranking-residentes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # O ranking deve listar os residentes e os totais de atendimentos
    assert "residente" in data[0]
    assert "total_atendimentos" in data[0]
    # Felipe Residente é o 11
    assert any(item["residente"] == "Felipe Residente" for item in data)

def test_analytics_preceptores_supervisao(client):
    # Ana Preceptora (id=6) tem 6 supervisões em junho de 2026 no seed (>5)
    response = client.get("/analytics/preceptores-supervisao?mes=2026-06")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["preceptor"] == "Ana Preceptora"
    assert data[0]["total_supervisoes"] == 6

    # Teste de validação de mês inválido
    response = client.get("/analytics/preceptores-supervisao?mes=2026-13")
    assert response.status_code == 400

def test_analytics_plantoes_por_unidade(client):
    response = client.get("/analytics/plantoes-por-unidade")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "unidade" in data[0]
    assert "residente" in data[0]
    assert "plantoes" in data[0]

def test_analytics_pacientes_sem_risco_alto(client):
    # Pedro SemRiscoAlto (id=5) só tem procedimentos de risco BAIXO/MEDIO, logo deve aparecer na lista
    response = client.get("/analytics/pacientes-sem-risco-alto")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(p["nome"] == "Pedro SemRiscoAlto" for p in data)


# --- TESTES DE CRUD (REQUISITO 3) ---

def test_list_pacientes(client):
    response = client.get("/pacientes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert "nome" in data[0]
    assert "id_pessoa" in data[0]

def test_list_residentes(client):
    response = client.get("/residentes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert "ano_residencia" in data[0]

def test_list_preceptores(client):
    response = client.get("/preceptores")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert "titulacao" in data[0]

def test_list_atendimentos(client):
    response = client.get("/atendimentos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    assert "nome_paciente" in data[0]
    assert "id_paciente" in data[0]

def test_get_paciente_atendimentos(client):
    # Paciente Carlos (id=1)
    response = client.get("/pacientes/1/atendimentos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Deve estar ordenado por data_hora
    datas = [item["data_hora"] for item in data]
    assert datas == sorted(datas)

    # Paciente inexistente
    response = client.get("/pacientes/999/atendimentos")
    assert response.status_code == 404

def test_get_atendimento_procedimentos(client):
    # Atendimento 1
    response = client.get("/atendimentos/1/procedimentos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "codigo" in data[0]
    assert "nome_procedimento" in data[0]
    assert "faturado" in data[0]
    assert "quantidade" in data[0]

    # Atendimento inexistente
    response = client.get("/atendimentos/999/procedimentos")
    assert response.status_code == 404

def test_update_paciente(client):
    update_payload = {
        "nome": "Carlos Paciente",
        "cpf": "11111111111",
        "data_nascimento": "1990-01-10",
        "is_flamengo": True,
        "telefone": "83990000001",
        "num_convenio": "TEST-CONV-NEW",
        "alergias": "Nenhuma conhecida",
        "grupo_sanguineo": "O-"
    }
    response = client.put("/pacientes/1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["num_convenio"] == "TEST-CONV-NEW"
    assert data["alergias"] == "Nenhuma conhecida"
    assert data["grupo_sanguineo"] == "O-"
    assert data["nome"] == "Carlos Paciente"

    response = client.put("/pacientes/999", json=update_payload)
    assert response.status_code == 404


def test_create_paciente(client):
    payload = {
        "nome": "Novo Paciente Teste",
        "cpf": "99988877766",
        "data_nascimento": "1995-05-20",
        "is_flamengo": False,
        "telefone": "83991112222",
        "num_convenio": "CONV-TEST",
        "alergias": "Nenhuma",
        "grupo_sanguineo": "A+"
    }
    response = client.post("/pacientes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Novo Paciente Teste"
    assert data["id_pessoa"] is not None


def test_create_residente(client):
    payload = {
        "nome": "Residente Teste",
        "cpf": "88877766655",
        "data_nascimento": "1998-03-10",
        "is_flamengo": True,
        "telefone": "83992223333",
        "crm": "CRM-PB-9999",
        "data_admissao": "2025-01-01",
        "especialidade": "Clinica Medica",
        "ano_residencia": "R1"
    }
    response = client.post("/residentes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Residente Teste"
    assert data["ano_residencia"] == "R1"


def test_create_preceptor(client):
    payload = {
        "nome": "Preceptor Teste",
        "cpf": "77766655544",
        "data_nascimento": "1975-08-15",
        "is_flamengo": False,
        "telefone": "83993334444",
        "crm": "CRM-PB-8888",
        "data_admissao": "2010-06-01",
        "especialidade": "Pediatria",
        "titulacao": "Doutor"
    }
    response = client.post("/preceptores", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Preceptor Teste"
    assert data["titulacao"] == "Doutor"

def test_delete_procedimento_realizado_validation(client):
    # Tenta remover procedimento faturado = TRUE (PROC-03 no atendimento 1) -> deve dar 400
    response = client.delete("/atendimentos/1/procedimentos/PROC-03")
    assert response.status_code == 400
    assert "já foi faturado" in response.json()["detail"]

    # Tenta remover procedimento inexistente no atendimento -> deve dar 404
    response = client.delete("/atendimentos/1/procedimentos/PROC-99")
    assert response.status_code == 404

    # Tenta remover procedimento faturado = FALSE (PROC-01 no atendimento 1) -> deve dar 204
    response = client.delete("/atendimentos/1/procedimentos/PROC-01")
    assert response.status_code == 204

def test_create_atendimento_validation(client):
    # Inserção válida
    payload = {
        "data_hora": "2026-07-14T10:00:00",
        "duracao_minutos": 45,
        "id_paciente": 1,
        "id_residente": 11,
        "id_preceptor": 6
    }
    response = client.post("/atendimentos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id_atendimento"] is not None
    
    # Inserção com paciente inválido -> deve dar 400
    payload["id_paciente"] = 999
    response = client.post("/atendimentos", json=payload)
    assert response.status_code == 400
    assert "Paciente com id_pessoa 999 não existe" in response.json()["detail"]

def test_get_tempo_medio_residentes(client):
    response = client.get("/residentes/tempo-medio")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "id_residente" in data[0]
    assert "tempo_medio_minutos" in data[0]
