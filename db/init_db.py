from .connection import engine, SessionLocal
from .models import Base, Allergy, ChronicDisease

# engine으로 db연결, 모든 ORM 모델의 메타정보
def init_db():
    Base.metadata.create_all(bind=engine)

    # create_all 을 통해 존재하지않으면 생성, 있으면 유지
    db = SessionLocal()
    try:
        seed_initial_data(db)  # ✅ 여기서 마스터 데이터 채움
    finally:
        db.close()

def seed_initial_data(db):
    allergy_list = [
        "알류", "우유", "메밀", "땅콩", "대두", "밀", "잣", "호두", "게", "새우",
        "오징어", "고등어", "조개류", "복숭아", "토마토",
        "닭고기", "돼지고기", "쇠고기", "아황산류"
    ]

    disease_list = [
        "항암치료", "뇌졸중", "역류성 식도염", "변비", "골다공증", "당뇨병", "빈혈",
        "지방간", "이상지질혈증", "통풍", "고혈압", "과민성 대장증후군",
        "갑상선기능항진증", "담석증", "만성 콩팥병", "염증성장질환",
        "만성폐쇄성폐질환", "혈관성 치매", "파킨슨병", "기능성 소화불량",
        "대장직장암", "심부전", "비만", "유당불내증", "대사증후군",
        "간경변증", "아토피피부염"
    ]

    # ✅ 기존 데이터 한 번에 가져와서 중복 확인
    existing_allergies = {a.name for a in db.query(Allergy.name).all()}
    existing_diseases = {d.name for d in db.query(ChronicDisease.name).all()}

    # ✅ 한꺼번에 add_all
    new_allergies = [Allergy(name=name) for name in allergy_list if name not in existing_allergies]
    new_diseases = [ChronicDisease(name=name) for name in disease_list if name not in existing_diseases]

    db.add_all(new_allergies + new_diseases)
    db.commit()
