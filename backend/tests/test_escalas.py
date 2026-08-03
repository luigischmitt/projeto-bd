import psycopg
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_list_escalas(client):
    response = client.get("/escalas")
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 7

    escala = next(item for item in data if item["id_escala"] == 1)
    assert escala["dia_semana"] == "SEG"
    assert escala["turno"] == "MANHA"
    assert escala["nome_unidade"] == "Enfermaria Norte"
    assert escala["id_residente"] == 11
    assert escala["id_preceptor"] == 6
    assert escala["nome_residente"]
    assert escala["nome_preceptor"]


def test_list_escalas_nao_e_subconjunto_da_view_de_supervisao(client):
    """A tela de Escalas consumia `vw_residentes_sem_supervisor` por falta de endpoint
    próprio, exibindo só os plantões cujo preceptor não é doutor. Este teste fixa a
    correção: a listagem cobre a grade inteira, não aquele subconjunto."""
    escalas = client.get("/escalas").json()
    sem_supervisor = client.get("/views/residentes-sem-supervisor").json()

    assert len(escalas) > len(sem_supervisor)
