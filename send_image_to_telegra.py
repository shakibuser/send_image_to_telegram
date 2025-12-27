import requests
import io
import random
import json
import os
import sys
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# --- Load Configuration ---


def load_config():
    """
    Loads configuration. 
    Priority 1: Environment Variables (For GitHub Actions/Cloud)
    Priority 2: config.json (For Local Run)
    """
    config = {}

    # 1. Try Environment Variables first
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        config["telegram_bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN")
        config["telegram_channel_id"] = os.environ.get("TELEGRAM_CHANNEL_ID")
        config["watermark_text"] = os.environ.get(
            "WATERMARK_TEXT", "saba_rasanehh@")
        return config

    # 2. Try config.json
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: Configuration not found (No Env Vars and no 'config.json').")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in 'config.json'.")
        sys.exit(1)


CONFIG = load_config()

# --- Constants from Config ---
TELEGRAM_BOT_TOKEN = CONFIG.get("telegram_bot_token")
TELEGRAM_CHANNEL_ID = CONFIG.get("telegram_channel_id")
WATERMARK_TEXT = CONFIG.get("watermark_text", "saba_rasanehh@")

# --- Dynamic Prompt Components ---

# 1. Subjects (Updated with Iranian & Asian Landmarks)
SUBJECTS = [
    # --- Iran ---
    {"p": "The majestic ruins of Persepolis (Takht-e Jamshid) at sunset, ancient Persian architecture, stone columns, dramatic lighting",
     "fa": "تخت جمشید", "en": "Persepolis, Iran"},
    {"p": "The Ziggurat of Chogha Zanbil, ancient Elamite complex, brick texture, golden hour sunlight, historical atmosphere",
        "fa": "زیگورات چغازنبیل", "en": "Chogha Zanbil, Iran"},
    {"p": "The ancient Arg-e Bam citadel, massive adobe fortress, desert sunset, intricate mudbrick details",
        "fa": "ارگ بم", "en": "Arg-e Bam, Iran"},
    {"p": "Naqsh-e Jahan Square in Isfahan, turquoise domes of Imam Mosque, Ali Qapu Palace, reflection in the central pool",
        "fa": "میدان نقش جهان", "en": "Naqsh-e Jahan Sq, Isfahan"},
    {"p": "Si-o-se-pol bridge in Isfahan at night, illuminated arches reflecting in the Zayandeh Rood river, romantic atmosphere",
        "fa": "سی‌وسه‌پل", "en": "Si-o-se-pol, Isfahan"},
    {"p": "Mount Damavand covered in snow, volcanic peak rising above clouds, wild poppies in foreground, majestic view",
        "fa": "کوه دماوند", "en": "Mount Damavand, Iran"},
    {"p": "Nasir al-Mulk Mosque (Pink Mosque) in Shiraz, morning light through stained glass, colorful patterns on carpet",
     "fa": "مسجد نصیرالملک", "en": "Pink Mosque, Shiraz"},
    {"p": "The Kaluts of Shahdad Desert (Lut Desert) at sunrise, strange sand formations, vast landscape, national geographic style",
     "fa": "کلوت‌های شهداد", "en": "Lut Desert, Iran"},
    {"p": "Tabatabaei Historical House in Kashan, traditional Persian architecture, stained glass, courtyard with pool",
        "fa": "خانه طباطبایی‌ها", "en": "Tabatabaei House, Kashan"},

    # --- Asia ---
    {"p": "Angkor Wat temple complex in Cambodia at sunrise, reflection in lotus pond, ancient stone carvings, mystical mist",
        "fa": "انگکور وات", "en": "Angkor Wat, Cambodia"},
    {"p": "Limestone karsts of Ha Long Bay in Vietnam, emerald waters, traditional junk boat sailing, misty mountains",
        "fa": "خلیج ها لونگ", "en": "Ha Long Bay, Vietnam"},
    {"p": "Fushimi Inari Taisha shrine in Kyoto Japan, path of thousands of red torii gates, forest background",
        "fa": "معبد فوشیمی ایناری", "en": "Fushimi Inari, Japan"},
    {"p": "The Great Wall of China winding through autumn mountains, sunrise, ancient fortification, majestic view",
        "fa": "دیوار بزرگ چین", "en": "Great Wall of China"},
    {"p": "Gardens by the Bay in Singapore, Supertree Grove at night, neon lights, futuristic garden, lush greenery",
        "fa": "باغ‌های خلیج", "en": "Gardens by the Bay, Singapore"},
    {"p": "The ancient temples of Bagan in Myanmar, hot air balloons floating at sunrise, golden pagodas, dreamy atmosphere",
        "fa": "معابد باگان", "en": "Bagan, Myanmar"},
    {"p": "The Forbidden City in Beijing, snow covering golden roofs, intricate red palace details, imperial history",
        "fa": "شهر ممنوعه", "en": "Forbidden City, China"},
    {"p": "Mount Fuji with cherry blossoms (Sakura) in the foreground, lake reflection, snow-capped peak, serene",
     "fa": "کوه فوجی", "en": "Mount Fuji, Japan"},
    {"p": "The Taj Mahal in India, white marble mausoleum, symmetrical reflection, soft morning mist, iconic landmark",
        "fa": "تاج محل", "en": "Taj Mahal, India"},
    {"p": "Petra in Jordan, The Treasury (Al-Khazneh) carved into red sandstone cliff, dramatic shadows, desert canyon",
     "fa": "پترا", "en": "Petra, Jordan"},
    {"p": "Arashiyama Bamboo Grove in Kyoto, towering green bamboo stalks, sunlight filtering through, path leading forward",
        "fa": "جنگل بامبو آراشیاما", "en": "Bamboo Grove, Japan"},

    # --- General Beautiful Locations ---
    {"p": "A cozy rainy street in Paris at night, reflection on wet cobblestones, glowing cafe lights",
        "fa": "خیابان بارانی در پاریس", "en": "Paris, France"},
    {"p": "Santorini, Greece, white buildings with blue domes, vibrant pink bougainvillea flowers, Aegean Sea view",
        "fa": "سانتورینی", "en": "Santorini, Greece"},
    {"p": "Venice canals at sunset, gondola, old architecture, reflection in water, romantic atmosphere",
        "fa": "ونیز", "en": "Venice, Italy"},
    {"p": "A futuristic cyberpunk city street, neon signs, rain, flying cars, high tech architecture",
        "fa": "شهر سایبرپانک", "en": "Cyberpunk City"},
    {"p": "A mystical library with floating books, dust motes dancing in light beams, fantasy art style",
        "fa": "کتابخانه جادویی", "en": "Magical Library"}
]

# 2. Styles/Mediums (How it looks)
STYLES = [
    "cinematic lighting, photorealistic, 8k",
    "digital art, vibrant colors, sharp focus",
    "oil painting style, textured brushstrokes, artistic",
    "watercolor painting, soft edges, dreamy",
    "cyberpunk style, neon lights, high contrast",
    "studio photography, professional lighting, crisp details",
    "anime style, makoto shinkai aesthetic, highly detailed",
    "vintage polaroid style, nostalgic, film grain",
    "concept art, fantasy style, epic composition",
    "national geographic style, nature photography"
]

# 3. Time/Weather/Atmosphere (The mood)
ATMOSPHERES = [
    "during a golden sunset",
    "under a dramatic stormy sky",
    "in the early morning mist",
    "at night with a bright full moon",
    "during a heavy rain shower",
    "bathed in soft warm sunlight",
    "in a snowy winter blizzard",
    "during the blue hour",
    "with dramatic shadows and light beams",
    "under the northern lights"
]


def get_dynamic_prompt():
    """Builds a random prompt from components."""
    subj = random.choice(SUBJECTS)
    style = random.choice(STYLES)
    atmosphere = random.choice(ATMOSPHERES)

    # Combine components: Subject + Atmosphere + Style
    full_prompt = f"{subj['p']}, {atmosphere}, {style}, masterpiece, trending on artstation."

    return {
        "text": full_prompt,
        "loc_fa": subj['fa'],
        "loc_en": subj['en']
    }


def generate_image(prompt):
    """
    Generates an image using Pollinations.ai (Free, High Quality, No Token needed).
    """
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(0, 1000000)
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&seed={seed}&nologo=true&model=flux"

    print(f"🎨 Generating image via Pollinations: {prompt[:40]}...")

    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            print("✅ Image generated successfully!")
            return Image.open(io.BytesIO(response.content))
        else:
            print(
                f"❌ Error generating image: {response.status_code} - {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ Connection error during generation: {e}")
        return None


def get_telegram_icon(size):
    """Downloads and prepares the Telegram icon."""
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/480px-Telegram_logo.svg.png"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            icon = Image.open(io.BytesIO(response.content)).convert("RGBA")
            if hasattr(Image, "Resampling"):
                resample = Image.Resampling.LANCZOS
            else:
                resample = Image.LANCZOS
            icon = icon.resize((size, size), resample)
            return icon
    except Exception as e:
        print(f"⚠️ Could not download icon, using fallback: {e}")

    # Fallback
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.ellipse((0, 0, size, size), fill="#24A1DE")
    draw.polygon([(size*0.2, size*0.5), (size*0.8, size*0.2),
                 (size*0.5, size*0.8)], fill="white")
    return icon


def add_watermark(image):
    """Adds a professional watermark with Telegram icon to the image."""
    base_image = image.convert("RGBA")
    txt_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Process Arabic/Persian text
    reshaped_text = arabic_reshaper.reshape(WATERMARK_TEXT)
    bidi_text = get_display(reshaped_text)

    try:
        # Smaller font size (width / 70 for very subtle look)
        font_size = int(image.width / 70)
        font = ImageFont.truetype("tahoma.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            print("⚠️ Fonts not found, using default.")
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    icon_size = int(text_height * 1.5)
    icon = get_telegram_icon(icon_size)

    # Icon is 100% Opacity (No transparency modification)

    margin_x = 30
    margin_y = 30
    gap = 12

    text_x = image.width - margin_x - text_width
    icon_x = text_x - gap - icon_size

    max_h = max(text_height, icon_size)
    center_y = image.height - margin_y - (max_h // 2)

    icon_y = center_y - (icon_size // 2)
    text_y = center_y - (text_height // 2)

    # 1. Paste Icon (100% Opacity)
    if icon:
        txt_layer.paste(icon, (icon_x, icon_y), icon)

    # 2. Text Shadow (Very light, low opacity)
    shadow_color = (0, 0, 0, 40)  # Very faint shadow
    draw.text((text_x + 1, text_y + 1), bidi_text,
              font=font, fill=shadow_color)

    # 3. Main Text (White, 45% Opacity -> ~115/255)
    text_color = (255, 255, 255, 115)
    draw.text((text_x, text_y), bidi_text, font=font, fill=text_color)

    return Image.alpha_composite(base_image, txt_layer).convert("RGB")


def send_to_telegram(image, loc_fa, loc_en):
    """Sends the image to the Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)

    files = {'photo': ('image.jpg', img_byte_arr)}

    # Caption with LRM mark (\u200E) for correct RTL/LTR mix
    caption_text = f"( صبا رسانه  ||  \u200E@saba_rasanehh )\n\n📍 {loc_fa}\n📍 {loc_en}"

    data = {'chat_id': TELEGRAM_CHANNEL_ID, 'caption': caption_text}

    print("🚀 Sending to Telegram...")
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            print("✅ Image sent successfully!")
        else:
            print(f"❌ Error sending to Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ Warning: Configuration incomplete. Check Env Vars or config.json")

    # Generate dynamic prompt
    prompt_data = get_dynamic_prompt()

    prompt_text = prompt_data["text"]
    location_fa = prompt_data["loc_fa"]
    location_en = prompt_data["loc_en"]

    generated_img = generate_image(prompt_text)

    if generated_img:
        final_img = add_watermark(generated_img)
        send_to_telegram(final_img, location_fa, location_en)
