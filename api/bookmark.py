# ✅ 북마크 라우터 (R2R 기반 인증 적용)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.connection import get_db
from db.models import Bookmark, Recipe
from utils.jwt_handler import get_current_user_from_cookie

router = APIRouter()

# 📌 북마크 등록 요청 형식
class BookmarkCreate(BaseModel):
    title: str
    image: str
    summary: str = ""
    link: str


# ✅ 북마크 생성 (레시피까지 저장)
@router.post("/bookmark-with-recipe")
def add_bookmark_with_recipe(
    data: BookmarkCreate,
    user = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        recipe = db.query(Recipe).filter_by(link=data.link).first()

        if not recipe:
            recipe = Recipe(
                title=data.title,
                image=data.image,
                summary=data.summary,
                link=data.link
            )
            db.add(recipe)
            db.commit()
            db.refresh(recipe)

        existing = db.query(Bookmark).filter_by(user_id=user.user_id, recipe_id=recipe.id).first()
        if existing:
            return {"message": "이미 북마크됨", "recipe_id": recipe.id}

        bookmark = Bookmark(user_id=user.user_id, recipe_id=recipe.id)
        db.add(bookmark)
        db.commit()
        return {"message": "북마크 완료!", "recipe_id": recipe.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"북마크 실패: {str(e)}")


# ✅ 내 북마크 목록 조회
@router.get("/bookmarks")
def get_bookmarks(
    user = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        bookmarks = db.query(Bookmark).filter_by(user_id=user.user_id).all()
        result = []
        for b in bookmarks:
            recipe = db.query(Recipe).filter_by(id=b.recipe_id).first()
            if recipe:
                result.append({
                    "id": recipe.id,
                    "title": recipe.title,
                    "image": recipe.image,
                    "summary": recipe.summary,
                    "link": recipe.link,
                })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# ✅ 북마크 삭제 (userId 제거)
@router.delete("/bookmark")
def delete_bookmark(
    recipeId: int,
    user = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        bookmark = db.query(Bookmark).filter_by(user_id=user.user_id, recipe_id=recipeId).first()
        if not bookmark:
            raise HTTPException(status_code=404, detail="북마크가 존재하지 않습니다.")

        db.delete(bookmark)
        db.commit()
        return {"message": "북마크가 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")
