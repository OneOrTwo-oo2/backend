from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.models import BookmarkFolder, FolderRecipe, Recipe, User
from db.connection import get_db
from utils.jwt_handler import get_current_user_from_cookie
from db.schemas import FolderCreate, FolderOut, FolderRecipeAdd, RecipeOut
from typing import List

router = APIRouter()


@router.post("/folders", response_model=FolderOut)
def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = BookmarkFolder(user_id=user.user_id, name=data.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/folders", response_model=List[FolderOut])
def get_user_folders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folders = db.query(BookmarkFolder).filter_by(user_id=user.user_id).all()
    return folders


@router.post("/folders/{folder_id}/recipes")
def add_recipe_to_folder(
    folder_id: int,
    data: FolderRecipeAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    exists = db.query(FolderRecipe).filter_by(folder_id=folder_id, recipe_id=data.recipe_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 추가된 레시피입니다.")

    db.add(FolderRecipe(folder_id=folder_id, recipe_id=data.recipe_id))
    db.commit()
    return {"message": "레시피가 폴더에 추가되었습니다."}


@router.get("/folders/{folder_id}/recipes", response_model=List[RecipeOut])
def get_folder_recipes(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    recipes = (
        db.query(Recipe)
        .join(FolderRecipe, FolderRecipe.recipe_id == Recipe.id)
        .filter(FolderRecipe.folder_id == folder_id)
        .all()
    )
    return recipes


@router.delete("/folders/{folder_id}/recipes/{recipe_id}")
def remove_recipe_from_folder(
    folder_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    folder_recipe = db.query(FolderRecipe).filter_by(folder_id=folder_id, recipe_id=recipe_id).first()
    if not folder_recipe:
        raise HTTPException(status_code=404, detail="해당 레시피는 폴더에 없습니다.")

    db.delete(folder_recipe)
    db.commit()
    return {"message": "레시피가 폴더에서 삭제되었습니다."}


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    db.delete(folder)
    db.commit()
    return {"message": "폴더가 삭제되었습니다."}
