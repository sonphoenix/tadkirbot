import os
import requests
import random
import textwrap
import time
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import arabic_reshaper
from bidi.algorithm import get_display

# Load secrets
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
TOTAL_VERSES = 6236

def get_random_verse():
    verse_id = random.randint(1, TOTAL_VERSES)

    en_url = f"https://api.alquran.cloud/v1/ayah/{verse_id}/en.asad"
    ar_url = f"https://api.alquran.cloud/v1/ayah/{verse_id}/ar"

    en_data = requests.get(en_url).json()
    ar_data = requests.get(ar_url).json()

    if en_data["status"] != "OK" or ar_data["status"] != "OK":
        raise Exception("API error")

    en_ayah = en_data["data"]
    ar_ayah = ar_data["data"]

    en_text = en_ayah["text"]
    ar_text = ar_ayah["text"]
    reference = f"{en_ayah['surah']['englishName']} - Ayah {en_ayah['numberInSurah']}"

    return ar_text, en_text, reference

def draw_centered_text(draw, text, font, img_width, y, fill="white"):
    lines = textwrap.wrap(text, width=50)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (img_width - w) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += h + 10
    return y

def create_image(arabic_verse, english_verse, reference):
    backgrounds = ["background1.jpg", "background2.jpg", "background3.jpg", "background4.jpg"]
    chosen_bg = random.choice(backgrounds)

    img = Image.open(os.path.join("images", chosen_bg)).convert("RGB")
    draw = ImageDraw.Draw(img)

    arabic_font = ImageFont.truetype("fonts/Amiri-Regular.ttf", 48)
    english_font = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
    small_font = ImageFont.truetype("fonts/Amiri-Regular.ttf", 28)

    img_width, _ = img.size
    y = 180

    reshaped = arabic_reshaper.reshape(arabic_verse)
    bidi_arabic = get_display(reshaped)

    y = draw_centered_text(draw, bidi_arabic, arabic_font, img_width, y)
    y += 20
    y = draw_centered_text(draw, english_verse, english_font, img_width, y)
    draw_centered_text(draw, reference, small_font, img_width, y + 30)

    out_path = "generated/output.jpg"
    img.save(out_path)
    return out_path

def post_to_facebook(img_path, caption):
    url = f"https://graph.facebook.com/v23.0/{PAGE_ID}/photos"
    with open(img_path, 'rb') as img_file:
        files = {'source': img_file}
        data = {
            'caption': caption,
            'access_token': ACCESS_TOKEN
        }
        response = requests.post(url, files=files, data=data)
        result = response.json()
        if "error" in result:
            print("❌ Facebook Error:", result["error"]["message"])
        else:
            print("✅ Successfully posted to Facebook.")
        return result

def main():
    ar_text, en_text, ref = get_random_verse()
    img_path = create_image(ar_text, en_text, ref)

    caption = f"{en_text}\n\n{ref}"
    result = post_to_facebook(img_path, caption)


if __name__ == "__main__":
    main()
