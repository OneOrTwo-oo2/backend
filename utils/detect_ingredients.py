from image_model.box_detector import detect_nms
from image_model.classifier import classify_clip


def detect_ingredient(image_path):
    keep, all_boxes, all_crops = detect_nms(image_path)
    detections, result_img = classify_clip(image_path,keep,all_boxes,all_crops)

    return detections    
