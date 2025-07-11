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

        # ✅ 재료
        ingredients = []
        ingre_elements = soup.select("div#divConfirmedMaterialArea ul li")

        for li in ingre_elements:
            # '구매' 버튼 제거
            for tag in li.select("button"):
                tag.decompose()

            # 텍스트 추출 후 '구매'라는 단어 제거
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
            steps.append({
                "desc": desc,
                "img": img
            })

        return {
            "summary": summary,
            "ingredients": ingredients,
            "steps": steps,
            "link": link
        }
    except Exception as e:
        print("❌ 상세 페이지 파싱 에러:", e)
        return {"error": "파싱 실패", "summary": "", "steps": []}