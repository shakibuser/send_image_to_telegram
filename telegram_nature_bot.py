import requests
import io
import random
import json
import os
import sys
import time
import urllib.parse
import tempfile
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# --- 1. CONFIGURATION ---


def load_token(key_name, json_key):
    val = os.environ.get(key_name)
    if val:
        return val
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, 'config.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(json_key)
    except:
        return None


TELEGRAM_BOT_TOKEN = load_token("TELEGRAM_BOT_TOKEN", "telegram_bot_token")
TELEGRAM_CHANNEL_ID = load_token("TELEGRAM_CHANNEL_ID", "telegram_channel_id")

# --- 2. TEXT SETTINGS (Environment Aware) ---
# تشخیص محیط اجرا: اگر در گیت‌هاب باشد True می‌شود
IS_GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"

# اگر در گیت‌هاب بودیم، متن فارسی را خالی می‌گذاریم تا فقط انگلیسی نمایش داده شود
# اگر در ویندوز بودیم، متن فارسی سر جای خود باقی می‌ماند
TEXT_PERSIAN = "" if IS_GITHUB else "صبا رسانه"
TEXT_ENGLISH = "@saba_rasanehh"

# --- 3. DYNAMIC PROMPTS ---
SUBJECTS = [
    {"p": "The majestic ruins of Persepolis (Takht-e Jamshid) at sunset, ancient Persian architecture",
     "fa": "تخت جمشید", "en": "Persepolis, Iran"},
    {"p": "The Ziggurat of Chogha Zanbil, ancient Elamite complex, brick texture, golden hour sunlight",
        "fa": "زیگورات چغازنبیل", "en": "Chogha Zanbil, Iran"},
    {"p": "The ancient Arg-e Bam citadel, massive adobe fortress, desert sunset, intricate mudbrick details",
        "fa": "ارگ بم", "en": "Arg-e Bam, Iran"},
    {"p": "Naqsh-e Jahan Square in Isfahan, turquoise domes of Imam Mosque, Ali Qapu Palace reflection",
        "fa": "میدان نقش جهان", "en": "Naqsh-e Jahan Sq, Isfahan"},
    {"p": "Mount Damavand covered in snow, volcanic peak rising above clouds, wild poppies in foreground",
        "fa": "کوه دماوند", "en": "Mount Damavand, Iran"},
    {"p": "Nasir al-Mulk Mosque (Pink Mosque) in Shiraz, morning light through stained glass, colorful patterns",
     "fa": "مسجد نصیرالملک", "en": "Pink Mosque, Shiraz"},
    {"p": "The Kaluts of Shahdad Desert (Lut Desert) at sunrise, strange sand formations, vast landscape",
     "fa": "کلوت‌های شهداد", "en": "Lut Desert, Iran"},
    {"p": "Tabatabaei Historical House in Kashan, traditional Persian architecture, stained glass, courtyard",
        "fa": "خانه طباطبایی‌ها", "en": "Tabatabaei House, Kashan"},
    {"p": "Angkor Wat temple complex in Cambodia at sunrise, reflection in lotus pond, mystical mist",
        "fa": "انگکور وات", "en": "Angkor Wat, Cambodia"},
    {"p": "Ha Long Bay in Vietnam, limestone karsts, emerald waters, traditional junk boat sailing",
        "fa": "خلیج ها لونگ", "en": "Ha Long Bay, Vietnam"},
    {"p": "Fushimi Inari Taisha shrine in Kyoto, path of thousands of red torii gates, forest background",
        "fa": "معبد فوشیمی ایناری", "en": "Fushimi Inari, Japan"},
    {"p": "The Great Wall of China winding through autumn mountains, sunrise, ancient fortification",
        "fa": "دیوار بزرگ چین", "en": "Great Wall of China"},
    {"p": "Gardens by the Bay in Singapore, Supertree Grove at night, neon lights, futuristic garden",
        "fa": "باغ‌های خلیج", "en": "Gardens by the Bay, Singapore"},
    {"p": "Mount Fuji with cherry blossoms (Sakura) in the foreground, lake reflection, snow-capped peak",
     "fa": "کوه فوجی", "en": "Mount Fuji, Japan"},
    {"p": "The Taj Mahal in India, white marble mausoleum, symmetrical reflection, soft morning mist",
        "fa": "تاج محل", "en": "Taj Mahal, India"},
    {"p": "Petra in Jordan, The Treasury (Al-Khazneh) carved into red sandstone cliff, dramatic shadows",
     "fa": "پترا", "en": "Petra, Jordan"},
    {"p": "Santorini, Greece, white buildings with blue domes, vibrant pink bougainvillea flowers, Aegean Sea",
        "fa": "سانتورینی", "en": "Santorini, Greece"},
    {"p": "Venice canals at sunset, gondola, old architecture, reflection in water, romantic atmosphere",
        "fa": "ونیز", "en": "Venice, Italy"},
    {"p": "A futuristic cyberpunk city street, neon signs, rain, flying cars, high tech architecture",
        "fa": "شهر سایبرپانک", "en": "Cyberpunk City"},
    {"p": "A mystical library with floating books, dust motes dancing in light beams, fantasy art style",
        "fa": "کتابخانه جادویی", "en": "Magical Library"}
]

STYLES = ["cinematic lighting, 8k", "digital art, vibrant colors", "oil painting style",
          "watercolor painting, soft edges", "cyberpunk style, neon lights", "national geographic style"]
ATMOSPHERES = ["during a golden sunset", "under a dramatic stormy sky",
               "in the early morning mist", "at night with a bright full moon", "bathed in soft warm sunlight"]


def get_dynamic_prompt():
    subj = random.choice(SUBJECTS)
    style = random.choice(STYLES)
    atm = random.choice(ATMOSPHERES)
    return {"text": f"{subj['p']}, {atm}, {style}, masterpiece.", "fa": subj['fa'], "en": subj['en']}

# --- 4. GENERATION ---


def generate_image(prompt):
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(0, 1000000)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&nologo=true&model=flux"
    print(f"🎨 Generating: {prompt[:40]}...")

    for i in range(3):
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                return Image.open(io.BytesIO(resp.content))
        except Exception as e:
            print(f"⚠️ Attempt {i+1} failed: {e}")
            time.sleep(3)
    return None


def get_telegram_icon(size):
    """
    Downloads Telegram icon. If fails, DRAWS a correct vector-like paper plane.
    """
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/480px-Telegram_logo.svg.png"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            icon = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            resample = getattr(Image, "Resampling", Image).LANCZOS
            return icon.resize((size, size), resample)
    except:
        pass

    # Fallback: Draw the actual Telegram Logo (Blue Circle + Paper Plane)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon)

    # 1. Blue Circle
    d.ellipse((0, 0, size, size), fill="#24A1DE")

    # 2. White Paper Plane (Coordinates relative to size)
    points = [
        (size * 0.18, size * 0.48),  # Left wing
        (size * 0.82, size * 0.22),  # Nose/Top-Right
        (size * 0.55, size * 0.72)   # Bottom
    ]
    d.polygon(points, fill="white")

    return icon


def get_font(size):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, "Vazir.ttf")

    if os.name == 'nt':
        try:
            return ImageFont.truetype("tahoma.ttf", size)
        except:
            pass

    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass

    print("⬇️ Downloading Vazir font...")
    url = "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(font_path, "wb") as f:
                f.write(resp.content)
            return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"⚠️ Font error: {e}")

    return ImageFont.load_default()


def add_watermark(image):
    base = image.convert("RGBA")
    txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Font Setup (Slightly bigger for readability)
    font_size = int(image.width / 45)
    font = get_font(font_size)

    # Prepare Text
    # Handle Persian text only if available (not running on GitHub)
    bidi_fa = ""
    if TEXT_PERSIAN:
        reshaped_fa = arabic_reshaper.reshape(TEXT_PERSIAN)
        bidi_fa = get_display(reshaped_fa)  # Text 1 (Top)

    text_en = TEXT_ENGLISH             # Text 2 (Bottom)

    # Calculate Dimensions for BOTH lines
    w_fa, h_fa = 0, 0
    if bidi_fa:
        bbox_fa = draw.textbbox((0, 0), bidi_fa, font=font)
        w_fa = bbox_fa[2] - bbox_fa[0]
        h_fa = bbox_fa[3] - bbox_fa[1]

    bbox_en = draw.textbbox((0, 0), text_en, font=font)
    w_en = bbox_en[2] - bbox_en[0]
    h_en = bbox_en[3] - bbox_en[1]

    # Layout Config
    # Explicit gap between lines
    line_spacing = int(font_size * 0.4) if bidi_fa else 0
    total_text_w = max(w_fa, w_en)
    total_text_h = h_fa + h_en + line_spacing

    # Icon config (Matches full height of text block)
    icon_size = int(total_text_h * 0.95)
    icon = get_telegram_icon(icon_size)

    margin = 35
    gap = 20
    pad_x, pad_y = 20, 15

    # Block Size
    content_w = icon_size + gap + total_text_w
    content_h = max(icon_size, total_text_h)

    # Global Position (Bottom Right)
    end_x = base.width - margin
    start_x = end_x - content_w
    center_y = base.height - margin - (content_h // 2)

    # --- CAPSULE BACKGROUND ---
    cap_x1 = start_x - pad_x
    cap_y1 = center_y - (content_h//2) - pad_y
    cap_x2 = end_x + pad_x
    cap_y2 = center_y + (content_h//2) + pad_y

    # Draw Capsule
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(
            [cap_x1, cap_y1, cap_x2, cap_y2], radius=25, fill=(0, 0, 0, 140))
    else:
        draw.rectangle([cap_x1, cap_y1, cap_x2, cap_y2], fill=(0, 0, 0, 140))

    # Draw Icon (Left side of capsule)
    icon_y = center_y - (icon_size // 2)
    if icon:
        txt_layer.paste(icon, (start_x, icon_y), icon)

    # Draw Text Lines (Right side of icon)
    text_block_x = start_x + icon_size + gap

    # Vertical position
    text_start_y = center_y - (total_text_h // 2)

    if bidi_fa:
        # Draw Persian (Top Line)
        draw.text((text_block_x, text_start_y), bidi_fa,
                  font=font, fill=(255, 255, 255, 255))
        # Draw English (Bottom Line)
        draw.text((text_block_x, text_start_y + h_fa + line_spacing),
                  text_en, font=font, fill=(255, 255, 255, 255))
    else:
        # Draw English Only (Centered Vertically)
        y_centered = center_y - (h_en // 2) - 4
        draw.text((text_block_x, y_centered), text_en,
                  font=font, fill=(255, 255, 255, 255))

    return Image.alpha_composite(base, txt_layer).convert("RGB")


def send_to_telegram(image, loc_fa, loc_en):
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: Bot token missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    byte_io = io.BytesIO()
    image.save(byte_io, 'JPEG', quality=95)
    byte_io.seek(0)

    caption = f"( صبا رسانه  ||  \u200E@saba_rasanehh )\n\n📍 {loc_fa}\n📍 {loc_en}"

    print("🚀 Sending to Telegram...")
    try:
        resp = requests.post(url, files={'photo': byte_io}, data={
                             'chat_id': TELEGRAM_CHANNEL_ID, 'caption': caption})
        print("✅ Sent!" if resp.status_code ==
              200 else f"❌ Telegram Error: {resp.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")


if __name__ == "__main__":
    p_data = get_dynamic_prompt()
    img = generate_image(p_data["text"])
    if img:
        img = add_watermark(img)
        send_to_telegram(img, p_data["fa"], p_data["en"])
