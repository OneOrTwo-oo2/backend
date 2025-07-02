from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup


router = APIRouter()

@router.get("/recipe-detail")
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