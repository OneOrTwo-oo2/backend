from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from fastapi import FastAPI
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Optional
import os
import json
from bs4 import BeautifulSoup
import random
import requests
from urllib.parse import urlencode


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# .env 파일 로드
load_dotenv()

app = FastAPI()

# 1. 벡터 DB 로드
embedding_model = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
vectordb = FAISS.load_local("vector_store/diet", embedding_model, allow_dangerous_deserialization=True)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트 도메인
    # allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 환경 변수 로딩
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")  # 구글 이메일
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")  # 구글 비밀번호
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")

def search_youtube_videos(query: str, max_results=3):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": query + " 레시피",
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount"
    }
    response = requests.get(url, params=params)
    data = response.json()

    results = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        link = f"https://www.youtube.com/watch?v={video_id}"
        results.append(f"{title}: {link}")

    return "\n".join(results)


# ✅ Watsonx 토큰 발급
def get_ibm_access_token(api_key: str) -> str:
    response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        },
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key
        },
        verify=False
    )
    response.raise_for_status()
    return response.json()["access_token"]

# ✅ access token 전역 저장
ACCESS_TOKEN = get_ibm_access_token(WATSON_API_KEY)

def ask_watsonx(prompt: str) -> str:
    url = f'https://us-south.ml.cloud.ibm.com/ml/v1/deployments/a75741b8-0ed0-403b-9690-7e8305f4b896/text/generation?version=2021-05-01'
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "parameters": {
            "prompt_variables": {
                "context": prompt
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return f"❌ watsonx 요청 실패: {response.status_code} {response.text}"
    return response.text

# ✅ prompt 작성
def build_prompt(ingredients: str, detailed_recipes: str, context: str = None, disease: str = None) -> str:
    
    prompt = f"""당신은 요리 전문가입니다.
    
    다음 문서를 참고하여 '{disease}' 환자에게 맞는 식단과 재료를 파악하고,
    사용자가 제공한 재료를 활용해 '{detailed_recipes}'에 있는 레시피 중 가장 적절한 하나를 한국어로 추천해주세요.
    마지막에는 어떤'{disease}'에 적절한 요리인지 설명하고, 검색된 '{detailed_recipes}'의 레시피 총 갯수를 적어주세요.
    
    
    문서:{context}
    
    질문:{ingredients}를 활용한 요리 레시피를 추천해줘."""
    
    if disease and context:
        return prompt
    else:
        return f"""당신은 요리 전문가입니다.

    사용자가 제공한 재료를 활용해 '{detailed_recipes}'에 있는 레시피 중 가장장 적절한 하나를 한국어로 추천해주세요.
    마지막에는 '{detailed_recipes}' 의 총 갯수를 적어주세요."""


# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str
    #disease: Optional[str] = None  # 질환은 선택 사항


# ✅ 기존 요약 + 유튜브
@app.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    ingredients = req.ingredients
    print(f"🔍 Ingredients received: {ingredients}")

    # Get recipes
    recipes_dict = get_recipes(ingredients=[])
    recipes = recipes_dict["results"]  # 리스트만 추출
    print(f"🔍 Recipes found: {len(recipes)}")

    # Crawl detailed recipes
    detailed_recipes = crawl_recipe_detail_bulk(recipes)
    print(f"🔍 Detailed recipes crawled: {len(detailed_recipes)}")

    disease = None   # 사용자 선호도 예시 / req.disease 추가해야함
    query = f"{disease}에 맞는 식단 조건을 알려줘"

    # 관련 context 추출 (Top 5)
    if disease:
        # 질환이 있는 경우, 벡터 DB에서 문맥 검색
        query = f"{disease} 식단"
        docs = vectordb.similarity_search(query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
    else:
        context = None

    # Build prompt
    prompt = build_prompt(ingredients=ingredients, detailed_recipes = detailed_recipes, context=context, disease=disease)
    print(f"🔍 Prompt built: {prompt[:200]}...")  # Print first 200 characters of prompt for debugging

    # Ask Watsonx
    ai_response = ask_watsonx(prompt)
    print(f"🔍 Watsonx response: {ai_response[:200]}...")  # First 200 characters of Watson's response

    # YouTube links
    youtube_links = search_youtube_videos(ingredients)
    print(f"🔍 YouTube links: {youtube_links}")
    
    return {
        "result": ai_response,
        "youtube": youtube_links
    }



@app.get("/recipes")
def get_recipes(
    ingredients: Optional[List[str]] = Query(None),
    kind: Optional[str] = None,
    situation: Optional[str] = None,
    method: Optional[str] = None,
    theme: Optional[str] = None
):
    base_url = "https://www.10000recipe.com/recipe/list.html"
    base_url2 = "https://www.10000recipe.com/theme/view.html"


    # 검색 파라미터
    params = {}
    query = ""

    if ingredients:
        query = " ".join(ingredients)
        params["q"] = query

    if kind:
        params["cat4"] = kind
    if situation:
        params["cat2"] = situation
    if method:
        params["cat1"] = method

    # theme만 단독으로 있을 경우 theme 전용 URL로 전환
    if theme and not ingredients:
        params = {"theme": theme}
        url = f"{base_url2}?{urlencode(params)}"
    else:
        url = f"{base_url}?{urlencode(params)}"

    print("✅ 최종 요청 URL:", url)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    recipes = []
    for card in soup.select("ul.common_sp_list_ul > li.common_sp_list_li")[:30]:
        try:
            title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
            img = card.select_one(".common_sp_thumb img")["src"]
            link = "https://www.10000recipe.com" + card.select_one("a.common_sp_link")["href"]
            recipes.append({
                "title": title,
                "image": img,
                "link": link
            })
        except Exception as e:
            print("❌ 파싱 에러:", e)
            continue

    return {"results": recipes, "count": len(recipes)}

# ✅ 검색된 레시피 정보 가져오기
def crawl_recipe_detail_bulk(recipes: List[dict]) -> List[dict]:
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    for recipe in recipes:
        url = recipe["link"]
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.content, "html.parser")

            title = soup.select_one("div.view2_summary h3").get_text(strip=True)
            image = soup.select_one("div.centeredcrop img")["src"]
            ingredients = [li.get_text(strip=True) for li in soup.select("#divConfirmedMaterialArea li")]
            steps = [s.get_text(strip=True) for s in soup.select(".view_step_cont")]
            intro = soup.select_one("#recipeIntro").get_text(strip=True)

            results.append({
                "title": title,
                "image": image,
                "intro": intro,
                "ingredients": ingredients,
                "steps": steps,
                "url": url
            })

        except Exception as e:
            print(f"❌ 크롤링 실패 ({url}):", e)
            continue

    return results

@app.get("/random-recipes")
def get_random_recipes(page: Optional[int] = Query(None)):
    if not page:
        page = random.randint(2, 10)

    url = f"https://www.10000recipe.com/issue/view.html?cid=9999scrap&page={page}"
    print(f"🔗 크롤링 대상 URL: {url}")

    # Chrome 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        # 동적 콘텐츠 로드 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rcp_m_list2 > li"))
        )
    except Exception as e:
        driver.quit()
        return {"results": [], "error": "❌ 페이지 로딩 실패", "details": str(e)}

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    recipe_cards = soup.select("ul.rcp_m_list2 > li")
    print(f"✅ 레시피 카드 수: {len(recipe_cards)}")

    results = []
    for card in recipe_cards:
        try:
            a_tag = card.select_one("a")
            link = "https://www.10000recipe.com" + a_tag["href"]
            title = card.select_one(".tit").get_text(strip=True)
            img_tag = card.select_one("img")
            img = img_tag.get("data-src") or img_tag.get("src")

            results.append({
                "title": title,
                "image": img,
                "link": link
            })
        except Exception as e:
            print("❌ 카드 파싱 에러:", e)
            continue

    return {"results": results, "count": len(results)}


# ✅ YOLO 클래스 리스트 제공 API
@app.get("/api/yolo-classes")
def get_yolo_classes():
    json_path = os.path.join(os.path.dirname(__file__), "yolo_classes.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            classes = json.load(f)
        return classes
    except Exception as e:
        return {"error": str(e)}
