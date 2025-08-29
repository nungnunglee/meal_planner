import sys
from pathlib import Path
import pandas as pd
import numpy as np
import re
import json

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.database import engine, Base, root_engine, MYSQL_DATABASE, MYSQL_USER
from sqlalchemy import text
from db.tables.user_table import *
from db.tables.food_table import *
from sqlalchemy.exc import IntegrityError
from db.db_manager import DBManager

def create_all_tables(food_data_path, food_tag_data_path, replace_db=False):
    db = DBManager()

    with open(food_tag_data_path, 'r', encoding='utf-8') as f:
        food_tag_data = json.load(f)

    print("모든 데이터베이스 테이블 생성 시작...")
    
    with root_engine.connect() as connection:
        if replace_db:
            connection.execute(text(f"DROP DATABASE IF EXISTS {MYSQL_DATABASE}"))
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}"))
        connection.commit()
        print(f"데이터베이스 '{MYSQL_DATABASE}' 생성 또는 이미 존재 확인 완료.")

        connection.execute(text(f"GRANT ALL PRIVILEGES ON {MYSQL_DATABASE}.* TO '{MYSQL_USER}'@'%';"))
        connection.execute(text("FLUSH PRIVILEGES"))
        connection.commit()
        print(f"사용자 '{MYSQL_USER}'에게 '{MYSQL_DATABASE}' 데이터베이스에 대한 권한 부여 완료.")

    Base.metadata.create_all(engine)
    print("모든 데이터베이스 테이블 생성 완료!")

    if food_data_path is None:
        return

    print("음식 데이터 입력 시작...")
    
    # 데이터를 청크 단위로 읽기
    chunk_size = 1000
    total_rows = 0
    
    for chunk in pd.read_csv(food_data_path, encoding="utf-8", chunksize=chunk_size):
        chunk = chunk.copy()
        chunk = chunk.replace({pd.NA: None})
        
        # 현재 청크 내에서의 중복 제거 (이전에도 했지만 유지)
        food_info_df_for_unique_check = chunk.loc[:, ['food_id', 'food_name', 'data_type_code']]
        food_info_df_unique_in_chunk = food_info_df_for_unique_check.drop_duplicates(subset=['food_name'], keep='first')
        
        # 현재 청크에서 유니크한 food_id 리스트
        unique_food_ids_in_chunk = food_info_df_unique_in_chunk['food_id'].tolist()
        filtered_chunk_for_all_tables = chunk[chunk['food_id'].isin(unique_food_ids_in_chunk)].copy()

        inserted_food_ids = []
        with db as manager:
            for index, row in food_info_df_unique_in_chunk.iterrows():
                try:
                    # FoodInfo 테이블에 한 행씩 데이터 삽입하여 중복 시 건너뛰기
                    row_df = pd.DataFrame([row])
                    row_df.to_sql('food_info', engine, if_exists='append', index=False)
                    inserted_food_ids.append(row['food_id'])
                except IntegrityError as e:
                    if "Duplicate entry" in str(e) and "for key 'food_info.food_name'" in str(e):
                        duplicate_food_name_match = re.search(r"Duplicate entry '(.*?)' for key 'food_info.food_name'", str(e))
                        duplicate_food_name = duplicate_food_name_match.group(1) if duplicate_food_name_match else "알 수 없음"

                        # 데이터베이스에서 이미 존재하는 food_id 조회
                        existing_food_id = None
                        
                        food = manager.get_food_by_name(duplicate_food_name)
                        if food:
                            existing_food_id = food.food_id

                        print(f"[경고] 중복된 food_name 발견, 건너뜀: '{duplicate_food_name}'")
                        print(f"  현재 데이터의 food_id: {row['food_id']}")
                        print(f"  이미 데이터베이스에 있는 food_id: {existing_food_id}")
                    else:
                        print(f"[오류] 데이터 삽입 중 IntegrityError 발생: {e}")
                        return # 심각한 오류이므로 중단
                except Exception as e:
                    print(f"[오류] FoodInfo 삽입 중 알 수 없는 오류 발생: {e}")
                    return # 심각한 오류이므로 중단

        # 실제로 삽입된 food_id를 기준으로 다른 테이블 데이터 필터링
        final_filtered_chunk = filtered_chunk_for_all_tables[filtered_chunk_for_all_tables['food_id'].isin(inserted_food_ids)].copy()
        # tags_dict = food_tag_data[list(food_tag_data.keys()).isin(final_filtered_chunk['food_id'])]
        tags_dict = {}
        for food_id in final_filtered_chunk['food_id']:
            tags_dict[food_id] = food_tag_data[food_id]

        if final_filtered_chunk.empty:
            print("현재 청크에서 삽입할 유니크한 food_info 데이터가 없어 다음 청크로 이동합니다.")
            continue

        try:
            # FoodCategory 테이블에 데이터 삽입
            category_df = final_filtered_chunk.loc[:, ['food_id', 'major_category_name', 
                               'medium_category_name', 'minor_category_name',
                               'detail_category_name', 'representative_food_name']]
            category_df.to_sql('food_categories', engine, if_exists='append', index=False)

            # FoodSourceInfo 테이블에 데이터 삽입
            source_info_df = final_filtered_chunk.loc[:, ['food_id', 'origin_name', 
                                  'source_name', 'generation_method_name',
                                  'reference_date']]
            source_info_df.loc[:, 'reference_date'] = pd.to_datetime(source_info_df['reference_date']).dt.date
            source_info_df.to_sql('food_source_info', engine, if_exists='append', index=False)

            # FoodCompany 테이블에 데이터 삽입
            company_df = final_filtered_chunk.loc[:, ['food_id', 'company_name', 'manufacturer_name', 
                                 'origin_country_name', 'importer_name', 
                                 'distributor_name', 'mfg_report_no']]
            # Convert scientific notation to integer for mfg_report_no
            company_df.loc[:, 'mfg_report_no'] = pd.to_numeric(company_df['mfg_report_no'], errors='coerce')
            company_df = company_df.replace({np.nan: None})
            
            # food_id를 제외한 모든 컬럼이 None인 행 제외
            columns_to_check = [col for col in company_df.columns if col != 'food_id']
            company_df = company_df[~company_df[columns_to_check].isna().all(axis=1)]
            
            if not company_df.empty:
                company_df.to_sql('food_companies', engine, if_exists='append', index=False)

            # FoodNutrition 테이블에 데이터 삽입
            nutrition_df = final_filtered_chunk.loc[:, ['food_id', 'weight', 'serving_size_g', 'nutrient_reference_amount_g',
                               'energy_kcal', 'moisture_g', 'protein_g', 'fat_g', 'ash_g',
                               'carbohydrate_g', 'sugars_g', 'dietary_fiber_g', 'calcium_mg',
                               'iron_mg', 'phosphorus_mg', 'potassium_mg', 'sodium_mg',
                               'vitamin_a_ug_rae', 'retinol_ug', 'beta_carotene_ug',
                               'thiamin_mg', 'riboflavin_mg', 'niacin_mg', 'vitamin_c_mg',
                               'vitamin_d_ug', 'cholesterol_mg', 'saturated_fat_g', 'trans_fat_g']]
            nutrition_df.to_sql('food_nutrition', engine, if_exists='append', index=False)

            # FoodTag 테이블에 데이터 삽입
            with db as manager:
                for food_id, tag_names in tags_dict.items():
                    manager.update_food_tags(food_id, tag_names)

        except Exception as e:
            print(f"[오류] 관련 테이블 데이터 입력 중 오류 발생: {e}")
            print(f"오류 발생 chunk의 head:\n{final_filtered_chunk.head()}")
            return

        total_rows += len(chunk)
        print(f"{total_rows}개 데이터 처리 완료")

    print("음식 데이터 입력 완료!")


if __name__ == "__main__":
    food_data_path = "data/foods/combine_data_cleaned.csv"
    food_tag_data_path = "data/foods/food_tags.json"
    create_all_tables(food_data_path, food_tag_data_path, replace_db=True)