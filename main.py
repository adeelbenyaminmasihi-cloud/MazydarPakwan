import io
import json
import os
import random
import subprocess
import time
import urllib.parse
from PIL import Image, ImageDraw, ImageEnhance
import requests

# =====================================================================
# 1. APNA GOOGLE FLOW CHARACTER PROMPT YAHAN PASTE KAREIN
# =====================================================================
CHARACTER_PROMPT = (
    "A friendly young Pakistani food vlogger chef, wearing a clean black chef apron, "
    "warm welcoming smile, expressive eyes, realistic skin texture, cinematic kitchen lighting"
)

# Awaz: Male character ke liye "ur-PK-AsadNeural", Female ke liye "ur-PK-UzmaNeural"
VOICE_NAME = "ur-PK-AsadNeural"

# =====================================================================
# 2. API KEYS & TOKENS (GitHub Secrets ya Direct Fallback)

HISTORY_FILE = "used_dishes.txt"

# Master Desi Dishes Pool (Plus dynamic generation so it never repeats)
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
    # Agar 40 dishes poori ho jayein to AI se bilkul nayi dish banwaye
    prompt = f"Give me ONLY the name of 1 unique Pakistani or Mughlai food dish not in this list: {', '.join(list(used)[-30:])}. Reply with just the dish name."
    try:
        r = requests.get(
            f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}",
            timeout=20,
        )
        if r.status_code == 200 and len(r.text.strip()) < 60:
            return r.text.strip().replace('"', "")
    except Exception:
        pass
    return f"Chef Special Royal Handi #{len(used) + 1}"


def generate_vlog_script(dish_name):
    print(f"Generating script for: {dish_name}")
    system_prompt = f"""You are the writer for 'Mazydar Pakwan', a Pakistani AI food vlogger channel.
Create a short, energetic 35-second food vlog script for the dish: "{dish_name}".

Return ONLY valid JSON in this exact format (no markdown blocks):
{{
  "voiceover_urdu": "Write a lively 70-85 word vlog voiceover in pure Urdu script (اردو رسم الخط) starting with السلام علیکم دوستو! مزے دار پکوان میں خوش آمدید. Describe cooking {dish_name}, its aroma, spices, and taste like an excited food vlogger.",
  "caption": "🔥 Mazydar Pakwan Special: {dish_name}! 🍲✨\\n\\nAaj hum ne banayi hai garma garam {dish_name}. Video kaisi lagi comment mein zaroor batayein! ❤️\\n\\n#MazydarPakwan #PakistaniFood #FoodVlog #DesiFood #Recipes",
  "scenes": [
    "{CHARACTER_PROMPT}, holding fresh ingredients in a Pakistani kitchen, smiling at camera, vertical 9:16",
    "{CHARACTER_PROMPT}, sizzling onions, tomatoes, and rich desi spices in a traditional wok/karahi with steam rising, vertical 9:16",
    "Close-up cinematic shot of {dish_name} cooking on high flame, rich gravy bubbling, aromatic spices, vertical 9:16",
    "{CHARACTER_PROMPT}, garnishing freshly cooked {dish_name} with green chillies and fresh coriander, looking excited, vertical 9:16",
    "{CHARACTER_PROMPT}, presenting the final hot plate of {dish_name} towards the camera, mouth-watering food photography, vertical 9:16"
  ]
}}"""

    # 1. Try Google Gemini API First
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
                f"Google API skipped/failed ({e}), switching to Free AI LLM..."
            )

    # 2. Free Fallback LLM (Pollinations OpenAI-compatible Endpoint - 100% Free)
    try:
        res = requests.post(
            "https://text.pollinations.ai/",
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
            timeout=40,
        )
        if res.status_code == 200:
            text = res.text.replace("```json", "").replace("```", "").strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])
    except Exception as e:
        print(f"Free LLM fallback warning: {e}")

    # 3. Bulletproof Local Fallback (Guarantees script never fails)
    return {
        "voiceover_urdu": f"السلام علیکم دوستو! مزے دار پکوان میں خوش آمدید۔ آج ہم اپنے کچن میں بنا رہے ہیں انتہائی لذیذ اور خوشبودار {dish_name}۔ سب سے پہلے ہم نے تازہ مصالحوں کو اچھی طرح بھون لیا ہے تاکہ اصل دیسی ذائقہ نکل کر سامنے آئے۔ ماشاءاللہ، اس کی خوشبو پورے کچن میں پھیل چکی ہے اور دیکھ کر ہی منہ میں پانی آ رہا ہے! اگر آپ کو آج کی یہ مزیدار ریسپی پسند آئی ہو تو ویڈیو کو لائک اور شیئر ضرور کریں۔",
        "caption": f"🔥 Mazydar Pakwan Special: {dish_name}! 🍲✨\n\nGarma garam aur chatpati {dish_name} tayyar hai! ❤️\n\n#MazydarPakwan #DesiFood #FoodVlog #PakistaniStreetFood",
        "scenes": [
            f"{CHARACTER_PROMPT}, welcoming viewers in a cozy Pakistani kitchen with fresh ingredients, vertical 9:16, photorealistic",
            f"{CHARACTER_PROMPT}, cooking and stirring aromatic masala spices in a traditional karahi with steam rising, vertical 9:16",
            f"Extreme close-up of delicious {dish_name} sizzling in a traditional pot, rich gravy and spices, vertical 9:16",
            f"{CHARACTER_PROMPT}, garnishing hot {dish_name} with fresh coriander and sliced ginger, happy expression, vertical 9:16",
            f"{CHARACTER_PROMPT}, holding up a steaming platter of {dish_name} towards the camera, cinematic food vlog, vertical 9:16",
        ],
    }


def prepare_vertical_image(img_bytes, output_path):
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
    img.save(output_path, "PNG")


def generate_scene_image(prompt, index, output_path):
    # Agar user ne character.png upload ki hai, to Scene 0 mein wohi original photo use hogi!
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
                    prepare_vertical_image(f.read(), output_path)
                return

    # 1. Try Replicate API (Flux-Schnell) if credits available
    if REPLICATE_API_TOKEN:
        try:
            headers = {
                "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
                "Content-Type": "application/json",
                "Prefer": "wait",
            }
            payload = {
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": "9:16",
                    "output_format": "png",
                }
            }
            r = requests.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions",
                headers=headers,
                json=payload,
                timeout=45,
            )
            if r.status_code in [200, 201]:
                data = r.json()
                out = data.get("output")
                img_url = out[0] if isinstance(out, list) else out
                if img_url:
                    img_res = requests.get(img_url, timeout=30)
                    if img_res.status_code == 200:
                        prepare_vertical_image(img_res.content, output_path)
                        print(f"Scene {index+1} generated via Replicate!")
                        return
        except Exception as e:
            print(f"Replicate skipped for scene {index+1}: {e}")

    # 2. 100% Free Unlimited AI Image Generation (Pollinations Flux Model)
    seed = random.randint(1000, 999999)
    encoded_prompt = urllib.parse.quote(prompt)
    free_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux&nologo=true&seed={seed}"

    for attempt in range(3):
        try:
            r = requests.get(free_url, timeout=60)
            if r.status_code == 200 and len(r.content) > 10000:
                prepare_vertical_image(r.content, output_path)
                print(f"Scene {index+1} generated via Free Flux AI!")
                return
        except Exception as e:
            print(f"Attempt {attempt+1} for scene {index+1} waiting: {e}")
            time.sleep(4)

    # 3. Emergency Fallback (if internet drops)
    fallback = Image.new("RGB", (1080, 1920), (35, 20, 10))
    fallback.save(output_path, "PNG")


def generate_voiceover(text, audio_path):
    cmd = [
        "edge-tts",
        "--voice",
        VOICE_NAME,
        "--rate=+3%",
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
        # Alternate smooth Zoom-In and Zoom-Out motion for realistic vlog feel
        if i % 2 == 0:
            z_expr = "min(zoom+0.0015,1.18)"
        else:
            z_expr = "if(eq(on,1),1.18,max(zoom-0.0015,1.0))"

        vf_filter = (
            f"scale=1200:2134,"
            f"zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
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
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
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
    for idx, scene_prompt in enumerate(script_data["scenes"][:5]):
        img_path = f"scene_{idx}.png"
        generate_scene_image(scene_prompt, idx, img_path)
        scene_paths.append(img_path)

    output_video = "mazydar_pakwan_reel.mp4"
    build_video(scene_paths, audio_path, output_video)

    send_to_telegram(output_video, script_data["caption"])
    save_used_dish(dish_name)
    print(f"Completed and logged dish: {dish_name}")


if __name__ == "__main__":
    main()
