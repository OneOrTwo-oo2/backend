from fastapi import APIRouter
from api import random_recipes, recipe_detail, recipes, recommend, yolo_classes

router = APIRouter()
router.include_router(random_recipes.router)
router.include_router(recipe_detail.router)
router.include_router(recipes.router)
router.include_router(recommend.router)
router.include_router(yolo_classes.router)
