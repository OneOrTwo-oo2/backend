from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 환경 변수
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# 🔎 유튜브 검색 함수
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


# 🧠 IBM WatsonX 토큰 요청 함수
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


def ask_watsonx(prompt: str) -> str:
    ACCESS_TOKEN = get_ibm_access_token(WATSON_API_KEY)
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



# 📦 레시피 요청 스키마
class RecipeRequest(BaseModel):
    ingredients: str


# ✅ 레시피 추천 API
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
