from fastapi import APIRouter, Query
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode


router = APIRouter()

@router.get("/recipes")
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