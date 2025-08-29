from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Literal

import sys, os, dotenv
dotenv.load_dotenv()

sys.path.insert(0, os.environ.get("PROJECT_ROOT"))

from model.domain.food import Food


class SleepPatternItem(BaseModel):
    start: str = Field(
        ...,
        # regex=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="시작 시간(HH:MM 형식, 00:00~23:59, 예: 07:30)"
    )
    end: str = Field(
        ...,
        # regex=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="종료 시간(HH:MM 형식, 00:00~23:59, 예: 23:00)"
    )



class UserBody(BaseModel):
    age: int | None = Field(None, ge=0, le=120, description="나이(0~120세)")
    gender: Literal['남성', '여성'] | None = Field(None, description="성별(남성, 여성, 중 택1)")
    tall: float | None = Field(None, ge=50, le=250, description="신장(cm, 50~250)")
    weight: float | None = Field(None, ge=10, le=300, description="체중(kg, 10~300)")
    sleep_pattern: List[SleepPatternItem] | None = Field(None, description="수면 패턴(시작 시간, 종료 시간)")
    activity_level: Literal['낮음', '보통', '높음'] | None = Field(
        None,
        description=(
            "활동 수준(낮음, 보통, 높음 중 택1) - "
            "낮음: 주로 앉아서 생활, 운동 거의 없음 / "
            "보통: 가벼운 활동 또는 주 1~2회 운동 / "
            "높음: 주 3회 이상 운동 또는 육체노동"
        )
    )
    diseases: List[str] | None = Field(None, description="질병 정보")
    favorite_foods: List[Food] | None = Field(None, description="선호 음식")
    disliked_foods: List[Food] | None = Field(None, description="비선호 음식")


class UserAuth(BaseModel):
    email: str | None = None
    phone: str | None = None


class UserSocialLogin(BaseModel):
    social_code: str
    access_token: str


class Subscription(BaseModel):
    plan: Literal["basic", "premium", "vip"]
    purchase: datetime
    expired: datetime


class MealPlan(BaseModel):
    datetime: datetime
    food_list: List[Food]
    

class User(BaseModel):
    uuid: str
    nickname: str
    user_auth: UserAuth
    user_body: UserBody
    password: str | None = None
    social_login: UserSocialLogin | None = None
    subscription: Subscription | None = None
    meal_plan: List[MealPlan] | None = None

    @classmethod
    def from_db_model(cls, user_info) -> 'User':
        if hasattr(user_info, 'social_login') and user_info.social_login is not None:
            social_login = UserSocialLogin(social_code=user_info.social_login.social_code, access_token=user_info.social_login.access_token)
        else:
            social_login = None
        
        if hasattr(user_info, 'subscription') and user_info.subscription is not None:
            subscription = Subscription(plan=user_info.subscription.plan, purchase=user_info.subscription.purchase, expired=user_info.subscription.expired)
        else:
            subscription = None
        
        if hasattr(user_info, 'meal_plan') and user_info.meal_plan is not None:
            meal_plan = [MealPlan(datetime=meal.datetime, food_list=[Food.from_db_model(food) for food in meal.food_list]) for meal in user_info.meal_plan]
        else:
            meal_plan = []
        
        return User(
            uuid=user_info.uuid,
            nickname=user_info.nickname,
            user_auth=UserAuth(email=user_info.user_auth.email, phone=user_info.user_auth.phone),
            user_body=UserBody(
                age=user_info.user_body.age,
                gender=user_info.user_body.gender,
                tall=user_info.user_body.tall,
                weight=user_info.user_body.weight,
            ),
            password=user_info.password.password,
            social_login=social_login,
            subscription=subscription,
            meal_plan=meal_plan,
        )


if __name__ == "__main__":
    user = User(
        uuid="1234567890",
        nickname="test",
        user_auth=UserAuth(email="test@test.com", phone="01012345678"),
        user_body=UserBody(
            age=20, gender="남성", tall=180, weight=70,
            sleep_pattern=[
                SleepPatternItem(start="23:00", end="07:00"),
                SleepPatternItem(start="14:00", end="14:30")
            ],
            activity_level="보통",
            diseases=["비만"],
            favorite_foods=[Food(food_id="1234567890", food_name="테스트")],
            disliked_foods=[Food(food_id="1234567890", food_name="테스트")]
        ),
        password="test",
        social_login=UserSocialLogin(social_code="test", access_token="test"),
        subscription=Subscription(plan="test", purchase=datetime.now(), expired=datetime.now() + timedelta(days=30)),
        meal_plan=[MealPlan(datetime=datetime.now(), food_list=[Food(food_id="1234567890", food_name="테스트")])]
    )
    dumped_user = user.model_dump()
    print("type(dumped_user):", type(dumped_user))
    print("dumped_user:", dumped_user)
    # print("type(dumped_user['user_body']):", type(dumped_user['user_body']))
    # print("dumped_user['user_body']:", dumped_user['user_body'])
    # print("type(dumped_user['user_body']['sleep_pattern']):", type(dumped_user['user_body']['sleep_pattern']))
    # print("dumped_user['user_body']['sleep_pattern']:", dumped_user['user_body']['sleep_pattern'])
    # print("type(dumped_user['user_body']['sleep_pattern'][0]):", type(dumped_user['user_body']['sleep_pattern'][0]))
    # print("dumped_user['user_body']['sleep_pattern'][0]:", dumped_user['user_body']['sleep_pattern'][0])
    # print("type(dumped_user['user_body']['sleep_pattern'][0]['start']):", type(dumped_user['user_body']['sleep_pattern'][0]['start']))
    # print("dumped_user['user_body']['sleep_pattern'][0]['start']:", dumped_user['user_body']['sleep_pattern'][0]['start'])
    # print("type(dumped_user['user_body']['sleep_pattern'][0]['end']):", type(dumped_user['user_body']['sleep_pattern'][0]['end']))
    # print("dumped_user['user_body']['sleep_pattern'][0]['end']:", dumped_user['user_body']['sleep_pattern'][0]['end'])
    print(str(user))
