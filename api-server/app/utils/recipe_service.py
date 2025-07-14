from bs4 import BeautifulSoup
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session
from db.models import Recipe

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

    def get_or_create_recipe_id(db, title, image, summary, link):
        # ✋ 동영상 썸네일은 저장 안 함
        if "icon_vod.png" in image:
            print(f"⏩ [SKIP: DB insert] icon_vod image: {image}")
            return None

        # 기존 레시피가 있는지 확인
        recipe = db.query(Recipe).filter_by(link=link).first()
        if recipe:
            return recipe.id

        # 새로 추가
        recipe = Recipe(title=title, image=image, summary=summary, link=link)
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return recipe.id


    def parse_card(card):
        try:
            # ✅ (1) 이미지 태그가 있는지
            img_tag = card.select_one(".common_sp_thumb img")
            if not img_tag:
                print("❌ [SKIP: no img tag] 이미지 태그 없음")
                return None

            # ✅ (2) 이미지 src 속성이 없거나 http 아닌 경우
            img_src = img_tag.get("src", "")
            if not img_src or not img_src.startswith("http"):
                print(f"❌ [SKIP: invalid src] src='{img_src}'")
                return None
            
            # ✅ (3) 동영상 썸네일 건너뛰기
            if "icon_vod.png" in img_src:
                print(f"⏩ [SKIP: video icon] 동영상 카드(icon_vod) 건너뜀: {img_src}")
                return None
            
            if card.select_one(".common_sp_thumb .play_time"):
                print("⏩ [SKIP: video] 동영상 썸네일 건너뜀")
                return None

            # ✅ 정상적인 카드 처리
            title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
            link = "https://www.10000recipe.com" + card.select_one("a.common_sp_link")["href"]
            print(f"✅ [PASS] 제목: {title}, 이미지: {img_src}")
            recipe_id = get_or_create_recipe_id(db, title, img_src, "", link)

            return {
                "id": recipe_id,
                "title": title,
                "image": img_src,
                "link": link
            }

        except Exception as e:
            print(f"❌ [EXCEPTION] 파싱 중 오류: {e}")
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
        for card in soup.select("ul.common_sp_list_ul > li.common_sp_list_li")[:40]:
            parsed = parse_card(card)
            if parsed: recipes.append(parsed)

    return {"results": recipes, "count": len(recipes)}

