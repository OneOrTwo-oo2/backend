from fastapi import APIRouter
from pydantic import BaseModel
from api.recipes import get_recipes
from utils.prompt import format_recipes_for_prompt
from utils.watsonx import ask_watsonx
from utils.crawl import crawl_recipe_detail_bulk
from utils.youtube import search_youtube_videos
from utils.prompt import filter_recipes_include_only
from utils.prompt import build_prompt
import config
import pandas as pd
from db.connection import SessionLocal
from utils.recipe_service import fetch_recipes_from_10000recipe


router = APIRouter()

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str
    #disease: Optional[str] = None  # 질환은 선택 사항
    #diet_preference   // 채식주의(고기x), 저탄수화물, 글루텐프리, 다이어트식, 저염식식
    #allergies

# ✅ 기존 요약 + 유튜브
@router.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    vectordb = config.vector_db

    ingredients = req.ingredients
    ingredients_list = [item.strip() for item in ingredients.split(",")]
    print(f"🔍 Ingredients received: {ingredients_list}")

    # Get recipes
    # with SessionLocal() as db:
    #     recipes_dict = fetch_recipes_from_10000recipe(db, ingredients=ingredients.split(","))
    # recipes = recipes_dict["results"]  # 리스트만 추출
    # print(f"🔍 Recipes found: {len(recipes)}")
    # print(f"🔍 Recipes : {recipes}")
    

    # # Crawl detailed recipes
    # detailed_recipes = crawl_recipe_detail_bulk(recipes)
    # print(f"🔍 Detailed recipes crawled: {len(detailed_recipes)}")
    # detailed_recipes = format_recipes_for_prompt(detailed_recipes)


    disease = '고혈압'   # 사용자 선호도 예시 / req.disease 추가해야함
    allergies = '계란, 달걀, 양파'
    diet_preference='채식주의'


    # 만개의 레시피 load
    recipes = pd.read_csv("./vector_store/recipe_cat4_reindexed.csv")
    print(f"🔍 total recipes: {recipes.shape[0]}")
    filtered_recipes = filter_recipes_include_only (recipes, ingredients, allergies)
    print(f"🔍 filtered_recipes: {filtered_recipes.shape[0]}")
    filtered_recipes = format_recipes_for_prompt(filtered_recipes)
    
    # 관련 context 추출 (Top 3)
    if disease:
        # 질환이 있는 경우, 벡터 DB에서 문맥 검색
        #query = f"{disease} 식단 관리 방법만 가져와, 숫자 뒤에 {disease} 키워드가 시작점이고 다음 숫자 앞까지의 텍스트만 가져와"
        query = f"{disease} 식단 관리 방법만 가져와, 숫자.{disease} 텍스트부터 검색해"     
        docs = vectordb.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
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

    print(f"🔍 Prompt built: {prompt}")  # Print first 200 characters of prompt for debugging

    # Ask Watsonx
    ai_response = ask_watsonx(prompt)
    #print(f"🔍 Watsonx response: {ai_response[:200]}...")  # First 200 characters of Watson's response
    print(f"🔍 Watsonx response: {ai_response}") 
    
    # YouTube links
    # youtube_links = search_youtube_videos(ingredients)
    # print(f"🔍 YouTube links: {youtube_links}")
    
    return {
        "result": ai_response,
        #"youtube": youtube_links
    }

