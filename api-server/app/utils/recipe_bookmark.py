# 📁 db/utils.py
from sqlalchemy.orm import Session
from db.models import Recipe

def get_or_create_recipe_id(db: Session, title: str, image: str, summary: str, link: str) -> int:
    recipe = db.query(Recipe).filter_by(link=link).first()
    if recipe:
        return recipe.id

    new_recipe = Recipe(title=title, image=image, summary=summary, link=link)
    db.add(new_recipe)
    db.commit()
    db.refresh(new_recipe)
    return new_recipe.id