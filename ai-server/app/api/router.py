from fastapi import APIRouter
from api import ingredients, recommend

router = APIRouter()
router.include_router(ingredients.router)
router.include_router(recommend.router)