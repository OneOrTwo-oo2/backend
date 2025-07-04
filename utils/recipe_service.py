from bs4 import BeautifulSoup
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session
from utils.recipe_bookmark import get_or_create_recipe_id

def fetch_recipes_from_10000recipe(
    db: Session,
    ingredients=None, kind=None, situation=None, method=None, theme=None
):
    base_url = "https://www.10000recipe.com/recipe/list.html"
    base_url2 = "https://www.10000recipe.com/theme/view.html"
    params = {}
    recipes = []

    if ingredients:
        params["q"] = " ".join(ingredients)
    if kind: params["cat4"] = kind
    if situation: params["cat2"] = situation
    if method: params["cat1"] = method

    def parse_card(card):
        try:
            title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
            img = card.select_one(".common_sp_thumb img")["src"]
            link = "https://www.10000recipe.com" + card.select_one("a.common_sp_link")["href"]
            recipe_id = get_or_create_recipe_id(db, title, img, "", link)
            return {
                "id": recipe_id,
                "title": title,
                "image": img,
                "link": link
            }
        except Exception as e:
            print("❌ 파싱 에러:", e)
            return None

    if theme and not ingredients:
        for page in range(1, 5):
            url = f"{base_url2}?{urlencode({'theme': theme, 'page': page})}"
            soup = BeautifulSoup(requests.get(url).content, "html.parser")
            for card in soup.select("ul.common_sp_list_ul > li.common_sp_list_li"):
                parsed = parse_card(card)
                if parsed: recipes.append(parsed)
    else:
        url = f"{base_url}?{urlencode(params)}"
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
        for card in soup.select("ul.common_sp_list_ul > li.common_sp_list_li")[:30]:
            parsed = parse_card(card)
            if parsed: recipes.append(parsed)

    return {"results": recipes, "count": len(recipes)}
