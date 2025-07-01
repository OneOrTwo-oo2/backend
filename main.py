from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

app = FastAPI()

# 1. 벡터 DB 로드
embedding_model = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
vectordb = FAISS.load_local("vector_store/diet", embedding_model, allow_dangerous_deserialization=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
# NOTE: you must set $API_KEY below using information retrieved from your IBM Cloud account (https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-authentication.html?context=wx)



# the above CURL request will return an auth token that you will use as $IAM_TOKEN in the scoring request below
# TODO:  manually define and pass values to be scored below
def get_ibm_access_token(api_key: str) -> str:
    import requests

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
        verify = False
    )
    response.raise_for_status()
    return response.json()["access_token"]

# get access tokens
ACCESS_TOKEN = get_ibm_access_token(WATSON_API_KEY)
# print(ACCESS_TOKEN)


# 🧠 watsonx에 요청
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

def build_prompt(ingredients: str, context: str = None, disease: str = None) -> str:
    if disease and context:
        return f"""당신은 질환별 식단 전문가입니다.

다음 문서를 참고하여 '{disease}' 환자에게 적절한 요리를,
사용자가 제공한 재료를 활용해 한국어로 추천해주세요.

문서:
{context}

질문:
{ingredients}를 활용한 요리 레시피를 추천해줘.
"""
    else:
        return f"""당신은 요리 전문가입니다.

{ingredients}를 활용한 요리 레시피를 추천해줘.
"""


class RecipeRequest(BaseModel):
    ingredients: str
    #disease: Optional[str] = None  # 질환은 선택 사항


@app.post("/recommend")
async def recommend_recipe(req: RecipeRequest):
    ingredients = req.ingredients
    disease = '통풍'   # 사용자 선호도 예시 / req.disease
    query = f"{disease}에 맞는 식단 조건을 알려줘"

    # 관련 context 추출 (Top 5)
    if disease:
        # 질환이 있는 경우, 벡터 DB에서 문맥 검색
        query = f"{disease} 식단"
        docs = vectordb.similarity_search(query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
    else:
        context = None

    prompt = build_prompt(ingredients=ingredients, context=context, disease=disease)
    ai_response = ask_watsonx(prompt)
    youtube_links = search_youtube_videos(ingredients)


    return {
        "result": ai_response,
        "youtube": youtube_links
    }
