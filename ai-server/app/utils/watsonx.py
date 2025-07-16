import config
import requests
import re
import json
import time

# 전역 변수로 토큰과 만료 시간 관리
_access_token = None
_expires_at = 0  # 유닉스 타임스탬프

# ✅ Watsonx 토큰 발급
def get_ibm_access_token(api_key: str) -> str:
    global _access_token, _expires_at

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
        verify=False  # 운영시에는 True or 생략 SSL 인증서 경고 무시하는격
    )
    response.raise_for_status()
    token_data = response.json()

    _access_token = token_data["access_token"]
    # expires_in은 초 단위 → 현재 시간 + 만료 시간
    _expires_at = time.time() + token_data.get("expires_in", 3600) - 60  # 60초 여유

    return _access_token

def get_valid_access_token() -> str:
    global _access_token, _expires_at

    if not _access_token or time.time() >= _expires_at:
        print("🔄 Watsonx 토큰 갱신 중...")
        return get_ibm_access_token(config.WATSON_API_KEY)
    return _access_token


def ask_watsonx(prompt: str) -> str:
    url = config.WATSONX_URL
    headers = {
        "Authorization": f"Bearer {get_valid_access_token()}",
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



def parse_watsonx_json(response_text: str) -> dict:
    """
    Watsonx의 raw 응답 문자열을 받아 JSON 파싱 가능한 딕셔너리로 변환
    """
    raw_text = None  # 에러 발생 시에도 접근 가능하게 미리 선언

    try:
        # 문자열을 딕셔너리로 먼저 파싱
        response = json.loads(response_text)

        # generated_text 추출
        raw_text = response["results"][0]["generated_text"]

        # ```json ``` 제거 및 공백 제거
        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        # JSON 형태 본문 추출
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        json_str = cleaned[start:end]

        return json.loads(json_str)

    except Exception as e:
        print("❌ JSON 파싱 실패:", e)
        return {"error": "JSON 파싱 실패", "raw": raw_text if raw_text else response_text}