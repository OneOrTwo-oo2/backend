from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.connection import get_db
from db.models import Allergy, ChronicDisease, User, UserAllergy, UserDisease
from db.schemas import AllergyOut, DiseaseOut, PreferenceIn
from utils.jwt_handler import get_current_user_from_cookie  # 사용자 인증 의존성


# 알러지 정보, 질환 정보를 받는 api
router = APIRouter()

@router.get("/allergies", response_model=list[AllergyOut])
def get_allergies(db: Session = Depends(get_db)):
    return db.query(Allergy).all()

@router.get("/diseases", response_model=list[DiseaseOut])
def get_diseases(db: Session = Depends(get_db)):
    return db.query(ChronicDisease).all()


# 유저 질환/알러지 정보 저장
@router.post("/save-preference")
def save_user_preference(
    preference: PreferenceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    # 기존 알러지/질환 삭제
    db.query(UserAllergy).filter_by(user_id=user.user_id).delete()
    db.query(UserDisease).filter_by(user_id=user.user_id).delete()

    # 새 알러지 저장
    for name in preference.allergies:
        allergy = db.query(Allergy).filter_by(name=name).first()
        if allergy:
            db.add(UserAllergy(user_id=user.user_id, allergy_id=allergy.id))

    # 새 질환 저장
    for name in preference.diseases:
        disease = db.query(ChronicDisease).filter_by(name=name).first()
        if disease:
            db.add(UserDisease(user_id=user.user_id, disease_id=disease.id))

    db.commit()
    return {"message": "Preferences saved"}

# 저장된 유저 알러지/질환 정보 가져오는 거
@router.get("/preferences", response_model=PreferenceIn)
def get_user_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_cookie)
):
    allergies = db.query(UserAllergy).filter_by(user_id=user.user_id).all()
    diseases = db.query(UserDisease).filter_by(user_id=user.user_id).all()

    allergy_names = [a.allergy.name for a in allergies]
    disease_names = [d.disease.name for d in diseases]

    return {"allergies": allergy_names, "diseases": disease_names}
