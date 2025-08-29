from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import time, date

from db.db_manager import DBManager
from qdrant_manager import qdrant_manager


# @tool
# def search_food_name(
#     food_name: str
# ) -> Dict[str, str] | None:
#     """
#     Qdrant에서 음식 이름을 검색하여 가장 유사한 음식의 food_id와 food_name을 반환합니다.  
#     유사도 측정은 코사인 유사도(cosine similarity)를 사용하여 Qdrant의 벡터 검색 기능을 통해 이루어집니다.

#     Args:
#         food_name: 검색할 음식 이름 (문자열)

#     Returns:
#         가장 유사한 음식의 food_id와 food_name을 포함하는 사전.  유사한 음식이 없거나 에러 발생 시 None을 반환합니다.
#         예시: {"food_id": "D101-004160000-0001", "food_name": "김치찌개"}
#     """
#     try:
#         result = qdrant_manager.get_documents(food_name, collection_name=qdrant_manager.collection_names.food_name_collection)
#         if result:
#             result = result[0].payload.get("metadata", None)
#             return {"food_id": result.get("food_id", None), "food_name": result.get("food_name", None)}
#         else:
#             return None  # 검색 결과가 없을 경우 None 반환
#     except Exception as e:
#         print(f"Error in search_food_name: {e}")
#         return None  # 에러 발생 시 None 반환
    

@tool
def search_food_tag(
    food_tag: str
) -> Dict[str, str] | None:
    """
    Qdrant에서 태그 이름을 검색하여 가장 유사한 태그의 tag_id와 tag_name을 반환합니다.
    유사도 측정은 코사인 유사도(cosine similarity)를 사용하여 Qdrant의 벡터 검색 기능을 통해 이루어집니다.

    Args:
        food_tag: 검색할 태그 이름 (문자열)

    Returns:
        가장 유사한 태그의 tag_id와 tag_name을 포함하는 사전. 유사한 태그가 없거나 에러 발생 시 None을 반환합니다.
        예시: {"tag_id": "T001", "tag_name": "고단백"}
    """
    try:
        result = qdrant_manager.get_documents(food_tag, collection_name=qdrant_manager.collection_names.food_tag_collection)
        if result:
            result = result[0].payload.get("metadata", None)
            return {"tag_id": result.get("tag_id", None), "tag_name": result.get("tag_name", None)}
        else:
            return None  # 검색 결과가 없을 경우 None 반환
    except Exception as e:
        print(f"Error in search_food_tag: {e}")
        return None  # 에러 발생 시 None 반환


# @tool
# def get_nutrient_info(
#     food_id: str
# ) -> Dict[str, float | None] | None:
#     """
#     DB에서 food_id에 해당하는 음식의 영양 정보를 사전 형태로 반환합니다.

#     Args:
#         food_id: 음식의 고유 ID (문자열).  예: "D101-004160000-0001"

#     Returns:
#         food_id에 해당하는 영양 정보를 담은 사전.  영양 정보가 없거나 데이터베이스에서 food_id를 찾을 수 없으면 None을 반환합니다.
#         각 영양소의 값은 float형이며,  데이터가 없는 경우 None으로 표시됩니다.
#         예시:
#         {
#             'energy_kcal': 200.5,
#             'moisture_g': 60.0,
#             'protein_g': 10.0,
#             'fat_g': 5.0,
#             'ash_g': 2.0,
#             'carbohydrate_g': 12.5,
#             'sugars_g': 5.0,
#             'dietary_fiber_g': 2.0,
#             'calcium_mg': 100.0,
#             'iron_mg': 2.0,
#             'phosphorus_mg': 80.0,
#             'potassium_mg': 300.0,
#             'sodium_mg': 150.0,
#             'vitamin_a_ug_rae': 50.0,
#             'retinol_ug': 25.0,
#             'beta_carotene_ug': 25.0,
#             'thiamin_mg': 0.5,
#             'riboflavin_mg': 0.6,
#             'niacin_mg': 5.0,
#             'vitamin_c_mg': 10.0,
#             'vitamin_d_ug': 2.0,
#             'cholesterol_mg': 50.0,
#             'saturated_fat_g': 2.0,
#             'trans_fat_g': 0.5
#         }

#     Raises:
#         Exception: 데이터베이스 연결 실패 또는 예상치 못한 에러 발생 시.
#     """
#     db = DBManager()
#     try:
#         with db as manager:
#             food_info = manager.get_food_info(food_id)
#             if food_info and food_info.get("nutrition"):
#                 return food_info["nutrition"]
#             else:
#                 return None
#     except Exception as e:
#         print(f"Error in get_nutrient_info: {e}")
#         return None
    

@tool
def get_food_nutrient(food_name: str) -> Dict[str, float | None] | str:
    """
    음식 이름으로 해당 음식의 영양 정보를 가져옵니다.

    Args:
        food_name: 검색할 음식 이름 (문자열)

    Returns:
        음식의 영양 정보를 담은 사전.
        해당 음식의 정보가 없거나 영양 정보를 가져오는 데 실패하면 None을 반환합니다.
        영양 정보 사전의 예시:
        {
            'serving_size_g': '100g',
            'nutrient_reference_amount_g': '100g',
            'energy_kcal': 200.5,
            'moisture_g': 60.0,
            'protein_g': 10.0,
            'fat_g': 5.0,
            'ash_g': 2.0,
            'carbohydrate_g': 12.5,
            'sugars_g': 5.0,
            'dietary_fiber_g': 2.0,
            'calcium_mg': 100.0,
            'iron_mg': 2.0,
            'phosphorus_mg': 80.0,
            'potassium_mg': 300.0,
            'sodium_mg': 150.0,
            'vitamin_a_ug_rae': 50.0,
            'retinol_ug': 25.0,
            'beta_carotene_ug': 25.0,
            'thiamin_mg': 0.5,
            'riboflavin_mg': 0.6,
            'niacin_mg': 5.0,
            'vitamin_c_mg': 10.0,
            'vitamin_d_ug': 2.0,
            'cholesterol_mg': 50.0,
            'saturated_fat_g': 2.0,
            'trans_fat_g': 0.5
        }
    """
    try:
        datas = qdrant_manager.get_documents(food_name, collection_name=qdrant_manager.collection_names.food_name_collection)
        if len(datas) == 0:
            return f"'{food_name}'에 대한 음식 ID를 찾을 수 없거나 검색에 실패했습니다."
        
        payload = datas[0].payload
        food_id = payload.get("metadata", {}).get("food_id", None)

        if food_id is None:
            return f"'{food_name}'에 대한 음식 ID를 찾을 수 없거나 검색에 실패했습니다."

        db = DBManager()
        with db as manager:
            food_info = manager.get_food_info(food_id)
            if food_info.get("nutrition", None) is None:
                return f"'{food_name}'에 대한 영양 정보를 찾을 수 없습니다."
            else:
                return food_info["nutrition"]
    except Exception as e:
        return f"'{food_name}'에 대한 영양 정보를 찾는 데 실패했습니다. {e}"


class NutrientData(BaseModel):
    """사용자의 일일 권장 영양소 섭취량 데이터."""
    energy_kcal: float = Field(..., description="권장 일일 에너지 섭취량 (kcal).")
    protein_g: float = Field(..., description="권장 일일 단백질 섭취량 (g).")
    fat_g: float = Field(..., description="권장 일일 지방 섭취량 (g).")
    carbohydrate_g: float = Field(..., description="권장 일일 탄수화물 섭취량 (g).")
    sugars_g: float = Field(..., description="권장 일일 당류 섭취량 (g).")
    sodium_mg: float = Field(..., description="권장 일일 나트륨 섭취량 (mg).")
    cholesterol_mg: float = Field(..., description="권장 일일 콜레스테롤 섭취량 (mg).")
    saturated_fat_g: float = Field(..., description="권장 일일 포화지방 섭취량 (g).")
    trans_fat_g: float = Field(..., description="권장 일일 트랜스지방 섭취량 (g).")


@tool
def format_nutrient_json(nutrient_data: NutrientData) -> Dict:
    """
    사용자의 계산된 영양소 값을 Pydantic 클래스를 통해 표준화된 JSON 구조로 포맷팅합니다.
    
    Args:
        nutrient_data: 일일 권장 영양소 섭취량 데이터가 담긴 NutrientData 객체입니다.
    """
    return nutrient_data.model_dump()

@tool
def calculate_nutrient_sum(nutrient_data: List[NutrientData]) -> NutrientData:
    """
    일일 권장 영양소 섭취량 데이터를 합산하여 일일 영양 정보를 계산합니다.
    """
    total_nutrient_data = NutrientData()
    for nutrient in nutrient_data:
        total_nutrient_data.energy_kcal += nutrient.energy_kcal if nutrient.energy_kcal is not None else 0
        total_nutrient_data.protein_g += nutrient.protein_g if nutrient.protein_g is not None else 0
        total_nutrient_data.fat_g += nutrient.fat_g if nutrient.fat_g is not None else 0
        total_nutrient_data.carbohydrate_g += nutrient.carbohydrate_g if nutrient.carbohydrate_g is not None else 0
        total_nutrient_data.sugars_g += nutrient.sugars_g if nutrient.sugars_g is not None else 0
        total_nutrient_data.sodium_mg += nutrient.sodium_mg if nutrient.sodium_mg is not None else 0
        total_nutrient_data.cholesterol_mg += nutrient.cholesterol_mg if nutrient.cholesterol_mg is not None else 0
        total_nutrient_data.saturated_fat_g += nutrient.saturated_fat_g if nutrient.saturated_fat_g is not None else 0
        total_nutrient_data.trans_fat_g += nutrient.trans_fat_g if nutrient.trans_fat_g is not None else 0
    return total_nutrient_data.model_dump()

# 음식 이름과 영양 정보를 함께 담을 Pydantic 모델
class FoodItem(BaseModel):
    """식단 내의 단일 음식 항목입니다. 이름과 함께 9가지 영양 정보를 포함합니다."""
    food_name: str = Field(..., description="음식의 이름입니다.")
    food_amount: str = Field(..., description="섭취할 음식의 양입니다.")

# 각 식사를 나타내는 Pydantic 모델 (food_list 타입 변경)
class Meal(BaseModel):
    """단일 식사에 대한 상세 정보입니다."""
    time_slot: time = Field(..., description="식사 시간입니다. 'HH:MM' 형식의 분 단위 시간으로 표시됩니다 (예: '13:00').")
    food_list: List[FoodItem] = Field(..., description="해당 식사에 포함되는 음식 목록입니다.")

# 하루의 식단 계획을 나타내는 Pydantic 모델
class DailyPlan(BaseModel):
    """하루의 식단 계획 정보입니다."""
    day: date = Field(..., description="해당 식단 계획의 날짜입니다. 'YYYY-MM-DD' 형식의 일단위 날짜로 표시됩니다 (예: '2025-06-23').")
    meals: List[Meal] = Field(..., description="해당 요일의 식사 목록입니다.")
    nutrients: NutrientData = Field(..., description="해당 날짜의 9가지 영양 정보입니다.")

# 주간 식단 계획 전체를 나타내는 Pydantic 모델
class WeeklyMealPlan(BaseModel):
    """7일간의 주간 식단 계획 전체입니다."""
    days: List[DailyPlan] = Field(..., description="각 요일의 식단 계획 목록입니다. 총 7개의 DailyPlan 객체를 포함해야 합니다.")


@tool
def generate_weekly_meal_plan(meal_plan: WeeklyMealPlan) -> Dict[str, Any]:
    """
    언어 모델이 생성한 주간 식단 계획 데이터를 표준화된 JSON 구조로 포맷팅합니다.
    이 도구는 7일간의 식단 계획이 요구되는 형식에 부합하는지 확인하며,
    각 요일에는 시간대와 음식 목록을 포함하는 식사 목록이 포함됩니다.
    
    Args:
        meal_plan: 언어 모델에 의해 생성된 WeeklyMealPlan Pydantic 객체입니다.
                   이 객체는 각 요일별 식단 계획을 포함하며, 시간과 날짜 형식이 명확히 지정되어 있습니다.
                   각 식사는 시간대('HH:MM' 형식)와 음식 이름 목록을 포함해야 합니다.

    Returns:
        WeeklyMealPlan Pydantic 객체를 딕셔너리 형태로 변환한 주간 식단 계획입니다.
        이 출력은 이후 시스템에서 쉽게 파싱하고 사용할 수 있는 구조화된 데이터입니다.
    """
    return meal_plan.model_dump() 


@tool
def calculate_tdee(
    age: int,
    weight: float,
    height: float,
    activity_level: str
) -> float | str:
    """
    사용자의 나이, 체중, 키, 활동 수준을 기반으로 일일 총 에너지 소비량(TDEE)을 계산합니다.
    
    Args:
        age: 사용자의 나이 (정수)
        weight: 사용자의 체중 (kg)
        height: 사용자의 키 (cm)
        activity_level: 사용자의 활동 수준 (sedentary, lightly_exercising, moderately_exercising, heavy_exercising)
    
    Returns:
        일일 총 에너지 소비량(TDEE)을 반환합니다.
        활동 수준이 올바르지 않으면 올바른 활동 수준 목록을 반환합니다.
        계산에 실패하면 오류 메시지를 반환합니다.
    """
    try:
        if activity_level == "sedentary":
            tdee = 1.2 * (10 * weight + 6.25 * height - 5 * age + 5)
        elif activity_level == "lightly_exercise":
            tdee = 1.375 * (10 * weight + 6.25 * height - 5 * age + 5)
        elif activity_level == "moderately_exercising":
            tdee = 1.55 * (10 * weight + 6.25 * height - 5 * age + 5)
        elif activity_level == "heavy_exercising":
            tdee = 1.725 * (10 * weight + 6.25 * height - 5 * age + 5)
        else:
            return f"활동 수준이 올바르지 않습니다. 활동 수준은 'sedentary', 'lightly_exercising', 'moderately_exercising', 'heavy_exercising' 중 하나여야 합니다."
        
        return tdee
    except Exception as e:
        return f"TDEE 계산에 실패했습니다. {e}"


qdrant_retriever = qdrant_manager.get_retriever(qdrant_manager.collection_names.food_docs_collection)

retriever_tool = create_retriever_tool(
    qdrant_retriever, 
    name="retriever",
    description="공식 지침 및 영양학, 생리학 문서를 검색할 때 사용하세요.", 
    document_prompt=PromptTemplate.from_template(
        "<document><context>{page_content}</context><source>{source}</source></document>"
    )
)


if __name__ == "__main__":
    print(get_food_nutrient())