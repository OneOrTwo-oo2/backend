# api/bookmark.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.connection import get_db
from db.models import Bookmark, Recipe

router = APIRouter()

class BookmarkCreate(BaseModel):
    user_id: int
    title: str
    image: str
    summary: str = ""
    link: str

# db에서 조회 후 새로운 레시피라면 추가하는 엔드포인트
@router.post("/bookmark-with-recipe")
def add_bookmark_with_recipe(data: BookmarkCreate, db: Session = Depends(get_db)):
    try:
        # 1. 레시피가 DB에 이미 있는지 확인
        recipe = db.query(Recipe).filter_by(link=data.link).first()

        # 2. 없으면 새로 저장
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

        # 3. 북마크 저장
        bookmark = Bookmark(user_id=data.user_id, recipe_id=recipe.id)
        db.add(bookmark)
        db.commit()
        return {"message": "북마크 완료!", "recipe_id": recipe.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"북마크 실패: {str(e)}")

# 사용자 북마크 조회용 엔드포인트 추가
@router.get("/bookmarks")
def get_bookmarks(userId: int, db: Session = Depends(get_db)):
    try:
        bookmarks = db.query(Bookmark).filter_by(user_id=userId).all()
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

# 북마크 삭제용 엔드포인트
@router.delete("/bookmark")
def delete_bookmark(userId: int, recipeId: int, db: Session = Depends(get_db)):
    try:
        # filter()를 사용하여 명시적으로 필터링
        bookmark = db.query(Bookmark).filter(Bookmark.user_id == userId, Bookmark.recipe_id == recipeId).first()

        if not bookmark:
            raise HTTPException(status_code=404, detail="북마크가 존재하지 않습니다.")

        db.delete(bookmark)
        db.commit()
        return {"message": "북마크가 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

