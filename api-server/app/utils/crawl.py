import requests
from typing import List
from bs4 import BeautifulSoup

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