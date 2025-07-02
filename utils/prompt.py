from typing import List


# ✅ prompt 작성
def build_prompt(ingredients: str, detailed_recipes: str, context: str = None, disease: str = None) -> str:
    if disease and context:
        prompt = f"""당신은 요리와 영양에 정통한 전문가입니다.

다음 문서를 참고하여 '{disease}' 질환을 가진 사용자를 위한 적절한 식단을 고려해주세요.  
사용자가 입력한 재료인 '{ingredients}'를 활용하여, '{detailed_recipes}' 중에서 가장 적절한 하나의 레시피를 한국어로 추천해주세요.

요청사항:
- 해당 레시피의 과정과 재료를 알려주세요.
- 어떤 점에서 '{disease}' 환자에게 이 레시피를 추천해줬는지 구체적으로 설명해주세요.
- '{detailed_recipes}'에서 총 몇 개의 레시피가 있는지 알려주세요.

참고 문서:
{context}
"""
    else:
        prompt = f"""당신은 요리 전문가입니다.

사용자가 입력한 재료인 '{ingredients}'를 활용하여, '{detailed_recipes}' 중에서 가장 적절한 하나의 레시피를 한국어로 추천해주세요.

요청사항:
- 해당 레시피의 과정과 재료를 알려주세요.
- '{detailed_recipes}'에서 총 몇 개의 레시피가 있는지 알려주세요.
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

