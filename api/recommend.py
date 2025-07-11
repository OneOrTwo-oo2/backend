from fastapi import APIRouter
from pydantic import BaseModel
from api.recipes import get_recipes
from utils.crawl import crawl_recipe_detail_bulk
from utils.youtube import search_youtube_videos
from utils.prompt import build_prompt, format_recipe, search_top_k, print_watsonx_response
import config
import pandas as pd
from db.connection import SessionLocal
from utils.recipe_service import fetch_recipes_from_10000recipe
import time
from utils.watsonx import ask_watsonx

router = APIRouter()

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str
    #disease: Optional[str] = None  # 질환은 선택 사항
    #diet_preference   // 채식주의(고기x), 저탄수화물, 글루텐프리, 다이어트식, 저염식
    #allergies

# ✅ 기존 요약 + 유튜브
@router.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    vectordb_recipe = config.vector_db_recipe
    vectordb_disease = config.vector_db_disease
    model = config.embedding_model

    ingredients = req.ingredients
    print(f"🔍 Ingredients received: {ingredients}")

    # 사용자 선호도 예시 / req.disease 추가해야함
    disease = '통풍'   
    allergies = '계란, 달걀, 새우'
    diet_preference='저탄수화물'

    # ✅ 유사 레시피 검색 (쿼리용 문자열 재조합, Top 50)
    query = ingredients
    top_k = 15
    
    start = time.time()
    results = search_top_k(query=query, 
                           vectordb=vectordb_recipe,
                            model=model, 
                            top_k=top_k,
                            exclude_ingredients_str=allergies
                            )

    filtered_recipes = "\n\n".join([format_recipe(doc, i+1) for i, (doc, _) in enumerate(results)])
    print(filtered_recipes)

    print(f"🔍 유사 레시피 {top_k}개 검색 완료 (소요: {time.time() - start:.2f}초)")

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
    print(f"🔍 Watsonx response: {ai_response}\n") 
    
    # YouTube links
    # youtube_links = search_youtube_videos(ingredients)  # 재료 대신 요리 제목도 가능
    # print(f"🔍 YouTube links: {youtube_links}")
    
    return {
        "result": print_watsonx_response(ai_response),
        #"youtube": youtube_links
    }

