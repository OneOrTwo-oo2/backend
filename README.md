# .env 파일 로드

load_dotenv()

# 🔐 환경 변수 로딩

WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")  # 구글 이메일
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")  # 구글 비밀번호

# ✅ CORS 설정

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트 도메인 배포시에는 설정 예정
    # allow_origins=["http://localhost:3000"],  # 프론트 주소 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🎁 함수 설명 

def search_youtube_videos
  YouTube API를 이용해 특정 검색어에 대한 조회수 높은 요리 레시피 영상을 찾아주는 함수입니다.
  query: 검색어
  max_results: 최대 몇 개의 영상 결과를 가져올지 설정 (기본값 3개).
  key: YouTube Data API 키 (YOUTUBE_API_KEY는 환경변수 또는 상수로 저장돼 있어야 함).
  part=snippet: 제목, 설명, 썸네일 등 기본 메타데이터를 요청.
  q=query + " 레시피": 예를 들어 "감자전 레시피"처럼 검색.
  type=video: 동영상만 검색.
  order=viewCount: 조회수 순으로 정렬.

def get_ibm_access_token
  IBM Cloud IAM(Identity and Access Management)을 통해 Watsonx API에 접근할 수 있는 access token을 발급받습니다.
  POST 요청을 통해 IBM IAM 서버에 API Key를 인증 정보로 전송합니다.
  grant_type: IBM의 OAuth 형식이며 "urn:ibm:params:oauth:grant-type:apikey"는 API key 기반 인증임을 의미.
  verify=False: SSL 인증서 검증을 끕니다. 보안상 권장되지 않으며, 테스트 용도일 가능성 높음.

ACCESS_TOKEN = get_ibm_access_token(WATSON_API_KEY)
  발급받은 토큰을 전역으로 저장하여, 여러 요청에 반복적으로 사용.
  WATSON_API_KEY는 외부에 하드코딩하지 말고 .env에 보관 후 os.getenv() 등으로 가져오는 것이 안전합니다

def ask_watsonx
  Watsonx의 텍스트 생성 모델에 프롬프트를 전달하여 결과를 생성합니다.
  us-south: 데이터 센터 위치 (IBM Cloud에서 선택한 리전).
  deployments/{deployment_id}: Watson Studio에서 배포한 LLM 모델의 ID.
  text/generation: 텍스트 생성 요청.
  version: API 버전 (2021-05-01은 v1 기준입니다).
  Authorization: 발급받은 토큰을 사용.
  Content-Type: JSON 형식 전송.
  Accept: 응답도 JSON으로 받겠다는 뜻.
  parameters.prompt_variables.context: 프롬프트가 들어가는 위치. 이는 IBM Watsonx에서 미리 정의된 프롬프트 템플릿에서 {{context}} 같은 변수 자리에 대입됩니다.

def build_prompt
  prompt 작성
  ingredients	str	사용자로부터 입력받은 재료들
  detailed_recipes	str	레시피 데이터 (크롤링 or DB에서 가져온)
  context	str or None	질환 관련 배경 정보 문서 (예: IBM Watson으로 학습된 텍스트)
  disease	str or None	특정 질환 이름 (예: "당뇨", "고혈압")

class RecipeRequest(BaseModel)
  FastAPI 백엔드에서 클라이언트로부터 전달받을 POST 요청의 형식을 정의하는 데이터 모델입니다.
  BaseModel	요청 JSON의 구조와 타입을 정의
  ingredients: str	필수 재료 목록 (문자열)
  disease: Optional[str]	선택적 질환 정보 (주석 처리됨)

@app.post("/recommend")
async def recommend_recipe
  FastAPI 핸들러 함수로 사용자가 입력한 재료를 기반으로: 레시피 검색 → 상세 정보 크롤링 → Watsonx LLM 요리 추천 → YouTube 영상 검색을 한 번에 수행하고 그 결과를 응답으로 반환합니다.
  RecipeRequest 객체에서 ingredients 필드를 가져옵니다.
  get_recipes()는 재료 기반의 요리 리스트를 가져오는 함수입니다.
  detailed_recipes: LLM에게 전달할 텍스트 데이터로 변환됨.
  disease가 입력되면 → 해당 키워드로 질환 식단 관련 문서를 벡터 DB에서 5개 검색. context는 프롬프트에 넣을 질환 관련 배경 지식.
  현재는 disease = None으로 꺼져 있음. → 프론트에서 req.disease를 받을 수 있도록 추가하면 동작함.

@app.get("/recipes")
def get_recipes
  만개의 레시피 사이트(https://www.10000recipe.com)를 크롤링하여 사용자의 검색 조건(재료, 분류 등)에 맞는 레시피를 찾아 반환합니다.
  ingredients	리스트(예: ?ingredients=감자&ingredients=양파)	재료 검색어  ingredients가 있을 경우 → 검색어를 한 문장으로 합쳐서 q 파라미터에 추가예: 감자 양파 계란 → ?q=감자+양파+계란
  kind	문자열	종류별 (ex. 국/탕, 밑반찬 등)
  situation	문자열	상황별 (ex. 손님접대, 야식 등)
  method	문자열	방법별 (ex. 볶기, 찌기 등)
  theme	문자열	테마별 (ex. 이유식, 다이어트 등)
  base_url: 일반 검색용
  base_url2: 테마별 전용 URL
  검색 결과 페이지에서 최대 30개의 레시피 카드를 선택 CSS 선택자 기준: .common_sp_list_ul > .common_sp_list_li
  title: 제목
  img: 이미지 URL
  link: 실제 레시피 상세 페이지 링크
  results: 파싱된 레시피 리스트 (title, image, link 포함)
  count: 결과 개수

@app.get("/recipe-detail")
def get_recipe_detail
  만개의 레시피 사이트의 개별 레시피 페이지를 크롤링해서 요약(summary)과 조리 순서(steps)를 파싱해주는 기능을 합니다.
  requests.get(link): 해당 레시피 상세 페이지 HTML 요청
  BeautifulSoup으로 HTML을 파싱해서 DOM 형태로 가공
  .view2_summary: 만개의 레시피에서 요약 설명이 들어 있는 div 없을 경우 "요약 없음"으로 처리
  desc	해당 조리 단계의 설명 텍스트
  img	이미지가 있으면 URL, 없으면 빈 문자열
  link 입력	사용자가 넘긴 레시피 링크
  summary	레시피 간단 설명
  steps	조리 단계별 설명 + 이미지
  error 처리	try-except로 파싱 실패 대비

def crawl_recipe_detail_bulk
  여러 개의 레시피 링크를 받아, 각 링크에서 상세한 요리 정보를 크롤링하여 정리된 데이터로 반환하는 역할을 합니다.
  recipes: { "title", "link", "image" } 형식의 레시피 목록 리스트 (기본 검색 결과)
  반환값: 각 레시피의 상세 정보가 담긴 리스트
  .view2_summary h3: 제목이 위치한 요소
  strip=True: 앞뒤 공백 제거
  #divConfirmedMaterialArea li: 재료 리스트 영역  <li> 하나씩 꺼내어 텍스트만 추출
  .view_step_cont: 각 조리 단계 설명 박스 이미지 없이 텍스트만 리스트로 정리됨

@app.get("/random-recipes")
def get_random_recipes
  /random-recipes 경로로 요청을 받으면, 만개의 레시피 사이트의 랜덤 인기 레시피 페이지를 크롤링해서 레시피 목록을 반환합니다.
  page	지정 안 하면 랜덤 (2~10)
  Selenium	동적 콘텐츠 로딩에 사용
  BeautifulSoup	HTML에서 레시피 데이터 추출
  응답	title, image, link 포함된 JSON 리스트 반환

@app.get("/api/yolo-classes")
def get_yolo_classes
   FastAPI 서버에서 YOLO 모델의 클래스 목록을 JSON 파일로부터 불러와 클라이언트에 전달해주는 간단한 API입니다.
   yolo_classes.json	YOLO 모델이 인식 가능한 클래스 정의
   클라이언트	이 목록을 기반으로 드롭다운 또는 분류 결과와 매칭
   응답 형식	JSON (리스트 또는 딕셔너리)
   예외 처리	파일 누락, 형식 오류 대비 가능

   
  
