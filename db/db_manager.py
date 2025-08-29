import sys
from pathlib import Path
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

project_root = os.getenv("PROJECT_ROOT")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.database import SessionLocal
from db.tables.user_table import *
from db.tables.food_table import *
from db.db_mixin.user_mixin import UserMixin
from db.db_mixin.food_mixin import FoodMixin

class DBManager(UserMixin, FoodMixin):
    """
    데이터베이스 관리 클래스
    세션을 효율적으로 관리하며 음식 및 태그 정보를 다룹니다.
    """
    
    def __init__(self):
        """DBManager 초기화"""
        self.session = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입 시 세션 시작"""
        if self.session is None:
            self.session = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 세션 종료"""
        if exc_type is not None:
            # 예외 발생 시 롤백
            if self.session:
                self.session.rollback()
        
        if self.session:
            self.session.close()
            self.session = None

    @contextmanager
    def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        if self.session is None:
            self.session = SessionLocal()
        try:
            yield self
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        
def get_db_manager():
    with DBManager() as db_manager:
        yield db_manager

class DBManagerTest:
    def __init__(self):
        self.db_manager = DBManager()

    def user_test(self):
        with self.db_manager.transaction() as manager:
            user_uuid = manager.create_user(
                nickname="test",
                email="test@test.com",
            )
            user = manager.get_user_by_uuid(user_uuid)
            print(user)

if __name__ == "__main__":
    db_manager_test = DBManagerTest()
    # db_manager_test.user_test()