from pydantic import BaseModel
from typing import List, Optional

# 알러지 스키마 검증
class AllergyOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# 질환정보 스키마 검증
class DiseaseOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# 프론트에서 선택한 질환, 알러지 검증
class PreferenceIn(BaseModel):
    allergies: List[str] = []
    diseases: List[str] = []

# 북마크 생성

class BookmarkCreate(BaseModel):
    title: str
    image: str
    summary: Optional[str] = ""
    link: str
    is_ai_generated: Optional[bool] = False
    recommendation_reason: Optional[str] = None  # ✅ 추가
    dietary_tips: Optional[str] = None           # ✅ 추가
    custom_title: Optional[str] = None  # ✅ 추가


# 북마크 응답 (레시피 정보 포함)
class BookmarkOut(BaseModel):
    id: int
    title: str
    image: str
    summary: Optional[str]
    link: str
    is_ai_generated: bool
    recommendation_reason: Optional[str] = ""
    dietary_tips: Optional[str] = ""
    custom_title: Optional[str] = None  # ✅ 추가

    class Config:
        orm_mode = True

# 폴더 생성 요청
class FolderCreate(BaseModel):
    name: str


# 폴더 응답
class FolderOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# 레시피 추가 요청
class FolderRecipeAdd(BaseModel):
    recipe_id: int

