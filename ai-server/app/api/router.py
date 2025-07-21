from fastapi import APIRouter
from api import ingredients, recommend

router = APIRouter()
router.include_router(ingredients.router,prefix='/ai')
router.include_router(recommend.router,prefix='/ai')