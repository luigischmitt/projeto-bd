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
