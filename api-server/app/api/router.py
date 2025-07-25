from fastapi import APIRouter
from api import random_recipes,recipe_detail,recipes,auth_router,bookmark,folder,preferences

router = APIRouter()
router.include_router(random_recipes.router,prefix="/api")
router.include_router(recipe_detail.router,prefix="/api")
router.include_router(recipes.router,prefix="/api")
router.include_router(auth_router.router,prefix="/api")
router.include_router(bookmark.router,prefix="/api")
router.include_router(folder.router, prefix="/api")
router.include_router(preferences.router, prefix="/api", tags=["preferences"])
