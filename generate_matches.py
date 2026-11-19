import json
import os
import re
from datetime import datetime, timedelta
import requests
import pytz

from poster_maker import create_poster

# --- টাইমজোন এবং টাইম কনফিগারেশন ---
BD = pytz.timezone("Asia/Dhaka")
NOW_BD = datetime.now(BD)
TODAY_BD = NOW_BD.date()
END_DATE = NOW_BD + timedelta(hours=48)

# --- এপিআই কনফিগারেশন ---
SONYLIV_API = os.getenv("SonyLiv_API")
FANCEODE_API = os.getenv("FANCEODE_API")
TAPMAD_API = os.getenv("TAPMAD_API")
SPORTS1_API = os.getenv("SPORTS1_API") 

DEFAULT_IMAGE = "https://raw.githubusercontent.com/samnite2290/img/gh-pages/HOME/HOME-LIVE-EVENT.png"
SUBTITLE_SUFFIX = " | Select 🅻🅸🆅🅴 🆂🅿🅾🆁🆃🆂 Button, Share Our Apps With Your Friends & Family."

GITHUB_USER = "samnite2290"
GITHUB_REPO = "PosterDATA" 
GITHUB_BRANCH = "main"

# --- লিগ এবং স্পোর্টস ম্যাপিং ---
IMPORTANT_LEAGUES = ["world cup", "nations league", "ipl", "bpl", "psl", "premier league", "champions league", "la liga", "test", "odi", "t20", "afc", "big bash", "pakistan", "sri lanka", "india", "bangladesh"]

FOOTBALL_LEAGUES = {
    "premier league":   ("🏆 ENGLISH ⚽ PREMIER LEAGUE 2026/27", "TNT 1"),
    "la liga":          ("🏆 SPANISH ⚽ LA LIGA 2026/27",       "SonyLiv"),
    "bundesliga":       ("🏆 GERMAN ⚽ BUNDESLIGA 2026/27",      "SonyLiv"),
    "serie a":          ("🏆 ITALIAN ⚽ SERIE A 2026/27",        "SonyLiv"),
    "ligue 1":          ("🏆 FRENCH ⚽ LIGUE 1 2026/27",         "SonyLiv"),
    "champions league": ("🏆 UEFA ⚽ CHAMPIONS LEAGUE 2026/27",  "SonyLiv"),
    "europa league":    ("🏆 UEFA ⚽ EUROPA LEAGUE 2026/27",     "SonyLiv"),
    "nations league":   ("🏆 UEFA ⚽ NATIONS LEAGUE 2026/27",    "SonyLiv"),
    "fifa world cup":   ("🏆 FIFA ⚽ WORLD CUP 2026",            "Sports"),
    "friendly":         ("🏆 Friendly Match ⚽ 2026",            "Sports"),
    "afc":              ("🏆 AFC ⚽ ASIAN CUP 2026",             "Sports"),
}

CRICKET_LEAGUES = {
    "t20i":      ("🏏 ICC MEN'S T20I CRICKET 2026",    "Fancode"),
    "t20":       ("🏏 T20 CRICKET 2026",               "Fancode"),
    "t10":       ("🏏 T10 CRICKET 2026",               "Fancode"),
    "odi":       ("🏏 ODI CRICKET 2026",               "Fancode"),
    "test":      ("🏏 TEST CRICKET 2026",              "Fancode"),
    "world cup": ("🏆 ICC 🏏 MEN'S T20 WORLD CUP 2026", "Willow"),
    "ipl":       ("🏏 INDIAN PREMIER LEAGUE 2026",     "SonyLiv"),
    "bbl":       ("🏏 BIG BASH LEAGUE 2026",           "SonyLiv"),
    "psl":       ("🏏 PSL 2026",                       "Tapmad"),
    "bpl":       ("🏏 BPL 2026",                       "Sports"),
    "nepal":     ("🏏 NEPAL PREMIER LEAGUE 2026",      "Fancode"),
}

POPULAR_KEYWORDS = ["bangladesh", "pakistan", "india", "bpl", "psl", "ipl", "world cup", "asia cup", "champions trophy", "premier league", "la liga", "champions league", "real madrid", "barcelona", "manchester", "liverpool", "arsenal", "chelsea", "bayern", "psg", "juventus", "brazil", "argentina", "kolkata", "mumbai", "chennai", "karachi", "lahore", "dhaka", "comilla", "brisbane", "sydney", "melbourne", "perth", "hobart", "women", "inter", "nations league", "afc", "awards", "sri lanka"]

# এখানে Golf, F1, Tennis ইত্যাদি বাদ দেওয়ার জন্য কীওয়ার্ড যুক্ত করা হয়েছে
IGNORE_SPORTS = ["doubles", "atp", "wta", "tur", "turin", "day 1", "day 2", "day 3", "day 4", "race", "practice", "qualifying", "grand prix", "tennis", "golf", "formula", "motorsports", "circuit", "round of 16", "quarter-final", "quarter final", "semi-final", "semi final"]

def format_team_name(name):
    formatted = name
    formatted = re.sub(r'\bWomen\b', '(W)', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bMen\b', '(M)', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bU(\d+)\b', r'(U\1)', formatted, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', formatted).strip()

def fetch_json(url, headers=None):
    if not url: 
        return []
    url = url.strip() # %0A বা নতুন লাইন এরর ফিক্স করার জন্য
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching from {url}: {e}")
        return []

def bst_str(dt):
    return dt.strftime("%d-%m-%Y-%I:%M 00 %p").lower()

def calc_multiple_time(sport, fmt, start_bd):
    if sport == "football": return start_bd + timedelta(minutes=60) # 45m + 15m break
    if fmt == "T20": return start_bd + timedelta(minutes=105)
    if fmt == "T10": return start_bd + timedelta(minutes=55)
    if fmt == "ODI": return start_bd + timedelta(minutes=240)
    if fmt == "Test": return start_bd + timedelta(minutes=150) 
    return start_bd + timedelta(minutes=60)

def get_poster_link(t1, t2, sub_name, fmt, sport, start):
    try:
        t1_safe = re.sub(r'[^a-zA-Z0-9]', '_', t1)
        date_str = start.strftime("%Y%m%d")
        
        if t2:
            t2_safe = re.sub(r'[^a-zA-Z0-9]', '_', t2)
            filename = f"{sport}_{t1_safe}_vs_{t2_safe}_{date_str}.png"
        else:
            filename = f"{sport}_{t1_safe}_{date_str}.png"
        
        sport_type = "Cricket" if sport == "cricket" else "Soccer"
        match_type = fmt if fmt else ""
        
        create_poster(team1=t1, team2=t2, series_name=sub_name, match_type=match_type, output_filename=filename, sport_type=sport_type)
        
        raw_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/posters/{filename}"
        return raw_link
    except Exception as e:
        print(f"Poster Error: {e}")
        return None

def detect_sport(ev, comp):
    s = (ev.get("sport") or ev.get("sportType") or ev.get("event_category") or ev.get("Category") or "").lower()
    c = (comp or "").lower()
    if "cricket" in s or any(x in c for x in ("cricket", "t20", "t10", "odi", "test", "ipl", "bbl", "psl", "bpl", "icc", "nepal")):
        return "cricket"
    return "football"

def guess_format(comp):
    c = (comp or "").lower()
    if "t10" in c: return "T10"
    if "t20" in c: return "T20"
    if "odi" in c or "one day" in c: return "ODI"
    if "test" in c: return "Test"
    return ""

def league_meta(sport, comp):
    c = (comp or "").lower()
    table = CRICKET_LEAGUES if sport == "cricket" else FOOTBALL_LEAGUES
    for key, val in table.items():
        if key in c: return val
    return ("🏏 CRICKET 2026" if sport == "cricket" else "⚽ FOOTBALL 2026", "Fancode" if sport == "cricket" else "T Sports")

def is_popular_and_valid(t1, t2, comp):
    full_text = f"{t1} {t2} {comp}".lower()
    if "tbc" in t1.lower() or "tbc" in t2.lower(): return False
    for word in IGNORE_SPORTS:
        if word in full_text: return False
    for keyword in POPULAR_KEYWORDS:
        if keyword in full_text: return True
    return False

def build_entry(start, t1, t2, comp, channel, sport, api_image=None):
    if not t1: return None
    if not start: return None
    
    # ফিল্টার চেক যুক্ত করা হয়েছে
    if not is_popular_and_valid(t1, t2, comp):
        return None

    sub_name, default_channel = league_meta(sport, comp)
    if not channel or channel == "":
        channel = default_channel
    fmt = guess_format(comp) if sport == "cricket" else ""

    t1_fmt = format_team_name(t1)
    t2_fmt = format_team_name(t2)
    
    if t2_fmt:
        title = f"{t1_fmt} 🆚 {t2_fmt} । Watch on {channel}"
    else:
        title = f"{t1_fmt} । Watch on {channel}"
        
    subtitle = f"{sub_name}{SUBTITLE_SUFFIX}"
    
    poster_url = get_poster_link(t1, t2, sub_name, fmt, sport, start)
    image = api_image if api_image else (poster_url if poster_url else DEFAULT_IMAGE)
    
    date_time = bst_str(start - timedelta(minutes=5))

    is_important = any(k in comp.lower() for k in IMPORTANT_LEAGUES) or any(k in channel.lower() for k in ["sonyliv", "fancode", "tapmad"])
    multiple_on = "On" if is_important else "Off"
    
    multiple_time = ""
    if multiple_on == "On":
        mt_time = calc_multiple_time(sport, fmt, start)
        multiple_time = f"({bst_str(mt_time)})"

    return {
        "Date & Time": date_time,
        "multipleTimeRun": multiple_on,
        "multipleTime": multiple_time,
        "Title": title,
        "Subtitle": subtitle,
        "Image": image,
    }

def process_fancode_api(data):
    entries = []
    if not isinstance(data, dict): return entries # list হলে ক্র্যাশ ঠেকানোর জন্য
    for ev in data.get("matches", []):
        status = ev.get("status", "").lower()
        try:
            start = datetime.strptime(ev["startTime"], "%I:%M:%S %p %d-%m-%Y").replace(tzinfo=BD)
        except:
            continue
            
        if status == "live" and NOW_BD > start + timedelta(hours=2):
            start = NOW_BD + timedelta(minutes=20)
            
        if status == "upcoming" and start > END_DATE:
            continue

        t1, t2 = ev.get("team_1", ""), ev.get("team_2", "")
        comp = ev.get("event_name", "")
        channel = "Fancode"
        api_image = ev.get("src")
        sport = "cricket" if ev.get("event_category", "").lower() == "cricket" else "football"
        
        entry = build_entry(start, t1, t2, comp, channel, sport, api_image)
        if entry: entries.append(entry)
    return entries

def process_tapmad_api(data):
    entries = []
    if not isinstance(data, dict): return entries # list হলে ক্র্যাশ ঠেকানোর জন্য
    for ev in data.get("Matches", []):
        status = ev.get("Status", "").lower()
        try:
            start = datetime.strptime(ev["EventStartDate"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=BD)
        except:
            continue
            
        if status == "live" and NOW_BD > start + timedelta(hours=2):
            start = NOW_BD + timedelta(minutes=20)
            
        if status == "upcoming" and start > END_DATE:
            continue

        video_name = ev.get("VideoName", "")
        if " vs " in video_name:
            t1, t2 = video_name.split(" vs ", 1)
        else:
            t1, t2 = video_name, ""
            
        comp = ev.get("CategoryName", "")
        stage = ev.get("StageName", "")
        channel = "Tapmad"
        api_image = ev.get("ThumbnailStandard")
        sport = detect_sport(ev, f"{comp} {stage}")
        
        entry = build_entry(start, t1.strip(), t2.strip(), comp, channel, sport, api_image)
        if entry: entries.append(entry)
    return entries

def process_sports1_api(data):
    entries = []
    events = data if isinstance(data, list) else data.get("events", [])
    
    for ev in events:
        status = ev.get("status", "").lower()
        info = ev.get("eventInfo", {})
        try:
            start = datetime.strptime(info["startTime"], "%d/%m/%Y %I:%M:%S %p").replace(tzinfo=BD)
        except:
            continue
            
        if status == "live" and NOW_BD > start + timedelta(hours=2):
            start = NOW_BD + timedelta(minutes=20)
            
        if status == "upcoming" and start > END_DATE:
            continue

        t1 = info.get("teamA", "")
        t2 = info.get("teamB", "")
        comp = ev.get("Category", "") or info.get("eventName", "")
        
        streams = ev.get("streams", [])
        channel = streams[0].get("channel_name", "Sports") if streams else "Sports"
        
        api_image = None # Sports1 API থেকে ইমেজ নেওয়া হবে না
        sport = detect_sport(ev, comp)
        
        entry = build_entry(start, t1, t2, comp, channel, sport, api_image)
        if entry: entries.append(entry)
    return entries

def main():
    all_results = []
    
    if FANCEODE_API:
        data = fetch_json(FANCEODE_API)
        all_results.extend(process_fancode_api(data))
        
    if TAPMAD_API:
        data = fetch_json(TAPMAD_API)
        all_results.extend(process_tapmad_api(data))
        
    if SPORTS1_API:
        data = fetch_json(SPORTS1_API)
        all_results.extend(process_sports1_api(data))

    seen = set()
    unique_results = []
    for entry in all_results:
        key = (entry["Title"], entry["Date & Time"])
        if key not in seen:
            seen.add(key)
            unique_results.append(entry)
            
    unique_results.sort(key=lambda x: datetime.strptime(x["Date & Time"], "%d-%m-%Y-%I:%M 00 %p"))

    gap = "\n" * 200
    json_output = json.dumps(unique_results, ensure_ascii=False, indent=2)
    
    with open("notifications.json", "w", encoding="utf-8") as f:
        f.write("[\n" + gap + json_output[1:])
        
    print(f"Generated notifications.json with {len(unique_results)} entries.", flush=True)

if __name__ == "__main__":
    main()
