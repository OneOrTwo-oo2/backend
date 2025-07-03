from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# 사용자
class User(Base):
    __tablename__ = "User"
    user_id = Column(Integer, primary_key=True)
    user_email = Column(String(100), nullable=False, unique=True)

    allergies = relationship("UserAllergy", back_populates="user", cascade="all, delete")
    diseases = relationship("UserDisease", back_populates="user", cascade="all, delete")


# 알러지 정보
class Allergy(Base):
    __tablename__ = "Allergy"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    users = relationship("UserAllergy", back_populates="allergy", cascade="all, delete")


# 유저 알러지 중간 테이블
class UserAllergy(Base):
    __tablename__ = "user_allergy"
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), primary_key=True)
    allergy_id = Column(Integer, ForeignKey("Allergy.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'allergy_id', name='user_id_allergy_id_uc'),
    )

    user = relationship("User", back_populates="allergies")
    allergy = relationship("Allergy", back_populates="users")

    # 복합 PK를 위해
    def __init__(self, user_id, allergy_id):
        self.user_id = user_id
        self.allergy_id = allergy_id


# 질환 정보
class ChronicDisease(Base):
    __tablename__ = "ChronicDisease"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    users = relationship("UserDisease", back_populates="disease", cascade="all, delete")


# 유저 질환 중간 테이블
class UserDisease(Base):
    __tablename__ = "user_disease"
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), primary_key=True)
    disease_id = Column(Integer, ForeignKey("ChronicDisease.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'disease_id', name='user_id_disease_id_uc'),
    )

    user = relationship("User", back_populates="diseases")
    disease = relationship("ChronicDisease", back_populates="users")

    def __init__(self, user_id, disease_id):
        self.user_id = user_id
        self.disease_id = disease_id
