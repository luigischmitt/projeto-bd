from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A issue #9 migrou os últimos endpoints (analíticos) que ainda dependiam do pool
    # psycopg cru (`app/core/database.py`, removido nesta issue). A aplicação é 100%
    # SQLAlchemy a partir daqui: `engine` não precisa de setup explícito de conexão —
    # ela abre conexões sob demanda e é apenas descartada (`dispose`) no shutdown.
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="Sistema de Gestão Hospitalar Dra. Yuska - API",
    description="API para gerenciamento de atendimentos, pacientes, procedimentos e relatórios analíticos.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bem-vindo à API do Sistema de Gestão Hospitalar Dra. Yuska!",
        "docs_url": "/docs"
    }
