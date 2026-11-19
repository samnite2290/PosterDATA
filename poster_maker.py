import json
import os
import re
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cairosvg 
import pycountry

# --- কনফিগারেশন ---
POSTER_WIDTH = 1200
POSTER_HEIGHT = 600
FONT_BOLD_PATH = "assets/fonts/Oswald-Bold.ttf" 
FONT_REGULAR_PATH = "assets/fonts/Oswald-Regular.ttf"
FONT_TEAM_PATH = "assets/fonts/Arimo-Bold.ttf" 

OUTPUT_DIR = "posters"
LOGO_BASE_DIR = "assets/Logo"
COUNTRY_LOGO_DIR = "assets/Logo-Country" 
DEFAULT_LOGO_PATH = "assets/Logo.png" 
APP_LOGO_PATH = "assets/Logo.png" 

os.makedirs(OUTPUT_DIR, exist_ok=True)

IGNORE_WORDS = ["women", "w", "fc", "afc", "cf", "sc", "club", "u19", "u21", "u23", "vs", "match", "round", "of", "day", "practice", "men"]

def clean_name(name):
    name = name.lower()
    for word in IGNORE_WORDS:
        name = re.sub(r'\b' + re.escape(word) + r'\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name).strip()

def format_team_name(name):
    if not name: return ""
    formatted = name
    formatted = re.sub(r'\bWomen\b', '(W)', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bMen\b', '(M)', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bU(\d+)\b', r'(U\1)', formatted, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', formatted).strip()

def get_svg_image(svg_path):
    try:
        png_data = cairosvg.svg2png(url=svg_path)
        return Image.open(BytesIO(png_data)).convert("RGBA")
    except Exception as e:
        print(f"SVG Error: {e}")
        return None

def find_logo_path(team_name):
    team_clean = clean_name(team_name)
    if not team_clean: return None
    best_match = None
    
    if not os.path.exists(LOGO_BASE_DIR): return None
    
    for root, dirs, files in os.walk(LOGO_BASE_DIR):
        for file in files:
            if file.lower().endswith(".png"):
                file_name_clean = clean_name(file.lower().replace(".png", ""))
                if team_clean == file_name_clean:
                    return os.path.join(root, file)
                if team_clean in file_name_clean or file_name_clean in team_clean:
                    best_match = os.path.join(root, file)
    return best_match

def get_team_logo(team_name):
    """
    রিটার্ন করে: (Image, is_flag)
    """
    if not team_name:
        # ডিফল্ট লোগো রিটার্ন করবে
        if os.path.exists(DEFAULT_LOGO_PATH):
            return Image.open(DEFAULT_LOGO_PATH).convert("RGBA"), False
        img = Image.new("RGBA", (300, 300), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, 300, 300), fill=(255, 255, 255, 50))
        return img, False

    # ১. pycountry দিয়ে দেশের নাম খুঁজে বের করা
    team_clean = clean_name(team_name)
    if team_clean:
        try:
            country = pycountry.countries.search_fuzzy(team_clean)
            if country:
                code = country[0].alpha_2.lower()
                svg_path = os.path.join(COUNTRY_LOGO_DIR, f"{code}.svg")
                if os.path.exists(svg_path):
                    img = get_svg_image(svg_path)
                    if img: return img, True
        except LookupError:
            pass

    # ২. ক্লাব লোগো (PNG) খুঁজবে
    path = find_logo_path(team_name)
    if path and os.path.exists(path):
        return Image.open(path).convert("RGBA"), False
    
    # ৩. ডিফল্ট লোগো
    if os.path.exists(DEFAULT_LOGO_PATH):
        return Image.open(DEFAULT_LOGO_PATH).convert("RGBA"), False
        
    img = Image.new("RGBA", (300, 300), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 300, 300), fill=(255, 255, 255, 50))
    return img, False

def get_font_size_to_fit(text, font_path, max_width, max_size=75):
    size = max_size
    while size > 20:
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            return ImageFont.load_default()
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            return font
        size -= 5
    try:
        return ImageFont.truetype(font_path, 20)
    except:
        return ImageFont.load_default()

def create_poster(team1, team2, series_name, match_type, output_filename, sport_type="Soccer"):
    print(f"Generating poster for {team1} vs {team2}...")
    
    bg_path = "assets/Football-BG.png" if sport_type.lower() == "soccer" else "assets/Cricket-BG.png"
    if not os.path.exists(bg_path): bg_path = "assets/bg_main.png"
        
    if os.path.exists(bg_path):
        canvas = Image.open(bg_path).convert("RGBA")
        canvas = canvas.resize((POSTER_WIDTH, POSTER_HEIGHT))
        canvas = ImageEnhance.Brightness(canvas).enhance(0.5)
    else:
        canvas = Image.new("RGBA", (POSTER_WIDTH, POSTER_HEIGHT), (20, 20, 30, 255))

    draw = ImageDraw.Draw(canvas)

    try:
        font_match = ImageFont.truetype(FONT_BOLD_PATH, 30)
        font_vs = ImageFont.truetype(FONT_TEAM_PATH, 90) 
        font_powered = ImageFont.truetype(FONT_REGULAR_PATH, 25)
        font_teams = ImageFont.truetype(FONT_TEAM_PATH, 65) 
    except:
        font_match = font_vs = font_powered = font_teams = ImageFont.load_default()

    # ১. সিরিজের নাম
    series_clean = re.sub(r'[^\w\s\-/\.]', '', series_name).strip().upper()
    font_series_fit = get_font_size_to_fit(series_clean, FONT_BOLD_PATH, 1000, 40)
    bbox = draw.textbbox((0, 0), series_clean, font=font_series_fit)
    text_w = bbox[2] - bbox[0]
    draw.text(((POSTER_WIDTH - text_w) / 2 + 2, 22), series_clean, font=font_series_fit, fill="black")
    draw.text(((POSTER_WIDTH - text_w) / 2, 20), series_clean, font=font_series_fit, fill="white")

    # ২. Powered by SAWARID APPS + Logo
    powered_text = "Powered by: SAWARID APPS"
    bbox_p = draw.textbbox((0, 0), powered_text, font=font_powered)
    p_w = bbox_p[2] - bbox_p[0]
    p_h = bbox_p[3] - bbox_p[1]
    
    if os.path.exists(APP_LOGO_PATH):
        app_logo = Image.open(APP_LOGO_PATH).convert("RGBA")
        logo_height = int(p_h * 1.2) 
        logo_width = int(app_logo.width * (logo_height / app_logo.height))
        app_logo = app_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        gap = 10
        total_width = p_w + gap + logo_width
        start_x = (POSTER_WIDTH - total_width) / 2
        
        draw.text((start_x, 75), powered_text, font=font_powered, fill="#CCCCCC")
        logo_y = 75 + (p_h - logo_height) // 2 
        canvas.paste(app_logo, (int(start_x + p_w + gap), int(logo_y)), app_logo)
    else:
        draw.text(((POSTER_WIDTH - p_w) / 2, 75), powered_text, font=font_powered, fill="#CCCCCC")

    # ৩. লোগো/ফ্ল্যাগ বসানো 
    logo1, is_flag1 = get_team_logo(team1)
    logo2, is_flag2 = get_team_logo(team2) if team2 else (None, False)
    
    # ফ্ল্যাগ হলে ৩:২ সাইজ (450x300), ক্লাব লোগো হলে ১:১ সাইজ (300x300)
    size1 = (450, 300) if is_flag1 else (300, 300)
    
    logo1 = logo1.resize(size1, Image.Resampling.LANCZOS)
    
    # টিম ১ বসানো
    x1 = POSTER_WIDTH//4 - size1[0]//2
    y1 = POSTER_HEIGHT//2 - 130
    canvas.paste(logo1, (x1, y1), logo1)
    
    # যদি টিম ২ থাকে
    if team2 and logo2:
        size2 = (450, 300) if is_flag2 else (300, 300)
        logo2 = logo2.resize(size2, Image.Resampling.LANCZOS)
        x2 = 3*POSTER_WIDTH//4 - size2[0]//2
        y2 = POSTER_HEIGHT//2 - 130
        canvas.paste(logo2, (x2, y2), logo2)

    draw = ImageDraw.Draw(canvas)

    # ৪. মাঝখানে VS (যদি টিম ২ থাকে)
    if team2:
        bbox_vs = draw.textbbox((0, 0), "VS", font=font_vs)
        vs_w = bbox_vs[2] - bbox_vs[0]
        draw.text(((POSTER_WIDTH - vs_w) / 2, POSTER_HEIGHT//2 - 60), "VS", font=font_vs, fill="white")

    # ৫. দলের নাম + ১০% ডার্ক ব্যাকগ্রাউন্ড
    team1_fmt = format_team_name(team1)
    team2_fmt = format_team_name(team2)
    
    if team2_fmt:
        team_text = f"{team1_fmt.upper()} vs {team2_fmt.upper()}"
    else:
        team_text = team1_fmt.upper()
    
    font_teams_fit = get_font_size_to_fit(team_text, FONT_TEAM_PATH, 1100, 65)
    bbox_t = draw.textbbox((0, 0), team_text, font=font_teams_fit)
    t_w = bbox_t[2] - bbox_t[0]
    t_h = bbox_t[3] - bbox_t[1]
    
    text_y = POSTER_HEIGHT - 130
    text_x = (POSTER_WIDTH - t_w) / 2
    
    pad_x = 20
    pad_y = 10
    bg_rect = [text_x - pad_x, text_y - pad_y, text_x + t_w + pad_x, text_y + t_h + pad_y]
    
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(bg_rect, fill=(0, 0, 0, 25)) 
    canvas = Image.alpha_composite(canvas, overlay)
    
    draw = ImageDraw.Draw(canvas)

    draw.text((text_x + 2, text_y + 2), team_text, font=font_teams_fit, fill="black")
    draw.text((text_x, text_y), team_text, font=font_teams_fit, fill="white")

    # ৬. ম্যাচের ধরন
    if match_type:
        m_text = match_type.upper()
        bbox_m = draw.textbbox((0, 0), m_text, font=font_match)
        m_w = bbox_m[2] - bbox_m[0]
        draw.text(((POSTER_WIDTH - m_w) / 2, text_y + 70), m_text, font=font_match, fill="#FFD700")

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    canvas.convert("RGB").save(output_path, format="PNG")
    return output_path
