from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import lifespan_db
from app.api.router import router as api_router

app = FastAPI(
    title="Sistema de Gestão Hospitalar Dra. Yuska - API",
    description="API da Etapa 1 para gerenciamento de atendimentos, pacientes, procedimentos e relatórios analíticos utilizando PostgreSQL com SQL puro.",
    version="1.0.0",
    lifespan=lifespan_db
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
