from image_model.box_detector import detect_nms
from image_model.classifier import classify_clip


def detect_ingredient(image_path):
    keep, all_boxes, all_crops = detect_nms(image_path)
    detections, result_img = classify_clip(image_path,keep,all_boxes,all_crops)

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
    
    # 최종 필터링: 너무 낮은 정확도 제거 (더 관대하게)
    filtered_ingredients = [item for item in sorted_ingredients if item['confidence'] >= 0.03]
    
    return filtered_ingredients
