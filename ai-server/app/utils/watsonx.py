import config
import requests
import re
import json

# ✅ Watsonx 토큰 발급
def get_ibm_access_token(api_key: str) -> str:
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
        verify=False
    )
    response.raise_for_status()
    return response.json()["access_token"]


def ask_watsonx(prompt: str) -> str:
    url = config.WATSONX_URL
    headers = {
        "Authorization": f"Bearer {config.ACCESS_TOKEN}",
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