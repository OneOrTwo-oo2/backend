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


@app.get("/recipe-detail")
def get_recipe_detail(link: str):
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.content, "html.parser")

        summary = soup.select_one("div.view2_summary").get_text(strip=True) if soup.select_one("div.view2_summary") else "요약 없음"

        # ✅ 조리 순서
        steps = []
        step_elements = soup.select("div.view_step > div.view_step_cont")

        for step in step_elements:
            desc = step.select_one("div.media-body").get_text(strip=True) if step.select_one("div.media-body") else ""
            img_tag = step.select_one("img")
            img = img_tag["src"] if img_tag else ""
            steps.append({
                "desc": desc,
                "img": img
            })

        return {
            "summary": summary,
            "steps": steps,
            "link": link
        }
    except Exception as e:
        print("❌ 상세 페이지 파싱 에러:", e)
        return {"error": "파싱 실패", "summary": "", "steps": []}


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
