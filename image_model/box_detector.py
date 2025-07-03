import os
import cv2
import torch
from ultralytics import YOLO
from torchvision.ops import nms

from config import *
from classifier import classify_yolocls, classify_clip, classify_resnet

# :흰색_확인_표시: 전체 파이프라인
def detect_nms(image_path):
    image = cv2.imread(image_path)  # 이미지 불러오기
    h, w = image.shape[:2]
    
    all_boxes, all_scores, all_crops = [], [], []
    
    # :일: 여러 YOLO detection 모델을 순서대로 실행 (Ensemble 느낌)
    for name, model_path in MODEL_PATHS.items():
        model_path = os.path.join(PRETRAINED_FOLDER,YOLO_BOX_FOLDER,model_path)
        model = YOLO(model_path)
        result = model(image_path, conf=0.05, iou=0.65)[0]
        for box in result.boxes.data:
            x1, y1, x2, y2 = map(int, box[:4])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            conf = float(box[-2])
            box_w, box_h = x2 - x1, y2 - y1
            # 크기 기준 필터링 (너무 작거나 크면 제외)
            if box_w < MIN_BOX_SIZE or box_h < MIN_BOX_SIZE or box_w > MAX_BOX_SIZE or box_h > MAX_BOX_SIZE:
                continue
            crop = image[y1:y2, x1:x2]  # 박스 부분 crop 추출
            all_boxes.append([x1, y1, x2, y2])
            all_scores.append(conf)
            all_crops.append(crop)
    # :둘: 박스가 하나도 없을 경우 종료
    if not all_boxes:
        print(":x: 감지된 객체 없음")
        return [], [], []
    # :셋: Non-Maximum Suppression (중복 박스 제거)
    t_boxes = torch.tensor(all_boxes, dtype=torch.float32)
    t_scores = torch.tensor(all_scores, dtype=torch.float32)
    keep = nms(t_boxes, t_scores, iou_threshold=0.7)
    
    return keep, all_boxes, all_crops
    
    
    
# :흰색_확인_표시: 메인 실행부
if __name__ == "__main__":
    # 테스트용 이미지 폴더 설정
    image_folder = os.path.join(os.path.dirname(__file__), "testimg")
    out_folder = os.path.join(image_folder, "results")
    os.makedirs(out_folder, exist_ok=True)
    
    # 폴더 내 이미지 파일 전체 반복
    for file in os.listdir(image_folder):
        if file.lower().endswith((".jpg", ".png", ".jpeg")):
            image_path = os.path.join(image_folder, file)
            print(f"{file} 처리 중...")

            keep, all_boxes, all_crops = detect_nms(image_path)
            # detections, result_img = classify_yolocls(image_path,keep,all_boxes,all_crops)
            detections, result_img = classify_clip(image_path,keep,all_boxes,all_crops)
            # detections, result_img = classify_resnet(image_path,keep,all_boxes,all_crops)
            
            # 결과 출력
            print(f"감지 결과 ({file}):")
            for det in detections:
                print(f"{det['category']}: {det['korean']} ({det['conf']:.2f}) at {det['bbox']}")
            # 결과 이미지 저장
            out_path = os.path.join(out_folder, f"result_{file}")
            cv2.imwrite(out_path, result_img)
            print(f"저장됨: {out_path}\n")
            
            