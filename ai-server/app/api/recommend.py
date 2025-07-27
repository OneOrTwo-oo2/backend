from fastapi import APIRouter
from pydantic import BaseModel
from utils.youtube import search_youtube_videos
from utils.prompt import build_prompt, search_bm25_only, print_watsonx_response    #search_recipe_with_filters
import config
import time
from utils.watsonx import ask_watsonx, parse_watsonx_json
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

router = APIRouter()

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: List[str] #list[str] 
    diseases: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    preference: Optional[str] = None
    kind: Optional[str] = None  
    level: Optional[str] = None  



def fetch_thumbnail_by_title(title: str) -> dict:
    try:
        base_url = "https://www.10000recipe.com/recipe/list.html"
        params = {"q": title, "order": "accuracy"}  # order=accuracy로 고정
        url = f"{base_url}?{urlencode(params)}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 여러 개 카드 중에서 icon_vod가 아닌 첫 번째 카드 사용
        cards = soup.select("ul.common_sp_list_ul > li.common_sp_list_li")
        for card in cards:
            img_tag = card.select_one(".common_sp_thumb img")
            link_tag = card.select_one("a.common_sp_link")

            img_url = img_tag["src"] if img_tag else ""
            recipe_url = "https://www.10000recipe.com" + link_tag["href"] if link_tag else ""

            if "icon_vod.png" not in img_url:
                return {"image": img_url, "link": recipe_url}
            else:
                print(f"⏩ [{title}] 동영상 썸네일 건너뜀: {img_url}")

        # 일반 썸네일 없으면 빈 값 리턴
        return {"image": "", "link": ""}

    except Exception as e:
        print(f"❌ [{title}] 썸네일 크롤링 실패: {e}")
        return {"image": "", "link": ""}

    
# ✅ 기존 요약 + 유튜브
@router.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    #vectordb_recipe = config.vector_db_recipe
    vectordb_disease = config.vector_db_disease
    #model = config.embedding_model
    bm25_retriever = config.bm25_retriever
    #faiss_loaded = config.faiss_loaded     

    ingredients_raw = req.ingredients or []
    diseases = req.diseases or []
    allergies = req.allergies or []
    preference = req.preference or ""
    kind = req.kind or ""
    level = req.level or ""

    # 알러지에 "달걀" 또는 "계란"이 있으면 둘 다 제외, "새우" 또는 "대하"도 마찬가지
    egg_aliases = {"달걀", "계란"}
    shrimp_aliases = {"새우", "대하"}

    # 알러지에 달걀/계란이 하나라도 있으면 ingredients에서 둘 다 제외
    exclude_eggs = any(a in egg_aliases for a in allergies)
    exclude_shrimps = any(a in shrimp_aliases for a in allergies)

    ingredients = []
    for item in ingredients_raw:
        if exclude_eggs and item in egg_aliases:
            continue
        if exclude_shrimps and item in shrimp_aliases:
            continue
        if item in allergies:
            continue
        ingredients.append(item)

    print(f"🔍 Ingredients received: {ingredients}")
    print(f"⚕️ 질환 정보: {diseases}")
    print(f"🚫 알러지 정보: {allergies}")
    print(f"🥗 식단 선호: {preference}")
    print(f"🥗 종류: {kind}")
    print(f"🥗 난이도: {level}")

    # ✅ 후보 레시피 검색 (쿼리용 문자열 재조합, Top 50)
    # 필터 생성 (빈 값은 제외)
    filters = {}
    if level:
        filters["난이도"] = level
    if kind:
        filters["종류"] = kind

    top_k = 50
    start = time.time()
    # filtered_recipes = search_recipe_with_filters(
    #    query=ingredients,
    #    bm25_retriever=bm25_retriever,
    #    faiss_loaded=faiss_loaded,
    #    filters=filters,
    #    top_k=top_k)
    filtered_recipes = search_bm25_only(
        query=ingredients,
        bm25_retriever=bm25_retriever,
        filters=filters,
        top_k=top_k
    )

    #     # filtered_recipes를 딕셔너리 리스트로 생성
    # filtered_recipes = []
    # for i, (doc, _) in enumerate(results):
    #     meta = doc.metadata
    #     filtered_recipes.append({
    #         "id": i+1,
    #         "제목": meta.get("제목", ""),
    #         "재료": [ing.strip() for ing in meta.get("재료", "").split(",") if ing.strip()],
    #         "URL": meta.get("URL", "")
    #     })

    print(f"🔍 유사 레시피 {top_k}개 검색 완료 (소요: {time.time() - start:.2f}초)")
    print(f"🔍 유사 레시피: {filtered_recipes[:20]}")
    context = ""

    # ✅ 관련 disease context 추출
    if diseases:
        results = []
        for disease in diseases:
            query = f"{disease}의 식사요법"
            result = vectordb_disease.similarity_search_with_score(query, k=1)
            results.extend(result)
        context = "\n\n".join([doc.page_content for doc, _ in results])
    else:
        context = None

    print(context)

    # Build prompt
    prompt = build_prompt(ingredients=ingredients, 
                        filtered_recipes = filtered_recipes, 
                        context=context, 
                        diseases=diseases,
                        allergies=allergies,
                        preference=preference
                        )

    print(f"🔍 Prompt built: {prompt[:1000]}")  # Print first 200 characters of prompt for debugging

    
    # Ask Watsonx
    ai_response = ask_watsonx(prompt)
    parsed = parse_watsonx_json(ai_response)
    print(f"🧠 Watsonx 응답 수신 완료")
    print(f"🔍 Watsonx response: {ai_response}\n")
    print("파싱 결과:", parsed)

    # cursor 수정 - Watson 응답 에러 처리 추가
    if not parsed or "recommended_recipes" not in parsed:
        print(f"❌ Watson 응답 파싱 실패 또는 예상 형식이 아님: {parsed}")
        return {
            "result": {
                "recommended_recipes": [],
                "dietary_tips": "죄송합니다. AI 추천을 생성하는 중 오류가 발생했습니다."
            }
        }
    
    # YouTube links
    # youtube_links = search_youtube_videos(ingredients)  # 재료 대신 요리 제목도 가능
    # print(f🔍 YouTube links: {youtube_links}")
    
    for recipe in parsed["recommended_recipes"]:
        title = recipe.get("제목", "")  # WatsonX 응답에서 "제목" 사용
        if title:
            thumbnail_info = fetch_thumbnail_by_title(title)
            recipe["image"] = thumbnail_info["image"]
            recipe["link"] = thumbnail_info["link"]
            print(f"📸 {title} 썸네일: {thumbnail_info['image']}")
        else:
            recipe["image"] = ""
            recipe["link"] = ""

    return {
        "result": parsed
        
    }

