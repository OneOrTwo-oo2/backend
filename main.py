from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List
import os
import requests
import json
from bs4 import BeautifulSoup

load_dotenv()

app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 환경 변수 로딩
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ✅ 유튜브 검색
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

# ✅ Watsonx 호출
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

# ✅ POST 요청 바디
class RecipeRequest(BaseModel):
    ingredients: str

# ✅ 기존 요약 + 유튜브
@app.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    ingredients = req.ingredients
    prompt = f"{ingredients}를 활용한 요리 레시피를 한국어로 추천해줘."
    ai_response = ask_watsonx(prompt)
    youtube_links = search_youtube_videos(ingredients)

    return {
        "result": ai_response,
        "youtube": youtube_links
    }

@app.get("/recipes")
def get_recipes_by_ingredients(ingredients: List[str] = Query(...)):
    if isinstance(ingredients, str):
        ingredients = [i.strip() for i in ingredients.split(",")]
    print("✅ 받은 재료 리스트:", ingredients)

    query = " ".join(ingredients)
    search_url = f"https://www.10000recipe.com/recipe/list.html?q={query}"
    print("🔎 요청 URL:", search_url)

    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, "html.parser")

    recipes = []
    for card in soup.select("ul.common_sp_list_ul > li.common_sp_list_li")[:12]:
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

    print("📦 크롤링된 레시피 수:", len(recipes))
    return {"results": recipes}