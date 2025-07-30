from image_model.box_detector import detect_nms
from image_model.classifier import classify_clip, classify_clip_filtered_bbox
import os
import uuid
from datetime import datetime
import threading
import time
import signal
import atexit


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
    
    # bounding box 이미지를 base64로 인코딩
    bbox_image_base64 = None
    if result_img is not None and len(detections) > 0:
        print(f"🖼️ Bounding box 이미지 base64 인코딩 시작 - detections 개수: {len(detections)}")
        
        import cv2
        import base64
        
        # 이미지를 JPEG로 인코딩
        _, buffer = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if buffer is not None:
            # base64로 인코딩
            bbox_image_base64 = base64.b64encode(buffer).decode('utf-8')
            print(f"✅ Bounding box 이미지 base64 인코딩 성공 (크기: {len(bbox_image_base64)} chars)")
        else:
            print(f"❌ Bounding box 이미지 인코딩 실패")
    else:
        print(f"⚠️ Bounding box 이미지 생성 건너뜀 - result_img: {result_img is not None}, detections: {len(detections) if detections else 0}")
    
    return filtered_ingredients, bbox_image_base64


# 전역 변수로 활성 스레드들을 추적
_active_threads = set()
_shutdown_event = threading.Event()

def delete_file_after_delay(file_path, delay_seconds=10):
    """지정된 시간 후에 파일을 삭제하는 함수"""
    def delete_file():
        print(f"⏰ {delay_seconds}초 후 파일 삭제 예약: {file_path}")
        
        # shutdown_event가 설정되면 즉시 종료
        if _shutdown_event.wait(timeout=delay_seconds):
            print(f"🛑 파일 삭제 스레드 종료됨: {file_path}")
            return
            
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ 파일 삭제 완료: {file_path}")
            else:
                print(f"⚠️ 파일이 이미 삭제됨: {file_path}")
        except Exception as e:
            print(f"❌ 파일 삭제 실패: {file_path}, 오류: {e}")
        finally:
            _active_threads.discard(thread)
    
    thread = threading.Thread(target=delete_file)
    thread.daemon = True
    _active_threads.add(thread)
    thread.start()
    print(f"🔄 파일 삭제 스레드 시작: {file_path}")


def cleanup_old_files(directory, max_age_minutes=60):
    """지정된 디렉토리에서 오래된 파일들을 정리하는 함수"""
    def cleanup():
        while not _shutdown_event.is_set():
            try:
                current_time = time.time()
                max_age_seconds = max_age_minutes * 60
                
                if os.path.exists(directory):
                    for filename in os.listdir(directory):
                        # 종료 신호 확인
                        if _shutdown_event.is_set():
                            break
                            
                        file_path = os.path.join(directory, filename)
                        if os.path.isfile(file_path):
                            file_age = current_time - os.path.getmtime(file_path)
                            if file_age > max_age_seconds:
                                try:
                                    os.remove(file_path)
                                    print(f"🧹 오래된 파일 정리: {file_path} (나이: {file_age/60:.1f}분)")
                                except Exception as e:
                                    print(f"❌ 파일 정리 실패: {file_path}, 오류: {e}")
                
                # 10분마다 정리 작업 실행 (종료 신호 대기)
                if _shutdown_event.wait(timeout=600):
                    break
            except Exception as e:
                print(f"❌ 정리 작업 오류: {e}")
                if _shutdown_event.wait(timeout=60):  # 오류 발생 시 1분 후 재시도
                    break
        
        print(f"🛑 파일 정리 스레드 종료됨: {directory}")
    
    thread = threading.Thread(target=cleanup)
    thread.daemon = True
    _active_threads.add(thread)
    thread.start()
    print(f"🧹 파일 정리 스레드 시작: {directory} (최대 보관: {max_age_minutes}분)")


def shutdown_cleanup_threads():
    """모든 정리 스레드들을 안전하게 종료"""
    print("🛑 정리 스레드 종료 신호 전송...")
    _shutdown_event.set()
    
    # 활성 스레드들이 종료될 때까지 대기 (최대 5초)
    for thread in list(_active_threads):
        thread.join(timeout=5.0)
        if thread.is_alive():
            print(f"⚠️ 스레드가 5초 내에 종료되지 않음: {thread.name}")
    
    print(f"✅ 정리 스레드 종료 완료 (활성 스레드: {len(_active_threads)}개)")


def signal_handler(signum, frame):
    """시그널 핸들러 - 서버 종료 시 정리 스레드들 종료"""
    print(f"📡 종료 시그널 수신: {signum}")
    shutdown_cleanup_threads()


# 종료 시그널 등록
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 프로그램 종료 시 자동 정리
atexit.register(shutdown_cleanup_threads)
