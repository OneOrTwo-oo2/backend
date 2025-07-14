from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup


from pydantic import BaseModel
from typing import List, Optional

class Step(BaseModel):
    desc: str
    img: Optional[str] = ""

class RecipeSummary(BaseModel):
    text: str
    serving: Optional[str] = ""
    time: Optional[str] = ""
    difficulty: Optional[str] = ""

class RecipeDetailOut(BaseModel):
    summary: RecipeSummary
    ingredients: List[str]
    steps: List[Step]
    link: str


router = APIRouter()

@router.get("/recipe-detail", response_model=RecipeDetailOut)
def get_recipe_detail(link: str):
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.content, "html.parser")

        summary_text = soup.select_one("div.view2_summary_in").get_text(strip=True) \
         if soup.select_one("div.view2_summary_in") else "요약 없음"

        serving = soup.select_one("span.view2_summary_info1")
        time = soup.select_one("span.view2_summary_info2")
        difficulty = soup.select_one("span.view2_summary_info3")

        summary = {
            "text": summary_text,
            "serving": serving.get_text(strip=True) if serving else "",
            "time": time.get_text(strip=True) if time else "",
            "difficulty": difficulty.get_text(strip=True) if difficulty else ""
        }
        # ✅ 재료
        ingredients = []
        ingre_elements = soup.select("div#divConfirmedMaterialArea ul li")
        for li in ingre_elements:
            for tag in li.select("button"):
                tag.decompose()
            text = li.get_text(strip=True).replace("구매", "").strip()
            if text:
                ingredients.append(text)

        # ✅ 조리 순서
        steps = []
        step_elements = soup.select("div.view_step > div.view_step_cont")
        for step in step_elements:
            desc = step.select_one("div.media-body").get_text(strip=True) if step.select_one("div.media-body") else ""
            img_tag = step.select_one("img")
            img = img_tag["src"] if img_tag else ""
            steps.append({"desc": desc, "img": img})

        return {
            "summary": summary,
            "ingredients": ingredients,
            "steps": steps,
            "link": link
        }

    except Exception as e:
        print("❌ 상세 페이지 파싱 에러:", e)
        return {"error": "파싱 실패", "summary": "", "steps": []}


