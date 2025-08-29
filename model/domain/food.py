from pydantic import BaseModel
from typing import List


class MandatoryNutrition(BaseModel):
    __pydantic_plugin_host__ = False
    energy_kcal: float | None = None # 에너지(kcal): 260.000
    protein_g: float | None = None # 단백질(g): 21.240
    fat_g: float | None = None # 지방(g): 17.870
    carbohydrate_g: float | None = None # 탄수화물(g): 3.580
    sugars_g: float | None = None # 당류(g): 0.310
    sodium_mg: float | None = None # 나트륨(mg): 177.000
    cholesterol_mg: float | None = None # 콜레스테롤(mg): 64.410
    saturated_fat_g: float | None = None # 포화지방산(g): 6.500
    trans_fat_g: float | None = None # 트랜스지방산(g): 0.070


class FoodNutrition(MandatoryNutrition):
    __pydantic_plugin_host__ = False
    weight: str | None = None # 식품중량: 900g
    serving_size_g: str | None = None # 1회 섭취참고량: 30g
    nutrient_reference_amount_g: str | None = None # 영양성분함량기준량: 100g
    moisture_g: float | None = None # 수분(g): 56.800
    ash_g: float | None = None # 회분(g): 0.530
    dietary_fiber_g: float | None = None # 식이섬유(g): 0.000
    calcium_mg: float | None = None # 칼슘(mg): 6.000
    iron_mg: float | None = None # 철(mg): 0.840
    phosphorus_mg: float | None = None # 인(mg): 89.000
    potassium_mg: float | None = None # 칼륨(mg): 58.000
    vitamin_a_ug_rae: float | None = None # 비타민A(μg RAE): 3.000
    retinol_ug: float | None = None # 레티놀(μg): 3.000
    beta_carotene_ug: float | None = None # 베타카로틴(μg): 0.000
    thiamin_mg: float | None = None # 티아민(mg): 0.192
    riboflavin_mg: float | None = None # 리보플라빈(mg): 0.065
    niacin_mg: float | None = None # 니아신(mg): 0.992
    vitamin_c_mg: float | None = None # 비타민 C(mg): 7.880
    vitamin_d_ug: float | None = None # 비타민 D(μg): 0.000

    def get_mandatory_nutrition(self) -> MandatoryNutrition:
        return MandatoryNutrition(
            energy_kcal=self.energy_kcal,
            protein_g=self.protein_g,
            fat_g=self.fat_g,
            carbohydrate_g=self.carbohydrate_g,
            sugars_g=self.sugars_g,
            sodium_mg=self.sodium_mg,
            cholesterol_mg=self.cholesterol_mg,
            saturated_fat_g=self.saturated_fat_g,
            trans_fat_g=self.trans_fat_g,
        )


class FoodTag(BaseModel):
    tag_id: int
    tag_name: str

class FoodCategory(BaseModel):
    major_category_name: str | None = None
    medium_category_name: str | None = None
    minor_category_name: str | None = None
    detail_category_name: str | None = None
    representative_food_name: str | None = None

class Food(BaseModel):
    food_id: str | None = None
    food_name: str
    food_nutrition: FoodNutrition | None = None
    food_tags: List[FoodTag] | None = None
    food_category: FoodCategory | None = None

    @classmethod
    def from_db_model(cls, food_info) -> 'Food':
        if (food_nutrition := food_info.nutrition) is not None:
            food_nutrition = FoodNutrition(
                weight=food_info.nutrition.weight,
                serving_size_g=food_info.nutrition.serving_size_g,
                nutrient_reference_amount_g=food_info.nutrition.nutrient_reference_amount_g,
                energy_kcal=food_info.nutrition.energy_kcal,
                protein_g=food_info.nutrition.protein_g,
                fat_g=food_info.nutrition.fat_g,
                carbohydrate_g=food_info.nutrition.carbohydrate_g,
                sugars_g=food_info.nutrition.sugars_g,
                sodium_mg=food_info.nutrition.sodium_mg,
                cholesterol_mg=food_info.nutrition.cholesterol_mg,
                saturated_fat_g=food_info.nutrition.saturated_fat_g,
                trans_fat_g=food_info.nutrition.trans_fat_g,
                moisture_g=food_info.nutrition.moisture_g,
                ash_g=food_info.nutrition.ash_g,
                dietary_fiber_g=food_info.nutrition.dietary_fiber_g,
                calcium_mg=food_info.nutrition.calcium_mg,
                iron_mg=food_info.nutrition.iron_mg,
                phosphorus_mg=food_info.nutrition.phosphorus_mg,
                potassium_mg=food_info.nutrition.potassium_mg,
                vitamin_a_ug_rae=food_info.nutrition.vitamin_a_ug_rae,
                retinol_ug=food_info.nutrition.retinol_ug,
                beta_carotene_ug=food_info.nutrition.beta_carotene_ug,
                thiamin_mg=food_info.nutrition.thiamin_mg,
                riboflavin_mg=food_info.nutrition.riboflavin_mg,
                niacin_mg=food_info.nutrition.niacin_mg,
                vitamin_c_mg=food_info.nutrition.vitamin_c_mg,
                vitamin_d_ug=food_info.nutrition.vitamin_d_ug,
            )

        if (food_tags := food_info.tags) is not None:
            food_tags = [FoodTag(tag_id=tag.tag_id, tag_name=tag.tag_name) for tag in food_info.tags]
        
        if (food_category := food_info.category) is not None:
            food_category = FoodCategory(
                major_category_name=food_info.category.major_category_name,
                medium_category_name=food_info.category.medium_category_name,
                minor_category_name=food_info.category.minor_category_name,
                detail_category_name=food_info.category.detail_category_name,
                representative_food_name=food_info.category.representative_food_name,
            )

        return Food(
            food_id=food_info.food_id,
            food_name=food_info.food_name,
            food_nutrition=food_nutrition,
            food_tags=food_tags,
            food_category=food_category,
        )