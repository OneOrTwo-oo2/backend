from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from db.connection import get_db
from utils.recipe_service import fetch_recipes_from_10000recipe

router = APIRouter()

@router.get("/recipes")
def get_recipes(
    ingredients: Optional[List[str]] = Query(None),
    kind: Optional[str] = None,
    situation: Optional[str] = None,
    method: Optional[str] = None,
    theme: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return fetch_recipes_from_10000recipe(
        db,
        ingredients=ingredients,
        kind=kind,
        situation=situation,
        method=method,
        theme=theme
    )
