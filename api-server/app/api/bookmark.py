# routes/bookmark_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from db.connection import get_db
from db.models import Bookmark, Recipe
from utils.jwt_handler import get_current_user_from_cookie
from db.schemas import BookmarkCreate, BookmarkOut

router = APIRouter()


# ✅ 북마크 생성 (레시피까지 저장)
@router.post("/bookmark-with-recipe")
def add_bookmark_with_recipe(
    data: BookmarkCreate,
    user=Depends(get_current_user_from_cookie),
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


# ✅ 북마크 목록 조회
@router.get("/bookmarks", response_model=list[BookmarkOut])
def get_bookmarks(
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        bookmarks = (
            db.query(Bookmark)
            .filter_by(user_id=user.user_id)
            .options(joinedload(Bookmark.recipe))  # ✅ 성능 최적화
            .all()
        )

        return [
            BookmarkOut(
                id=b.recipe.id,
                title=b.recipe.title,
                image=b.recipe.image,
                summary=b.recipe.summary,
                link=b.recipe.link
            )
            for b in bookmarks if b.recipe
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# ✅ 북마크 삭제
@router.delete("/bookmark")
def delete_bookmark(
    recipeId: int,
    user=Depends(get_current_user_from_cookie),
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
