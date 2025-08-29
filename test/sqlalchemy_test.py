import os
from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey,
    MetaData, Table, select, update, delete
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError

# --- 1. 데이터베이스 연결 설정 ---
# !! 중요: 아래 플레이스홀더 값들을 실제 DB 정보로 교체하세요 !!
# 이 값들은 docker-compose.yml 파일의 환경 변수와 일치해야 합니다.

DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
# 만약 이 스크립트를 Docker 네트워크 *외부*(예: 로컬 개발 머신)에서 실행하고
# docker-compose.yml에서 포트를 매핑했다면, 'localhost' 또는 '127.0.0.1'을 사용하세요.
# 만약 이 스크립트를 'db' 서비스와 *같은* Docker 네트워크 *내부*에서 실행한다면,
# 서비스 이름 'db'(또는 docker-compose.yml에서 정의한 다른 이름)를 사용하세요.
DB_HOST = os.getenv("MYSQL_HOST", "localhost") # 또는 Docker 네트워크 내에서는 'db'
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

# 연결 문자열
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. SQLAlchemy 설정 ---
# 엔진 생성 (echo=True는 생성된 SQL 문을 출력합니다)
engine = create_engine(DATABASE_URL, echo=True)

# 설정된 "Session" 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 선언적 모델을 위한 기본 클래스
Base = declarative_base()

# --- 3. 모델 정의 (테이블) ---

class UserInfo(Base):
    __tablename__ = 'user_info' # 테이블 이름 정의

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # 기본 키, 자동 증가
    username = Column(String(50), unique=True, index=True, nullable=False) # 사용자 이름, 고유값, 필수
    email = Column(String(100), unique=True, index=True, nullable=False) # 이메일, 고유값, 필수

    # 관계 설정: UserAuth와 일대일 관계
    # cascade="all, delete-orphan": UserInfo가 삭제되면 관련된 UserAuth도 삭제됨 (종속 삭제)
    auth = relationship("UserAuth", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        # 객체를 문자열로 표현할 때 사용 (디버깅용)
        return f"<UserInfo(id={self.id}, username='{self.username}', email='{self.email}')>"

class UserAuth(Base):
    __tablename__ = 'user_auth' # 테이블 이름 정의

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # 기본 키, 자동 증가
    # 실제 앱에서는 안전한 해시값(예: bcrypt)을 저장해야 합니다! 평문 저장 금지!
    password_hash = Column(String(255), nullable=False) # 비밀번호 해시, 필수

    # 외래 키: user_info 테이블의 id 참조
    # unique=True는 DB 레벨에서 일대일 관계를 강제합니다.
    user_id = Column(Integer, ForeignKey('user_info.id'), unique=True, nullable=False) # 외래 키, 고유값, 필수

    # 관계 설정: UserInfo를 다시 참조 (양방향)
    user = relationship("UserInfo", back_populates="auth")

    def __repr__(self):
        # 보안/명확성을 위해 비밀번호 해시는 직접 출력하지 않음
        return f"<UserAuth(id={self.id}, user_id={self.user_id})>"

# --- 4. 데이터베이스에 테이블 생성 ---
# 이 코드는 테이블이 존재하지 않으면 생성합니다.
try:
    print("데이터베이스 테이블이 존재하지 않으면 생성합니다...")
    Base.metadata.create_all(bind=engine)
    print("테이블 확인/생성 완료.")
except Exception as e:
    print(f"테이블 생성 중 오류 발생: {e}")
    # 테이블 생성이 중요 실패 요인이라면 여기서 프로그램 종료 고려
    # exit(1)

# --- 5. CRUD 작업 함수 ---

def create_user(db: Session, username: str, email: str, password: str):
    """새로운 사용자와 해당 인증 정보를 생성합니다."""
    # 실제 앱에서는 여기서 비밀번호를 해싱한 후 저장해야 합니다!
    hashed_password = f"hashed_{password}" # 해싱 예시 (실제로는 강력한 해시 함수 사용)

    # 사용자 이름 또는 이메일이 이미 존재하는지 확인
    existing_user = db.query(UserInfo).filter(
        (UserInfo.username == username) | (UserInfo.email == email)
    ).first()
    if existing_user:
        print(f"오류: 사용자 이름 '{username}' 또는 이메일 '{email}'이(가) 이미 존재합니다.")
        return None

    try:
        # 객체 인스턴스 생성
        db_user_info = UserInfo(username=username, email=email)
        db_user_auth = UserAuth(password_hash=hashed_password)

        # 관계를 통해 연결
        db_user_info.auth = db_user_auth
        # 참고: db_user_auth.user는 SQLAlchemy에 의해 자동으로 설정되거나,
        # 명시적으로 db_user_auth.user = db_user_info 와 같이 설정할 수도 있습니다.

        # 주 객체(UserInfo)를 세션에 추가합니다.
        # cascade 설정 때문에 관련된 UserAuth도 함께 추가됩니다.
        db.add(db_user_info)
        db.commit() # 트랜잭션 커밋
        db.refresh(db_user_info) # 생성된 ID 등을 얻기 위해 객체 새로고침
        # 관련된 객체도 필요하다면 새로고침 (예: 관련 객체의 ID를 얻기 위해)
        if db_user_info.auth:
            db.refresh(db_user_info.auth)
        print(f"사용자 생성 성공: {db_user_info} / 인증 정보: {db_user_info.auth}")
        return db_user_info
    except SQLAlchemyError as e:
        db.rollback() # 오류 발생 시 트랜잭션 롤백
        print(f"사용자 생성 중 오류 발생: {e}")
        return None

def get_user_by_id(db: Session, user_id: int):
    """ID로 사용자를 조회합니다."""
    user = db.query(UserInfo).filter(UserInfo.id == user_id).first()
    if user:
        print(f"ID {user_id} 사용자 조회 성공: {user}")
        # 필요한 경우 관련된 인증 정보 접근
        if user.auth:
            print(f"  - 인증 정보: {user.auth}")
        else:
             print(f"  - 연관된 인증 정보 없음.")
    else:
        print(f"ID {user_id} 사용자를 찾을 수 없습니다.")
    return user

def get_user_by_username(db: Session, username: str):
    """사용자 이름으로 사용자를 조회합니다."""
    user = db.query(UserInfo).filter(UserInfo.username == username).first()
    if user:
        print(f"사용자 이름 '{username}' 조회 성공: {user}")
        if user.auth:
            print(f"  - 인증 정보: {user.auth}")
    else:
        print(f"사용자 이름 '{username}' 사용자를 찾을 수 없습니다.")
    return user

def get_all_users(db: Session):
    """모든 사용자를 조회합니다."""
    users = db.query(UserInfo).all()
    print(f"\n--- 모든 사용자 ({len(users)}명) ---")
    if not users:
        print("데이터베이스에 사용자가 없습니다.")
    for user in users:
        print(f"- {user} (인증 정보 ID: {user.auth.id if user.auth else '없음'})")
    print("--------------------------")
    return users

def update_user_email(db: Session, user_id: int, new_email: str):
    """사용자의 이메일 주소를 업데이트합니다."""
    try:
        user = db.query(UserInfo).filter(UserInfo.id == user_id).first()
        if user:
            # 새 이메일이 다른 사용자에 의해 이미 사용 중인지 확인
            existing_email = db.query(UserInfo).filter(UserInfo.email == new_email, UserInfo.id != user_id).first()
            if existing_email:
                print(f"오류: 이메일 '{new_email}'은(는) 다른 사용자(ID: {existing_email.id})가 이미 사용 중입니다.")
                return None

            print(f"사용자 ID {user_id}의 이메일을 '{user.email}'에서 '{new_email}'(으)로 변경합니다.")
            user.email = new_email
            db.commit() # 변경사항 커밋
            db.refresh(user) # 변경된 정보로 객체 새로고침
            print(f"사용자 정보 업데이트 성공: {user}")
            return user
        else:
            print(f"업데이트할 사용자 ID {user_id}를 찾을 수 없습니다.")
            return None
    except SQLAlchemyError as e:
        db.rollback() # 오류 발생 시 롤백
        print(f"사용자 이메일 업데이트 중 오류 발생: {e}")
        return None

def delete_user(db: Session, user_id: int):
    """사용자와 관련된 인증 정보를 삭제합니다 (cascade 설정에 의해)."""
    try:
        user = db.query(UserInfo).filter(UserInfo.id == user_id).first()
        if user:
            print(f"사용자 삭제 시도: {user}")
            db.delete(user) # 사용자 객체 삭제 요청
            db.commit() # 변경사항 커밋 (이때 cascade에 의해 연관된 auth도 삭제됨)
            print(f"ID {user_id} 사용자 삭제 성공.")
            return True
        else:
            print(f"삭제할 사용자 ID {user_id}를 찾을 수 없습니다.")
            return False
    except SQLAlchemyError as e:
        db.rollback() # 오류 발생 시 롤백
        print(f"사용자 삭제 중 오류 발생: {e}")
        return False

# --- 6. 예제 사용법 ---
if __name__ == "__main__":
    # 세션 관리를 위해 컨텍스트 매니저 사용
    print("\n--- CRUD 작업 시작 ---")
    with SessionLocal() as session:
        # --- 생성 (CREATE) ---
        print("\n[생성]")
        user1 = create_user(session, "alice", "alice@example.com", "password123")
        user2 = create_user(session, "bob", "bob@example.com", "securepass")
        create_user(session, "charlie", "charlie@example.com", "pass")
        # 중복된 사용자 이름/이메일로 생성 시도
        create_user(session, "alice", "new_alice@example.com", "pw") # 사용자 이름 중복
        create_user(session, "new_bob", "bob@example.com", "pw")   # 이메일 중복

        # --- 읽기 (READ) ---
        print("\n[읽기]")
        get_all_users(session) # 모든 사용자 조회
        if user1:
            get_user_by_id(session, user1.id) # ID로 조회
        get_user_by_id(session, 999) # 존재하지 않는 ID 조회
        get_user_by_username(session, "bob") # 사용자 이름으로 조회
        get_user_by_username(session, "dave") # 존재하지 않는 사용자 이름 조회

        # --- 수정 (UPDATE) ---
        print("\n[수정]")
        if user1:
            update_user_email(session, user1.id, "alice_updated@example.com") # 이메일 변경
            # 다른 사용자가 이미 사용 중인 이메일로 변경 시도
            if user2:
                 update_user_email(session, user1.id, user2.email) # 이메일 중복

        # 업데이트 확인
        if user1:
            get_user_by_id(session, user1.id)

        # --- 삭제 (DELETE) ---
        print("\n[삭제]")
        if user2:
            delete_user(session, user2.id) # 사용자 삭제
        delete_user(session, 999) # 존재하지 않는 ID 삭제

        # 삭제 확인
        get_all_users(session)

    print("\n--- CRUD 작업 완료 ---")