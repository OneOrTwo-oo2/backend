from fastapi import APIRouter
from api import random_recipes, recipe_detail, recipes, recommend, ingredients, auth_router,bookmark,folder,preferences

router = APIRouter()
router.include_router(random_recipes.router)
router.include_router(recipe_detail.router)
router.include_router(recipes.router)
router.include_router(recommend.router)
router.include_router(auth_router.router,prefix="/api")
router.include_router(ingredients.router)
router.include_router(bookmark.router,prefix="/api")
router.include_router(folder.router, prefix="/api")
router.include_router(preferences.router, prefix="/api", tags=["preferences"])
