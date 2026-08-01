from fastapi import APIRouter

from app.api import analytics, atendimentos, pacientes, preceptores, residentes, unidades

router = APIRouter()
router.include_router(pacientes.router)
router.include_router(residentes.router)
router.include_router(preceptores.router)
router.include_router(unidades.router)
router.include_router(atendimentos.router)
router.include_router(analytics.router)
