import io
import json
import os
import random
import subprocess
import sys
import time
import urllib.parse
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
import requests

# =====================================================================
# 1. APNA GOOGLE FLOW FEMALE CHARACTER PROMPT YAHAN PASTE KAREIN
# =====================================================================
CHARACTER_PROMPT = (
    "A friendly young Pakistani female food vlogger chef, wearing a modest stylish apron "
    "and headscarf, warm welcoming smile, expressive eyes, realistic skin texture, "
    "modern Pakistani kitchen with warm cinematic lighting"
)

# Pakistani Female Voice Artist (Uzma Neural)
VOICE_NAME = "ur-PK-UzmaNeural"

# =====================================================================
# 2. SECURE ENVIRONMENT VARIABLES (Strictly from GitHub Secrets)
# =====================================================================
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print(
        "Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID GitHub Secrets mein mojood nahi!"
    )
    sys.exit(1)

HISTORY_FILE = "used_dishes.txt"

MASTER_DISHES = [
    "Karachi Special Degi Chicken Biryani",
    "Peshawari Charsi Mutton Karahi",
    "Lahori Chargha with Masala Fries",
    "Special Beef Nalli Nihari",
    "Hyderabadi Dum Kachay Gosht Ki Biryani",
    "Shahi Malai Kofta Curry",
    "Dhaba Style Daal Makhani",
    "Crispy Fried Fish Masala",
    "Mughlai Chicken Handi",
    "Special Reshmi Seekh Kabab Karahi",
    "Sindhi Mutton Biryani",
    "Butter Chicken Masala with Garlic Naan",
    "Peshawari Chapli Kabab",
    "Shahi Chicken Haleem",
    "Balochi Sajji with Kabuli Pulao",
    "Tawa Chicken Piece Lahore Style",
    "Mutton Kunna Chiniot Style",
    "Creamy White Chicken Karahi",
    "Beef Bihari Boti Roll",
    "Halwa Puri with Aloo Cholay",
    "Katakat Masala Street Style",
    "Chicken Jalfrezi Restaurant Style",
    "Smoky Koyla Chicken Karahi",
    "Mutton Yakhni Pulao",
    "Gajar Ka Halwa Khoya Special",
    "Shahi Tukray with Rabri",
    "Palak Gosht Dhaba Style",
    "Aloo Qeema Masala",
    "Chicken Shashlik with Egg Fried Rice",
    "Masaledar Bhindi Gosht",
    "Lahori Murgh Chanay",
    "Prawn Masala Karahi",
    "Special Brain Masala",
    "Kachori with Aloo Tarkari",
    "Degi Zarda Matanjan",
    "Afghani Beef Pulao",
    "Tandoori Chicken Tikka Masala",
    "Harissa Lahori Style",
    "Special Mutton Paya Curry",
    "Crispy Chicken Broast",
]


def get_pollinations_headers():
    headers = {"Content-Type": "application/json"}
    if POLLINATIONS_API_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"
    return headers


def get_used_dishes():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def save_used_dish(dish_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{dish_name}\n")


def pick_unique_dish():
    used = set(get_used_dishes())
    available = [d for d in MASTER_DISHES if d not in used]
    if available:
        return random.choice(available)

    prompt = (
        f"Give me ONLY the name of 1 unique Pakistani or Mughlai food dish not in this list: "
        f"{', '.join(list(used)[-35:])}. Reply with just the dish name."
    )
    try:
        r = requests.get(
            f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}",
            headers=get_pollinations_headers(),
            timeout=25,
        )
        if r.status_code == 200 and len(r.text.strip()) < 60:
            return r.text.strip().replace('"', "")
    except Exception:
        pass
    return f"Mazydar Chef Special Handi #{len(used) + 1}"


def generate_vlog_script(dish_name):
    print(f"Generating female vlog script for: {dish_name}")
    system_prompt = f"""You are the writer for 'Mazydar Pakwan', a popular Pakistani female AI food vlogger channel.
Create an engaging 35-40 second food vlog script for the dish: "{dish_name}".
IMPORTANT: The speaker is FEMALE, so use feminine Urdu grammar (e.g., میں بنا رہی ہوں، میں نے شامل کیا ہے، آپ کو دکھاتی ہوں).

Return ONLY valid JSON in this exact structure (no markdown blocks):
{{
  "voiceover_urdu": "Write a warm, energetic 75-90 word vlog voiceover in pure Urdu script (اردو رسم الخط) using feminine grammar, starting with السلام علیکم دوستو! مزے دار پکوان میں خوش آمدید. Describe how you are cooking {dish_name}, its rich aroma, desi spices, and mouth-watering taste.",
  "caption": "🔥 Mazydar Pakwan Special: {dish_name}! 🍲✨\\n\\nAaj main ne aap sab ke liye banayi hai garma garam aur chatpati {dish_name}. Recipe aur vlog kaisa laga comment mein zaroor batayein! ❤️👇\\n\\n#MazydarPakwan #PakistaniFood #FoodVlog #DesiFood #CookingReels",
  "scenes": [
    "{CHARACTER_PROMPT}, holding fresh ingredients and spices in a cozy Pakistani kitchen, smiling warmly at camera, vertical 9:16, ultra realistic",
    "{CHARACTER_PROMPT}, adding chopped onions, tomatoes, and vibrant desi masala into a sizzling karahi, aromatic steam rising, vertical 9:16",
    "Extreme close-up cinematic food shot of {dish_name} cooking on high flame, rich thick gravy bubbling with traditional spices, vertical 9:16",
    "{CHARACTER_PROMPT}, stirring the delicious {dish_name} with a wooden spoon, looking happy and impressed by the aroma, vertical 9:16",
    "{CHARACTER_PROMPT}, garnishing freshly cooked {dish_name} with chopped green chillies, ginger juliennes, and fresh coriander, vertical 9:16",
    "{CHARACTER_PROMPT}, proudly presenting the steaming hot final dish of {dish_name} towards the camera, mouth-watering food photography, vertical 9:16"
  ]
}}"""

    # 1. Try Google Gemini API (if valid AIza key is provided)
    if GOOGLE_API_KEY and GOOGLE_API_KEY.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
            payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
        except Exception as e:
            print(
                f"Google API skipped ({e}), using Pollinations AI with API Key..."
            )

    # 2. Pollinations Authenticated LLM Endpoint
    try:
        res = requests.post(
            "https://text.pollinations.ai/",
            headers=get_pollinations_headers(),
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "You output only valid raw JSON.",
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
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])
    except Exception as e:
        print(f"Pollinations LLM warning: {e}")

    # 3. Reliable Feminine Urdu Fallback
    return {
        "voiceover_urdu": f"السلام علیکم دوستو! مزے دار پکوان میں خوش آمدید۔ آج میں اپنے کچن میں آپ سب کے لیے بنا رہی ہوں انتہائی لذیذ اور خوشبودار {dish_name}۔ سب سے پہلے میں نے تازہ مصالحوں کو دیسی گھی میں اچھی طرح بھون لیا ہے تاکہ اصل روایتی ذائقہ نکل کر سامنے آئے۔ ماشاءاللہ، اس کی لاجواب خوشبو پورے کچن میں پھیل چکی ہے اور دیکھ کر ہی منہ میں پانی آ رہا ہے! اب میں نے اس پر ہرا دھنیا اور ہری مرچیں چھڑک دی ہیں۔ اگر آپ کو میری آج کی یہ مزیدار ریسپی پسند آئی ہو تو ویڈیو کو لائک اور شیئر ضرور کریں۔",
        "caption": f"🔥 Mazydar Pakwan Special: {dish_name}! 🍲✨\n\nAaj main ne banayi hai garma garam {dish_name}. Video kaisi lagi zaroor batayein! ❤️\n\n#MazydarPakwan #DesiFood #FoodVlog #PakistaniRecipes",
        "scenes": [
            f"{CHARACTER_PROMPT}, welcoming viewers in a cozy Pakistani kitchen with fresh ingredients, vertical 9:16, photorealistic",
            f"{CHARACTER_PROMPT}, cooking and stirring aromatic masala spices in a traditional karahi with steam rising, vertical 9:16",
            f"Extreme close-up of delicious {dish_name} sizzling in a traditional pot, rich gravy and spices, vertical 9:16",
            f"{CHARACTER_PROMPT}, tasting the aroma of {dish_name} while cooking on stove, happy expression, vertical 9:16",
            f"{CHARACTER_PROMPT}, garnishing hot {dish_name} with fresh coriander and sliced ginger, smiling, vertical 9:16",
            f"{CHARACTER_PROMPT}, holding up a steaming platter of {dish_name} towards the camera, cinematic food vlog, vertical 9:16",
        ],
    }


def polish_and_brand_image(img_bytes, dish_name, output_path):
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

    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    # Cinematic color pop (Contrast + Saturation)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Color(img).enhance(1.14)

    # Subtle top & bottom branding badge
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top pill badge for channel & dish title
    draw.rounded_rectangle(
        [(60, 70), (target_w - 60, 185)],
        radius=28,
        fill=(15, 10, 5, 175),
        outline=(255, 185, 50, 220),
        width=3,
    )

    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34
        )
        font_sub = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26
        )
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text(
        (target_w // 2, 105),
        "MAZYDAR PAKWAN",
        fill=(255, 200, 60, 255),
        font=font_title,
        anchor="mm",
    )
    draw.text(
        (target_w // 2, 152),
        dish_name[:42],
        fill=(255, 255, 255, 245),
        font=font_sub,
        anchor="mm",
    )

    final_img = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
        "RGB"
    )
    final_img.save(output_path, "PNG")


def generate_scene_image(prompt, index, dish_name, output_path):
    # Scene 0 uses uploaded character.png if present in repository
    if index == 0:
        for ext in [
            "character.png",
            "character.jpg",
            "character.jpeg",
            "assets/character.png",
        ]:
            if os.path.exists(ext):
                print(f"Using uploaded character file '{ext}' for Intro Scene!")
                with open(ext, "rb") as f:
                    polish_and_brand_image(f.read(), dish_name, output_path)
                return

    seed = random.randint(10000, 9999999)
    encoded_prompt = urllib.parse.quote(prompt)

    # Use Pollinations Flux with API Key for priority, high-res, watermark-free media
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1080&height=1920&model=flux&nologo=true&enhance=true&seed={seed}"
    )
    if POLLINATIONS_API_KEY:
        url += f"&key={urllib.parse.quote(POLLINATIONS_API_KEY)}"

    headers = {}
    if POLLINATIONS_API_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

    for attempt in range(4):
        try:
            r = requests.get(url, headers=headers, timeout=75)
            if r.status_code == 200 and len(r.content) > 10000:
                polish_and_brand_image(r.content, dish_name, output_path)
                print(f"Scene {index+1} generated via Pollinations Flux API!")
                return
            else:
                print(
                    f"Scene {index+1} status {r.status_code}, retrying ({attempt+1}/4)..."
                )
        except Exception as e:
            print(f"Attempt {attempt+1} for scene {index+1} warning: {e}")
        time.sleep(4)

    # Fallback dark culinary canvas if network drops completely
    fallback = Image.new("RGB", (1080, 1920), (35, 20, 10))
    buf = io.BytesIO()
    fallback.save(buf, format="PNG")
    polish_and_brand_image(buf.getvalue(), dish_name, output_path)


def generate_voiceover(text, audio_path):
    cmd = [
        "edge-tts",
        "--voice",
        VOICE_NAME,
        "--rate=+4%",
        "--pitch=+2Hz",
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


def build_video(scene_paths, audio_path, output_video):
    total_duration = get_audio_duration(audio_path)
    num_scenes = len(scene_paths)
    clip_duration = max(total_duration / num_scenes, 3.0)
    fps = 25
    frames = int(clip_duration * fps)

    clip_files = []
    for i, img_path in enumerate(scene_paths):
        clip_name = f"clip_{i}.mp4"
        motion_type = i % 4

        # 4 Dynamic Camera Movements (Zoom In, Zoom Out, Pan Right, Pan Left)
        if motion_type == 0:
            z_expr = "min(zoom+0.0016,1.18)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == 1:
            z_expr = "if(eq(on,1),1.18,max(zoom-0.0016,1.0))"
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
            f"scale=1240:2204,"
            f"zoompan=z='{z_expr}':d={frames}:x='{x_expr}':y='{y_expr}':s=1080x1920:fps={fps},"
            f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(clip_duration-0.25, 0.5)}:d=0.25,"
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
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            clip_name,
        ]
        subprocess.run(cmd, check=True)
        clip_files.append(clip_name)

    with open("concat_list.txt", "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    # Combine clips with normalized studio-grade female voiceover
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
        audio_path,
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "22",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "44100",
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
            "supports_streaming": True,
        }
        res = requests.post(url, data=data, files=files, timeout=120)
        res.raise_for_status()
        print("Video successfully sent to Telegram!")


def main():
    dish_name = pick_unique_dish()
    script_data = generate_vlog_script(dish_name)

    audio_path = "voice.mp3"
    generate_voiceover(script_data["voiceover_urdu"], audio_path)

    scene_paths = []
    scenes = script_data.get("scenes", [])[:6]
    for idx, scene_prompt in enumerate(scenes):
        img_path = f"scene_{idx}.png"
        generate_scene_image(scene_prompt, idx, dish_name, img_path)
        scene_paths.append(img_path)

    output_video = "mazydar_pakwan_reel.mp4"
    build_video(scene_paths, audio_path, output_video)

    send_to_telegram(output_video, script_data["caption"])
    save_used_dish(dish_name)
    print(f"Successfully completed and logged dish: {dish_name}")


if __name__ == "__main__":
    main()
