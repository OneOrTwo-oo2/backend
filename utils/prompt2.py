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
2. 입력한 재료와 유사하거나 포함된 레시피를 우선적으로 선택해주세요.
3. 질환 정보가 있다면, `<context>` 문서를 참고해 추천 이유를 반드시 작성해주세요.
4. 각 레시피를 추천하는 이유를 사용자 정보를 바탕으로 논리적으로 작성해주세요.
5. 반드시 아래 JSON 형식을 따라 응답하세요. 설명 없이 JSON 객체만 반환해야 합니다.
</instructions>

<json_output_example>
{
  "recommended_recipes": [
    {
      "id": 1,
      "제목": "닭가슴살 샐러드",
      "url": "http://example.com/recipe/1",
      "recommendation_reason": "이 레시피는 사용자가 입력한 재료인 닭가슴살과 양상추를 바탕으로 구성되어 있어 재료 활용도가 높습니다. 특히 고혈압을 앓고 있는 사용자의 건강 상태를 고려하여, 전체적인 나트륨 함량을 낮게 유지하고 가공식품이나 고염도 양념을 배제함으로써 혈압 상승 위험을 줄였습니다.
또한, 단백질이 풍부한 닭가슴살은 고혈압 환자에게 권장되는 저지방 육류이며, 양상추는 수분과 식이섬유가 풍부하여 혈관 건강에 도움을 줍니다. 이와 함께 사용자의 식단 선호인 ‘채식에 가까운 구성’을 고려하여, 동물성 식재료는 최소화하고 식물성 재료를 중심으로 조리법을 구성했습니다. 알러지 정보 또한 반영되어, 달걀은 전혀 사용하지 않아 안전한 섭취가 가능합니다."
    },
    {
      "id": 2,
      "제목": "...",
      "url": "..."
  "recommendation_reason": "이 레시피는 사용자가 입력한 두부와 시금치를 주재료로 하여 구성되어 있으며, 만성 신장병 환자의 식이 제한 사항을 철저히 고려하였습니다. 두부는 단백질 공급원 중 비교적 인이 적은 편이며, 시금치는 조리 시 물에 데쳐 옥살산을 줄임으로써 칼륨 섭취도 조절할 수 있습니다.
특히 알러지 정보에 따라 유제품과 견과류는 일절 포함되지 않았고, 가공 조미료 사용을 최소화하여 신장 기능에 무리를 주지 않도록 설계되었습니다. 전체적으로 저염식이며, 인과 칼륨 함량을 의도적으로 낮춘 식단입니다",
  },
  "dietary_tips": "고혈압 환자는 음식을 선택할 때 무엇보다 나트륨 섭취를 줄이는 것이 중요합니다. 이를 위해 간장, 소금, 액젓 등의 사용을 줄이고, 천연 재료의 풍미를 살린 조리법을 택하는 것이 좋습니다.
또한, 식이섬유와 칼륨이 풍부한 채소류를 충분히 섭취하면 나트륨 배출을 도와 혈압 조절에 긍정적인 영향을 줄 수 있습니다. 이 레시피는 생채소를 충분히 활용하며, 가열 시에도 기름이나 소금을 과도하게 사용하지 않도록 구성되어 있어 고혈압 관리에 도움이 됩니다.
물을 충분히 마시고, 정제 탄수화물과 가공식품은 줄이는 습관을 병행하면 보다 효과적인 식이 조절이 가능합니다."
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
            print(f"🍽️  **{recipe.get('제목', '제목 없음')}** (ID: {recipe.get('id', 'N/A')})")
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
