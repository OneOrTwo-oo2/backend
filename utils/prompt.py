import pandas as pd
import ast
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from tqdm import tqdm
import time

def search_top_k(
    query,
    vectordb,
    model,
    top_k=5,
    exclude_ingredients_str=None,
    difficulty_levels_str=None,
    types_str=None
):
    # 문자열 → 리스트 변환
    exclude_ingredients = [i.strip() for i in exclude_ingredients_str.split(",")] if exclude_ingredients_str else []
    difficulty_levels = [d.strip() for d in difficulty_levels_str.split(",")] if difficulty_levels_str else []
    types = [t.strip() for t in types_str.split(",")] if types_str else []

    # ✅ 벡터 검색 (여유 있게 top_k * 10개 가져와서 필터링)
    query_vector = model.encode([query]).astype("float32")
    scores, indices = vectordb.index.search(query_vector, k=top_k * 10)

    results = []
    for i, idx in enumerate(indices[0]):
        doc_id = vectordb.index_to_docstore_id[idx]
        doc = vectordb.docstore.search(doc_id)
        meta = doc.metadata
        score = scores[0][i]

        재료 = meta.get("재료", "")
        난이도 = meta.get("난이도", "").strip()
        종류 = meta.get("종류", "").strip()

        # 2. exclude_ingredients: 재료 문자열 안에 하나라도 포함되면 제외
        if any(exc in 재료 for exc in exclude_ingredients):
            continue

        # 3. 난이도 필터링 (정확히 일치)
        if difficulty_levels and 난이도 not in difficulty_levels:
            continue

        # 4. 종류 필터링 (정확히 일치)
        if types and 종류 not in types:
            continue

        # ✅ 결과 저장
        meta["score"] = score
        results.append((doc, score))

        # ✅ top_k만 남기고 중단
        if len(results) >= top_k:
            break

    return results


# ✅ 결과 정리: WatsonX로 넘길 후보 레시피 텍스트 구성
def format_recipe(doc: Document, index: int) -> str:
    meta = doc.metadata
    return f"""{index}. {meta.get('제목', '')}
- 종류: {meta.get('종류','')}
- 인분: {meta.get('인분', '')}
- 난이도: {meta.get('난이도', '')}
- 조리시간: {meta.get('조리시간', '')}
- 재료: {meta.get('재료', '')}
- 조리순서: {meta.get('조리순서', '')}
- url: {meta.get('URL', '')}
"""


def build_prompt(
    ingredients,
    filtered_recipes,
    context=None,
    disease=None,
    allergies=None,
    diet_preference=None
) -> str:
    
    user_info = f"입력한 재료: {ingredients}"
    if allergies and allergies != "해당없음":
        user_info += f"\n알러지 정보: {allergies}"
    if diet_preference and diet_preference != "해당없음":
        user_info += f"\n식단 선호: {diet_preference}"
    if disease and disease != "해당없음":
        user_info += f"\n질환 정보: {disease}"

    if disease and context:
        prompt = f"""당신은 요리와 영양에 정통한 전문가입니다.

{user_info}

아래 문서를 참고하여 '{disease}' 질환을 가진 사용자를 위한 적절한 레시피를 추천해주세요.

후보 레시피 목록:
{filtered_recipes}

요청사항:
- 위 정보를 종합해 가장 적절한 레시피 3개를 추천해주세요.
- 반드시 레시피 목록에서 고른 레시피여야 합니다.
- 입력한 재료와 가장 비슷한 재료를 사용한 레시피를 우선으로 추천해주세요.
- 해당 레시피의 제목, 인분, 난이도, 조리시간, 재료, 조리순서를 알려주세요 (해당 레시피와 똑같이!).
- 어떤 점에서 '{disease}' 환자에게 이 레시피가 적합한지 설명해주세요.
- '{disease}' 환자에게 좋은 식습관을 간단하게 설명해주세요.
- 마지막에 추천한 레시피들의 URL을 함께 제공해주세요.

참고 문서:
{context}
"""
    else:
        prompt = f"""당신은 요리 전문가입니다.

{user_info}

후보 레시피 목록:
{filtered_recipes}

요청사항:
- 위 정보를 종합해 가장 적절한 레시피 3개를 추천해주세요.
- 반드시 후보 레시피 목록에서 고른 레시피여야 합니다.
- 입력한 재료와 가장 비슷한 재료를 사용한 레시피를 우선으로 추천해주세요.
- 해당 레시피의 제목, 인분, 난이도, 조리시간, 재료, 조리순서를 알려주세요 (해당 레시피와 똑같이!).
- 마지막에 추천한 레시피들의 URL을 함께 제공해주세요.
"""
    return prompt