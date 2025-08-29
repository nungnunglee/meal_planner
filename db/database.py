from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")

DATABASE_URL_ROOT = f'mysql+mysqlconnector://root:{MYSQL_ROOT_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}'

DATABASE_URL = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'

class Base(DeclarativeBase):
    pass

root_engine = create_engine(
    DATABASE_URL_ROOT,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
    pool_recycle=3600,
    pool_timeout=30,
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 연결 사용 전에 유효성 검사
    pool_size=10,            # 풀에 최소 10개의 연결 유지
    max_overflow=20,         # 최대 20개까지 추가 연결 허용
    pool_recycle=3600,       # 1시간(3600초)마다 연결 재활용
    pool_timeout=30,         # 연결을 얻기 위해 최대 30초 대기
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
