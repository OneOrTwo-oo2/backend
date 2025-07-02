from fastapi import APIRouter
import os
import json


router = APIRouter()

# ✅ YOLO 클래스 리스트 제공 API
@router.get("/api/yolo-classes")
def get_yolo_classes():
    json_path = os.path.join(os.path.dirname(__file__), "yolo_classes.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            classes = json.load(f)
        return classes
    except Exception as e:
        return {"error": str(e)}