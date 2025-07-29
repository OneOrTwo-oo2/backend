from image_model.box_detector import detect_nms
from image_model.classifier import classify_clip, classify_clip_filtered_bbox
import os
import uuid
from datetime import datetime
import threading
import time


def detect_ingredient(image_path):
    keep, all_boxes, all_crops = detect_nms(image_path)
    
    # 정확도 70% 미만만 bounding box 표시하는 함수 사용
    detections, result_img = classify_clip_filtered_bbox(image_path, keep, all_boxes, all_crops, confidence_threshold=0.7)

    # 정확도 정보를 포함한 결과 생성
    ingredients_with_confidence = []
    for det in detections:
        ingredients_with_confidence.append({
            'label': det['label'],
            'confidence': det['conf']
        })
    
    # 중복 제거 및 정확도 기반 필터링
    unique_ingredients = {}
    for item in ingredients_with_confidence:
        label = item['label']
        confidence = item['confidence']
        
        # 기존 항목이 있으면 더 높은 정확도 선택
        if label not in unique_ingredients or confidence > unique_ingredients[label]['confidence']:
            unique_ingredients[label] = item
    
    # 정확도 순으로 정렬하고 낮은 정확도 항목 필터링
    sorted_ingredients = sorted(unique_ingredients.values(), key=lambda x: x['confidence'], reverse=True)
    
    # 최종 필터링: 너무 낮은 정확도 제거 (18% 미만 제거)
    filtered_ingredients = [item for item in sorted_ingredients if item['confidence'] >= 0.18]
    
    # bounding box 이미지 저장
    bbox_image_url = None
    bbox_save_path = None
    if result_img is not None and len(detections) > 0:
        print(f"🖼️ Bounding box 이미지 저장 시작 - detections 개수: {len(detections)}")
        results_dir = "static/results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"bbox_result_{timestamp}_{unique_id}.jpg"
        bbox_save_path = os.path.join(results_dir, filename)
        
        import cv2
        success = cv2.imwrite(bbox_save_path, result_img)
        if success:
            bbox_image_url = f"/static/results/{filename}"
            print(f"✅ Bounding box 이미지 저장 성공: {bbox_image_url}")
            print(f"✅ 파일 경로: {bbox_save_path}")
        else:
            print(f"❌ Bounding box 이미지 저장 실패: {bbox_save_path}")
    else:
        print(f"⚠️ Bounding box 이미지 저장 건너뜀 - result_img: {result_img is not None}, detections: {len(detections) if detections else 0}")
    
    return filtered_ingredients, bbox_image_url, bbox_save_path


def delete_file_after_delay(file_path, delay_seconds=10):
    """지정된 시간 후에 파일을 삭제하는 함수"""
    def delete_file():
        print(f"⏰ {delay_seconds}초 후 파일 삭제 예약: {file_path}")
        time.sleep(delay_seconds)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ 파일 삭제 완료: {file_path}")
            else:
                print(f"⚠️ 파일이 이미 삭제됨: {file_path}")
        except Exception as e:
            print(f"❌ 파일 삭제 실패: {file_path}, 오류: {e}")
    
    thread = threading.Thread(target=delete_file)
    thread.daemon = True
    thread.start()
    print(f"🔄 파일 삭제 스레드 시작: {file_path}")
