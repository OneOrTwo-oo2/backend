from fastapi import APIRouter
from pydantic import BaseModel
from api.recipes import get_recipes
from utils.prompt import build_prompt, format_recipes_for_prompt
from utils.watsonx import ask_watsonx
from utils.crawl import crawl_recipe_detail_bulk
from utils.youtube import search_youtube_videos
import config


router = APIRouter()

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str
    #disease: Optional[str] = None  # 질환은 선택 사항
    

# ✅ 기존 요약 + 유튜브
@router.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    vectordb = config.vector_db

    ingredients = req.ingredients
    print(f"🔍 Ingredients received: {ingredients}")
    
    import time
    
    start = time.time()
    # Get recipes
    recipes_dict = get_recipes(ingredients=ingredients.split(","))
    recipes = recipes_dict["results"]  # 리스트만 추출
    print(f"🔍 Recipes found: {len(recipes)}")
    print(f"🔍 Recipes : {recipes}")
    end = time.time()
    print(f"만개레시피 추출 실행 시간: {end - start:.4f}초")    


    start = time.time()
    # Crawl detailed recipes
    detailed_recipes = crawl_recipe_detail_bulk(recipes)
    print(f"🔍 Detailed recipes crawled: {len(detailed_recipes)}")
    detailed_recipes = format_recipes_for_prompt(detailed_recipes)
    end = time.time()
    print(f"레시피 크롤링 실행 시간: {end - start:.4f}초")    


    start = time.time()
    disease = '고혈압'   # 사용자 선호도 예시 / req.disease 추가해야함

    # 관련 context 추출 (Top 5)
    if disease:
        # 질환이 있는 경우, 벡터 DB에서 문맥 검색
        query = f"{disease} 식단"
        docs = vectordb.similarity_search(query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
    else:
        context = None

    print(context)
    # Build prompt
    prompt = build_prompt(ingredients=ingredients, detailed_recipes = detailed_recipes, context=context, disease=disease)
    print(f"🔍 Prompt built: {prompt}...")  # Print first 200 characters of prompt for debugging
    end = time.time()
    print(f"프롬프트 생성 실행 시간: {end - start:.4f}초") 
    
    start = time.time()
    # Ask Watsonx
    ai_response = ask_watsonx(prompt)
    #print(f"🔍 Watsonx response: {ai_response[:200]}...")  # First 200 characters of Watson's response
    print(f"🔍 Watsonx response: {ai_response}")
    end = time.time()
    print(f"왓슨 result 생성 실행 시간: {end - start:.4f}초") 

    
    # YouTube links
    # youtube_links = search_youtube_videos(ingredients)
    # print(f"🔍 YouTube links: {youtube_links}")
    
    return {
        "result": ai_response,
        #"youtube": youtube_links
    }

