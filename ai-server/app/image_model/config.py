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
CLASS_LABELS2 = [
"BBQ_sauce", "Bag_ramen", "Baguette", "Beer", "Canned_beans", "Canned_clams", "Canned_corn", "Canned_fruits", "Canned_mackerel", "Canned_pizza_sauce", "Canned_potatoes", "Canned_salmon", "Canned_seafood", "Canned_soup", "Canned_tomatoes", "Canned_tuna", "Canned_vegetables", "Canned_whelk", "Cheddar_cheese", "Chinese-style_noodles", "Chocolate_milk", "Ciabatta", "Coffee", "Croissant", "Doubanjang", "Glass_noodles", "Ice_cream", "Instant_curry", "Jjolmyeon", "Juice", "Kalguksu_noodles", "Makgeolli", "Mozzarella_cheese", "Naengmyeon_noodles", "Oyster_mushrooms", "Parmesan_cheese", "Perilla_leaves", "Ramen_noodles", "Ramyeon_noodles", "Rice_noodles", "Sliced_cheese", "Soju", "Somyeon", "Sparkling_water", "Strawberry_milk", "Tea", "Udon_noodles", "Water", "Wine", "Yogurt_drink", "abalone", "alfredo_sauce", "apple", "avocado", "bacon", "balsamic_vinegar", "banana", "basil", "bean_sprout", "beef", "blueberry", "bok_choy", "brisket", "broccoli", "brown_rice", "buldak_sauce", "butter", "button_mushroom", "cabbage", "carrot", "cauliflower", "celery", "cherry", "chicken_breast", "chicken_drumstick", "chicken_thigh", "chicken_wing", "chili_flakes", "chili_pepper", "chili_sauce", "chipotle_sauce", "chive", "cilantro", "clam", "cod_roe", "condensed_milk", "cooking_oil", "cooking_syrup", "crab", "cream_cheese", "cucumber", "cumin", "cup_ramen", "curry_powder", "dried_anchovy", "dried_pollack_strips", "dried_shrimp", "duck", "dumpling", "egg", "eggplant", "enoki_mushroom", "fermented_soybean_paste", "fish", "fish_sauce", "flavored_soy_sauce", "flounder", "flying_fish_roe", "for_bulgogi", "fresh_cream", "fusilli", "garlic", "ginger", "ginseng", "grape", "green_onion", "ham", "hoisin_sauce", "honey", "instant_rice", "instant_soup", "jujube", "kelp", "kimbap", "kimchi", "king_oyster_mushroom", "kiwi", "lamb", "lasagna_sheet", "laver", "lemon", "lettuce", "lobster", "macaroni", "mala_sauce", "mango", "maple_syrup", "margarine", "matsutake_mushroom", "mayonnaise", "meatball", "milk", "minced_garlic", "minced_ginger", "mixed_grain_rice", "mung_bean_sprouts", "mussel", "mustard", "napa_cabbage", "nuts", "octopus", "olive_oil", "orange", "oregano", "oyster_sauce", "paprika", "peach", "pear", "penne", "pepper", "perilla_oil", "pineapple", "plain_bread", "plum", "pollock_roe", "pork_back_ribs", "pork_belly", "pork_front_leg", "pork_hind_leg", "pork_neck", "potato", "radish", "red_chili_paste", "red_onion", "red_pepper_powder", "ribs", "rosemary", "saffron", "salad", "salmon", "salmon_roe", "salt", "sausage", "scallop", "sea_squirt", "sea_urchin_roe", "seasoned_dried_squid", "seaweed", "sesame_oil", "shank", "shiitake_mushroom", "shrimp", "sirloin", "sliced_rice_cake", "soy_sauce", "soybean_paste", "spaghetti", "spam", "spinach", "sprite", "squid", "strawberry", "sugar", "sweet_potato", "teriyaki_sauce", "thyme", "tomato", "tomato_sauce", "tuna", "vinegar", "water_parsley", "watermelon", "whipping_cream", "white_rice", "whole_grain_mustard", "yogurt", "zucchini"
]

CLASS_LABELS = [
    "Baguette", "Coffee","onion","soy_sauce", "pepper", "chili_pepper", "Juice", "Perilla_leaves", "Sliced_cheese", "Soju", "Tea", "Water", "Wine", "abalone", "apple", "avocado", "bacon", "bean_sprout", "beef", "blueberry", "brisket", "broccoli",  "butter", "button_mushroom", "cabbage", "napa_cabbage", "carrot", "cauliflower", "celery", "cherry", "chicken_breast", "chicken_wing", "chive", "cilantro", "clam",  "cooking_oil", "cooking_syrup", "crab", "cucumber", "duck", "egg", "eggplant", "fish",  "flounder", "fresh_cream", "fusilli", "garlic", "ginger", "grape", "green_onion", "ham", "hoisin_sauce", "honey", "kelp", "kimbap", "kimchi", "kiwi",  "lasagna_sheet", "laver", "lemon", "lettuce", "lobster", "macaroni", "mango",  "margarine", "mayonnaise", "meatball", "milk", "minced_garlic", "mussel",  "nuts", "octopus", "olive_oil", "orange", "peach", "pear", "banana","penne", "pineapple", "plain_bread","plum", "pork_back_ribs", "pork_belly", "pork_neck", "potato", "radish", "red_onion", "ribs", "salad", "salmon", "salt", "sausage",  "seaweed", "sesame_oil", "shank",  "shrimp", "sirloin", "sliced_rice_cake",  "soybean_paste", "spaghetti", "spam", "spinach", "sprite", "squid", "strawberry", "sugar", "sweet_potato",  "tomato", "tuna", "vinegar", "watermelon", "whipping_cream", "white_rice", "yogurt", "zucchini","paprika"
]

# CLASS_LABELS 기반 화이트리스트 매핑 (한글, 영어, 다양한 영어 표현)
WHITELIST_MAP = {
    'Baguette': 'Baguette', '바게트': 'Baguette', 'baguette': 'Baguette',
    'Coffee': 'Coffee', '커피': 'Coffee', 'coffee': 'Coffee',
    'chili_pepper': 'chili_pepper', 'Chili pepper': 'chili_pepper', '고추': 'chili_pepper',
    'Juice': 'Juice', '주스': 'Juice', 'juice': 'Juice',
    'Perilla_leaves': 'Perilla_leaves', 'Perilla leaves': 'Perilla_leaves', '깻잎': 'Perilla_leaves',
    'Sliced_cheese': 'Sliced_cheese', '슬라이스 치즈': 'Sliced_cheese', 'sliced_cheese': 'Sliced_cheese',
    'Soju': 'Soju', '소주': 'Soju', 'soju': 'Soju',
    'Tea': 'Tea', '차': 'Tea', 'tea': 'Tea',
    'Water': 'Water', '물': 'Water', 'water': 'Water',
    'Wine': 'Wine', '와인': 'Wine', 'wine': 'Wine',
    'abalone': 'abalone', '전복': 'abalone', 'Abalone': 'abalone',
    'apple': 'apple', '사과': 'apple', 'Apple': 'apple',
    'avocado': 'avocado', '아보카도': 'avocado', 'Avocado': 'avocado',
    'bacon': 'bacon', '베이컨': 'bacon', 'Bacon': 'bacon',
    'bean_sprout': 'bean_sprout', '콩나물': 'bean_sprout', 'Bean sprout': 'bean_sprout',
    'beef': 'beef', '소고기': 'beef', 'Beef': 'beef',
    'blueberry': 'blueberry', '블루베리': 'blueberry', 'Blueberry': 'blueberry',
    'brisket': 'brisket', '차돌박이': 'brisket', 'Brisket': 'brisket',
    'broccoli': 'broccoli', '브로콜리': 'broccoli', 'Broccoli': 'broccoli',
    'butter': 'butter', '버터': 'butter', 'Butter': 'butter',
    'button_mushroom': 'button_mushroom', '양송이 버섯': 'button_mushroom', 'Button mushroom': 'button_mushroom',
    'cabbage': 'cabbage', '양배추': 'cabbage', 'Cabbage': 'cabbage',
    'napa_cabbage': 'napa_cabbage', '배추': 'napa_cabbage', 'Napa cabbage': 'napa_cabbage',
    'carrot': 'carrot', '당근': 'carrot', 'Carrot': 'carrot',
    'cauliflower': 'cauliflower', '콜리플라워': 'cauliflower', 'Cauliflower': 'cauliflower',
    'celery': 'celery', '샐러리': 'celery', 'Celery': 'celery',
    'cherry': 'cherry', '체리': 'cherry', 'Cherry': 'cherry',
    'chicken_breast': 'chicken_breast', '닭 가슴살': 'chicken_breast', 'Chicken breast': 'chicken_breast',
    'chicken_wing': 'chicken_wing', '닭날개': 'chicken_wing', 'Chicken wing': 'chicken_wing',
    'chive': 'chive', '부추': 'chive', 'Chive': 'chive',
    'cilantro': 'cilantro', '고수': 'cilantro', 'Cilantro': 'cilantro',
    'clam': 'clam', '바지락': 'clam', 'Clam': 'clam',
    'cooking_oil': 'cooking_oil', '식용유': 'cooking_oil', 'Cooking oil': 'cooking_oil',
    'cooking_syrup': 'cooking_syrup', '요리당': 'cooking_syrup', 'Cooking syrup': 'cooking_syrup',
    'crab': 'crab', '게': 'crab', 'Crab': 'crab',
    'cucumber': 'cucumber', '오이': 'cucumber', 'Cucumber': 'cucumber',
    'duck': 'duck', '오리': 'duck', 'Duck': 'duck',
    'egg': 'egg', '계란': 'egg', 'Egg': 'egg',
    'eggplant': 'eggplant', '가지': 'eggplant', 'Eggplant': 'eggplant',
    'enoki_mushroom': 'enoki_mushroom', '인천오이버섯': 'enoki_mushroom', 'Enoki mushroom': 'enoki_mushroom',
    'fermented_soybean_paste': 'fermented_soybean_paste', '발효된 된장': 'fermented_soybean_paste', 'Fermented soybean paste': 'fermented_soybean_paste',
    'fish': 'fish', '생선': 'fish', 'Fish': 'fish',
    'fish_sauce': 'fish_sauce', '생선 소스': 'fish_sauce', 'Fish sauce': 'fish_sauce',
    'flavored_soy_sauce': 'flavored_soy_sauce', '맛있는 된장': 'flavored_soy_sauce', 'Flavored soy sauce': 'flavored_soy_sauce',
    'flounder': 'flounder', '빙어': 'flounder', 'Flounder': 'flounder',
    'flying_fish_roe': 'flying_fish_roe', '빙어 알': 'flying_fish_roe', 'Flying fish roe': 'flying_fish_roe',
    'for_bulgogi': 'for_bulgogi', '불고기': 'for_bulgogi', 'For bulgogi': 'for_bulgogi',
    'fresh_cream': 'fresh_cream', '신선한 크림': 'fresh_cream', 'Fresh cream': 'fresh_cream',
    'fusilli': 'fusilli', '파스타': 'fusilli', 'Fusilli': 'fusilli',
    'garlic': 'garlic', '마늘': 'garlic', 'Garlic': 'garlic',
    'ginger': 'ginger', '미나리': 'ginger', 'Ginger': 'ginger',
    'ginseng': 'ginseng', '산삼': 'ginseng', 'Ginseng': 'ginseng',
    'grape': 'grape', '포도': 'grape', 'Grape': 'grape',
    'green_onion': 'green_onion', '대파': 'green_onion', 'Green onion': 'green_onion',
    'ham': 'ham', '햄': 'ham', 'Ham': 'ham',
    'hoisin_sauce': 'hoisin_sauce', '해선장 소스': 'hoisin_sauce', 'Hoisin sauce': 'hoisin_sauce',
    'honey': 'honey', '꿀': 'honey', 'Honey': 'honey',
    'instant_rice': 'instant_rice', '즉석 밥': 'instant_rice', 'Instant rice': 'instant_rice',
    'instant_soup': 'instant_soup', '즉석 국': 'instant_soup', 'Instant soup': 'instant_soup',
    'jujube': 'jujube', '주자': 'jujube', 'Jujube': 'jujube',
    'kelp': 'kelp', '청어': 'kelp', 'Kelp': 'kelp',
    'kimbap': 'kimbap', '김밥': 'kimbap', 'Kimbap': 'kimbap',
    'kimchi': 'kimchi', '김치': 'kimchi', 'Kimchi': 'kimchi',
    'king_oyster_mushroom': 'king_oyster_mushroom', '왕오이버섯': 'king_oyster_mushroom', 'King oyster mushroom': 'king_oyster_mushroom',
    'kiwi': 'kiwi', '키위': 'kiwi', 'Kiwi': 'kiwi',
    'lamb': 'lamb', '양고기': 'lamb', 'Lamb': 'lamb',
    'lasagna_sheet': 'lasagna_sheet', '라자냐 시트': 'lasagna_sheet', 'Lasagna sheet': 'lasagna_sheet',
    'laver': 'laver', '라베': 'laver', 'Laver': 'laver',
    'lemon': 'lemon', '레몬': 'lemon', 'Lemon': 'lemon',
    'lettuce': 'lettuce', '샐러드 채소': 'lettuce', 'Lettuce': 'lettuce',
    'lobster': 'lobster', '게': 'lobster', 'Lobster': 'lobster',
    'macaroni': 'macaroni', '마카로니': 'macaroni', 'Macaroni': 'macaroni',
    'mala_sauce': 'mala_sauce', '말라 소스': 'mala_sauce', 'Mala sauce': 'mala_sauce',
    'mango': 'mango', '망고': 'mango', 'Mango': 'mango',
    'maple_syrup': 'maple_syrup', '메이플 시럽': 'maple_syrup', 'Maple syrup': 'maple_syrup',
    'margarine': 'margarine', '마가린': 'margarine', 'Margarine': 'margarine',
    'matsutake_mushroom': 'matsutake_mushroom', '마늘 버섯': 'matsutake_mushroom', 'Matsutake mushroom': 'matsutake_mushroom',
    'mayonnaise': 'mayonnaise', '마요네즈': 'mayonnaise', 'Mayonnaise': 'mayonnaise',
    'meatball': 'meatball', '고기 덩어리': 'meatball', 'Meatball': 'meatball',
    'milk': 'milk', '우유': 'milk', 'Milk': 'milk',
    'minced_garlic': 'minced_garlic', '마늘 송송': 'minced_garlic', 'Minced garlic': 'minced_garlic',
    'minced_ginger': 'minced_ginger', '마늘 송송': 'minced_ginger', 'Minced ginger': 'minced_ginger',
    'mixed_grain_rice': 'mixed_grain_rice', '혼합 곡물 쌀': 'mixed_grain_rice', 'Mixed grain rice': 'mixed_grain_rice',
    'mung_bean_sprouts': 'mung_bean_sprouts', '멩기 버섯': 'mung_bean_sprouts', 'Mung bean sprouts': 'mung_bean_sprouts',
    'mussel': 'mussel', '굴': 'mussel', 'Mussel': 'mussel',
    'mustard': 'mustard', '머스터드': 'mustard', 'Mustard': 'mustard',
    'napa_cabbage': 'napa_cabbage', '배추': 'napa_cabbage', 'Napa cabbage': 'napa_cabbage',
    'nuts': 'nuts', '견과류': 'nuts', 'Nuts': 'nuts',
    'octopus': 'octopus', '문어': 'octopus', 'Octopus': 'octopus',
    'olive_oil': 'olive_oil', '올리브 오일': 'olive_oil', 'Olive oil': 'olive_oil',
    'orange': 'orange', '오렌지': 'orange', 'Orange': 'orange',
    'oregano': 'oregano', '오레가노': 'oregano', 'Oregano': 'oregano',
    'oyster_sauce': 'oyster_sauce', '오징어 소스': 'oyster_sauce', 'Oyster sauce': 'oyster_sauce',
    'paprika': 'paprika', '파프리카': 'paprika', 'Paprika': 'paprika',
    'peach': 'peach', '복숭아': 'peach', 'Peach': 'peach',
    'pear': 'pear', '배': 'pear', 'Pear': 'pear',
    'penne': 'penne', '페네': 'penne', 'Penne': 'penne',
    'pepper': 'pepper', '후추': 'pepper', 'Pepper': 'pepper',
    'perilla_oil': 'perilla_oil', '들기름': 'perilla_oil', 'Perilla oil': 'perilla_oil',
    'pineapple': 'pineapple', '파인애플': 'pineapple', 'Pineapple': 'pineapple',
    'plain_bread': 'plain_bread', '빵': 'plain_bread', 'Plain bread': 'plain_bread',
    'plum': 'plum', '자두': 'plum', 'Plum': 'plum',
    'pollock_roe': 'pollock_roe', '명란': 'pollock_roe', 'Pollock roe': 'pollock_roe',
    'pork_back_ribs': 'pork_back_ribs', '갈비': 'pork_back_ribs', 'Pork back ribs': 'pork_back_ribs',
    'pork_belly': 'pork_belly', '몸통': 'pork_belly', 'Pork belly': 'pork_belly',
    'pork_front_leg': 'pork_front_leg', '앞다리': 'pork_front_leg', 'Pork front leg': 'pork_front_leg',
    'pork_hind_leg': 'pork_hind_leg', '뒷다리': 'pork_hind_leg', 'Pork hind leg': 'pork_hind_leg',
    'pork_neck': 'pork_neck', '목': 'pork_neck', 'Pork neck': 'pork_neck',
    'potato': 'potato', '감자': 'potato', 'Potato': 'potato',
    'radish': 'radish', '무': 'radish', 'Radish': 'radish',
    'red_chili_paste': 'red_chili_paste', '빨간 고추 소스': 'red_chili_paste', 'Red chili paste': 'red_chili_paste',
    'red_onion': 'red_onion', '빨간 양파': 'red_onion', 'Red onion': 'red_onion',
    'red_pepper_powder': 'red_pepper_powder', '빨간 고추 가루': 'red_pepper_powder', 'Red pepper powder': 'red_pepper_powder',
    'ribs': 'ribs', '개미': 'ribs', 'Ribs': 'ribs',
    'rosemary': 'rosemary', '로즈마리': 'rosemary', 'Rosemary': 'rosemary',
    'saffron': 'saffron', '사프란': 'saffron', 'Saffron': 'saffron',
    'salad': 'salad', '샐러드': 'salad', 'Salad': 'salad',
    'salmon': 'salmon', '연어': 'salmon', 'Salmon': 'salmon',
    'salmon_roe': 'salmon_roe', '연어 알': 'salmon_roe', 'Salmon roe': 'salmon_roe',
    'salt': 'salt', '소금': 'salt', 'Salt': 'salt',
    'sausage': 'sausage', '소시지': 'sausage', 'Sausage': 'sausage',
    'scallop': 'scallop', '조개': 'scallop', 'Scallop': 'scallop',
    'sea_squirt': 'sea_squirt', '해조류': 'sea_squirt', 'Sea squirt': 'sea_squirt',
    'sea_urchin_roe': 'sea_urchin_roe', '해조류 알': 'sea_urchin_roe', 'Sea urchin roe': 'sea_urchin_roe',
    'seasoned_dried_squid': 'seasoned_dried_squid', '조미된 말린 오징어': 'seasoned_dried_squid', 'Seasoned dried squid': 'seasoned_dried_squid',
    'seaweed': 'seaweed', '해조류': 'seaweed', 'Seaweed': 'seaweed',
    'sesame_oil': 'sesame_oil', '참깨 오일': 'sesame_oil', 'Sesame oil': 'sesame_oil',
    'shank': 'shank', '쇠고기': 'shank', 'Shank': 'shank',
    'shiitake_mushroom': 'shiitake_mushroom', '시청어 버섯': 'shiitake_mushroom', 'Shiitake mushroom': 'shiitake_mushroom',
    'shrimp': 'shrimp', '새우': 'shrimp', 'Shrimp': 'shrimp',
    'sirloin': 'sirloin', '등심': 'sirloin', 'Sirloin': 'sirloin',
    'sliced_rice_cake': 'sliced_rice_cake', '소금 떡': 'sliced_rice_cake', 'Sliced rice cake': 'sliced_rice_cake',
    'soy_sauce': 'soy_sauce', '간장': 'soy_sauce', 'Soy sauce': 'soy_sauce',
    'soybean_paste': 'soybean_paste', '된장': 'soybean_paste', 'Soybean paste': 'soybean_paste',
    'spaghetti': 'spaghetti', '스파게티': 'spaghetti', 'Spaghetti': 'spaghetti',
    'spam': 'spam', '스팸': 'spam', 'Spam': 'spam',
    'spinach': 'spinach', '시금치': 'spinach', 'Spinach': 'spinach',
    'sprite': 'sprite', '스프라이트': 'sprite', 'Sprite': 'sprite',
    'squid': 'squid', '오징어': 'squid', 'Squid': 'squid',
    'strawberry': 'strawberry', '딸기': 'strawberry', 'Strawberry': 'strawberry',
    'sugar': 'sugar', '설탕': 'sugar', 'Sugar': 'sugar',
    'sweet_potato': 'sweet_potato', '고구마': 'sweet_potato', 'Sweet potato': 'sweet_potato',
    'teriyaki_sauce': 'teriyaki_sauce', '토마토 소스': 'teriyaki_sauce', 'Teriyaki sauce': 'teriyaki_sauce',
    'thyme': 'thyme', '타임': 'thyme', 'Thyme': 'thyme',
    'tomato': 'tomato', '토마토': 'tomato', 'Tomato': 'tomato',
    'tomato_sauce': 'tomato_sauce', '토마토 소스': 'tomato_sauce', 'Tomato sauce': 'tomato_sauce',
    'tuna': 'tuna', '참치': 'tuna', 'Tuna': 'tuna',
    'vinegar': 'vinegar', '식초': 'vinegar', 'Vinegar': 'vinegar',
    'water_parsley': 'water_parsley', '물푸레': 'water_parsley', 'Water parsley': 'water_parsley',
    'watermelon': 'watermelon', '수박': 'watermelon', 'Watermelon': 'watermelon',
    'whipping_cream': 'whipping_cream', '휘핑 크림': 'whipping_cream', 'Whipping cream': 'whipping_cream',
    'white_rice': 'white_rice', '흰 쌀': 'white_rice', 'White rice': 'white_rice',
    'whole_grain_mustard': 'whole_grain_mustard', '현미 머스터드': 'whole_grain_mustard', 'Whole grain mustard': 'whole_grain_mustard',
    'yogurt': 'yogurt', '요거트': 'yogurt', 'Yogurt': 'yogurt',
    'zucchini': 'zucchini', '호박': 'zucchini', 'Zucchini': 'zucchini'
}

# 예외처리 labels
BLOCKLIST = {"bowl", "spoon", "fork", "knife", "dining table", "plate","Baguette","pork_neck","sausage","hoisin_sauce","chicken_wing","scallop","mayonnaise","whipping_cream","coffee","banana","zucchini"}



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


# hyperparams
CONF_THRESHOLD = 0.05        # 전체 detection confidence 임계값 (더 낮춤)
CLS_CONF_THRESHOLD = 0.15    # classification confidence 임계값 (더 관대하게)
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