# routes/bookmark_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from db.connection import get_db
from db.models import Bookmark, Recipe, FolderRecipe
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
            # 새 레시피 생성
            recipe = Recipe(
                title=data.title,
                image=data.image,
                summary=data.summary,
                link=data.link,
                is_ai_generated=int(data.is_ai_generated),
                recommendation_reason=data.recommendation_reason,
                dietary_tips=data.dietary_tips
            )
            db.add(recipe)
            db.commit()
            db.refresh(recipe)
        else:
            # ✅ Watson 추천이면 기존 레시피 필드 업데이트
            updated = False
            if data.is_ai_generated and recipe.is_ai_generated == 0:
                recipe.is_ai_generated = 1
                updated = True
            if data.recommendation_reason and not recipe.recommendation_reason:
                recipe.recommendation_reason = data.recommendation_reason
                updated = True
            if data.dietary_tips and not recipe.dietary_tips:
                recipe.dietary_tips = data.dietary_tips
                updated = True
            if updated:
                db.add(recipe)
                db.commit()
                db.refresh(recipe)

        # 북마크 중복 체크
        existing = db.query(Bookmark).filter_by(user_id=user.user_id, recipe_id=recipe.id).first()
        if existing:
            return {"message": "이미 북마크됨", "recipe_id": recipe.id}

        # 북마크 생성
        bookmark = Bookmark(
                                user_id=user.user_id,
                                recipe_id=recipe.id,
                                custom_title=data.custom_title  # ✅ 사용자 정의 제목 저장
                            )
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
                title=b.custom_title or b.recipe.title,
                image=b.recipe.image,
                summary=b.recipe.summary,
                link=b.recipe.link,
                is_ai_generated=bool(b.recipe.is_ai_generated),
                recommendation_reason=b.recipe.recommendation_reason or "",
                dietary_tips=b.recipe.dietary_tips or "",
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

        # ✅ 폴더에서 연결된 레시피도 제거
        db.query(FolderRecipe).filter_by(recipe_id=recipeId).delete()

        db.delete(bookmark)
        db.commit()
        return {"message": "북마크가 삭제되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

@router.delete("/bookmarks/all")
def delete_all_bookmarks(
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        bookmarks = db.query(Bookmark).filter_by(user_id=user.user_id).all()
        for b in bookmarks:
            db.delete(b)
        db.commit()
        return {"message": "모든 북마크가 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"전체 삭제 실패: {str(e)}")
    
# 북마크 타이틀 업데이트!
@router.put("/bookmark/title")
def update_bookmark_title(
    recipeId: int,
    new_title: str,
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    bookmark = db.query(Bookmark).filter_by(user_id=user.user_id, recipe_id=recipeId).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="북마크가 존재하지 않습니다.")

    bookmark.custom_title = new_title
    db.commit()
    return {"message": "제목이 업데이트되었습니다."}
