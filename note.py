# from db.model.food_table import *
# from db.model.user_table import *
# from db.database import SessionLocal

# def print_food_nutrition(uuid: str):
#     with SessionLocal() as db:
#         # 음식 정보와 영양성분 정보를 함께 조회
#         user_info = db.query(UserInfo).filter(UserInfo.uuid == uuid).first()
        
#         if user_info:

#             print(f"user_info: ")
#             for key, value in user_info.__dict__.items():
#                 print(f"{key}: {value}")

#             if user_info.user_body:

#                 print(f"user_info.user_body: ")
#                 for key, value in user_info.user_body.__dict__.items():
#                     print(f"{key}: {value}")

#             else:
#                 print(f"user_info.user_body is None")
#         else:
#             print(f"음식 ID {uuid}에 대한 정보를 찾을 수 없습니다.")

# def len_food_table():
#     with SessionLocal() as db:
#         food_info = db.query(FoodInfo).all()
#         for idx, food in enumerate(sorted(food_info, key=lambda x: x.food_id)):
#             print(f"{idx}:\t{food.food_id}: {food.food_name}")
#             if idx > 10:
#                 break

# if __name__ == "__main__":
#     # 예시: 음식 ID를 입력받아 영양성분 출력
#     print_food_nutrition("D101-004160000-0001")
#     len_food_table()

# from contextlib import contextmanager

# class with_test:
#     def __init__(self):
#         print("init")
#         self.test1 = 1
    
#     def __enter__(self):
#         print("enter")
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         print("exit")

#     @contextmanager
#     def test_context(self):
#         print("test_context enter")
#         yield self
#         print("test_context exit")

# if __name__ == "__main__":
#     print("main")
#     with with_test().test_context() as test:
#         print(test.test1)
#         # with test.test_context() as test2:
#         #     print(test2.test1)
#     print("main end")

import os
from dotenv import load_dotenv
load_dotenv()
import smtplib
from email.mime.text import MIMEText

smtp = smtplib.SMTP('smtp.gmail.com', 587)

smtp.ehlo()

smtp.starttls()

smtp.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))

msg = MIMEText('내용 : 본문 내용')
msg['Subject'] = '제목: 파이썬으로 gmail 보내기'

smtp.sendmail('lkw4582@gmail.com', 'lkw4582@gmail.com', msg.as_string())

smtp.quit()
