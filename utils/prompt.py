

# ✅ prompt 작성
def build_prompt(ingredients: str, detailed_recipes: str, context: str = None, disease: str = None) -> str:
    
    prompt = f"""당신은 요리 전문가입니다.
    
    다음 문서를 참고하여 '{disease}' 환자에게 맞는 식단과 재료를 파악하고,
    사용자가 제공한 재료를 활용해 '{detailed_recipes}'에 있는 레시피 중 가장 적절한 하나를 한국어로 추천해주세요.
    마지막에는 어떤'{disease}'에 적절한 요리인지 설명하고, 검색된 '{detailed_recipes}'의 레시피 총 갯수를 적어주세요.
    
    
    문서:{context}
    
    질문:{ingredients}를 활용한 요리 레시피를 추천해줘."""
    
    if disease and context:
        return prompt
    else:
        return f"""당신은 요리 전문가입니다.

    사용자가 제공한 재료를 활용해 '{detailed_recipes}'에 있는 레시피 중 가장장 적절한 하나를 한국어로 추천해주세요.
    마지막에는 '{detailed_recipes}' 의 총 갯수를 적어주세요."""
    
