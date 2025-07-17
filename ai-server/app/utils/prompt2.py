from langchain.schema import Document
import json
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods

def search_top_k(
    query,
    vectordb,
    model,
    top_k=5,
    exclude_ingredients=None,
    level=None,
    kind=None
):
    # # 문자열 → 리스트 변환
    #exclude_ingredients = [i.strip() for i in exclude_ingredients.split(",")] if exclude_ingredients else []
    # difficulty_levels = [d.strip() for d in difficulty_levels_str.split(",")] if difficulty_levels_str else []
    # types = [t.strip() for t in types_str.split(",")] if types_str else []

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
        if level and 난이도 not in level:
            continue

        # 4. 종류 필터링 (정확히 일치)
        if kind and 종류 not in kind:
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
    diseases=None,
    allergies=None,
    preference=None
) -> str:
    # 1. 사용자 정보 조립
    user_info = f"입력한 재료: {ingredients}"
    if allergies and allergies != "해당없음":
        user_info += f"\n알러지 정보: {allergies}"
    if preference and preference != "해당없음":
        user_info += f"\n식단 선호: {preference}"
    if diseases and diseases != "해당없음":
        user_info += f"\n질환 정보: {diseases}"

    # 2. 후보 레시피 정제 (각 레시피를 구조적으로 나열)
    recipe_section = ""
    for r in filtered_recipes:
        recipe_section += f"- ID: {r.get('id')}\n"
        recipe_section += f"  제목: {r.get('title')}\n"
        recipe_section += f"  주요 재료: {', '.join(r.get('ingredients', []))}\n"
        if r.get("tags"):
            recipe_section += f"  태그: {', '.join(r['tags'])}\n"
        recipe_section += "\n"

    # 3. context가 없더라도 빈 블록 유지
    context_text = context.strip() if context else "N/A"

    # 4. 프롬프트 전체 구성
    prompt = f"""<role>
당신은 요리와 영양에 정통한 최고의 AI 셰프입니다.
</role>

<user_info>
{user_info}
</user_info>

<candidate_recipes>
{recipe_section.strip()}
</candidate_recipes>

<context>
{context_text}
</context>

<instructions>
1. 위 정보를 참고하여 사용자에게 가장 적합한 레시피 3개를 JSON 형식으로 추천해주세요.
2. 입력한 재료와 유사하거나 포함된 레시피를 우선적으로 고려하세요.
3. 질환 정보가 있다면, <context> 정보를 반드시 활용하고 설명에 반영하세요.
4. 각 추천에는 '이 레시피를 추천하는 이유'를 사용자 정보에 기반해 구체적으로 작성하세요.
5. 아래 JSON 형식만 그대로 반환하세요. 텍스트 설명 없이 JSON만 출력해야 합니다.
</instructions>

<json_output_example>
{{
  "recommended_recipes": [
    {{
      "id": 1,
      "title": "닭가슴살 샐러드",
      "url": "http://example.com/recipe/1",
      "recommendation_reason": "이 레시피는 사용자의 재료와 질환 상태를 반영하여 저염식, 고단백 식단으로 구성되어 있습니다..."
    }},
    {{
      "id": 2,
      "title": "...",
      "url": "...",
      "recommendation_reason": "..."
    }},
    {{
      "id": 3,
      "title": "...",
      "url": "...",
      "recommendation_reason": "..."
    }}
  ],
  "dietary_tips": "질환 관리에 도움이 되는 전반적인 식단 조언을 포함해주세요. 예: 고혈압 환자는 나트륨 섭취를 줄이고, 채소 섭취를 늘리는 것이 중요합니다."
}}
</json_output_example>

<response>
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
