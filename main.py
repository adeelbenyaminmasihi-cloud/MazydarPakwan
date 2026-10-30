import io
import json
import math
import os
import random
import subprocess
import sys
import urllib.parse
from PIL import Image, ImageEnhance, ImageFilter
import requests

# =====================================================================
# 1. VOICE & TIMING CONFIGURATION
# =====================================================================
VOICE_NAME = "ur-PK-UzmaNeural"
CLIP_DURATION = 3.0  # Fast pace: New scene every 3 seconds!
MIN_TARGET_DURATION = 75.0  # Minimum 1 minute 15 seconds video length

# =====================================================================
# 2. SECURE ENVIRONMENT VARIABLES (From GitHub Secrets Only)
# =====================================================================
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if not PIXABAY_API_KEY:
    print("Error: PIXABAY_API_KEY GitHub Secrets mein mojood nahi hai!")
    sys.exit(1)

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print(
        "Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID GitHub Secrets mein mojood nahi!"
    )
    sys.exit(1)

HISTORY_FILE = "used_dishes.txt"

# 60+ Seed Historical Food Topics + Infinite AI Topic Generator
HISTORICAL_FOOD_TOPICS = [
    (
        "Royal Mughlai Biryani",
        "شاہی مغلائی بریانی",
        [
            "biryani",
            "indian rice",
            "spices",
            "saffron",
            "cooking pot",
            "meat curry",
            "basmati rice",
            "traditional food",
        ],
    ),
    (
        "Old Delhi Shahi Nihari",
        "پرانی دہلی کی شاہی نہاری",
        [
            "beef stew",
            "curry",
            "indian spices",
            "slow cooking",
            "naan bread",
            "gravy",
            "meat dish",
            "traditional cooking",
        ],
    ),
    (
        "Peshawari Namkeen Karahi",
        "پشاوری چرسی نمکین کڑاہی",
        [
            "wok cooking",
            "tomatoes",
            "meat frying",
            "green chili",
            "street food",
            "fire cooking",
            "curry",
            "roti",
        ],
    ),
    (
        "Shahi Haleem / Daleem",
        "شاہی حلیم اور عرب کی ہریسہ",
        [
            "lentils",
            "wheat grains",
            "slow cooked stew",
            "spices",
            "fried onions",
            "ginger",
            "traditional soup",
            "wooden spoon",
        ],
    ),
    (
        "Samosa: From Middle East to South Asia",
        "سموسے کی ہزار سالہ تاریخ",
        [
            "samosa",
            "fried pastry",
            "street food",
            "frying oil",
            "chutney",
            "dough",
            "potatoes",
            "tea time",
        ],
    ),
    (
        "Seekh Kabab of Royal Kitchens",
        "شاہی باورچی خانوں کے سیخ کباب",
        [
            "kebab",
            "barbecue",
            "charcoal grill",
            "skewers",
            "smoke",
            "roasted meat",
            "spices",
            "mint sauce",
        ],
    ),
    (
        "Gulab Jamun from Persia to Subcontinent",
        "گلاب جامن کی ایران سے برصغیر تک تاریخ",
        [
            "indian sweets",
            "syrup",
            "dessert",
            "saffron",
            "cardamom",
            "milk dessert",
            "sweet dish",
            "festive food",
        ],
    ),
    (
        "Kashmiri Pink Chai (Noon Chai)",
        "کشمیری گلابی چائے کی قدیم داستان",
        [
            "tea cup",
            "boiling tea",
            "pistachio",
            "almonds",
            "tea leaves",
            "kettle",
            "winter drink",
            "spices",
        ],
    ),
    (
        "Peshawari Chapli Kabab",
        "پشاوری چپلی کباب کی تاریخی داستان",
        [
            "meat patty",
            "frying pan",
            "pomegranate seeds",
            "tomatoes",
            "barbecue",
            "street food",
            "spices",
            "flatbread",
        ],
    ),
    (
        "Jalebi: Ancient Sweet of Sultans",
        "جلیبی کی سلطانوں کے دور سے جڑی تاریخ",
        [
            "sweet pretzel",
            "frying syrup",
            "saffron sweet",
            "street dessert",
            "sugar syrup",
            "crispy sweet",
            "indian dessert",
            "festival food",
        ],
    ),
    (
        "Lahori Chargha & Tandoori Roast",
        "لاہوری چرغے اور تندوری روسٹ کی تاریخ",
        [
            "roasted chicken",
            "whole chicken",
            "spices",
            "grill",
            "lemon",
            "frying",
            "masala",
            "street food",
        ],
    ),
    (
        "Kabuli Pulao of Silk Road",
        "شاہراہِ ریشم اور قابلی پلاؤ کی تاریخ",
        [
            "pilaf",
            "rice dish",
            "carrots",
            "raisins",
            "lamb meat",
            "almonds",
            "traditional feast",
            "steam rice",
        ],
    ),
    (
        "Naan & Tandoor History",
        "تندور اور گرما گرم نان کی پانچ ہزار سالہ تاریخ",
        [
            "naan bread",
            "clay oven",
            "baking bread",
            "dough",
            "fire oven",
            "garlic bread",
            "flour",
            "traditional bakery",
        ],
    ),
    (
        "Halwa Puri Breakfast Tradition",
        "لاہوری حلوہ پوری کے ناشتے کی تاریخ",
        [
            "fried bread",
            "chickpea curry",
            "sweet halwa",
            "breakfast",
            "street food",
            "frying oil",
            "spices",
            "pickles",
        ],
    ),
    (
        "Nargisi Kofta of Mughal Courts",
        "مغل دربار کے شاہی نرگسی کوفتے",
        [
            "meatballs",
            "boiled eggs",
            "curry gravy",
            "spices",
            "coriander",
            "cooking pot",
            "traditional dish",
            "dinner",
        ],
    ),
    (
        "Shahi Tukray of Nawab Kitchens",
        "نوابوں کے دسترخوان کے شاہی ٹکڑے",
        [
            "bread pudding",
            "milk cream",
            "saffron",
            "pistachio",
            "almonds",
            "sweet syrup",
            "royal dessert",
            "cardamom",
        ],
    ),
    (
        "Mutton Kunna of Chiniot",
        "چنیوٹ کے مٹی کے برتن والے مٹن کنا کی تاریخ",
        [
            "clay pot cooking",
            "mutton curry",
            "slow cooked meat",
            "spices",
            "gravy",
            "traditional stove",
            "ginger",
            "naan",
        ],
    ),
    (
        "Falooda: Royal Persian Cold Dessert",
        "فارسی بادشاہوں کے فالودے کی تاریخ",
        [
            "ice cream dessert",
            "rose syrup",
            "vermicelli",
            "milkshake",
            "nuts",
            "sweet drink",
            "summer dessert",
            "glass dessert",
        ],
    ),
    (
        "Kulfi: How Mughals Made Ice Cream Without Freezers",
        "بغیر فریج کے مغل بادشاہوں نے قلفی کیسے بنائی",
        [
            "popsicle",
            "ice cream",
            "pistachio",
            "milk boiling",
            "saffron",
            "cardamom",
            "sweet treat",
            "frozen dessert",
        ],
    ),
    (
        "Butter Chicken & Tikka Masala Origin",
        "بٹر چکن کی حادثاتی ایجاد کی دلچسپ کہانی",
        [
            "butter chicken",
            "tomato gravy",
            "cream",
            "grilled chicken",
            "spices",
            "butter",
            "naan",
            "indian restaurant",
        ],
    ),
    (
        "Balochi Sajji of Mountain Tribes",
        "بلوچستان کے پہاڑوں کی روایتی سجی کی تاریخ",
        [
            "campfire cooking",
            "roast meat",
            "firewood",
            "whole chicken roast",
            "charcoal",
            "spices",
            "outdoor cooking",
            "rice",
        ],
    ),
    (
        "Paya Curry of Walled City Lahore",
        "اندرون لاہور کے سری پائے کی تاریخی داستان",
        [
            "soup stew",
            "slow cooking",
            "spices",
            "garlic",
            "boiling pot",
            "traditional breakfast",
            "naan bread",
            "lemon",
        ],
    ),
    (
        "Lassi: Ancient Punjabi Energy Drink",
        "پنجاب کی لسی کی ہزاروں سال پرانی تاریخ",
        [
            "yogurt drink",
            "buttermilk",
            "clay cup",
            "milk churning",
            "mint",
            "summer drink",
            "dairy",
            "traditional drink",
        ],
    ),
    (
        "Gajar Ka Halwa in Mughal Winters",
        "مغل دور میں گاجر کے حلوے کی ایجاد",
        [
            "carrots",
            "grated carrots",
            "milk dessert",
            "almonds",
            "cashews",
            "ghee",
            "sweet dish",
            "winter food",
        ],
    ),
    (
        "Zarda & Matanjan of Royal Weddings",
        "شاہی شادیوں کے دیگی متنجن اور زردے کی تاریخ",
        [
            "sweet rice",
            "saffron rice",
            "dry fruits",
            "almonds",
            "raisins",
            "colorful food",
            "festive dish",
            "cooking pot",
        ],
    ),
    (
        "Daal Makhani & Dhaba Culture",
        "جی ٹی روڈ کے ڈھابوں اور دال مکھنی کی تاریخ",
        [
            "lentil soup",
            "butter",
            "cream",
            "kidney beans",
            "clay pot",
            "spices",
            "garlic",
            "roti",
        ],
    ),
    (
        "Rogan Josh of Royal Kashmir",
        "کشمیر کے شاہی روغن جوش کی تاریخی داستان",
        [
            "red curry",
            "lamb stew",
            "kashmiri chili",
            "spices",
            "steamed rice",
            "cooking pot",
            "aromatic herbs",
            "traditional food",
        ],
    ),
    (
        "Gol Gappay / Pani Puri Ancient History",
        "گول گپے کی مگدھ سلطنت سے جڑی حیرت انگیز تاریخ",
        [
            "street food",
            "crispy snack",
            "chickpeas",
            "tamarind sauce",
            "spices",
            "mint water",
            "indian snack",
            "market food",
        ],
    ),
    (
        "Bihari Kabab & Boti Tradition",
        "بہاری کباب اور بوٹی کی صدیوں پرانی تاریخ",
        [
            "skewered meat",
            "charcoal grill",
            "spicy meat",
            "barbecue smoke",
            "mustard oil",
            "onions",
            "paratha",
            "street food",
        ],
    ),
    (
        "Chai: How Tea Conquered South Asia",
        "چائے برصغیر کے ہر گھر کی ضرورت کیسے بنی",
        [
            "tea plantation",
            "boiling milk tea",
            "cardamom",
            "tea stall",
            "pouring tea",
            "clay cup",
            "spices",
            "morning tea",
        ],
    ),
]


def get_used_dishes():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def save_used_dish(topic_en):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{topic_en}\n")


def pick_unique_topic():
    used = set(get_used_dishes())
    available = [
        item for item in HISTORICAL_FOOD_TOPICS if item[0] not in used
    ]
    if available:
        return random.choice(available)

    # Lifetime Infinite Topic Generator once seed list is completed
    prompt = (
        f"Generate 1 unique historical food topic from South Asian, Persian, Turkish, or Arab history "
        f"not in this list: {', '.join(list(used)[-40:])}. "
        f'Return ONLY JSON: {{"en": "Dish Name", "ur": "اردو نام", "keywords": ["food", "cooking", "spices", "meat", "rice", "grill", "curry", "kitchen"]}}'
    )
    try:
        r = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "openai",
                "jsonMode": True,
            },
            timeout=30,
        )
        if r.status_code == 200:
            data = json.loads(
                r.text.replace("```json", "").replace("```", "").strip()
            )
            return (
                data["en"],
                data["ur"],
                data.get(
                    "keywords",
                    [
                        "cooking",
                        "spices",
                        "curry",
                        "rice",
                        "meat",
                        "grill",
                        "kitchen",
                        "food",
                    ],
                ),
            )
    except Exception:
        pass

    idx = len(used) + 1
    return (
        f"Royal Dastarkhwan Secret Dish #{idx}",
        f"شاہی دسترخوان کے قدیم پکوان کی داستان نمبر {idx}",
        [
            "spices",
            "curry",
            "rice dish",
            "barbecue",
            "cooking pot",
            "meat stew",
            "herbs",
            "traditional kitchen",
        ],
    )


def has_urdu_script(text):
    urdu_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    return urdu_chars > 120


def build_guaranteed_75s_history_script(topic_en, topic_ur):
    """Guaranteed 210+ word rich Urdu historical documentary script (~78-85 seconds narration)."""
    return (
        f"السلام علیکم دوستو! مزے دار پکوان کے تاریخی سلسلے میں میں آپ سب کو خوش آمدید کہتی ہوں۔ "
        f"آج ہم جس لاجواب اور تاریخی پکوان کی صدیوں پرانی داستان کھنگالنے جا رہے ہیں، اس کا نام ہے {topic_ur}۔ "
        f"کیا آپ نے کبھی گرما گرم دسترخوان پر بیٹھ کر یہ سوچا ہے کہ جس ذائقے کو آج ہم اتنے شوق سے کھاتے ہیں، وہ دراصل بادشاہوں، سلطانوں اور قدیم قافلوں کے باورچی خانوں سے سفر کرتا ہوا ہم تک کیسے پہنچا؟ "
        f"تاریخ کی پرانی کتابوں کے مطابق، جب وسطی ایشیا، ایران اور عرب کے تاجر اور فاتحین برصغیر پاک و ہند میں داخل ہوئے، تو وہ اپنے ساتھ نایاب مصالحوں، زعفران، خشک میوہ جات اور گوشت کو دھیمی آنچ پر پکانے کے شاہی طریقے بھی لے کر آئے۔ "
        f"جب یہ غیر ملکی تراکیب مقامی باورچیوں کے ہنر اور برصغیر کے تیکھے دیسی مصالحوں سے ملیں، تو شاہی رکابداروں نے مہینوں کی محنت کے بعد {topic_ur} جیسی شاہکار ڈش ایجاد کی۔ "
        f"ابتدائی دور میں یہ خاص پکوان صرف شاہی قلعوں، نوابوں کی حویلیوں اور خاص درباری دعوتوں کی زینت بنا کرتا تھا، جہاں اسے سونے اور چاندی کے ظروف میں پیش کیا جاتا تھا۔ "
        f"پھر وقت گزرنے کے ساتھ ساتھ جب شاہی باورچیوں نے لاہور، دہلی، پشاور اور لکھنؤ کے قدیم بازاروں کا رخ کیا، تو یہ ذائقہ محلوں کی دیواروں سے نکل کر عام لوگوں کی گلیوں اور ڈھابوں تک پہنچ گیا۔ "
        f"آج بھی جب کڑاہی یا دیگ میں خالص گھی، ادرک لہسن اور گرم مصالحوں کی خوشبو اٹھتی ہے، تو وہ ہمیں اسی سنہری دور کی یاد دلاتی ہے۔ "
        f"آپ کو {topic_ur} کی یہ تاریخی کہانی کیسی لگی، کمنٹ میں ضرور بتائیں اور مزیدار پکوان کو فالو کرنا نہ بھولیں۔"
    )


def generate_history_script(topic_en, topic_ur, base_keywords):
    print(f"Generating 75s+ Food History Script for: {topic_en} ({topic_ur})")
    system_prompt = f"""You are the female documentary narrator for 'Mazydar Pakwan', a food history channel.
Write a deeply engaging, 1 minute 15 second (minimum 200 to 235 words) historical food documentary script about "{topic_en}" ({topic_ur}).

STRICT REQUIREMENTS:
1. LENGTH: Must be between 200 and 235 words in pure Urdu script (اردو رسم الخط) so the audio lasts at least 75 to 85 seconds.
2. TONE & GRAMMAR: Female narrator (use feminine Urdu grammar like میں آپ کو بتاتی ہوں، خوش آمدید کہتی ہوں). Cover the royal/ancient origin, who invented it, how spices & cooking techniques evolved, and how it became famous today.
3. NO Latin English words inside "voiceover_urdu".
4. Return ONLY valid JSON in this exact format:
{{
  "voiceover_urdu": "Full 200-235 word Urdu historical narration...",
  "caption": "📜 History of {topic_en} ({topic_ur})! 🍲✨\\n\\nKya aap jante hain ke {topic_en} ki shuruwat kahan se hui aur yeh shahi dastarkhwan se hamarialiyon tak kaise pohancha? Puri kahani sunein! ❤️👇\\n\\n#MazydarPakwan #FoodHistory #PakistaniFood #DesiFood #HistoryInUrdu #FoodDocumentary",
  "search_queries": [
    "indian spices", "cooking fire", "meat curry", "rice cooking", "traditional kitchen",
    "roasted meat", "boiling stew", "saffron", "garlic ginger", "street food", "clay pot", "flatbread"
  ]
}}"""

    script_data = None

    # 1. Try Google Gemini API if valid AIza key is provided
    if GOOGLE_API_KEY and GOOGLE_API_KEY.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
            res = requests.post(
                url,
                json={"contents": [{"parts": [{"text": system_prompt}]}]},
                timeout=35,
            )
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                text = text.replace("```json", "").replace("```", "").strip()
                script_data = json.loads(text)
        except Exception as e:
            print(f"Google API skipped ({e}), using Pollinations Text AI...")

    # 2. Try Pollinations Text API
    if not script_data:
        try:
            res = requests.post(
                "https://text.pollinations.ai/",
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "Output only valid JSON in pure Urdu script.",
                        },
                        {"role": "user", "content": system_prompt},
                    ],
                    "model": "openai",
                    "jsonMode": True,
                },
                timeout=45,
            )
            if res.status_code == 200:
                text = res.text.replace("```json", "").replace("```", "").strip()
                start, end = text.find("{"), text.rfind("}") + 1
                if start != -1 and end > start:
                    script_data = json.loads(text[start:end])
        except Exception as e:
            print(f"Pollinations LLM notice: {e}")

    default_text = build_guaranteed_75s_history_script(topic_en, topic_ur)

    if not script_data or not has_urdu_script(
        script_data.get("voiceover_urdu", "")
    ):
        voiceover = default_text
        caption = (
            f"📜 History of {topic_en} ({topic_ur})! 🍲✨\n\n"
            f"Janiye {topic_en} ki sadiyon purani tareekh aur shahi dastarkhwan ke raaz! "
            f"Video kaisi lagi comment mein zaroor batayein ❤️👇\n\n"
            f"#MazydarPakwan #FoodHistory #PakistaniFood #DesiFood #FoodDocumentary"
        )
        queries = base_keywords
    else:
        voiceover = script_data["voiceover_urdu"].strip()
        # Enforce 75-second minimum length (at least ~185 Urdu words)
        if len(voiceover.split()) < 180:
            voiceover = (
                voiceover
                + " "
                + (
                    f"تاریخ دانوں کے مطابق {topic_ur} کی مقبولیت کا سب سے بڑا راز اس کے خالص دیسی مصالحے اور پکانے کا وہ قدیم طریقہ ہے جو نسل در نسل سینے بہ سینے منتقل ہوتا رہا۔ "
                    f"شاہی باورچی خانوں میں اس ڈش کو تیار کرنے کے لیے خاص طور پر تجربہ کار رکابدار رکھے جاتے تھے جو مصالحوں کی خوشبو اور آنچ کے توازن کا خاص خیال رکھتے تھے۔ "
                    f"یہی وجہ ہے کہ صدیوں گزرنے کے باوجود آج بھی ہر خاص و عام کی دعوت اس شاندار پکوان کے بغیر ادھوری سمجھی جاتی ہے۔ "
                    f"اگر آپ کو کھانوں کی تاریخ کا یہ سفر پسند آیا ہو تو ویڈیو کو لائک کریں اور کمنٹ میں اپنی پسندیدہ ڈش کا نام ضرور لکھیں۔"
                )
            )
        caption = script_data.get("caption") or f"📜 {topic_en} ({topic_ur}) #MazydarPakwan"
        queries = script_data.get("search_queries", []) + base_keywords

    return {
        "voiceover_urdu": voiceover,
        "caption": caption,
        "queries": queries,
    }


def generate_voiceover(text, audio_path):
    # Slightly measured documentary pace (-4%) for clear historical storytelling and 75s+ duration
    cmd = [
        "edge-tts",
        "--voice",
        VOICE_NAME,
        "--rate=-4%",
        "--pitch=+1Hz",
        "--text",
        text,
        "--write-media",
        audio_path,
    ]
    subprocess.run(cmd, check=True)


def get_audio_duration(audio_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def ensure_minimum_audio_duration(topic_en, topic_ur, voice_path):
    duration = get_audio_duration(voice_path)
    print(f"Initial voiceover duration: {duration:.1f} seconds")
    if duration < MIN_TARGET_DURATION:
        print(
            "Expanding script narration to guarantee 1 min 15 sec+ duration..."
        )
        extra_narration = (
            f" مزید دلچسپ بات یہ ہے کہ برصغیر کے مختلف شہروں، جیسے لاہور، کراچی، پشاور، ملتان اور حیدرآباد میں {topic_ur} کو مقامی ذائقوں کے مطابق الگ الگ انداز میں بنایا جاتا ہے۔ "
            f"کہیں اس میں تیز مصالحوں اور ہری مرچوں کا تڑکہ لگایا جاتا ہے تو کہیں دیسی گھی، زعفران اور خشک میوہ جات کے ساتھ اس کی لذت کو دوبالا کیا جاتا ہے۔ "
            f"ہماری ثقافت اور مہمان نوازی کی یہ خوبصورت روایت آج پوری دنیا میں پاکستان اور برصغیر کے کھانوں کی پہچان بن چکی ہے۔"
        )
        full_text = (
            build_guaranteed_75s_history_script(topic_en, topic_ur)
            + extra_narration
        )
        generate_voiceover(full_text, voice_path)
        duration = get_audio_duration(voice_path)
        print(f"Expanded voiceover duration: {duration:.1f} seconds")
    return duration


def fetch_pixabay_media_pool(queries, needed_count):
    """Fetches high-definition Pixabay food videos (primary) and high-res photos (secondary)

    so we have enough unique fast-paced clips for the entire 75+ second video.
    """
    fallback_food_Pool = [
        "indian food",
        "curry cooking",
        "spices",
        "biryani",
        "kebab grill",
        "frying pan",
        "cooking fire",
        "chef cooking",
        "street food",
        "traditional food",
        "rice dish",
        "meat stew",
        "garlic spices",
        "fresh herbs",
        "flatbread baking",
        "boiling pot",
        "saffron",
        "oriental spices",
        "barbecue smoke",
        "sweet dessert",
    ]
    all_queries = []
    for q in queries + fallback_food_Pool:
        if q not in all_queries:
            all_queries.append(q)

    video_urls = []
    photo_urls = []
    seen_ids = set()

    print(
        f"Searching Pixabay HD Library for {needed_count} fast-paced clips..."
    )

    # 1. Fetch Pixabay HD Stock Videos
    for q in all_queries:
        if len(video_urls) >= needed_count:
            break
        params = {
            "key": PIXABAY_API_KEY,
            "q": q,
            "safesearch": "true",
            "per_page": 10,
        }
        try:
            r = requests.get(
                "https://pixabay.com/api/videos/", params=params, timeout=20
            )
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for h in hits:
                    vid_id = f"vid_{h.get('id')}"
                    if vid_id in seen_ids:
                        continue
                    vids = h.get("videos", {})
                    url = (
                        vids.get("large", {}).get("url")
                        or vids.get("medium", {}).get("url")
                        or vids.get("small", {}).get("url")
                    )
                    if url:
                        seen_ids.add(vid_id)
                        video_urls.append(("video", url))
                        if len(video_urls) >= needed_count:
                            break
        except Exception as e:
            print(f"Pixabay video search notice for '{q}': {e}")

    # 2. Fetch Pixabay High-Res Photos to interleave or top up if needed
    for q in all_queries:
        if len(video_urls) + len(photo_urls) >= needed_count + 6:
            break
        params = {
            "key": PIXABAY_API_KEY,
            "q": q,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 10,
        }
        try:
            r = requests.get(
                "https://pixabay.com/api/", params=params, timeout=20
            )
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for h in hits:
                    img_id = f"img_{h.get('id')}"
                    if img_id in seen_ids:
                        continue
                    url = h.get("largeImageURL") or h.get("webformatURL")
                    if url:
                        seen_ids.add(img_id)
                        photo_urls.append(("photo", url))
        except Exception as e:
            print(f"Pixabay photo search notice for '{q}': {e}")

    combined = video_urls + photo_urls
    if not combined:
        raise RuntimeError(
            "Pixabay returned no media! Check if PIXABAY_API_KEY is valid."
        )

    # Ensure we have at least `needed_count` items
    while len(combined) < needed_count:
        combined.extend(combined[: needed_count - len(combined)])

    return combined[:needed_count]


def render_single_fast_clip(
    media_type, url, index, clip_duration, topic_en, output_clip
):
    fps = 30
    safe_title = (
        topic_en[:36].replace("'", "").replace(":", " -").replace('"', "")
    )

    # Sleek top branding bar drawn directly by FFmpeg in crisp 1080p HD
    drawbox_filter = (
        f"drawbox=x=40:y=60:w=1000:h=130:color=black@0.68:t=fill,"
        f"drawbox=x=40:y=60:w=1000:h=130:color=0xFFC837@0.9:t=4,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text='MAZYDAR PAKWAN  |  FOOD HISTORY':fontcolor=0xFFC837:fontsize=29:x=(w-text_w)/2:y=86,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text='{safe_title}':fontcolor=white:fontsize=26:x=(w-text_w)/2:y=136"
    )

    if media_type == "video":
        raw_vid = f"raw_{index}.mp4"
        r = requests.get(url, timeout=45)
        r.raise_for_status()
        with open(raw_vid, "wb") as f:
            f.write(r.content)

        # Center crop to 1080x1920 vertical HD + slight speed boost (1.15x) for energetic visual pace
        vf = (
            f"setpts=0.88*PTS,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"eq=contrast=1.06:saturation=1.15,"
            f"{drawbox_filter},"
            f"fps={fps},format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            raw_vid,
            "-vf",
            vf,
            "-t",
            f"{clip_duration:.2f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            output_clip,
        ]
        subprocess.run(cmd, check=True)
        if os.path.exists(raw_vid):
            os.remove(raw_vid)
    else:
        raw_img = f"raw_{index}.jpg"
        r = requests.get(url, timeout=35)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        target_w, target_h = 1080, 1920
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h
        if img_ratio > target_ratio:
            new_h, new_w = target_h, int(target_h * img_ratio)
        else:
            new_w, new_h = target_w, int(target_w / img_ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left, top = (new_w - target_w) // 2, (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))
        img = img.filter(
            ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3)
        )
        img = ImageEnhance.Color(img).enhance(1.15)
        img.save(raw_img, "JPEG", quality=95)

        frames = int(clip_duration * fps)
        z_expr = (
            "min(zoom+0.0025,1.22)"
            if index % 2 == 0
            else "if(eq(on,1),1.22,max(zoom-0.0025,1.0))"
        )
        vf = (
            f"scale=1300:2312,"
            f"zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
            f"{drawbox_filter},format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            raw_img,
            "-vf",
            vf,
            "-t",
            f"{clip_duration:.2f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            output_clip,
        ]
        subprocess.run(cmd, check=True)
        if os.path.exists(raw_img):
            os.remove(raw_img)


def generate_sfx_and_master_audio(voice_path, final_audio_path, duration):
    """Generates subtle kitchen cooking sizzle + soft documentary ambience underneath the female voiceover."""
    sfx_path = "kitchen_sfx.wav"
    sfx_filter = (
        f"anoisesrc=d={duration}:c=pink:r=44100:a=0.028,"
        f"highpass=f=1100,lowpass=f=6000,"
        f"tremolo=f=6:d=0.4,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(duration-2.0, 1.0)}:d=2.0"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            sfx_filter,
            "-c:a",
            "pcm_s16le",
            sfx_path,
        ],
        check=True,
    )

    mix_filter = (
        "[0:a]volume=1.4,highpass=f=80[voice];"
        "[1:a]volume=0.2
