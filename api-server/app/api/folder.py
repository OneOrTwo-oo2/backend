from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from db.models import BookmarkFolder, FolderRecipe, Recipe, User, Bookmark
from db.connection import get_db
from utils.jwt_handler import get_current_user_from_cookie
from db.schemas import FolderCreate, FolderOut, FolderRecipeAdd
from typing import List
from fastapi.responses import JSONResponse
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


@router.get("/folders/{folder_id}/recipes")
def get_folder_recipes(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    # 🔥 Bookmark를 조인하여 custom_title 포함
    folder_recipes = (
        db.query(FolderRecipe)
        .join(Recipe, FolderRecipe.recipe_id == Recipe.id)
        .join(Bookmark, (Bookmark.recipe_id == Recipe.id) & (Bookmark.user_id == user.user_id))  # ✅ 북마크와 조인
        .filter(FolderRecipe.folder_id == folder_id)
        .with_entities(
            Recipe.id,
            Recipe.image,
            Recipe.link,
            Recipe.summary,
            Recipe.is_ai_generated,
            Recipe.recommendation_reason,
            Recipe.dietary_tips,
            Bookmark.custom_title,
            Recipe.title  # 원래 제목도 백업용으로
        )
        .all()
    )

    result = []
    for row in folder_recipes:
        result.append({
            "id": row.id,
            "title": row.custom_title or row.title,  # ✅ 사용자 제목 우선
            "image": row.image,
            "summary": row.summary,
            "link": row.link,
            "is_ai_generated": bool(row.is_ai_generated),
            "recommendation_reason": row.recommendation_reason or "",
            "dietary_tips": row.dietary_tips or ""
        })

    return JSONResponse(content=result)


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
