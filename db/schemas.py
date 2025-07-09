from pydantic import BaseModel
from typing import List

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
