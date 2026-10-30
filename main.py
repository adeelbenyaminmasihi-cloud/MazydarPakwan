import io
import json
import os
import random
import subprocess
import sys
import time
import urllib.parse
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageStat
import requests

# =====================================================================
# 1. APNA GOOGLE FLOW FEMALE CHARACTER PROMPT YAHAN PASTE KAREIN
# =====================================================================
CHARACTER_PROMPT = (
    "A friendly young Pakistani female food vlogger chef, wearing a modest stylish apron "
    "and neatly draped headscarf, warm welcoming smile, expressive eyes, natural skin texture, "
    "modern Pakistani kitchen background with warm cinematic lighting, photorealistic, 8k"
)

# Pakistani Female Voice Artist
VOICE_NAME = "ur-PK-UzmaNeural"

# =====================================================================
# 2. SECURE ENVIRONMENT VARIABLES (From GitHub Secrets Only)
# =====================================================================
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print(
        "Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID GitHub Secrets mein set nahi hai!"
    )
    sys.exit(1)

HISTORY_FILE = "used_dishes.txt"

# Master Dishes with Authentic Urdu Names for 100% Accurate Voiceover
MASTER_DISHES = [
    ("Karachi Special Degi Chicken Biryani", "کراچی اسپیشل دیگی چکن بریانی"),
    ("Peshawari Charsi Mutton Karahi", "پشاوری چرسی مٹن کڑاہی"),
    ("Lahori Chargha with Masala Fries", "لاہوری چرغہ اور مصالحہ فرائز"),
    ("Special Beef Nalli Nihari", "اسپیشل بیف نلی نہاری"),
    (
        "Hyderabadi Dum Kachay Gosht Ki Biryani",
        "حیدرآبادی دم کچے گوشت کی بریانی",
    ),
    ("Shahi Malai Kofta Curry", "شاہی ملائی کوفتہ سالن"),
    ("Dhaba Style Daal Makhani", "ڈھابہ اسٹائل دال مکھنی"),
    ("Lahori Crispy Fried Fish Masala", "لاہوری کرسپی فرائیڈ فش مصالحہ"),
    ("Mughlai Boneless Chicken Handi", "مغلائی بون لیس چکن ہانڈی"),
    ("Special Reshmi Seekh Kabab Karahi", "اسپیشل ریشمی سیخ کباب کڑاہی"),
    ("Sindhi Special Mutton Biryani", "سندھی اسپیشل مٹن بریانی"),
    ("Butter Chicken Masala with Garlic Naan", "بٹر چکن مصالحہ اور گارلک نان"),
    ("Peshawari Crispy Chapli Kabab", "پشاوری کرسپی چپلی کباب"),
    ("Shahi Reshedar Chicken Haleem", "شاہی ریشے دار چکن حلیم"),
    ("Balochi Sajji with Kabuli Pulao", "بلوچی سجی اور قابلی پلاؤ"),
    ("Tawa Chicken Piece Lahore Style", "لاہوری توا چکن پیس"),
    ("Chinioti Mutton Kunna Gosht", "چنیوٹی مٹن کنا گوشت"),
    ("Creamy White Chicken Karahi", "کریمی وائٹ چکن کڑاہی"),
    ("Spicy Beef Bihari Boti", "چٹپٹی بیف بہاری بوٹی"),
    ("Garama Garam Halwa Puri Chana", "گرما گرم حلوہ پوری اور چنے"),
    ("Street Style Tawa Katakat", "اسٹریٹ اسٹائل توا کٹا کٹ"),
    ("Restaurant Style Chicken Jalfrezi", "ریسٹورنٹ اسٹائل چکن جلفریزی"),
    ("Smoky Koyla Chicken Karahi", "اسموکی کوئلہ چکن کڑاہی"),
    ("Khushbudar Mutton Yakhni Pulao", "خوشبودار مٹن یخنی پلاؤ"),
    ("Sardiyon Ka Special Gajar Ka Halwa", "کھوئے والا اسپیشل گاجر کا حلوہ"),
    ("Shahi Tukray with Zafrani Rabri", "شاہی ٹکڑے اور زعفرانی ربڑی"),
    ("Deg Style Palak Gosht", "دیگی اسٹائل پالک گوشت"),
    ("Dhaba Style Aloo Qeema Masala", "ڈھابہ اسٹائل آلو قیمہ مصالحہ"),
    ("Chicken Shashlik with Fried Rice", "چکن شاشلک اور فرائیڈ رائس"),
    ("Masaledar Bhindi Gosht", "مصالحے دار بھنڈی گوشت"),
    ("Lahori Naan Chanay Special", "لاہوری مرغ چنے اور کلچے"),
    ("Spicy Prawn Masala Karahi", "مسالے دار جھینگا کڑاہی"),
    ("Street Style Tawa Brain Masala", "توا مغز مصالحہ فرائی"),
    ("Khasta Kachori with Aloo Tarkari", "خستہ کچوری اور آلو کی ترکاری"),
    ("Shadiyon Wala Degi Zarda Matanjan", "شادیوں والا دیگی متنجن زردہ"),
    ("Afghani Beef Tikka Pulao", "افغانی بیف تکہ پلاؤ"),
    ("Tandoori Chicken Tikka Karahi", "تندوری چکن تکہ کڑاہی"),
    ("Lahori Special Desi Harissa", "لاہوری اسپیشل دیسی ہریسہ"),
    ("Subah Ka Nashta Mutton Paya", "لاہوری مٹن پائے کا سالن"),
    ("Crispy Juicy Chicken Broast", "کرسپی جوسی چکن بروسٹ"),
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


def save_used_dish(dish_en):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{dish_en}\n")


def pick_unique_dish():
    used = set(get_used_dishes())
    available = [item for item in MASTER_DISHES if item[0] not in used]
    if available:
        return random.choice(available)
    idx = len(used) + 1
    return (
        f"Chef Special Royal Handi #{idx}",
        f"شیف اسپیشل شاہی ہانڈی نمبر {idx}",
    )


def has_urdu_script(text):
    urdu_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    return urdu_chars > 40


def build_default_scenes(dish_en):
    return [
        f"{CHARACTER_PROMPT}, holding a tray of fresh colorful spices and ingredients for {dish_en}, smiling warmly at camera, vertical 9:16",
        f"Close-up cinematic food shot of fresh ingredients, chopped onions, tomatoes, green chillies, garlic paste, and whole desi spices for {dish_en} on a wooden counter, vertical 9:16, 8k",
        f"{CHARACTER_PROMPT}, stirring sizzling masala and meat in a traditional wok karahi over stove flame, aromatic steam rising, vertical 9:16",
        f"Extreme macro close-up of {dish_en} cooking on high flame, rich thick gravy bubbling with red chili oil and aromatic herbs, mouth-watering food photography, vertical 9:16",
        f"{CHARACTER_PROMPT}, garnishing freshly cooked {dish_en} with chopped green coriander, ginger juliennes, and green chillies, joyful expression, vertical 9:16",
        f"{CHARACTER_PROMPT}, proudly holding and presenting a steaming hot traditional platter of {dish_en} towards the camera, restaurant quality food presentation, vertical 9:16",
    ]


def generate_vlog_script(dish_en, dish_ur):
    print(f"Generating Urdu female vlog script for: {dish_en} ({dish_ur})")
    system_prompt = f"""You are the scriptwriter for 'Mazydar Pakwan', a Pakistani female AI food vlogger channel.
Write an authentic, mouth-watering 35-40 second food vlog script for "{dish_en}" ({dish_ur}).

STRICT RULES:
1. The speaker is a Pakistani FEMALE chef. Use 100% grammatically correct feminine Urdu (اردو رسم الخط) such as: "آج میں بنا رہی ہوں", "میں نے اس میں شامل کیا ہے", "دیکھیں کتنی پیاری خوشبو آ رہی ہے".
2. DO NOT put English words in Latin alphabet inside "voiceover_urdu" so the Urdu voice artist pronounces every word naturally.
3. Return ONLY valid JSON in this exact format:
{{
  "voiceover_urdu": "Write 75 to 95 words in pure Urdu script starting with: السلام علیکم دوستو! مزے دار پکوان میں خوش آمدید۔ آج میں اپنے کچن میں بنا رہی ہوں گرما گرم اور بے حد لذیذ {dish_ur}...",
  "caption": "🔥 Mazydar Pakwan Special: {dish_en}! 🍲✨\\n\\n{dish_ur} ki aisi lajawab khushbu aur zaiqa jo dil jeet le! Aaj ka vlog kaisa laga comment mein zaroor batayein ❤️👇\\n\\n#MazydarPakwan #PakistaniFood #DesiFood #FoodVlog #UrduRecipes",
  "scenes": [
    "{CHARACTER_PROMPT}, welcoming viewers in a Pakistani kitchen with fresh ingredients for {dish_en}, smiling at camera, vertical 9:16",
    "Close-up cinematic top-down shot of fresh desi spices, ginger garlic, tomatoes, and ingredients for {dish_en}, warm kitchen lighting, vertical 9:16",
    "{CHARACTER_PROMPT}, frying and stirring masala in a sizzling karahi with aromatic steam rising, cooking {dish_en}, vertical 9:16",
    "Extreme close-up food videography shot of {dish_en} simmering and bubbling in rich masala gravy on stove flame, vertical 9:16",
    "{CHARACTER_PROMPT}, sprinkling fresh green coriander and sliced ginger over hot {dish_en}, looking delighted, vertical 9:16",
    "{CHARACTER_PROMPT}, presenting the final steaming hot dish of {dish_en} towards the camera, ultra-detailed food photography, vertical 9:16"
  ]
}}"""

    # 1. Try Google Gemini API if valid AIza key is configured
    if GOOGLE_API_KEY and GOOGLE_API_KEY.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
            res = requests.post(
                url,
                json={"contents": [{"parts": [{"text": system_prompt}]}]},
                timeout=30,
            )
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                text = text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                if has_urdu_script(data.get("voiceover_urdu", "")):
                    return data
        except Exception as e:
            print(f"Google Gemini skipped ({e}), trying Pollinations Text AI...")

    # 2. Try Pollinations Text API
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
            timeout=40,
        )
        if res.status_code == 200:
            text = res.text.replace("```json", "").replace("```", "").strip()
            start, end = text.find("{"), text.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(text[start:end])
                if has_urdu_script(data.get("voiceover_urdu", "")):
                    if (
                        not data.get("scenes")
                        or len(data.get("scenes", [])) < 6
                    ):
                        data["scenes"] = build_default_scenes(dish_en)
                    return data
    except Exception as e:
        print(f"Pollinations LLM fallback notice: {e}")

    # 3. Rich, Varied, 100% Pure Urdu Feminine Script Fallback
    templates = [
        (
            f"السلام علیکم دوستو! مزے دار پکوان میں آپ سب کو خوش آمدید۔ "
            f"آج میں اپنے کچن میں آپ کے لیے بنا رہی ہوں انتہائی لذیذ اور گرما گرم {dish_ur}۔ "
            f"سب سے پہلے میں نے کڑاہی میں تازہ ادرک لہسن، ٹماٹر اور خالص دیسی مصالحوں کو اچھی طرح بھون لیا ہے تاکہ مصالحے کا کچا پن ختم ہو جائے اور اصل روایتی ذائقہ نکل کر سامنے آئے۔ "
            f"ماشاءاللہ، دیکھیں کتنا خوبصورت رنگ آیا ہے اور اس کی لاجواب خوشبو پورے کچن میں پھیل چکی ہے! "
            f"اب آخر میں میں نے اس کے اوپر باریک کٹا ہوا ہرا دھنیا، ادرک اور ہری مرچیں چھڑک دی ہیں۔ "
            f"لیجیے دوستو، ہماری شاندار {dish_ur} بالکل تیار ہے۔ اگر آپ کو میری آج کی محنت پسند آئی ہو تو ویڈیو کو لائک اور شیئر ضرور کریں۔"
        ),
        (
            f"السلام علیکم میرے پیارے دوستو! مزے دار پکوان کے کچن سے میں آپ کو خوش آمدید کہتی ہوں۔ "
            f"آج کے ولاگ میں میں تیار کر رہی ہوں سب کی پسندیدہ اور خوشبودار {dish_ur}۔ "
            f"اس خاص ریسپی کے لیے میں نے تازہ ترین اجزاء اور گھر کے پسے ہوئے خوشبودار گرم مصالحے استعمال کیے ہیں، جنہیں ہلکی آنچ پر بڑی محبت سے پکایا گیا ہے۔ "
            f"سبحان اللہ، جب مصالحہ اچھی طرح بھن جائے تو اس کا ذائقہ دگنا ہو جاتا ہے، اور سچ میں اسے دیکھ کر ہی منہ میں پانی آ رہا ہے! "
            f"تازہ ہرے دھنیے اور لیموں کے ساتھ گارنش کرنے کے بعد اب میں اسے گرما گرم پیش کر رہی ہوں۔ "
            f"آپ کو آج کی یہ مزیدار ڈش کیسی لگی، کمنٹ میں اپنی رائے کا اظہار ضرور کیجیے گا۔"
        ),
    ]
    return {
        "voiceover_urdu": random.choice(templates),
        "caption": (
            f"🔥 Mazydar Pakwan Special: {dish_en}! 🍲✨\n\n"
            f"Aaj main ne apne kitchen mein banayi hai garma garam {dish_en} ({dish_ur}). "
            f"Vlog kaisa laga comment mein zaroor batayein! ❤️👇\n\n"
            f"#MazydarPakwan #PakistaniFood #FoodVlog #DesiFood #CookingReels"
        ),
        "scenes": build_default_scenes(dish_en),
    }


def is_valid_rendered_image(img_bytes):
    if not img_bytes or len(img_bytes) < 12000:
        return False
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        stat = ImageStat.Stat(img)
        # Ensure image is not a solid/flat color wallpaper (check pixel standard deviation)
        avg_stddev = sum(stat.stddev) / 3.0
        return avg_stddev > 18.0
    except Exception:
        return False


def polish_and_brand_hd_image(img_bytes, dish_en, scene_idx, output_path):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    target_w, target_h = 1080, 1920
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * img_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / img_ratio)

    # High-Definition LANCZOS upscale + UnsharpMask crisp filter
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    img = img.filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=125, threshold=3)
    )
    img = ImageEnhance.Contrast(img).enhance(1.07)
    img = ImageEnhance.Color(img).enhance(1.15)

    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Sleek HD Top Branding Header
    draw.rounded_rectangle(
        [(55, 65), (target_w - 55, 190)],
        radius=30,
        fill=(12, 8, 4, 185),
        outline=(255, 195, 45, 235),
        width=4,
    )

    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
        )
        font_sub = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25
        )
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text(
        (target_w // 2, 104),
        "MAZYDAR PAKWAN",
        fill=(255, 205, 55, 255),
        font=font_title,
        anchor="mm",
    )
    draw.text(
        (target_w // 2, 154),
        dish_en[:40],
        fill=(255, 255, 255, 250),
        font=font_sub,
        anchor="mm",
    )

    final_img = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
        "RGB"
    )
    final_img.save(output_path, "PNG", optimize=True)


def generate_scene_image(prompt, index, dish_en, output_path, generated_paths):
    # Check if user uploaded character.png for Scene 0
    if index == 0:
        for ext in [
            "character.png",
            "character.jpg",
            "character.jpeg",
            "assets/character.png",
        ]:
            if os.path.exists(ext):
                print(
                    f"Scene 1: Using uploaded '{ext}' base character image..."
                )
                with open(ext, "rb") as f:
                    polish_and_brand_hd_image(
                        f.read(), dish_en, index, output_path
                    )
                return

    # Crucial 20-second relaxation pause between scenes so Pollinations never triggers HTTP 402
    if index > 0:
        print(
            f"Waiting 20 seconds before Scene {index+1} so AI server stays relaxed..."
        )
        time.sleep(20)

    clean_prompt = f"{prompt}, ultra HD food photography, sharp focus, natural lighting, no text, no watermark"
    encoded_prompt = urllib.parse.quote(clean_prompt)

    # Rotate across models & endpoints (768x1344 native 9:16 avoids 402 memory limits, then upscaled to 1080x1920 HD)
    attempts = [
        ("Pollinations Flux (Free Direct)", "flux", False, 768, 1344),
        ("Pollinations Flux (API Key)", "flux", True, 768, 1344),
        ("Pollinations Turbo (Fast HD)", "turbo", False, 768, 1344),
        ("Pollinations Flux (Standard 9:16)", "flux", False, 576, 1024),
        ("Pollinations Default Engine", "gptimage", False, 768, 1344),
    ]

    for attempt_num, (label, model_name, use_key, w, h) in enumerate(
        attempts, start=1
    ):
        if use_key and not POLLINATIONS_API_KEY:
            continue

        seed = random.randint(10000, 9999999)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={w}&height={h}&model={model_name}&nologo=true&seed={seed}"
        )
        headers = {
            "User-Agent": f"Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
        }
        if use_key and POLLINATIONS_API_KEY:
            headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

        try:
            print(f"Scene {index+1} [Try {attempt_num} - {label}]: Generating...")
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200 and is_valid_rendered_image(r.content):
                polish_and_brand_hd_image(
                    r.content, dish_en, index, output_path
                )
                print(
                    f"Scene {index+1} successfully generated in HD via {label}!"
                )
                return
            else:
                print(
                    f"Scene {index+1} [{label}] status {r.status_code}. Cooling down 15s before next try..."
                )
        except Exception as e:
            print(
                f"Scene {index+1} [{label}] network notice: {e}. Cooling down 15s..."
            )

        time.sleep(15)

    # Zero-Brown-Screen Guarantee: If all 5 tries fail, create a zoomed/cropped variation of a previous valid scene
    if generated_paths:
        source_scene = random.choice(generated_paths)
        print(
            f"Scene {index+1}: Creating close-up variation from {source_scene} (Zero brown screen guarantee)"
        )
        img = Image.open(source_scene).convert("RGB")
        w, h = img.size
        crop_box = (int(w * 0.08), int(h * 0.10), int(w * 0.92), int(h * 0.90))
        cropped = img.crop(crop_box).resize(
            (1080, 1920), Image.Resampling.LANCZOS
        )
        cropped.save(output_path, "PNG")
        return

    raise RuntimeError(
        "Could not generate initial scene from AI server. Please re-run workflow."
    )


def generate_voiceover(text, audio_path):
    cmd = [
        "edge-tts",
        "--voice",
        VOICE_NAME,
        "--rate=+2%",
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


def generate_kitchen_sfx_and_mix(voice_path, final_audio_path, duration):
    """Generates realistic kitchen cooking sizzle + soft culinary intro chime using FFmpeg DSP

    and mixes it cleanly beneath the female Urdu voiceover.
    """
    sfx_path = "kitchen_ambience.wav"
    # Pink noise shaped with highpass/lowpass & tremolo creates a warm, realistic karahi frying sizzle
    sfx_filter = (
        f"anoisesrc=d={duration}:c=pink:r=44100:a=0.035,"
        f"highpass=f=1200,lowpass=f=6500,"
        f"tremolo=f=7:d=0.45,"
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

    # Mix voiceover (dominant, crystal clear) + kitchen cooking sizzle (subtle ambience)
    mix_filter = (
        "[0:a]volume=1.35,highpass=f=80[voice];"
        "[1:a]volume=0.28[sfx];"
        "[voice][sfx]amix=inputs=2:duration=first:dropout_transition=2,"
        "loudnorm=I=-15:TP=-1.5:LRA=11[outa]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            voice_path,
            "-i",
            sfx_path,
            "-filter_complex",
            mix_filter,
            "-map",
            "[outa]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "44100",
            final_audio_path,
        ],
        check=True,
    )


def build_hd_video(scene_paths, voice_path, output_video):
    total_duration = get_audio_duration(voice_path)
    final_audio_path = "mixed_master_audio.m4a"
    generate_kitchen_sfx_and_mix(voice_path, final_audio_path, total_duration)

    num_scenes = len(scene_paths)
    clip_duration = max(total_duration / num_scenes, 3.2)
    fps = 30
    frames = int(clip_duration * fps)

    clip_files = []
    for i, img_path in enumerate(scene_paths):
        clip_name = f"clip_{i}.mp4"
        motion_type = i % 4

        if motion_type == 0:
            z_expr = "min(zoom+0.0012,1.16)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == 1:
            z_expr = "if(eq(on,1),1.16,max(zoom-0.0012,1.0))"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == 2:
            z_expr = "1.12"
            x_expr = f"max(0,min((iw-iw/zoom)*on/{frames},iw-iw/zoom))"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            z_expr = "1.12"
            x_expr = f"max(0,(iw-iw/zoom)*(1-on/{frames}))"
            y_expr = "ih/2-(ih/zoom/2)"

        vf_filter = (
            f"scale=1350:2400,"
            f"zoompan=z='{z_expr}':d={frames}:x='{x_expr}':y='{y_expr}':s=1080x1920:fps={fps},"
            f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(clip_duration-0.3, 0.5)}:d=0.3,"
            f"format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            img_path,
            "-vf",
            vf_filter,
            "-t",
            str(clip_duration),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            clip_name,
        ]
        subprocess.run(cmd, check=True)
        clip_files.append(clip_name)

    with open("concat_list.txt", "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    cmd_final = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "concat_list.txt",
        "-i",
        final_audio_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-profile:v",
        "high",
        "-crf",
        "19",
        "-c:a",
        "copy",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_video,
    ]
    subprocess.run(cmd_final, check=True)


def send_to_telegram(video_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as video_file:
        files = {"video": video_file}
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "width": 1080,
            "height": 1920,
            "supports_streaming": True,
        }
        res = requests.post(url, data=data, files=files, timeout=180)
        res.raise_for_status()
        print("HD Video successfully sent to Telegram!")


def main():
    dish_en, dish_ur = pick_unique_dish()
    script_data = generate_vlog_script(dish_en, dish_ur)

    voice_path = "voice.mp3"
    generate_voiceover(script_data["voiceover_urdu"], voice_path)

    scene_paths = []
    scenes = script_data.get("scenes", build_default_scenes(dish_en))[:6]
    for idx, scene_prompt in enumerate(scenes):
        img_path = f"scene_{idx}.png"
        generate_scene_image(scene_prompt, idx, dish_en, img_path, scene_paths)
        scene_paths.append(img_path)

    output_video = "mazydar_pakwan_hd_reel.mp4"
    build_hd_video(scene_paths, voice_path, output_video)

    send_to_telegram(output_video, script_data["caption"])
    save_used_dish(dish_en)
    print(f"Successfully completed and logged HD vlog for: {dish_en}")


if __name__ == "__main__":
    main()
