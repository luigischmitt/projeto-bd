from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import lifespan_db
from app.crud import router as crud_router
from app.analytics import router as analytics_router

app = FastAPI(
    title="Sistema de Gestão Hospitalar Dra. Yuska - API",
    description="API da Etapa 1 para gerenciamento de atendimentos, pacientes, procedimentos e relatórios analíticos utilizando PostgreSQL com SQL puro.",
    version="1.0.0",
    lifespan=lifespan_db
)

# Configuração de CORS para permitir conexões do frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens em desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas
app.include_router(crud_router, tags=["CRUD"])
app.include_router(analytics_router, tags=["Analytics"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bem-vindo à API do Sistema de Gestão Hospitalar Dra. Yuska!",
        "docs_url": "/docs"
    }
