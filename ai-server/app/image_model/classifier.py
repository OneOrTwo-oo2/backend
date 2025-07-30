import torch
import cv2
import os
from ultralytics import YOLO
from image_model.config import *  # CLASS_LABELS, CLS_MODEL_PATH, COLOR, BLOCKLIST, CLS_CONF_THRESHOLD 등
import open_clip
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from torchvision import transforms
import config
from utils.emoji_mapper import get_korean_name, get_english_label


def is_korean_text(text):
    """텍스트가 한글을 포함하는지 확인"""
    for char in text:
        if '\uAC00' <= char <= '\uD7AF':  # 한글 유니코드 범위
            return True
    return False


def find_working_font(font_paths, font_size=12):
    """작동하는 폰트를 찾는 함수"""
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                # 테스트 텍스트로 폰트 검증
                test_text = "가나다라"
                bbox = font.getbbox(test_text)
                if bbox[2] > 0 and bbox[3] > 0:  # 유효한 바운딩 박스
                    print(f"✅ 폰트 검증 성공: {font_path}")
                    return font
        except Exception as e:
            print(f"⚠️ 폰트 검증 실패: {font_path}, 오류: {e}")
            continue
    return None


# 파일 상단(최초 1회만 로딩)


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

    # 한글 폰트 경로들 (우선순위 순)
    korean_font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Arial.ttf",  # macOS
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    
    # 텍스트가 한글인지 확인
    is_korean = is_korean_text(label)
    
    if is_korean:
        # 한글 폰트 찾기
        font = find_working_font(korean_font_paths, font_size)
        if font is None:
            print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트 사용")
            font = ImageFont.load_default()
    else:
        # 영어 텍스트는 기본 폰트 사용
        font = ImageFont.load_default()

    # 텍스트 렌더링 시도
    try:
        draw.text((x1, y1 - font_size - 2), label, font=font, fill=(255, 0, 0))
        if is_korean:
            print(f"✅ 한글 텍스트 렌더링 성공: {label}")
        else:
            print(f"✅ 영어 텍스트 렌더링 성공: {label}")
    except Exception as e:
        print(f"❌ 텍스트 렌더링 실패: {label}, 오류: {e}")
        if is_korean:
            # 한글 렌더링 실패 시 영어로 대체
            english_label = get_english_label(label)
            draw.text((x1, y1 - font_size - 2), english_label, font=font, fill=(255, 0, 0))
            print(f"🔄 영어로 대체: {label} → {english_label}")
        else:
            # 영어도 실패하면 간단한 텍스트로 대체
            simple_label = label[:10] if len(label) > 10 else label
            draw.text((x1, y1 - font_size - 2), simple_label, font=font, fill=(255, 0, 0))
            print(f"🔄 간단한 텍스트로 대체: {label} → {simple_label}")

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

        # BLOCKLIST 조건부 필터링: 블록리스트 라벨은 conf 0.95 이상일 때만 허용
        if cls_label in BLOCKLIST and cls_conf < 0.95:
            continue
        if cls_conf < CLS_CONF_THRESHOLD:
            continue

        kor_label, category = get_class_info(cls_label)
        
        # 한글 라벨로 변환 (emojiMap 기준)
        korean_label = get_korean_name(cls_label)
        
        # box 및 label 이미지에 표시 (한글 라벨 사용)
        image = draw_labeled_box(image=image,bbox=[x1,y1,x2,y2],label=korean_label)
        
        detections.append({
            "label": cls_label,
            "korean": korean_label,
            "category": category,
            "conf": round(cls_conf, 3),
            "bbox": [x1, y1, x2, y2]
        })

    return detections, image


def load_finetuned_clip(model_path, device="cuda"):
    model_name = "ViT-L-14"
    pretrained = "openai"
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained, device=device
    )
    if os.path.exists(model_path):
        print('using pretrained model')
        model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    tokenizer = open_clip.get_tokenizer(model_name)
    return model, preprocess, tokenizer



def get_clip_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = os.path.join(PRETRAINED_FOLDER, "clip", CLIP_PRETRAINED)
    clip_model, preprocess, tokenizer = load_finetuned_clip(model_path, device=device)
    return clip_model, preprocess, tokenizer


##### open_clip 사용하여 fine-tune 시도
def classify_clip(image_path, keep, all_boxes, all_crops):
    """CLIP 모델을 이용한 자유 라벨 기반 분류"""
    import time
    image = cv2.imread(image_path)
    detections = []
    device = "cuda" if torch.cuda.is_available() else "cpu"

    clip_model, preprocess, tokenizer = config.clip_model, config.preprocess, config.tokenizer
    
    # --- 2. 텍스트 임베딩 생성 ---
    t1 = time.time()
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

        # WHITELIST_MAP 표준화 적용
        from image_model.config import WHITELIST_MAP
        if cls_label in WHITELIST_MAP:
            std_label = WHITELIST_MAP[cls_label]
            print(f"[WHITELIST 표준화] {cls_label} → {std_label}")
            cls_label = std_label

        # BLOCKLIST 체크 프린트
        print(f"[BLOCKLIST 체크] label: {cls_label}, conf: {cls_conf:.3f}, BLOCKLIST: {cls_label in BLOCKLIST}")

        # BLOCKLIST 조건부 필터링: 블록리스트 라벨은 conf 0.9 이상일 때만 허용
        if cls_label in BLOCKLIST and cls_conf < 0.7:
            continue
        if cls_conf < CLS_CONF_THRESHOLD:
            continue

        # 한글 라벨로 변환
        korean_label = get_korean_name(cls_label)

        # box 및 label 이미지에 표시 (한글 라벨 사용)
        image = draw_labeled_box(image=image,bbox=[x1,y1,x2,y2],label=korean_label)

        detections.append({
            "label": cls_label,
            "korean": korean_label,
            "category": 'clip',
            "conf": round(cls_conf, 3),
            "bbox": [x1, y1, x2, y2]
        })
        # CLIP 결과 프린트
        print(f"[CLIP 결과] label: {cls_label}, conf: {cls_conf:.3f}, bbox: {[x1, y1, x2, y2]}")
        crop_elapsed = time.time() - crop_start
        print(f"[CLIP 분류] crop {i+1}/{len(keep)}: {crop_elapsed:.3f}초")

    # --- 전체 타이머 끝 ---
    elapsed = time.time() - start_time
    print(f"[CLIP 분류 소요 시간] {elapsed:.3f}초 (YOLO 박스 이후 ~ CLIP 분류 전체)")

    return detections, image


def classify_clip_filtered_bbox(image_path, keep, all_boxes, all_crops, confidence_threshold=0.7):
    """CLIP 모델을 이용한 자유 라벨 기반 분류 (정확도 70% 미만만 bounding box 표시)"""
    import time
    image = cv2.imread(image_path)
    detections = []
    device = "cuda" if torch.cuda.is_available() else "cpu"

    clip_model, preprocess, tokenizer = config.clip_model, config.preprocess, config.tokenizer
    
    # --- 2. 텍스트 임베딩 생성 ---
    t1 = time.time()
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

        # WHITELIST_MAP 표준화 적용
        from image_model.config import WHITELIST_MAP
        if cls_label in WHITELIST_MAP:
            std_label = WHITELIST_MAP[cls_label]
            print(f"[WHITELIST 표준화] {cls_label} → {std_label}")
            cls_label = std_label

        # BLOCKLIST 체크 프린트
        print(f"[BLOCKLIST 체크] label: {cls_label}, conf: {cls_conf:.3f}, BLOCKLIST: {cls_label in BLOCKLIST}")

        # BLOCKLIST 조건부 필터링: 블록리스트 라벨은 conf 0.9 이상일 때만 허용
        if cls_label in BLOCKLIST and cls_conf < 0.7:
            continue
        if cls_conf < CLS_CONF_THRESHOLD:
            continue

        # 한글 라벨로 변환
        korean_label = get_korean_name(cls_label)
        
        # 정확도 70% 미만이고 18% 이상인 경우에만 bounding box 그리기
        if cls_conf < confidence_threshold and cls_conf >= 0.18:
            # 정확도에 따른 색상 결정
            if cls_conf >= 0.3:
                color = (0, 165, 255)  # 주황색 (30-70%)
            else:
                color = (0, 0, 255)    # 빨간색 (18-30%)
            
            # box 및 label 이미지에 표시 (한글 라벨 사용, 색상 지정)
            image = draw_labeled_box(image=image, bbox=[x1,y1,x2,y2], label=korean_label, color=color)

        detections.append({
            "label": cls_label,
            "korean": korean_label,
            "category": 'clip',
            "conf": round(cls_conf, 3),
            "bbox": [x1, y1, x2, y2]
        })
        # CLIP 결과 프린트
        print(f"[CLIP 결과] label: {cls_label}, conf: {cls_conf:.3f}, bbox: {[x1, y1, x2, y2]}")
        crop_elapsed = time.time() - crop_start
        print(f"[CLIP 분류] crop {i+1}/{len(keep)}: {crop_elapsed:.3f}초")

    # --- 전체 타이머 끝 ---
    elapsed = time.time() - start_time
    print(f"[CLIP 분류 소요 시간] {elapsed:.3f}초 (YOLO 박스 이후 ~ CLIP 분류 전체)")
    
    # bounding box 그리기 결과 요약
    bbox_drawn_count = 0
    for detection in detections:
        if detection['conf'] < confidence_threshold and detection['conf'] >= 0.18:
            bbox_drawn_count += 1
    
    print(f"[BOUNDING BOX 요약] 전체 detections: {len(detections)}, bounding box 그려진 개수: {bbox_drawn_count}")
    print(f"[BOUNDING BOX 요약] confidence_threshold: {confidence_threshold}, 최소 임계값: 0.18")
    
    if bbox_drawn_count == 0:
        print(f"⚠️ [BOUNDING BOX 경고] 그려진 bounding box가 없습니다. 이미지가 원본과 동일할 수 있습니다.")

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
        
    
    
    