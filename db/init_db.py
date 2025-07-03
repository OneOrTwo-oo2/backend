from .connection import engine
from .models import Base

# engine으로 db연결, 모든 ORM 모델의 메타정보
def init_db():
    Base.metadata.create_all(bind=engine)

# create_all 을 통해 존재하지않으면 생성, 있으면 유지