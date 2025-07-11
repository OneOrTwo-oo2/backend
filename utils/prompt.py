import pandas as pd
import ast
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from tqdm import tqdm
import time
import json

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
    # 사용자 입력 정보 요약
    user_info = f"입력한 재료: {ingredients}"
    if allergies and allergies != "해당없음":
        user_info += f"\n알러지 정보: {allergies}"
    if diet_preference and diet_preference != "해당없음":
        user_info += f"\n식단 선호: {diet_preference}"
    if disease and disease != "해당없음":
        user_info += f"\n질환 정보: {disease}"

    # 프롬프트 조립
    prompt = f"""<role>
당신은 요리와 영양에 정통한 최고의 AI 셰프입니다.
</role>

<user_info>
{user_info}
</user_info>

<candidate_recipes>
{filtered_recipes}
</candidate_recipes>
"""

    # context가 있을 경우
    if disease and context:
        prompt += f"""
<context>
{context}
</context>
"""

    prompt += """
<instructions>
1. 위 정보를 참고해 사용자에게 가장 적합한 레시피 3개를 추천해주세요.
2. 질환 정보가 있다면, `<context>` 문서를 참고해 추천 이유를 반드시 작성해주세요.
3. 입력한 재료와 유사하거나 포함된 레시피를 우선적으로 선택해주세요.
4. 반드시 아래 JSON 형식을 따라 응답하세요. 설명 없이 JSON 객체만 반환해야 합니다.
</instructions>

<json_output_example>
{
  "recommended_recipes": [
    {
      "id": 1,
      "title": "닭가슴살 샐러드",
      "serving": "2인분",
      "difficulty": "초급",
      "cooking_time": "15분",
      "ingredients": "닭가슴살, 양상추, 토마토",
      "steps": "1. 닭가슴살을 삶는다. 2. 채소를 손질한다.",
      "url": "http://example.com/recipe/1",
      "recommendation_reason": "이 레시피는 사용자가 입력한 재료(닭가슴살, 양상추)를 활용하면서도, 고혈압 질환 정보를 고려해 나트륨이 적고 가공식품을 포함하지 않아 적합합니다. 또한 채식에 가까운 식단 선호와 알러지 정보(달걀 제외)를 반영하여 구성되었습니다.",
      "dietary_tips": "고혈압 환자는 나트륨 섭취를 줄이고 채소를 충분히 섭취해야 합니다."
    },
    {
      "id": 2,
      "title": "...",
      "serving": "...",
      "difficulty": "...",
      "cooking_time": "...",
      "ingredients": "...",
      "steps": "...",
      "url": "..."
  "recommendation_reason": "선택된 레시피들은 사용자의 재료, 식단 선호, 질환 및 알러지 정보를 바탕으로 필터링 및 우선순위화 되었습니다.",
  },
  "dietary_tips": "..."
]
}
</json_output_example>


<response>
이제 위 형식을 따르는 JSON 응답을 생성해주세요.
</response>
"""
    return prompt



def print_watsonx_response(response_text):
    try:
        # WatsonX 응답 문자열 → 파싱
        response_data = json.loads(response_text)
        generated_json_str = response_data["results"][0]["generated_text"]
        
        # 모델의 출력은 JSON 문자열이므로 다시 파싱합니다.
        result_data = json.loads(generated_json_str)

        print("✅ 추천 레시피\n" + "="*20)
        for recipe in result_data.get("recommended_recipes", []):
            print(f"🍽️  **{recipe.get('title', '제목 없음')}** (ID: {recipe.get('id', 'N/A')})")
            print(f"    - 인분: {recipe.get('serving', '정보 없음')}")
            print(f"    - 난이도: {recipe.get('difficulty', '정보 없음')}")
            print(f"    - 조리 시간: {recipe.get('cooking_time', '정보 없음')}")
            print(f"    - 재료: {recipe.get('ingredients', '정보 없음')}")
            print(f"    - 조리 순서: {recipe.get('steps', '정보 없음')}")
            print(f"    - URL: {recipe.get('url', '정보 없음')}")
            print("-" * 20)

        if "recommendation_reason" in result_data:
            print("\n✅ 추천 이유\n" + "="*20)
            print(result_data["recommendation_reason"])

        if "dietary_tips" in result_data:
            print("\n✅ 식단 팁\n" + "="*20)
            print(result_data["dietary_tips"])

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        print("원본 응답:")
        print(response_text)
    except Exception as e:
        print(f"❌ 응답 처리 중 오류 발생: {e}")
