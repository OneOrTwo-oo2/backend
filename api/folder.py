# ✅ 폴더 라우터 (R2R 기반 인증 적용)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db.models import BookmarkFolder, FolderRecipe, User, Recipe
from db.connection import get_db
from utils.jwt_handler import get_current_user_from_cookie  # ✅ 쿠키 기반 인증
from pydantic import BaseModel
from typing import List

router = APIRouter()

# 📁 폴더 생성
class FolderCreate(BaseModel):
    name: str

@router.post("/folders")
def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = BookmarkFolder(user_id=user.user_id, name=data.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return {"id": folder.id, "name": folder.name}


# 📁 유저의 폴더 목록 조회
@router.get("/folders")
def get_user_folders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folders = db.query(BookmarkFolder).filter(BookmarkFolder.user_id == user.user_id).all()
    return folders


# 📌 폴더에 레시피 추가
class FolderRecipeAdd(BaseModel):
    recipe_id: int

@router.post("/folders/{folder_id}/recipes")
def add_recipe_to_folder(
    folder_id: int,
    data: FolderRecipeAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="❌ 폴더를 찾을 수 없습니다.")

    exists = db.query(FolderRecipe).filter_by(folder_id=folder_id, recipe_id=data.recipe_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="⚠️ 이미 폴더에 추가된 레시피입니다.")

    folder_recipe = FolderRecipe(folder_id=folder_id, recipe_id=data.recipe_id)
    db.add(folder_recipe)
    db.commit()
    return {"message": "✅ 레시피가 폴더에 성공적으로 추가되었습니다."}


# 📂 폴더 내 레시피 리스트
@router.get("/folders/{folder_id}/recipes")
def get_folder_recipes(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="❌ 폴더를 찾을 수 없습니다.")

    recipes = db.query(Recipe).join(FolderRecipe).filter(FolderRecipe.folder_id == folder_id).all()
    return recipes


# ❌ 폴더에서 레시피 제거
@router.delete("/folders/{folder_id}/recipes/{recipe_id}")
def remove_recipe_from_folder(
    folder_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="❌ 폴더를 찾을 수 없습니다.")

    folder_recipe = db.query(FolderRecipe).filter_by(folder_id=folder_id, recipe_id=recipe_id).first()
    if not folder_recipe:
        raise HTTPException(status_code=404, detail="❌ 해당 레시피는 폴더에 없습니다.")

    db.delete(folder_recipe)
    db.commit()
    return {"message": "🗑️ 레시피가 폴더에서 삭제되었습니다."}


# ❌ 폴더 삭제
@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    folder = db.query(BookmarkFolder).filter_by(id=folder_id, user_id=user.user_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="❌ 폴더를 찾을 수 없습니다.")

    db.delete(folder)
    db.commit()
    return {"message": "🗑️ 폴더가 삭제되었습니다."}
