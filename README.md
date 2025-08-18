# Recipe Go 로고

<img width="344" height="197" alt="recipego_logo" src="https://github.com/user-attachments/assets/4b7588e0-b990-45a6-8557-0a6f572863d3" />


## 개요

- 사진 속 재료를 자동으로 인식해 개인 맞춤형 레시피를 추천해주는 AI 기반 서비스입니다.

## 개발 기간

- 2025.06.11 ~ 2025.08.04

## 팀원 구성

<br/>

<div align="left">

- 팀명 : OneOrTwo

| **임호규** || **김용준** || **천송현** || **권신영** |

</div>

<br/>

---

## front

- 기술 스택: HTML, CSS, JavaScript, React

- 설명 : 사용자 인터페이스를 구현한 프런트엔드 웹 애플리케이션입니다. React 기반으로 동적인 UI를 구성하고 있습니다.
  
<br/>

## backend

- 기술 스택: Python, FastAPI, langchain, RAG(Retrieval-Augmented Generation)

- 설명 : 프런트엔드와 연동되는 API 서버 와 langchain , RAG 를 이용해 Watsonx-ai 와 연동하였습니다.
  
<br/>

## AI Model

- 기술 스택: YOLOv8/YOLO11(You Only Look Once), WATSONX-AI(llama-4-maverick-17b-128e-instruct-fp8), CLIP(ViT-L-14/openai), ko-sbert-nli (한국어 SBERT 임베딩 모델)

- 설명 : 이미지 탐지를 통해 분석하는 모델입니다. 2단계 파이프라인으로 구성되어 있으며 YOLO 와 CLIP 을 사용하였습니다. 레시피 추천에는 Watsonx-ai 를 활용하였습니다.
  
<br/>

## CI/CD & Deployment

- 기술 스택: Github action, ArgoCD, Kubernetes

- 설명 : CI/CD 파이프라인을 구축하고 Kubernetes 를 통해 배포하였습니다.

<br/>

## Infra

- 기술 스택: FAISS, BM25, MariaDB, AWS EC2. S3. RDS(Relational Database Service), Router53

- 설명 : 전체적으로 AWS 를 통해 구성하였으며 Recipe Go 서비스의 데이터베이스는 mariaDB, 질환별 식단 데이터를 FAISS 기반 벡터DB로 구성하였고 레시피 데이터는 검색 알고리즘인 BM25 방식을 사용하였습니다.

---

<br/>

## Main Page

<img width="1917" height="736" alt="main" src="https://github.com/user-attachments/assets/ad0040ca-9e4f-478e-83a1-90ecca475cdd" />

메인화면은 세가지의 메인기능으로 구성되어 있습니다.

<br/>

## 재료선택

- 먼저 재료 선택 페이지 에서는 각 카테고리별로 재료를 선택할 수 있습니다.
  
<br/>

<img width="1519" height="493" alt="image" src="https://github.com/user-attachments/assets/7fd877e3-6a14-45ec-a890-0adcf4b3f642" />

- 재료 카테고리 +버튼 토글을 통해 원하는 재료를 쉽게 찾을 수 있습니다.
  
<br/>

<img width="1837" height="275" alt="image" src="https://github.com/user-attachments/assets/f3962d14-501f-4576-bce4-2c85249cd7b9" />

- 좌측에서는 선호도와 종류, 난이도를 선택할 수 있습니다.
  
<br/>

<img width="285" height="444" alt="image" src="https://github.com/user-attachments/assets/2034d70b-5be2-4b87-bc75-4bcad20a641c" />

<br/>

## 사진검색

<br/>

<img width="533" height="309" alt="image" src="https://github.com/user-attachments/assets/fcf54745-443d-4a53-a588-1f51ebf2c782" />

- 사진 검색 페이지에서는 사진촬영이나 보유하고 있는 사진을 통해 검색이 가능하며 추후에 선택된 재료를 수정하여 사용할 수 있습니다.
  
<br/>

## 테마검색

<br/>

<img width="1763" height="260" alt="image" src="https://github.com/user-attachments/assets/93375e01-825e-46d2-8d63-ed2eca703bab" />

<br/>

- 테마 검색 페이지에서는 재료선택 없이도 테마 선택을 통해 레시피 검색이 가능합니다.
  
<br/>

---

# 트러블 슈팅 과정

<br/>

## 이미지 모델

<br/>

<img width="937" height="301" alt="image" src="https://github.com/user-attachments/assets/4ca0941c-ec1b-4b80-93fe-2284322759c8" />

<br/>

- YOLO 특성상 1-Stage Detecting 방식이기 때문에 일부 객체를 누락하는 한계가 존재.

<br/>

<img width="868" height="220" alt="image" src="https://github.com/user-attachments/assets/b4ac56b4-54f3-4a79-a049-0e2461ba849b" />

<br/>

- YOLO Model 8개를 병렬 처리 하여 박스 탐지 결과를 NMS 를 통해 하나로 통합.

<br/>

<img width="1015" height="193" alt="image" src="https://github.com/user-attachments/assets/efe7f5ad-9af2-4ff6-ad50-7d95a6051acd" />

<br/>

CLIP 모델은 주어진 라벨과 다를경우 라벨 인식 실패 하거나 탐지되면 안되는 객체들도 탐지 되는 사실 확인

<br/>

<img width="927" height="396" alt="image" src="https://github.com/user-attachments/assets/15c37dd9-e4c9-4ca6-bed2-ca6d82e05922" />

<br/>

White_List 도입으로 라벨 통일화 작업 및 Block_List 로 오탐 객체 필터링 

<br/>

<img width="1078" height="486" alt="image" src="https://github.com/user-attachments/assets/f74eefbb-48fc-4375-a978-14ff37f81046" />

<br/>

- 결과적으로 테스트 이미지 기준 60% ~ 65% 의 탐지율을 85% ~ 90% 까지 상승하였고 오탐률 또한 감소 하였습니다. 또한 탐지 이후 결과창을 통해 정확도를 기반으로 수정가능 

<br/>

## LLM 모델

> FAISS 기반 의미 유사도 검색은 재료 기반의 정확한 검색에 한계
(예: ‘백미’, ‘양고기’ 입력 시 → ‘소고기 요리’ 추천됨: ‘고기’로 일반화되어 매칭)

<br/>

> 레시피 FAISS 저장 방식 ----> JSON 저장 방식으로 변환
단어 기반 검색(BM25)을 사용하여 더 정확하게 레시피를 가져 올 수 있게 변경

<br/>

<img width="1007" height="400" alt="image" src="https://github.com/user-attachments/assets/0bb8d61a-385c-441d-a163-4f13192d44e8" />

<br/>

- 동일한 재료여도 선호도에 따른 정상적인 AI 추천 원활하게 진행
  
<br/>

<img width="1031" height="559" alt="image" src="https://github.com/user-attachments/assets/f73ccef7-3c47-4d2a-beca-92de25983533" />


---

<br/>

# 인프라 구성

<br/>

<img width="1143" height="641" alt="image" src="https://github.com/user-attachments/assets/1634b476-a9f5-4e62-9dca-7c6950d3df56" />

<br/>

- 쿠버네티스 클러스터 구성

<img width="1159" height="647" alt="image" src="https://github.com/user-attachments/assets/e55c377f-3bab-4e45-a750-d61b251425f2" />

<br/>

- 쿠버네티스 보안성을 위해 Ingress-NGINX 컨트롤러 설치하여 외부에서 직접적으로 POD에 접근하는 것은 차단되며, 모든 클라이언트의 요청은 Ingress 컨트롤러를 거쳐 처리되게 만들었습니다.

<br/>

<img width="1159" height="647" alt="image" src="https://github.com/user-attachments/assets/bec79987-5b98-4f70-b5a8-3bf513497001" />

<br/>

- Github Actions 을 통해 App Repo에 있는 파일이 바뀌면 이미지를 빌드해서 이미지 저장소로 보내고, Argo Repo 에 있는 메니페스트 파일의 이미지 태그를 수정하고 업데이트 합니다.
그러면 Argocd는 Argo Repo에 있는 매니페스트 파일의 변화를 감지하고 변경이 되면 이미지를 풀해서 기존 POD를 갱신하게 됩니다.

<br/>

<img width="1095" height="656" alt="image" src="https://github.com/user-attachments/assets/a5e4f263-13b4-4eb6-a236-15bfceb7f015" />

<br/>

- 최종 인프라 구성
  
<br/>

---

<br/>

# 프로젝트 성과

<br/>

- 2025.08.04

[IBM x Redhat] AI Transformation(AX) Academy 프로젝트 발표회 : 최우수상 (1등)

<br/>

<img width="628" height="469" alt="image" src="https://github.com/user-attachments/assets/765bb2a8-94d8-48f8-a493-825ab5a6813f" />





