from fastapi import APIRouter

from app.api import (
    analytics,
    atendimentos,
    auditoria,
    escalas,
    internacoes,
    pacientes,
    preceptores,
    procedimentos,
    residentes,
    unidades,
    views,
)

router = APIRouter()
router.include_router(pacientes.router)
router.include_router(residentes.router)
router.include_router(preceptores.router)
router.include_router(unidades.router)
router.include_router(atendimentos.router)
router.include_router(procedimentos.router)
router.include_router(analytics.router)
router.include_router(escalas.router)
router.include_router(views.router)
router.include_router(internacoes.router)
router.include_router(auditoria.router)
