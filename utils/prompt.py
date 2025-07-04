from typing import List
import pandas as pd
import ast
from langchain.prompts import PromptTemplate

# ✅ prompt 작성
def build_prompt(
    ingredients,
    filtered_recipes,
    context=None,
    disease=None,
    allergies=None,
    diet_preference=None
) -> str:
    
    # 기본 사용자 정보 문자열 구성
    user_info = f"입력한 재료: {ingredients}"
    if allergies and allergies != "해당없음":
        user_info += f"\n알러지 정보: {allergies}"
    if diet_preference and diet_preference != "해당없음":
        user_info += f"\n식단 선호: {diet_preference}"
    if disease and disease != "해당없음":
        user_info += f"\n질환 정보: {disease}"

    # context가 존재하는 경우
    if disease and context:
        prompt = f"""당신은 요리와 영양에 정통한 전문가입니다.

{user_info}

아래 문서를 참고하여 '{disease}' 질환을 가진 사용자를 위한 적절한 레시피를 추천해주세요.

후보 레시피 목록:
{filtered_recipes}

요청사항:
- 위 정보를 종합해 가장 적절한 레시피 하나를 추천해주세요.
- 반드시 레시피 목록에서 고른 레시피여야 합니다.
- 해당 레시피의 재료와 조리 과정을 알려주세요.
- 어떤 점에서 '{disease}' 환자에게 이 레시피가 적합한지 설명해주세요.

참고 문서:
{context}
"""
    else:
        # 일반 사용자 프롬프트
        prompt = f"""당신은 요리 전문가입니다.

{user_info}

후보 레시피 목록:
{filtered_recipes}

요청사항:
- 위 정보를 종합해 가장 적절한 레시피 하나를 추천해주세요.
- 반드시 레시피 목록에서 고른 레시피여야 합니다.
- 해당 레시피의 재료와 조리 과정을 알려주세요.
"""
    return prompt

# # RAG 프롬프트 생성 함수
# def build_prompt_with_context(
#     ingredients,
#     filtered_recipes,
#     context=None,
#     disease=None,
#     allergies=None,
#     diet_preference=None
# ) -> str:
#     # 조건별 정보 처리
#     disease_text = f"- 질환: {disease}" if disease and disease != "해당없음" else ""
#     allergies_text = f"- 알러지: {allergies}" if allergies and allergies != "해당없음" else ""
#     diet_text = f"- 선호 식단: {diet_preference}" if diet_preference and diet_preference != "해당없음" else ""
    
#     # context가 있을 경우만 문서 포함
#     context_section = f"\n참고 문서:\n{context}\n" if disease and context and context != "해당없음" else ""

#     return f"""당신은 요리와 영양에 정통한 전문가입니다.

# 사용자 정보:
# - 입력 재료: {ingredients}
# {disease_text}
# {allergies_text}
# {diet_text}
# {context_section}
# 아래는 추천 후보 레시피 목록입니다:
# {filtered_recipes}

# 요청사항:
# - 사용자 정보를 기반으로, 위 레시피 중 입력 재료와 가장 유사한 재료를 사용하는 **가장 적절한 레시피 하나만** 선택하여 추천해주세요.
# - 사용자 정보의 질환에 {disease}이 있다면, 위 참고 문서 기반으로 {disease}의 식단 정보를 참고하여 위 레시피 중 **가장 적절한 하나만** 선택하여 추천해주세요.
# - 반드시 레시피 목록에서 고른 레시피여야 합니다.
# - 추천 이유를 설명해주세요.
# - 해당 레시피의 재료와 조리 과정을 요약해주세요.
# """

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
                                 ingredients: str,
                                 allergy: str) -> pd.DataFrame:
    
    # 입력 문자열을 리스트로 변환
    selected_ingredients = [item.strip() for item in ingredients.split(',')] if ingredients else []
    allergy_list = [item.strip() for item in allergy.split(',')] if allergy and allergy.strip() != "해당없음" else []

    def is_valid(row):
        try:
            row_ingredients = ast.literal_eval(row["재료"])
            clean_ingredients = [i.split()[0] for i in row_ingredients if i]
        except Exception:
            return False

        # ❌ 알러지 성분이 하나라도 포함되면 제외
        if any(allergen in clean_ingredients for allergen in allergy_list):
            return False

        # ✅ 선택한 재료가 하나라도 포함되면 통과
        return any(sel in clean_ingredients for sel in selected_ingredients)

    filtered_df = df[df.apply(is_valid, axis=1)].reset_index(drop=True)

    # 최대 300개까지만 반환
    if len(filtered_df) > 100:
        filtered_df = filtered_df.sample(n=300, random_state=42).reset_index(drop=True)

    return filtered_df

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


