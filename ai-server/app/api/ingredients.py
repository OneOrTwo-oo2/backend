from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

import numpy as np
import cv2
from utils.detect_ingredients import detect_ingredient

import os
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


@router.post("/ingredients")
async def get_ingredients(file: UploadFile = File(...)):
    # 이미지 형식 확인
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 허용됩니다.")

    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="이미지 디코딩 실패")

    # 저장 경로 설정 (파일명은 고유하게 만드는 게 좋음)
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # 이미지 저장
    success = cv2.imwrite(save_path, image)
    if not success:
        raise HTTPException(status_code=500, detail="이미지 저장 실패")
    
    ingredients_with_confidence = detect_ingredient(save_path)

    # 이미지 분석 후 저장된 파일 삭제
    try:
        os.remove(save_path)
    except Exception as e:
        print(f"이미지 삭제 실패: {e}")

    return JSONResponse(content={
        "filename": file.filename,
        "saved_path": save_path,
        "ingredients": ingredients_with_confidence,
        "content_type": file.content_type
    })