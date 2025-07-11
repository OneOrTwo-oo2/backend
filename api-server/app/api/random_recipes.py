# 📁 api/random_recipes.py
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from db.connection import get_db
from utils.recipe_bookmark import get_or_create_recipe_id
from typing import Optional

router = APIRouter()

@router.get("/random-recipes")
def get_random_recipes(page: Optional[int] = Query(None), db: Session = Depends(get_db)):
    import random
    if not page:
        page = random.randint(2, 10)

    url = f"https://www.10000recipe.com/issue/view.html?cid=9999scrap&page={page}"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rcp_m_list2 > li"))
        )
    except Exception as e:
        driver.quit()
        return {"results": [], "error": "❌ 페이지 로딩 실패", "details": str(e)}

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    results = []
    for card in soup.select("ul.rcp_m_list2 > li"):
        try:
            a_tag = card.select_one("a")
            link = "https://www.10000recipe.com" + a_tag["href"]
            title = card.select_one(".tit").get_text(strip=True)
            img_tag = card.select_one("img")
            img = img_tag.get("data-src") or img_tag.get("src")

            recipe_id = get_or_create_recipe_id(db, title, img, "", link)

            results.append({
                "id": recipe_id,
                "title": title,
                "image": img,
                "link": link
            })
        except Exception as e:
            print("❌ 카드 파싱 에러:", e)
            continue

    return {"results": results, "count": len(results)}
