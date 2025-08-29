from db.tables.food_table import FoodTag, FoodInfo, FoodInfoTag, FoodCategory, FoodSourceInfo, FoodCompany, FoodNutrition
import model.domain.food as food_domain
from typing import List, Optional
import functools
import logging

"""
food:
    create
        name only not id
    search by id
    search by name
    search by tag
    update
        add tags
        remove tags
    delete by id
"""

logger = logging.getLogger(__name__)

class FoodMixin:
    """음식 관련 DB입출력 기능 모음, 상속해서 사용"""

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
    
    def get_food_by_id(self, food_id: str) -> food_domain.Food:
        """음식 조회"""
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
        food_info = self.session.query(FoodInfo).filter(FoodInfo.food_id == food_id).first()
        return food_domain.Food.from_db_model(food_info)
    
    def get_food_by_name(self, food_name: str) -> food_domain.Food:
        """음식 조회"""
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
        food_info = self.session.query(FoodInfo).filter(FoodInfo.food_name == food_name).first()
        return food_domain.Food.from_db_model(food_info)
    
    def get_food_by_tag(self, tag_name: str) -> List[food_domain.Food]:
        """음식 태그 조회"""
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. 반드시 with문 또는 transaction 컨텍스트 내에서 사용하세요.")
        food_infos = self.session.query(FoodInfo).filter(FoodInfo.tags.any(FoodTag.tag_name == tag_name)).all()
        return [food_domain.Food.from_db_model(food_info) for food_info in food_infos]
    

    @check_session
    def create_food(
        self, 
        food_id: str,
        name: str,
        data_type_code: str | None = None,
        major_category_name: str | None = None,
        medium_category_name: str | None = None,
        minor_category_name: str | None = None,
        detail_category_name: str | None = None,
        representative_food_name: str | None = None,
        origin_name: str | None = None,
        source_name: str | None = None,
        generation_method_name: str | None = None,
        reference_date: str | None = None,
        company_name: str | None = None,
        manufacturer_name: str | None = None,
        origin_country_name: str | None = None,
        importer_name: str | None = None,
        distributor_name: str | None = None,
        mfg_report_no: str | None = None,
        weight: str | None = None,
        serving_size_g: str | None = None,
        nutrient_reference_amount_g: str | None = None,
        energy_kcal: str | None = None,
        moisture_g: str | None = None,
        protein_g: str | None = None,
        fat_g: str | None = None,
        ash_g: str | None = None,
        carbohydrate_g: str | None = None,
        sugars_g: str | None = None,
        dietary_fiber_g: str | None = None,
        calcium_mg: str | None = None,
        iron_mg: str | None = None,
        phosphorus_mg: str | None = None,
        potassium_mg: str | None = None,
        sodium_mg: str | None = None,
        vitamin_a_ug_rae: str | None = None,
        retinol_ug: str | None = None,
        beta_carotene_ug: str | None = None,
        thiamin_mg: str | None = None,
        riboflavin_mg: str | None = None,
        niacin_mg: str | None = None,
        vitamin_c_mg: str | None = None,
        vitamin_d_ug: str | None = None,
        cholesterol_mg: str | None = None,
        saturated_fat_g: str | None = None,
        trans_fat_g: str | None = None,
        tags: list[str] | None = None) -> bool:
        """음식 생성"""

        try:
            food = FoodInfo(
                food_id=food_id,
                food_name=name,
                data_type_code=data_type_code,
                category=FoodCategory(
                    major_category_name=major_category_name,
                    medium_category_name=medium_category_name,
                    minor_category_name=minor_category_name,
                    detail_category_name=detail_category_name,
                    representative_food_name=representative_food_name,
                ),
                source_info=FoodSourceInfo(
                    origin_name=origin_name,
                    source_name=source_name,
                    generation_method_name=generation_method_name,
                    reference_date=reference_date,
                ),
                company=FoodCompany(
                    company_name=company_name,
                    manufacturer_name=manufacturer_name,
                    origin_country_name=origin_country_name,
                    importer_name=importer_name,
                    distributor_name=distributor_name,
                    mfg_report_no=mfg_report_no,
                ),
                nutrition=FoodNutrition(
                    weight=weight,
                    serving_size_g=serving_size_g,
                    nutrient_reference_amount_g=nutrient_reference_amount_g,
                    energy_kcal=energy_kcal,
                    moisture_g=moisture_g,
                    protein_g=protein_g,
                    fat_g=fat_g,
                    ash_g=ash_g,
                    carbohydrate_g=carbohydrate_g,
                    sugars_g=sugars_g,
                    dietary_fiber_g=dietary_fiber_g,
                    calcium_mg=calcium_mg,
                    iron_mg=iron_mg,
                    phosphorus_mg=phosphorus_mg,
                    potassium_mg=potassium_mg,
                    sodium_mg=sodium_mg,
                    vitamin_a_ug_rae=vitamin_a_ug_rae,
                    retinol_ug=retinol_ug,
                    beta_carotene_ug=beta_carotene_ug,
                    thiamin_mg=thiamin_mg,
                    riboflavin_mg=riboflavin_mg,
                    niacin_mg=niacin_mg,
                    vitamin_c_mg=vitamin_c_mg,
                    vitamin_d_ug=vitamin_d_ug,
                    cholesterol_mg=cholesterol_mg,
                    saturated_fat_g=saturated_fat_g,
                    trans_fat_g=trans_fat_g,
                ),
                tags=[FoodTag(tag_name=tag) for tag in tags],
            )
            self.session.add(food)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"음식 생성 실패: {e}")
            return False
    

    @check_session
    def update_food_tags(self, food_id: str, tags: list[str]) -> bool:
        """음식 태그 업데이트"""
        food = self.get_food_by_id(food_id)
        if food is None:
            return False
        food.food_tags = [FoodTag(tag_name=tag) for tag in tags]
        return True
    

    @check_session
    def delete_food_tags(self, food_id: str) -> bool:
        """음식 태그 삭제"""
        food = self.get_food_by_id(food_id)
        if food is None:
            return False
        food.tags = []
        return True