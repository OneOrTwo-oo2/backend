import torch
import cv2
import os
from ultralytics import YOLO
from image_model.config import *  # CLASS_LABELS, CLS_MODEL_PATH, COLOR, BLOCKLIST, CLS_CONF_THRESHOLD 등
import open_clip
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from torchvision import transforms



def draw_labeled_box(image: np.ndarray, bbox: list[int], label: str, color=COLOR, font_size=12):
    """
    이미지에 라벨과 박스를 그리는 함수
    :param image: BGR 이미지 (OpenCV)
    :param bbox: [x1, y1, x2, y2] 좌표
    :param label: 표시할 텍스트
    :param color: 박스 색상 (BGR)
    :param font_size: 텍스트 폰트 크기
    :return: 박스와 텍스트가 그려진 이미지
    """
    x1, y1, x2, y2 = bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    # OpenCV → PIL 변환
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    draw.text((x1, y1 - font_size - 2), label, font=font, fill=(255, 0, 0))

    # PIL → OpenCV 변환
    return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)


def get_class_info(label):
    """YOLO class label을 한글과 카테고리로 변환"""
    return CLASS_MAP.get(label.lower(), ("알 수 없음", "기타"))


def classify_yolocls(image_path, keep, all_boxes, all_crops):
    """YOLO 기반 분류 모델로 crop 이미지 분류"""
    image = cv2.imread(image_path)
    cls_model = YOLO(YOLO_CLS_MODEL_PATH)
    detections = []

    for i in keep:
        idx = int(i.item()) if isinstance(i, torch.Tensor) else int(i)
        x1, y1, x2, y2 = map(int, all_boxes[idx])
        crop = all_crops[idx]

        cls_result = cls_model(crop)[0]
        if not hasattr(cls_result, "probs"):
            continue

        cls_id = int(cls_result.probs.top1)
        cls_label = cls_result.names[cls_id]
        cls_conf = float(cls_result.probs.data[cls_id])

        if cls_label in BLOCKLIST or cls_conf < CLS_CONF_THRESHOLD:
            continue

        kor_label, category = get_class_info(cls_label)
        
        # box 및 label 이미지에 표시
        image = draw_labeled_box(image=image,bbox=[x1,y1,x2,y2],label=kor_label)
        
        detections.append({
            "label": cls_label,
            "korean": kor_label,
            "category": category,
            "conf": round(cls_conf, 3),
            "bbox": [x1, y1, x2, y2]
        })

    return detections, image


def load_finetuned_clip(model_path, device="cuda"):
    model_name = "ViT-SO400M-14-SigLIP"
    pretrained = "webli"
    
    model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained, device=device, force_quick_gelu=True)
    if os.path.exists(model_path):
        print('using pretrained model')
        model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    tokenizer = open_clip.get_tokenizer(model_name)

    return model, preprocess, tokenizer


# 파일 상단(최초 1회만 로딩)
clip_model = None
preprocess = None
tokenizer = None

def get_clip_model():
    global clip_model, preprocess, tokenizer
    if clip_model is None:
        model_path = os.path.join(PRETRAINED_FOLDER, "clip", CLIP_PRETRAINED)
        clip_model, preprocess, tokenizer = load_finetuned_clip(model_path, device="cuda")
    return clip_model, preprocess, tokenizer


##### open_clip 사용하여 fine-tune 시도
def classify_clip(image_path, keep, all_boxes, all_crops):
    """CLIP 모델을 이용한 자유 라벨 기반 분류"""
    import time
    image = cv2.imread(image_path)
    detections = []
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # --- 1. YOLO 박스 검출 이후 ~ CLIP 모델 로딩 시작 ---
    t0 = time.time()
    clip_model, preprocess, tokenizer = get_clip_model()
    t1 = time.time()
    print(f"[TIME] CLIP 모델 로딩: {t1-t0:.3f}초")

    # --- 2. 텍스트 임베딩 생성 ---
    text_prompts = [f"A photo of {label.replace('_', ' ')}" for label in CLASS_LABELS]
    text_tokens = tokenizer(text_prompts).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
    t2 = time.time()
    print(f"[TIME] 텍스트 임베딩 생성: {t2-t1:.3f}초")

    # --- 3. crop별 루프 시작 전 ---
    t3 = time.time()
    print(f"[TIME] crop별 분류 루프 진입: {t3-t2:.3f}초")

    # --- 전체 타이머 시작 ---
    start_time = time.time()

    for i, box_idx in enumerate(keep):
        crop_start = time.time()
        idx = int(box_idx.item()) if isinstance(box_idx, torch.Tensor) else int(box_idx)
        x1, y1, x2, y2 = map(int, all_boxes[idx])
        crop = all_crops[idx]

        crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        crop_input = preprocess(crop_pil).unsqueeze(0).to(device)

        with torch.no_grad():
            image_feature = clip_model.encode_image(crop_input)
            image_feature /= image_feature.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_feature @ text_features.T).softmax(dim=-1)

        cls_id = int(similarity.argmax().item())
        cls_label = CLASS_LABELS[cls_id]
        cls_conf = float(similarity[0, cls_id])

        if cls_label in BLOCKLIST or cls_conf < CLS_CONF_THRESHOLD:
            continue

        # box 및 label 이미지에 표시
        image = draw_labeled_box(image=image,bbox=[x1,y1,x2,y2],label=cls_label)

        detections.append({
            "label": cls_label,
            "korean": cls_label,
            "category": 'clip',
            "conf": round(cls_conf, 3),
            "bbox": [x1, y1, x2, y2]
        })
        crop_elapsed = time.time() - crop_start
        print(f"[CLIP 분류] crop {i+1}/{len(keep)}: {crop_elapsed:.3f}초")

    # --- 전체 타이머 끝 ---
    elapsed = time.time() - start_time
    print(f"[CLIP 분류 소요 시간] {elapsed:.3f}초 (YOLO 박스 이후 ~ CLIP 분류 전체)")

    return detections, image


def classify_resnet(image_path, keep, all_boxes, all_crops):
    # read img
    image = cv2.imread(image_path)
    
    # preprocessing before classification 
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)])
    
    # load classifier
    device = "cuda" if torch.cuda.is_available() else "cpu"
    classifiers = {}
    for key, item in CLASSIFIER_MODELS.items():
        model = torch.load(os.path.join(PRETRAINED_FOLDER,'resnet',item['path']), map_location=device)
        model.eval()
        classifiers[key] = {'model': model, 'offset': item['class_offset']}
        
        
    detections = []
    for i in keep:
        idx = int(i.item()) if isinstance(i, torch.Tensor) else int(i)
        x1, y1, x2, y2 = map(int, all_boxes[idx])
        crop = all_crops[idx]
        
        inputs = transform(crop).unsqueeze(0).to(device)
        best_class, best_logit = None, float('-inf')

        with torch.no_grad():
            for key, info in classifiers.items():
                model = info['model']
                logits = model(inputs)[0]  # softmax 없이 logit 그대로 사용
                top1_idx = torch.argmax(logits).item()
                top1_logit = logits[top1_idx].item()
                global_class = info['offset'] + top1_idx

                if top1_logit > best_logit:
                    best_class = global_class
                    best_logit = top1_logit
        
        predicted_class = best_class
        class_name = CLASS_NAME_MAP.get(predicted_class, "알수없음")
        cls_label = f"{class_name} (logit:{best_logit:.2f})"

        # 시각화
        image = draw_labeled_box(image=image,bbox=[x1,y1,x2,y2],label=cls_label)

        detections.append({
            "label": cls_label,
            "korean": cls_label,
            "category": 'resnet',
            "conf": round(best_logit, 3),
            "bbox": [x1, y1, x2, y2]
        })

    return detections, image
        
    
    
    