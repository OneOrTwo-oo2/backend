from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# 사용자
class User(Base):
    __tablename__ = "User"
    user_id = Column(Integer, primary_key=True)
    user_email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=True)  # 자체 회원가입용 비밀번호 (Google 로그인은 null)
    login_type = Column(String(20), default="google")  # "google" 또는 "email"

    allergies = relationship("UserAllergy", back_populates="user", cascade="all, delete")
    diseases = relationship("UserDisease", back_populates="user", cascade="all, delete")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete")
    bookmark_folders = relationship("BookmarkFolder", back_populates="user", cascade="all, delete")

# 알러지 정보
class Allergy(Base):
    __tablename__ = "Allergy"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    users = relationship("UserAllergy", back_populates="allergy", cascade="all, delete")

# 유저 알러지 중간 테이블 (인조키 사용)
class UserAllergy(Base):
    __tablename__ = "user_allergy"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"))
    allergy_id = Column(Integer, ForeignKey("Allergy.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="allergies")
    allergy = relationship("Allergy", back_populates="users")

    __table_args__ = (
        UniqueConstraint('user_id', 'allergy_id', name='user_id_allergy_id_uc'),
    )

# 질환 정보
class ChronicDisease(Base):
    __tablename__ = "ChronicDisease"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    users = relationship("UserDisease", back_populates="disease", cascade="all, delete")

# 유저 질환 중간 테이블 (인조키 사용)
class UserDisease(Base):
    __tablename__ = "user_disease"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"))
    disease_id = Column(Integer, ForeignKey("ChronicDisease.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="diseases")
    disease = relationship("ChronicDisease", back_populates="users")

    __table_args__ = (
        UniqueConstraint('user_id', 'disease_id', name='user_id_disease_id_uc'),
    )

# 레시피
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    image = Column(String(500))
    summary = Column(String(1000))
    link = Column(String(255), unique=True)
    recommendation_reason = Column(String(1000), nullable=True)
    dietary_tips = Column(String(1000), nullable=True) 
    is_ai_generated = Column(Integer, default=0)  # ✅ 추가

    bookmarks = relationship("Bookmark", back_populates="recipe", cascade="all, delete")
    folder_recipes = relationship("FolderRecipe", back_populates="recipe", cascade="all, delete")


# 북마크
class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"))
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))
    custom_title = Column(String(255), nullable=True)  # ✅ 사용자 지정 제목 필드 추가

    user = relationship("User", back_populates="bookmarks")
    recipe = relationship("Recipe", back_populates="bookmarks")

    __table_args__ = (
        UniqueConstraint('user_id', 'recipe_id', name='user_id_recipe_id_uc'),
    )

# ✅ 북마크 폴더
class BookmarkFolder(Base):
    __tablename__ = "bookmark_folders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)

    user = relationship("User", back_populates="bookmark_folders")
    folder_recipes = relationship("FolderRecipe", back_populates="folder", cascade="all, delete")

# ✅ 폴더-레시피 중간 테이블
class FolderRecipe(Base):
    __tablename__ = "folder_recipes"
    id = Column(Integer, primary_key=True)
    folder_id = Column(Integer, ForeignKey("bookmark_folders.id", ondelete="CASCADE"))
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))

    folder = relationship("BookmarkFolder", back_populates="folder_recipes")
    recipe = relationship("Recipe", back_populates="folder_recipes")

    __table_args__ = (
        UniqueConstraint('folder_id', 'recipe_id', name='folder_id_recipe_id_uc'),
    )
