from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import lifespan_db
from app.db.session import engine
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # O pool psycopg (SQL cru) e a engine SQLAlchemy convivem de propósito nesta issue
    # (#7): os repositories em `app/repositories/` ainda usam `get_db`/pool e só migram
    # para a DSL do SQLAlchemy nas issues #8 e #9. Remover o pool agora quebraria a
    # aplicação. `engine` não precisa de setup explícito de conexão aqui — ela abre
    # conexões sob demanda e é apenas descartada (`dispose`) no shutdown.
    async with lifespan_db(app):
        try:
            yield
        finally:
            await engine.dispose()


app = FastAPI(
    title="Sistema de Gestão Hospitalar Dra. Yuska - API",
    description="API da Etapa 1 para gerenciamento de atendimentos, pacientes, procedimentos e relatórios analíticos utilizando PostgreSQL com SQL puro.",
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
