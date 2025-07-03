from typing import List
import pandas as pd
import ast
from langchain.prompts import PromptTemplate

# ✅ prompt 작성
def build_prompt(ingredients: str, detailed_recipes: str, context: str = None, disease: str = None) -> str:
    if disease and context:
        prompt = f"""다음 문서를 참고하여 '{disease}' 질환을 가진 사용자를 위한 적절한 식단을 고려해주세요.  
사용자가 입력한 재료인 '{ingredients}'를 활용하여, '{detailed_recipes}' 중에서 가장 적절한 하나의 레시피를 한국어로 추천해주세요.

요청사항:
- 해당 레시피의 과정과 재료를 알려주세요.
- 어떤 점에서 '{disease}' 환자에게 이 레시피를 추천해줬는지 구체적으로 설명해주세요.

참고 문서:
{context}
"""
    else:
        prompt = f"""사용자가 입력한 재료인 '{ingredients}'를 활용하여, '{detailed_recipes}' 중에서 가장 적절한 하나의 레시피를 한국어로 추천해주세요.

요청사항:
- 해당 레시피의 과정과 재료를 알려주세요.
"""
    return prompt


# RAG 프롬프트 생성 함수
def build_prompt_with_context(
    ingredients,
    filtered_recipes,
    context,
    disease,
    allergies,
    diet_preference
) -> str:
    prompt = f"""당신은 요리와 영양에 정통한 전문가입니다.

사용자 정보:
- 입력 재료: {ingredients}
- 질환: {disease or "없음"}
- 알러지: {allergies}
- 선호 식단단: {diet_preference}

참고 문서:
{context or "해당 없음"}

아래는 추천 후보 레시피 목록입니다:
{filtered_recipes}

요청사항:
- 위 조건을 종합해 가장 적절한 레시피 하나를 추천해주세요.
- 추천한 레시피의 재료, 과정을 정리해주세요.
- 추천 이유를 명확히 설명해주세요.
- 총 후보 레시피 수를 알려주세요.
"""
    return prompt


# ✅ 포맷 변환 함수 (레시피 정보 json -> 자연어 포맷)
def format_recipes_for_prompt(detailed_recipes: List[dict], max_count=5) -> str:
    formatted = []

    for i, recipe in enumerate(detailed_recipes[:max_count], 1):
        title = recipe["title"]
        intro = recipe["intro"]
        ingredients = ", ".join(recipe["ingredients"])
        steps = " → ".join(recipe["steps"])

        formatted.append(
            f"{i}. {title}\n소개: {intro}\n재료: {ingredients}\n조리법: {steps}\n"
        )

    return "\n\n".join(formatted)

# ✅ 알러지 제외, 재료가 포함된 레시피만 추출
def filter_recipes_include_only(df: pd.DataFrame,
                                 selected_ingredients: list,
                                 allergy_list: list) -> pd.DataFrame:
    
    def is_valid(row):
        try:
            ingredients = ast.literal_eval(row["재료"])
            clean_ingredients = [i.split()[0] for i in ingredients if i]  # "감자 2개" → "감자"
        except Exception:
            return False

        # ❌ 알러지 재료가 하나라도 포함되어 있으면 제외
        if any(allergen in clean_ingredients for allergen in allergy_list):
            return False

        # ✅ 선택한 재료 중 하나라도 포함되어 있으면 포함
        if any(sel in clean_ingredients for sel in selected_ingredients):
            return True
        
        return False

    return df[df.apply(is_valid, axis=1)].reset_index(drop=True)


# CSV 일부 레시피를 요약 포맷으로 변환
def format_recipes_for_prompt(df: pd.DataFrame) -> str:
    formatted = []
    for i, row in df.iterrows():
        formatted.append(
            f"{i+1}. {row['제목']}\n"
            f"- 재료: {row['재료']}\n"
            f"- 조리법: {row['종류']}\n"
            f"- 소개: {row['소개글']}\n"
            f"- 해시태그: {row['해시태그']}"
        )
    return "\n\n".join(formatted)


# # 병합 실행
# filtered_df = filter_by_allergy(df, user_profile["allergies"])
# recipes_text = format_recipes_for_prompt(filtered_df)
# context_text = "\n\n".join([doc.page_content for doc in vectordb.similarity_search(user_profile["disease"] + " 식단", k=5)])

# prompt = build_prompt_with_context(user_profile, recipes_text, context_text)

# print(prompt)


