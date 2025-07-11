import os

# :흰색_확인_표시: 클래스 매핑: 영어 클래스명을 한글 이름과 카테고리로 변환
CLASS_NAME_MAP = {
    0: "딸기",
    1: "레몬",
    2: "바나나",
    3: "생크림",
    4: "슬라이스치즈",
    5: "아이스크림",
    6: "음식_재료_날치알",
    7: "음식_재료_대구알",
    8: "음식_재료_성게알"
}
# CLASS_LABELS = [
# "BBQ_sauce", "Bag_ramen", "Baguette", "Beer", "Canned_beans", "Canned_clams", "Canned_corn", "Canned_fruits", "Canned_mackerel", "Canned_pizza_sauce", "Canned_potatoes", "Canned_salmon", "Canned_seafood", "Canned_soup", "Canned_tomatoes", "Canned_tuna", "Canned_vegetables", "Canned_whelk", "Cheddar_cheese", "Chinese-style_noodles", "Chocolate_milk", "Ciabatta", "Coffee", "Croissant", "Doubanjang", "Glass_noodles", "Ice_cream", "Instant_curry", "Jjolmyeon", "Juice", "Kalguksu_noodles", "Makgeolli", "Mozzarella_cheese", "Naengmyeon_noodles", "Oyster_mushrooms", "Parmesan_cheese", "Perilla_leaves", "Ramen_noodles", "Ramyeon_noodles", "Rice_noodles", "Sliced_cheese", "Soju", "Somyeon", "Sparkling_water", "Strawberry_milk", "Tea", "Udon_noodles", "Water", "Wine", "Yogurt_drink", "abalone", "alfredo_sauce", "apple", "avocado", "bacon", "balsamic_vinegar", "banana", "basil", "bean_sprout", "beef", "blueberry", "bok_choy", "brisket", "broccoli", "brown_rice", "buldak_sauce", "butter", "button_mushroom", "cabbage", "carrot", "cauliflower", "celery", "cherry", "chicken_breast", "chicken_drumstick", "chicken_thigh", "chicken_wing", "chili_flakes", "chili_pepper", "chili_sauce", "chipotle_sauce", "chive", "cilantro", "clam", "cod_roe", "condensed_milk", "cooking_oil", "cooking_syrup", "crab", "cream_cheese", "cucumber", "cumin", "cup_ramen", "curry_powder", "dried_anchovy", "dried_pollack_strips", "dried_shrimp", "duck", "dumpling", "egg", "eggplant", "enoki_mushroom", "fermented_soybean_paste", "fish", "fish_sauce", "flavored_soy_sauce", "flounder", "flying_fish_roe", "for_bulgogi", "fresh_cream", "fusilli", "garlic", "ginger", "ginseng", "grape", "green_onion", "ham", "hoisin_sauce", "honey", "instant_rice", "instant_soup", "jujube", "kelp", "kimbap", "kimchi", "king_oyster_mushroom", "kiwi", "lamb", "lasagna_sheet", "laver", "lemon", "lettuce", "lobster", "macaroni", "mala_sauce", "mango", "maple_syrup", "margarine", "matsutake_mushroom", "mayonnaise", "meatball", "milk", "minced_garlic", "minced_ginger", "mixed_grain_rice", "mung_bean_sprouts", "mussel", "mustard", "napa_cabbage", "nuts", "octopus", "olive_oil", "orange", "oregano", "oyster_sauce", "paprika", "peach", "pear", "penne", "pepper", "perilla_oil", "pineapple", "plain_bread", "plum", "pollock_roe", "pork_back_ribs", "pork_belly", "pork_front_leg", "pork_hind_leg", "pork_neck", "potato", "radish", "red_chili_paste", "red_onion", "red_pepper_powder", "ribs", "rosemary", "saffron", "salad", "salmon", "salmon_roe", "salt", "sausage", "scallop", "sea_squirt", "sea_urchin_roe", "seasoned_dried_squid", "seaweed", "sesame_oil", "shank", "shiitake_mushroom", "shrimp", "sirloin", "sliced_rice_cake", "soy_sauce", "soybean_paste", "spaghetti", "spam", "spinach", "sprite", "squid", "strawberry", "sugar", "sweet_potato", "teriyaki_sauce", "thyme", "tomato", "tomato_sauce", "tuna", "vinegar", "water_parsley", "watermelon", "whipping_cream", "white_rice", "whole_grain_mustard", "yogurt", "zucchini"
# ]

CLASS_LABELS = [
    "Baguette", "Beer",  "Chocolate_milk",  "Coffee", "Croissant", "Ice_cream", "Juice",  "Perilla_leaves", "Sliced_cheese", "Soju", "Strawberry_milk", "Tea", "Water", "Wine", "Yogurt_drink", "abalone", "alfredo_sauce", "apple", "avocado", "bacon", "balsamic_vinegar", "banana", "bean_sprout", "beef", "blueberry", "brisket", "broccoli",  "butter", "button_mushroom", "cabbage", "carrot", "cauliflower", "celery", "cherry", "chicken_breast", "chicken_wing", "chive", "cilantro", "clam",  "cooking_oil", "cooking_syrup", "crab", "cream_cheese", "cucumber",   "dried_shrimp", "duck", "dumpling", "egg", "eggplant", "fish",  "flounder", "fresh_cream", "fusilli", "garlic", "ginger", "grape", "green_onion", "ham", "hoisin_sauce", "honey", "kelp", "kimbap", "kimchi", "kiwi",  "lasagna_sheet", "laver", "lemon", "lettuce", "lobster", "macaroni", "mango",  "margarine", "mayonnaise", "meatball", "milk", "minced_garlic", "mussel",  "nuts", "octopus", "olive_oil", "orange", "peach", "pear", "penne", "pineapple", "plain_bread", "plum", "pork_back_ribs", "pork_belly", "pork_neck", "potato", "radish", "red_onion", "ribs", "salad", "salmon", "salt", "sausage", "scallop",  "seaweed", "sesame_oil", "shank",  "shrimp", "sirloin", "sliced_rice_cake",  "soybean_paste", "spaghetti", "spam", "spinach", "sprite", "squid", "strawberry", "sugar", "sweet_potato",  "tomato", "tuna", "vinegar", "watermelon", "whipping_cream", "white_rice", "yogurt", "zucchini"
]

CLASS_MAP = {
    "간편식": ("간편식", "간편식류"),
    "김밥": ("김밥", "간편식류"),
    "김치": ("김치", "반찬류"),
    "떡국떡": ("떡국떡", "떡류"),
    "떡볶이": ("떡볶이", "간식류"),
    "라면": ("라면", "면류"),
    "만두": ("만두", "간식류"),
    "맥주": ("맥주", "주류"),
    "물": ("물", "음료"),
    "볶음밥": ("볶음밥", "간편식류"),
    "사이다": ("사이다", "음료"),
    "소주": ("소주", "주류"),
    "스낵": ("스낵", "간식류"),
    "와인": ("와인", "주류"),
    "요거트음료": ("요거트음료", "음료"),
    "우유": ("우유", "음료"),
    "주스": ("주스", "음료"),
    "즉석국": ("즉석국", "즉석류"),
    "즉석밥": ("즉석밥", "즉석류"),
    "즉석카레": ("즉석카레", "즉석류"),
    "차": ("차", "음료"),
    "커피가루": ("커피가루", "음료"),
    "컵라면": ("컵라면", "면류"),
    "탄산수": ("탄산수", "음료"),
    "핫도그": ("핫도그", "간식류")
}

# 예외처리 labels
BLOCKLIST = {"bowl", "spoon", "fork", "knife", "dining table", "plate"}

# hyperparams
CONF_THRESHOLD = 0.12        # 전체 detection confidence 임계값
CLS_CONF_THRESHOLD = 0.1     # classification confidence 임계값
MIN_BOX_SIZE = 15            # 너무 작은 박스 제거
MAX_BOX_SIZE = 510           # 너무 큰 박스 제거


# pretrained model roots
PRETRAINED_FOLDER = 'pretrained_models'
YOLO_BOX_FOLDER = 'yolo_box'
CLIP_PRETRAINED = 'clip_best3.pt'
# CLIP_PRETRAINED = 'clip_ingredient_finetuned.pt'

# yolo_cls
YOLO_CLS_MODEL_PATH = os.path.join(PRETRAINED_FOLDER,'yolo_cls',"best.pt")


# resnet
CLASSIFIER_MODELS = {
    'A': {'path': 'classifier_A.pth', 'class_offset': 0, 'num_classes': 3},
    'B': {'path': 'classifier_B.pth', 'class_offset': 3, 'num_classes': 3},
    'C': {'path': 'classifier_C.pth', 'class_offset': 6, 'num_classes': 3}
}

MODEL_PATHS = {
    "YOLOv8n": "yolov8n.pt",
    "YOLOv8s": "yolov8s.pt",
    "YOLO11n": "yolo11n.pt",
    "YOLO11s": "yolo11s.pt",
    "YOLO11m": "yolo11m.pt",
    "YOLO11l": "yolo11l.pt",
    "YOLO11x": "yolo11x.pt",
    "YOLO11n-seg": "yolo11n-seg.pt",
    "YOLO11s-seg": "yolo11s-seg.pt",
    "YOLO11m-seg": "yolo11m-seg.pt"
}



# :흰색_확인_표시: 박스 시각화 색상
COLOR = (0, 255, 0)