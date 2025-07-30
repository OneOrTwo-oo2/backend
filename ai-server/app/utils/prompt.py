from langchain.schema import Document
import json
# #from ibm_watsonx_ai.credentials import Credentials
# #from ibm_watsonx_ai.foundation_models import ModelInference
# from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
# from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods
from collections import defaultdict

def bm25_filter(documents, filters: dict):
    return [
        doc for doc in documents
        if all(doc.metadata.get(k) == v for k, v in filters.items())
    ]


def search_recipe_with_filters(query, bm25_retriever, faiss_loaded, filters: dict = None, top_k: int = 10):
    # 쿼리 전처리: 리스트면 join, 문자열이면 그대로
    if isinstance(query, list):
        query_str = " ".join(query)
    else:
        query_str = query
    print("함수 진입!", query_str)
    bm25_results = bm25_retriever.get_relevant_documents(query_str)
    if filters:
        bm25_results = bm25_filter(bm25_results, filters)
    print("bm25_results!!! ",bm25_results[:1])

    # ✅ FAISS 검색 시 필터 전달
    faiss_kwargs = {"k": 50}
    if filters:
        faiss_kwargs["filters"] = filters
    faiss_results = faiss_loaded.as_retriever(search_kwargs=faiss_kwargs).get_relevant_documents(query_str)
    print("faiss_results!!! ",faiss_results[:1])
    # 점수 합산을 위한 dict
    scored_docs = defaultdict(lambda: {"doc": None, "bm25": 0, "faiss": 0, "sources": set()})

    for rank, doc in enumerate(bm25_results):
        key = doc.metadata.get("URL") #or doc.page_content.strip()[:100]
        scored_docs[key]["doc"] = doc
        scored_docs[key]["bm25"] = 1 - rank / len(bm25_results)  # 0~1 사이 점수
        scored_docs[key]["sources"].add("BM25")

    for rank, doc in enumerate(faiss_results):
        key = doc.metadata.get("URL") #or doc.page_content.strip()[:100]
        scored_docs[key]["doc"] = doc
        scored_docs[key]["faiss"] = 1 - rank / len(faiss_results)
        scored_docs[key]["sources"].add("FAISS")

    # 최종 점수 계산 (가중치 적용)
    results = [
        (v["doc"], 0.8 * v["bm25"] + 0.2 * v["faiss"], v["sources"])
        for v in scored_docs.values()
    ]
    results.sort(key=lambda x: x[1], reverse=True)

    # 결과 출력
    for i, (doc, score, sources) in enumerate(results[:20]):
        print(f"\n📌 Top {i+1} (점수: {score:.3f}) [출처: {', '.join(sources)}]")
        print(doc.page_content)
        print("-" * 60)

    return [doc for doc, _, _ in results[:top_k]]


def search_bm25_only(query, bm25_retriever, filters: dict = None, top_k: int = 10):
    # BM25 검색
    results = bm25_retriever.get_relevant_documents(" ".join(query))
    # 필터링
    if filters:
        results = bm25_filter(results, filters)
    # 출력
    for i, doc in enumerate(results[:top_k]):
        print(f"\n📌 Top {i+1}")
        print(doc.page_content)
        print("-" * 60)

    return results[:top_k]

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

    # 3. context가 없더라도 빈 블록 유지
    context_text = context.strip() if context else "N/A"
    # 4. 프롬프트 전체 구성
    prompt = f"""<role>
당신은 요리와 영양에 정통한 최고의 AI 한국인 셰프 입니다. 한국인 셰프는 한국인의 입맛과 취향을 잘 파악하고, 한국인의 식단 선호도를 잘 반영하여 추천합니다.
</role>
<user_info>
{user_info}
</user_info>
<candidate_recipes>
{filtered_recipes}
</candidate_recipes>
<context>
{context_text}
</context>
<instructions>

1. 위 정보를 조건을 모두 반영하여 가장 적합한 레시피 3개를 JSON 형식으로 추천해주세요.
2. 반드시 후보 레시피 목록에서 고른 레시피여야 합니다.
3. 입력한 재료와 유사하거나 포함된 레시피를 우선적으로 고려하세요.
4. 질환 정보가 있다면, <context> 정보를 반드시 활용하고 설명에 반영하세요.
5. 각 레시피의 recommendation_reason는 최소 3문장 이상 작성하고, 사용자의 보유 재료, 질환(예: 당뇨병), 알러지, 식이 성향(예: 저탄수화물 식단)을 모두 상세하게 반영하여 구체적이고 논리적으로 설명하세요.
6. 각 레시피의 dietary_tips은 질환 관리나 영양 관리에 도움이 되는 전반적인 식단 조언을 포함해주세요. 예: 고혈압 환자는 나트륨 섭취를 줄이고, 채소 섭취를 늘리는 것이 중요합니다.
7. 각 설명은 요리의 재료 구성, 조리 방법, 질환과 영양학적 적합성, 식이 제한 요소 반영 여부까지 포괄해야 합니다.
8. 아래 예시처럼 아무런 설명, 코드, 주석, 영어 텍스트 없이 JSON만 반환하세요.
</instructions>
<json_output_example>
{{
  "recommended_recipes": [
    {{
      "id": 1,
      "제목": "닭가슴살 샐러드",
      "url": "http://example.com/recipe/1",
      "recommendation_reason": "이 레시피는 사용자의 재료, 선호도와 질환 상태를 반영하여 저염식, 고단백 식단으로 구성되어 있습니다..."
      "dietary_tips": "질환 관리에 도움이 되는 전반적인 식단 조언을 포함해주세요. 예: 고혈압 환자는 나트륨 섭취를 줄이고, 채소 섭취를 늘리는 것이 중요합니다."
    }},
    {{
      "id": 2,
      "제목": "...",
      "url": "...",
      "recommendation_reason": "..."
      "dietary_tips": "..."
    }},
    {{
      "id": 3,
      "제목": "...",
      "url": "...",
      "recommendation_reason": "..."
      "dietary_tips": "..."
    }}
  ]
}}
</json_output_example>
<response>
반드시 대답 신중하게 다시한번 생각하고 답변은 한국어로만 할것
"""
    return prompt

def print_watsonx_response(response_text):
    try:
        # WatsonX 응답 문자열 → 파싱
        response_data = json.loads(response_text)
        generated_json_str = response_data["results"][0]["generated_text"]
        # 모델의 출력은 JSON 문자열이므로 다시 파싱합니다.
        result_data = json.loads(generated_json_str)
        print(":흰색_확인_표시: 추천 레시피\n" + "="*20)
        for recipe in result_data.get("recommended_recipes", []):
            print(f":나이프_포크_접시:  **{recipe.get('제목', '제목 없음')}** (ID: {recipe.get('id', 'N/A')})")
            print(f"    - URL: {recipe.get('url', '정보 없음')}")
            print("-" * 20)
        if "recommendation_reason" in result_data:
            print("\n✅ 추천 이유\n" + "="*20)
            print(result_data["recommendation_reason"])
            print("\n✅ 식단 팁\n" + "="*20)
            print(result_data["dietary_tips"])


        # if "dietary_tips" in result_data:
        #     print("\n✅ 식단 팁\n" + "="*20)
        #     print(result_data["dietary_tips"])

    except json.JSONDecodeError as e:
        print(f":x: JSON 파싱 실패: {e}")
        print("원본 응답:")
        print(response_text)
    except Exception as e:
        print(f":x: 응답 처리 중 오류 발생: {e}")