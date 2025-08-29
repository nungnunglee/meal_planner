from db.tables.user_table import *
import model.domain.user as user_domain
from datetime import datetime
from typing import Dict, Any, Union, Literal
import uuid
import functools
import logging

"""
user:
    search by uuid
    create
            nickname, email, (password or social_code), 
            body(age, tall, weight, sleep_pattern, activity_level, 
                gender, diseases, favorite_foods, disliked_foods)
    update
        body, schedule, inventory, subscription, social_login, password
    delete by uuid

log:
    record login
"""

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UserMixin:
    """유저 관련 DB입출력 기능 모음, 상속해서 사용"""

    def check_session(func):
        """세션 체크 및 트랜잭션 관리 데코레이터"""
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.session is None:
                raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
            try:
                result = func(self, *args, **kwargs)
                self.session.commit()
                return result
            except Exception as e:
                self.session.rollback()
                raise e
        return wrapper

    def check_user_exists(func):
        """사용자 존재 확인 데코레이터"""
        @functools.wraps(func)
        def wrapper(self, uuid, *args, **kwargs):
            user_info = self.get_user_by_uuid(uuid=uuid)
            if user_info is None:
                return False
            return func(self, uuid, *args, user_info=user_info, **kwargs)
        return wrapper

    def get_user_by_uuid(self, uuid: str) -> user_domain.User | None:
        """UUID로 사용자 정보 조회"""
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
        user_info = self.session.query(UserInfo).filter(UserInfo.uuid == uuid).first()
        return user_domain.User.from_db_model(user_info) if user_info else None
    
    def get_user_by_email(self, email: str) -> user_domain.User | None:
        """이메일로 사용자 정보 조회"""
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
        user_info = self.session.query(UserInfo).join(UserAuth).filter(UserAuth.email == email).first()
        return user_domain.User.from_db_model(user_info) if user_info else None

    @check_session
    def create_user(
            self,
            nickname: str,
            email: str,
            password: str | None = None,
            social_code: str | None = None,
            access_token: str | None = None,
            phone: str = None,
            age: int = None,
            tall: int = None,
            weight: int = None,
            sleep_pattern: str = None,
            activity_level: str = None,
            gender: str = None,
            diseases: str = None,
            favorite_foods: str = None,
            disliked_foods: str = None) -> str:
        """유저 생성"""
        while True:
            user_uuid = str(uuid.uuid4())
            if self.get_user_by_uuid(uuid=user_uuid) is None:
                break
        logger.debug(f"유저 uuid 생성: {user_uuid}")
        user_info = UserInfo(
                uuid=user_uuid,
                nickname=nickname,
                user_auth=UserAuth(
                    uuid=user_uuid,
                    email=email,
                    phone=phone
                ),
                user_body=UserBody(
                    uuid=user_uuid,
                    age=age,
                    tall=tall,
                    weight=weight,
                    sleep_pattern=sleep_pattern,
                    activity_level=activity_level,
                    gender=gender,
                    diseases=diseases,
                    favorite_foods=favorite_foods,
                    disliked_foods=disliked_foods
                )
            )

        if password:
            user_info.password = Password(
                uuid=user_uuid,
                password=password
            )
        elif social_code:
            user_info.social_login = SocialLogin(
                uuid=user_uuid,
                social_code=social_code,
                access_token=access_token
            )
        self.session.add(user_info)
        return user_uuid

    @check_session
    @check_user_exists
    def update_user_body(
            self, 
            uuid: str, 
            age: int = None,
            tall: int = None,
            weight: int = None,
            sleep_pattern: str = None,
            activity_level: str = None,
            gender: str = None,
            diseases: str = None,
            favorite_foods: str = None,
            disliked_foods: str = None,
            user_info=None) -> bool:
        """유저 신체 정보 업데이트"""
        user_info.user_body = UserBody(
            uuid=uuid,
            age=age,
            tall=tall,
            weight=weight,
            sleep_pattern=sleep_pattern,
            activity_level=activity_level,
            gender=gender,
            diseases=diseases,
            favorite_foods=favorite_foods,
            disliked_foods=disliked_foods
        )
        return True

    @check_session
    @check_user_exists
    def update_user_schedule(self, uuid: str, datetime: datetime, foods: list, user_info=None) -> bool:
        """유저 식사 일정 업데이트"""
        # 기존 일정이 있으면 삭제
        existing_schedule = self.session.query(UserSchedule).filter(
            UserSchedule.uuid == uuid,
            UserSchedule.datetime == datetime
        ).first()
        
        if existing_schedule:
            # 관련 음식 삭제
            self.session.query(ScheduleFood).filter(
                ScheduleFood.meal_id == existing_schedule.meal_id
            ).delete()
            self.session.delete(existing_schedule)
        
        # 새 일정 추가
        schedule = UserSchedule(
            uuid=uuid,
            datetime=datetime
        )
        self.session.add(schedule)
        
        # 음식 추가
        for food in foods:
            food_item = ScheduleFood(
                meal_id=schedule.meal_id,
                food_id=food.get('food_id'),
                food_name=food.get('food_name'),
                quantity=food.get('quantity')
            )
            self.session.add(food_item)
        
        return True
    
    @check_session
    @check_user_exists
    def update_user_inventory(self, uuid: str, food_id: str, quantity: str, expired: datetime = None, user_info=None) -> bool:
        """유저 식품 인벤토리 업데이트"""
        # 기존 인벤토리 항목 검색
        inventory_item = self.session.query(UserFoodInventory).filter(
            UserFoodInventory.uuid == uuid,
            UserFoodInventory.food_id == food_id
        ).first()
        
        if inventory_item:
            # 수량이 0이면 삭제
            if quantity in [None, '', '0g', '0ml', '0', '0.0']:
                self.session.delete(inventory_item)
            else:
                # 기존 항목 업데이트
                inventory_item.quantity = quantity
                inventory_item.expired = expired
        else:
            # 새 항목 추가 (수량이 0보다 클 때만)
            if quantity not in [None, '', '0g', '0ml', '0', '0.0']:
                inventory_item = UserFoodInventory(
                    uuid=uuid,
                    food_id=food_id,
                    quantity=quantity,
                    expired=expired
                )
                self.session.add(inventory_item)
        
        return True
    
    @check_session
    @check_user_exists
    def update_user_subscription(self, uuid: str, plan: str, purchase: datetime, expired: datetime, user_info=None) -> bool:
        """유저 구독 정보 업데이트"""
        # 기존 구독 정보 검색
        subscription = self.session.query(Subscription).filter(
            Subscription.uuid == uuid
        ).first()
        
        if subscription:
            # 기존 구독 정보 업데이트
            subscription.plan = plan
            subscription.purchase = purchase
            subscription.expired = expired
        else:
            # 새 구독 정보 추가
            subscription = Subscription(
                uuid=uuid,
                plan=plan,
                purchase=purchase,
                expired=expired
            )
            self.session.add(subscription)
        
        return True
    
    @check_session
    @check_user_exists
    def update_social_login(self, uuid: str, social_code: str, access_token: str, user_info=None) -> bool:
        """유저 소셜 로그인 정보 업데이트"""
        # 기존 소셜 로그인 정보 검색
        social_login = self.session.query(SocialLogin).filter(
            SocialLogin.uuid == uuid
        ).first()
        
        if social_login:
            # 기존 소셜 로그인 정보 업데이트
            social_login.social_code = social_code
            social_login.access_token = access_token
        else:
            # 새 소셜 로그인 정보 추가
            social_login = SocialLogin(
                uuid=uuid,
                social_code=social_code,
                access_token=access_token
            )
            self.session.add(social_login)
        
        return True
    
    @check_session
    @check_user_exists
    def update_password(self, uuid: str, password: str, user_info=None) -> bool:
        """유저 비밀번호 업데이트"""
        # 기존 비밀번호 정보 검색
        password_info = self.session.query(Password).filter(
            Password.uuid == uuid
        ).first()
        
        if password_info:
            # 기존 비밀번호 정보 업데이트
            password_info.password = password
        else:
            # 새 비밀번호 정보 추가
            password_info = Password(
                uuid=uuid,
                password=password
            )
            self.session.add(password_info)
        
        return True
    
    @check_session
    def delete_user(self, uuid: str) -> bool:
        """유저 삭제"""
        user_info = self.get_user_by_uuid(uuid=uuid)
        if user_info is None:
            return False
        
        # 관련된 모든 데이터 삭제
        for food in user_info.user_schedule.schedule_foods:
            self.session.delete(food)
        self.session.delete(user_info.user_schedule)
        self.session.delete(user_info.food_inventory)
        self.session.delete(user_info.login_logs)
        self.session.delete(user_info.subscription)
        self.session.delete(user_info.password)
        self.session.delete(user_info.social_login)
        self.session.delete(user_info.user_body)
        self.session.delete(user_info.user_auth)
        self.session.delete(user_info)
        
        return True
    
    @check_session
    def record_login(self, uuid: str, status_code: int, ip: str) -> bool:
        """로그인 기록 저장"""
        login_log = LoginLog(
            uuid=uuid,
            status_code=status_code,
            ip=ip,
            datetime=datetime.now()
        )
        self.session.add(login_log)
        return True


