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
HADITH_API_KEY = os.getenv("HADITH_API_KEY")
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

def get_random_hadith():
    url = (
        "https://www.hadithapi.com/api/hadiths"
        f"?apiKey={HADITH_API_KEY}"
        "&book=sahih-bukhari"
        "&status=Sahih"
        "&paginate=1"
    )
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or not data.get("hadiths", {}).get("data"):
        raise Exception(f"Hadith API error: {data}")

    hadith = random.choice(data["hadiths"]["data"])

    ar_text = hadith.get("hadithArabic", "").strip()
    en_text = hadith.get("hadithEnglish", "").strip()
    number = hadith.get("hadithNumber", "N/A")
    book_name = hadith.get("book", {}).get("bookName", "Unknown Book")
    status = hadith.get("status", "Unknown Status")
    ref = f"{status} – {book_name} – Hadith #{number}"
    return ar_text, en_text, ref



def get_adaptive_font_size(text, font_path, max_width, max_height, min_size=20, max_size=80):
    """Dynamically adjust font size to fit text within bounds"""
    best_size = min_size
    
    for size in range(min_size, max_size + 1, 2):
        try:
            font = ImageFont.truetype(font_path, size)
            # Create temporary draw to measure text
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Calculate text dimensions with word wrapping
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                
                if line_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Single word is too long, force it
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate total height
            total_height = 0
            for line in lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_height += line_height + 10  # 10px line spacing
            
            if total_height <= max_height:
                best_size = size
            else:
                break
                
        except Exception:
            break
    
    return best_size

def draw_adaptive_text(draw, text, font_path, img_width, img_height, y_start, max_height_ratio=0.25, fill="white", stroke_width=2, stroke_fill="black"):
    """Draw text that adapts to image dimensions with outline for better readability"""
    max_width = int(img_width * 0.9)  # 90% of image width
    max_height = int(img_height * max_height_ratio)  # Percentage of image height
    
    # Get optimal font size
    font_size = get_adaptive_font_size(text, font_path, max_width, max_height)
    font = ImageFont.truetype(font_path, font_size)
    
    # Wrap text to fit within width
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw each line centered with outline
    current_y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        x = (img_width - line_width) / 2
        
        # Draw outline for better readability
        for adj in range(-stroke_width, stroke_width + 1):
            for adj2 in range(-stroke_width, stroke_width + 1):
                draw.text((x + adj, current_y + adj2), line, font=font, fill=stroke_fill)
        
        # Draw main text
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += line_height + 10
    
    return current_y

def create_image(arabic_verse, english_verse, reference):
    backgrounds = ["background1.jpg", "background2.jpg", "background3.jpg", "background4.jpg", "background5.jpg", "background6.jpg"]
    chosen_bg = random.choice(backgrounds)
    
    img = Image.open(os.path.join("images", chosen_bg)).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    img_width, img_height = img.size
    print(f"📏 Image dimensions: {img_width}x{img_height}")
    
    # Process Arabic text properly
    reshaped = arabic_reshaper.reshape(arabic_verse)
    bidi_arabic = get_display(reshaped)
    
    print("🔤 Original Arabic:", arabic_verse)
    print("🔤 Reshaped Arabic:", reshaped)
    print("🔤 BIDI Arabic:", bidi_arabic)
    
    # Calculate layout based on image dimensions
    if img_width > img_height:  # Landscape
        arabic_start_y = int(img_height * 0.15)  # Start at 15% from top
        arabic_max_height = 0.3  # Use 30% of height for Arabic
        english_max_height = 0.35  # Use 35% of height for English
        reference_y_offset = 40
    else:  # Portrait or square
        arabic_start_y = int(img_height * 0.2)   # Start at 20% from top
        arabic_max_height = 0.25  # Use 25% of height for Arabic
        english_max_height = 0.3   # Use 30% of height for English
        reference_y_offset = 30
    
    # Draw Arabic text
    y = draw_adaptive_text(
        draw, arabic_verse, "fonts/Amiri-Regular.ttf", 
        img_width, img_height, arabic_start_y, 
        arabic_max_height, fill="white", stroke_width=2, stroke_fill="black"
    )
    
    # Add spacing between Arabic and English
    y += 30
    
    # Draw English text
    y = draw_adaptive_text(
        draw, english_verse, "fonts/Amiri-Regular.ttf", 
        img_width, img_height, y, 
        english_max_height, fill="white", stroke_width=1, stroke_fill="black"
    )
    
    # Draw reference with smaller max height
    y += reference_y_offset
    draw_adaptive_text(
        draw, reference, "fonts/Amiri-Regular.ttf", 
        img_width, img_height, y, 
        0.15, fill="lightgray", stroke_width=1, stroke_fill="black"
    )
    
    out_path = "generated/output.jpg"
    os.makedirs("generated", exist_ok=True)
    img.save(out_path, quality=95)  # High quality output
    return out_path

def post_to_facebook(img_path, caption):
    # Step 1: Upload the image as unpublished
    upload_url = f"https://graph.facebook.com/v23.0/{PAGE_ID}/photos"
    with open(img_path, 'rb') as img_file:
        files = {'source': img_file}
        data = {
            'published': 'false',
            'access_token': ACCESS_TOKEN
        }
        upload_response = requests.post(upload_url, files=files, data=data)
        upload_result = upload_response.json()
        
        if "error" in upload_result:
            print("❌ Upload Error:", upload_result["error"]["message"])
            return upload_result
        
        photo_id = upload_result["id"]
        print(f"📸 Uploaded photo ID: {photo_id}")
    
    # Step 2: Create a post with that uploaded photo
    post_url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed"
    post_data = {
        'message': caption,
        'attached_media': f'[{{"media_fbid":"{photo_id}"}}]',
        'access_token': ACCESS_TOKEN
    }
    
    post_response = requests.post(post_url, data=post_data)
    post_result = post_response.json()
    
    if post_response.status_code==200:
        print("✅ Successfully posted to Facebook feed.")
    else:
        print("❌ Post Error:", post_result["error"]["message"])    
    return post_result


def main():
    if random.random() < 0.5:
        print("📖 Posting a Quran verse.")
        ar_text, en_text, ref = get_random_verse()
    else:
        print("📜 Posting a Hadith from Sahih Bukhari.")
        ar_text, en_text, ref = get_random_hadith()
    
    img_path = create_image(ar_text, en_text, ref)
    caption = f"{en_text}\n\n{ref}"
    #result = post_to_facebook(img_path, caption)


if __name__ == "__main__":
    main()