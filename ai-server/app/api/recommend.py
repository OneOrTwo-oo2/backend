from fastapi import APIRouter
from pydantic import BaseModel
from utils.youtube import search_youtube_videos
from utils.prompt import build_prompt, format_recipe, search_top_k, print_watsonx_response
import config
import time
from utils.watsonx import ask_watsonx, parse_watsonx_json
from typing import Optional

router = APIRouter()

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str
    disease: Optional[str] = None
    allergies: Optional[str] = None
    diet_preference: Optional[str] = None

# ✅ 기존 요약 + 유튜브
@router.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    vectordb_recipe = config.vector_db_recipe
    vectordb_disease = config.vector_db_disease
    model = config.embedding_model

    ingredients = req.ingredients
    disease = req.disease or ""
    allergies = req.allergies or ""
    diet_preference = req.diet_preference or ""

    print(f"🔍 Ingredients received: {ingredients}")
    print(f"⚕️ 질환 정보: {disease}")
    print(f"🚫 알러지 정보: {allergies}")
    print(f"🥗 식단 선호: {diet_preference}")

    # ✅ 유사 레시피 검색 (쿼리용 문자열 재조합, Top 50)
    
    top_k = 15
    
    start = time.time()
    results = search_top_k(query = ingredients,
                           vectordb=vectordb_recipe,
                            model=model, 
                            top_k=top_k,
                            exclude_ingredients_str=allergies,
                            difficulty_levels_str=None,
                            types_str=None
                            )

    filtered_recipes = "\n\n".join([format_recipe(doc, i+1) for i, (doc, _) in enumerate(results)])
    print(f"🔍 유사 레시피 {top_k}개 검색 완료 (소요: {time.time() - start:.2f}초)")

    context = ""

    # ✅ 관련 disease context 추출
    if disease:
        # 질환이 있는 경우, 벡터 DB에서 문맥 검색
        query = f"{disease}의 식사요법"     
        results = vectordb_disease.similarity_search_with_score(query, k=1)
        context = "\n\n".join([doc.page_content for doc, _ in results])
    else:
        context = None

    print(context)

    # Build prompt
    prompt = build_prompt(ingredients=ingredients, 
                        filtered_recipes = filtered_recipes, 
                        context=context, 
                        disease=disease,
                        allergies=allergies,
                        diet_preference=diet_preference
                        )

    print(f"🔍 Prompt built: {prompt[:1000]}")  # Print first 200 characters of prompt for debugging

    # Ask Watsonx
    ai_response = ask_watsonx(prompt)
    print(f"🧠 Watsonx 응답 수신 완료")
    print(f"🔍 Watsonx response: {ai_response}\n") 
    
    # YouTube links
    # youtube_links = search_youtube_videos(ingredients)  # 재료 대신 요리 제목도 가능
    # print(f"🔍 YouTube links: {youtube_links}")
    
    return {
        "result": parse_watsonx_json(ai_response)
        #"youtube": youtube_links
    }