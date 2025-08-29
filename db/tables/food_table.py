from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, Numeric, Boolean, BigInteger
from sqlalchemy.orm import relationship
from ..database import Base

__all__ = [
    "FoodInfo",
    "FoodCategory",
    "FoodSourceInfo",
    "FoodCompany",
    "FoodNutrition",
    "FoodInfoTag",
    "FoodTag",
]

# food_info 테이블 모델 (식품정보)
class FoodInfo(Base):
    __tablename__ = "food_info"

    food_id = Column(String(19), primary_key=True, index=True)  # 식품코드: D101-004160000-0001
    food_name = Column(String(767), unique=True, nullable=False)  # 식품명: 국밥_돼지머리
    data_type_code = Column(String(1), nullable=False)  # 데이터구분코드: D, F

    # Relationships
    category = relationship("FoodCategory", back_populates="food_info", uselist=False)
    source_info = relationship("FoodSourceInfo", back_populates="food_info", uselist=False)
    company = relationship("FoodCompany", back_populates="food_info", uselist=False)
    nutrition = relationship("FoodNutrition", back_populates="food_info", uselist=False)
    tags = relationship("FoodTag", back_populates="food_info", secondary="food_info_tag")

class FoodCategory(Base):
    __tablename__ = "food_categories"

    food_id = Column(String(19), ForeignKey("food_info.food_id"), primary_key=True)  # 식품코드: D101-004160000-0001
    major_category_name = Column(String(100))  # 식품대분류명: 밥류
    medium_category_name = Column(String(100))  # 식품중분류명: 돼지머리
    minor_category_name = Column(String(100))  # 식품소분류명: 발효소시지
    detail_category_name = Column(String(100))  # 식품세분류명: 생것
    representative_food_name = Column(String(100))  # 대표식품명: 국밥

    # Relationship
    food_info = relationship("FoodInfo", back_populates="category", uselist=False)

class FoodSourceInfo(Base):
    __tablename__ = "food_source_info"

    food_id = Column(String(19), ForeignKey("food_info.food_id"), primary_key=True)  # 식품코드: D101-004160000-0001
    origin_name = Column(String(100))  # 식품기원명: 가정식(분석 함량)
    source_name = Column(String(100))  # 출처명: 식품의약품안전처
    generation_method_name = Column(String(100))  # 데이터생성방법명: 분석
    reference_date = Column(Date)  # 데이터기준일자: 2025-04-08

    # Relationship
    food_info = relationship("FoodInfo", back_populates="source_info", uselist=False)

class FoodCompany(Base):
    __tablename__ = "food_companies"

    food_id = Column(String(19), ForeignKey("food_info.food_id"), primary_key=True)  # 식품코드: D101-004160000-0001
    company_name = Column(String(500))  # 업체명: 스타벅스
    manufacturer_name = Column(String(500))  # 제조사명: 에쓰푸드(주)음성공장
    origin_country_name = Column(String(500))  # 원산지국명: 미국
    importer_name = Column(String(500))  # 수입업체명: Yantai Longxiang Foodstuff Co.,LTD.
    distributor_name = Column(String(500))  # 유통업체명: ㈜마이비
    mfg_report_no = Column(BigInteger)  # 품목제조보고번호: 2013040000000

    # Relationship
    food_info = relationship("FoodInfo", back_populates="company", uselist=False)

class FoodNutrition(Base):
    __tablename__ = "food_nutrition"

    food_id = Column(String(19), ForeignKey("food_info.food_id"), primary_key=True)  # 식품코드: D101-004160000-0001
    weight = Column(String(100))  # 식품중량: 900g
    serving_size_g = Column(String(100))  # 1회 섭취참고량: 30g
    nutrient_reference_amount_g = Column(String(100))  # 영양성분함량기준량: 100g
    energy_kcal = Column(Numeric(10, 3))  # 에너지(kcal): 260.000
    moisture_g = Column(Numeric(10, 3))  # 수분(g): 56.800
    protein_g = Column(Numeric(10, 3))  # 단백질(g): 21.240
    fat_g = Column(Numeric(10, 3))  # 지방(g): 17.870
    ash_g = Column(Numeric(10, 3))  # 회분(g): 0.530
    carbohydrate_g = Column(Numeric(10, 3))  # 탄수화물(g): 3.580
    sugars_g = Column(Numeric(10, 3))  # 당류(g): 0.310
    dietary_fiber_g = Column(Numeric(10, 3))  # 식이섬유(g): 0.000
    calcium_mg = Column(Numeric(10, 3))  # 칼슘(mg): 6.000
    iron_mg = Column(Numeric(10, 3))  # 철(mg): 0.840
    phosphorus_mg = Column(Numeric(10, 3))  # 인(mg): 89.000
    potassium_mg = Column(Numeric(10, 3))  # 칼륨(mg): 58.000
    sodium_mg = Column(Numeric(10, 3))  # 나트륨(mg): 177.000
    vitamin_a_ug_rae = Column(Numeric(10, 3))  # 비타민A(μg RAE): 3.000
    retinol_ug = Column(Numeric(10, 3))  # 레티놀(μg): 3.000
    beta_carotene_ug = Column(Numeric(10, 3))  # 베타카로틴(μg): 0.000
    thiamin_mg = Column(Numeric(10, 3))  # 티아민(mg): 0.192
    riboflavin_mg = Column(Numeric(10, 3))  # 리보플라빈(mg): 0.065
    niacin_mg = Column(Numeric(10, 3))  # 니아신(mg): 0.992
    vitamin_c_mg = Column(Numeric(10, 3))  # 비타민 C(mg): 7.880
    vitamin_d_ug = Column(Numeric(10, 3))  # 비타민 D(μg): 0.000
    cholesterol_mg = Column(Numeric(10, 3))  # 콜레스테롤(mg): 64.410
    saturated_fat_g = Column(Numeric(10, 3))  # 포화지방산(g): 6.500
    trans_fat_g = Column(Numeric(10, 3))  # 트랜스지방산(g): 0.070

    # Relationship
    food_info = relationship("FoodInfo", back_populates="nutrition", uselist=False)
    
class FoodInfoTag(Base):
    __tablename__ = "food_info_tag"

    food_id = Column(String(19), ForeignKey("food_info.food_id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("food_tag.tag_id"), primary_key=True)

class FoodTag(Base):
    __tablename__ = "food_tag"

    tag_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag_name = Column(String(500), nullable=False)

    # Relationship
    food_info = relationship("FoodInfo", back_populates="tags", secondary="food_info_tag")
