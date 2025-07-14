from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup

router = APIRouter()

@router.get("/recipe-detail")
def get_recipe_detail(link: str):
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.content, "html.parser")

        # ✅ 제목
        title_tag = soup.select_one("meta[property='og:title']")
        title = title_tag["content"] if title_tag else "제목 없음"

        # ✅ 메인 썸네일 이미지
        og_img_tag = soup.select_one("meta[property='og:image']")
        image = og_img_tag["content"] if og_img_tag else ""

        if "icon_vod.png" in image:
            print(f"⏩ [SKIP] 동영상 썸네일: {image}")
            return {"error": "동영상 썸네일 제외됨", "link": link}

        # ✅ 요약
        summary_tag = soup.select_one("div.view2_summary")
        summary = summary_tag.get_text(strip=True) if summary_tag else "요약 없음"

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
            desc = step.select_one("div.media-body")
            desc_text = desc.get_text(strip=True) if desc else ""
            img_tag = step.select_one("img")
            img_src = img_tag["src"] if img_tag else ""
            steps.append({
                "desc": desc_text,
                "img": img_src
            })

        return {
            "title": title,
            "image": image,
            "summary": summary,
            "ingredients": ingredients,
            "steps": steps,
            "link": link
        }

    except Exception as e:
        print("❌ 상세 페이지 파싱 에러:", e)
        return {
            "error": "파싱 실패",
            "title": "",
            "image": "",
            "summary": "",
            "ingredients": [],
            "steps": [],
            "link": link
        }
