import config
import requests


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