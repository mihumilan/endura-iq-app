import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import xml.etree.ElementTree as ET
from fpdf import FPDF
import base64
import struct
import time
import unicodedata
from streamlit_calendar import calendar

st.set_page_config(page_title="Endura IQ", layout="wide", initial_sidebar_state="expanded")

# --- MODUŁ BAZY DANYCH MONGODB (CLOUD) ---
import pymongo
import urllib.parse

@st.cache_resource
def get_database_client():
    password = urllib.parse.quote_plus("2001SOSna!")
    uri = f"mongodb+srv://admin:{password}@cluster0.rruonnh.mongodb.net/?appName=Cluster0"
    return pymongo.MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)

class MongoDBWrapper:
    def __init__(self, client, db_name="tricoach_pro"):
        self.collection = client[db_name]["app_data"]
        
    def __getitem__(self, key):
        doc = self.collection.find_one({"_id": key})
        if doc: return doc.get("value")
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        self.collection.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)
        
    def get(self, key, default=None):
        doc = self.collection.find_one({"_id": key})
        if doc: return doc.get("value", default)
        return default
        
    def __contains__(self, key):
        return self.collection.count_documents({"_id": key}, limit=1) > 0

# Inicjalizacja profesjonalnej bazy w chmurze!
mongo_client = get_database_client()
db = MongoDBWrapper(mongo_client)

# ==========================================
# 1. KONFIGURACJA, TŁUMACZENIA I CSS
# ==========================================
if 'lang' not in st.session_state: st.session_state.lang = 'PL'

TRANSLATIONS = {
    "EN": {
        "Użytkownik": "Username", "Hasło": "Password", "Zaloguj": "Log In", "Wyloguj": "Log Out",
        "MENU": "MENU", "Dashboard": "Dashboard", "Kalendarz": "Calendar", "Wiadomości": "Messages",
        "Statystyki": "Statistics", "Raporty": "Reports", "Fizjologia": "Physiology", 
        "Strefy": "Zones", "Kreator": "Builder", "Plany": "Plans", "Baza": "Database",
        "Dodaj aktywność": "Add Activity", "Dane zawodnika": "Athlete Data", 
        "Bieganie": "Running", "Rower": "Cycling", "Pływanie": "Swimming", "Siłownia": "Strength", "Inne": "Other",
        "Rozgrzewka": "Warm-up", "Interwał": "Interval", "Przerwa": "Rest", "Rozjazd": "Cool-down",
        "Zawodnik:": "Athlete:", "Wybierz zawodnika:": "Select athlete:", "Wszyscy": "All",
        "Cześć": "Hello", "Zgłoś Trening (Upload TCX)": "Submit Workout (Upload TCX)",
        "Wgraj plik z zegarka": "Upload watch file", "Dyscyplina": "Discipline", "Data": "Date",
        "Czas (min)": "Duration (min)", "Dystans (km)": "Distance (km)", "Notatka dla Trenera": "Note for Coach",
        "Samopoczucie": "Feeling", "ZAPISZ TRENING": "SAVE WORKOUT", "Zapisano!": "Saved successfully!",
        "Loguj Wagę Ciała": "Log Body Weight", "Data ważenia": "Weigh-in Date", "Waga (kg)": "Weight (kg)",
        "Zapisz Wagę": "Save Weight", "Zapisano wagę!": "Weight saved!", "Ostatnie Aktywności": "Recent Activities",
        "Analiza": "Analysis", "Brak danych": "No data", "PANEL PLANOWANIA (TRENER)": "PLANNING PANEL (COACH)",
        "Wczytaj Szablon": "Load Template", "Tytuł": "Title", "Instrukcje dla zawodnika": "Instructions for athlete",
        "Dodaj do Planu": "Add to Plan", "Zaplanowano!": "Scheduled successfully!",
        "Nie znaleziono szczegółów. Sprawdź listę zadań.": "Details not found. Check activity list.",
        "Centrum Zarządzania": "Management Center", "Dyscyplina (Wykonanie Planu)": "Compliance (Plan Execution)",
        "Wykres Formy (PMC)": "Fitness Chart (PMC)", "Laboratorium Fizjologiczne": "Physiology Laboratory",
        "Dane Zawodnika i Fizjologia": "Athlete Data & Physiology", "Profil Mocy (CP)": "Power Profile (CP)",
        "Rekordy Biegowe": "Running Records", "Badania & Trendy": "Tests & Trends", "Waga": "Weight",
        "Profil Mocy Rowerowej (Automatyczny)": "Cycling Power Profile (Auto)", "Edytuj Ręcznie": "Edit Manually",
        "Aktualizuj": "Update", "Krzywa Mocy": "Power Curve", "Najlepsze Czasy Biegowe (Personal Bests)": "Running Personal Bests",
        "Edytuj Ręcznie (w sekundach)": "Edit Manually (in seconds)", "Dodaj Wynik Badań": "Add Test Result",
        "Wskaźnik": "Metric", "Wartość": "Value", "Historia:": "History:", "Historia Wagi": "Weight History",
        "Dodaj Wagę Zawodnika": "Add Athlete Weight", "Trend Wagi (kg)": "Weight Trend (kg)",
        "Centrum Raportowania": "Reporting Center", "Dla trenera.": "For coach only.", "Rok": "Year", "Tydzień": "Week",
        "Komentarz Trenera": "Coach's Comment", "Generuj PDF": "Generate PDF", "POBIERZ PDF": "DOWNLOAD PDF",
        "Strefy": "Zones", "Przelicz / Zresetuj": "Calculate / Reset", "Moc": "Power", "Tętno": "Heart Rate",
        "Zapisz Zmiany": "Save Changes", "Zapisano strefy!": "Zones saved!", "Kreator": "Workout Builder",
        "Szablon": "Template", "Załaduj": "Load", "Typ": "Type", "Min": "Min", "Intensywność": "Intensity", "Od": "From",
        "Do": "To", "Nazwa": "Name", "Zapisz": "Save", "RESET DANYCH": "RESET DATA", "Czas": "Time", "Dystans": "Distance",
        "Kadencja": "Cadence", "Tempo": "Pace", "Zaplanowany Trening:": "Planned Workout:", "Instrukcje Trenera:": "Coach Instructions:",
        "Zobacz Rozpiskę": "View Structure", "Pobierz plik .ZWO (Zwift)": "Download .ZWO file (Zwift)",
        "Pobierz plik .FIT (Garmin)": "Download .FIT file (Garmin)", "Tylko opis tekstowy.": "Text description only.", 
        "Przetworzono:": "Processed:", "Dodano!": "Added!", "PLAN": "PLAN", "Zaloguj się": "Sign In", 
        "Nieprawidłowy login lub hasło.": "Invalid username or password.", "Fitness (CTL)": "Fitness (CTL)", 
        "Zmęczenie (ATL)": "Fatigue (ATL)", "Forma (TSB)": "Form (TSB)", "Ważenie z dnia": "Weigh-in from", 
        "Brak wpisów wagi w bazie.": "No weight entries in DB.", "Brak wpisów wagi dla tego zawodnika.": "No weight entries for this athlete.",
        "Dodaj Krok": "Add Step", "Bieg": "Run", "Rower": "Bike", "Pływanie": "Swim", "Pojedynczy Krok": "Single Step", 
        "Seria Interwałów": "Interval Set", "Jednostka": "Unit", "Liczba powtórzeń": "Repetitions", "Praca": "Work", 
        "Odpoczynek": "Rest", "Dodaj Serię": "Add Set", "Wyczyść Kreator": "Clear Builder", "Czas/Dystans": "Time/Dist",
        "Pobierz .FIT i wgraj go na zegarek do folderu GARMIN/NewFiles. Zegarek sam go przetworzy!": "Download .FIT and copy to GARMIN/NewFiles on your watch. It will process automatically!",
        "Dodaj zawody / cel": "Add Race / Goal", "Nazwa zawodów": "Race Name", "Data zawodów": "Race Date", 
        "Dodaj Start": "Add Race", "Dodano zawody!": "Race added!", "Cel:": "Goal:", "dni do startu": "days to go", 
        "dzisiaj!": "today!", "Czat z": "Chat with", "Napisz wiadomość...": "Type a message...",
        "Wykonane Treningi (Licznik)": "Completed Workouts (Streak)", "Podsumowanie aktywności": "Activity Summary",
        "Wybierz rok": "Select Year", "Wybierz miesiąc": "Select Month", "Cały rok": "Whole Year",
        "Czas całkowity": "Total Time", "Dystans całkowity": "Total Distance", "Proporcja czasu wg dyscyplin": "Time Proportion by Discipline",
        "Szczegóły dyscyplin": "Discipline Details", "Brak danych w wybranym okresie.": "No data in selected period.",
        "Brak wykonanych aktywności.": "No completed activities.",
        "Powiąż z planowanym treningiem:": "Link to planned workout:", "Brak (dodaj jako nowy)": "None (add as new)",
        "Zgodność z planem:": "Plan compliance:", "Krzywa Mocy (MMP)": "Power Duration Curve (MMP)",
        "Wszystkie czasy (All-time)": "All-time Best", "Ostatnie 90 dni": "Last 90 days",
        "Biblioteka Planów": "Plan Library", "Przypisz Plan": "Assign Plan", "Kreator Planów": "Plan Builder",
        "Przypisz gotowy plan zawodnikowi": "Assign a ready plan to an athlete", "Brak zapisanych planów w bazie.": "No saved plans in database.",
        "Wybierz Plan": "Select Plan", "Data startu": "Start Date", "Plan przypisany!": "Plan assigned!",
        "Tworzenie Planu (Makro/Mikrocykl)": "Plan Creation (Macro/Microcycle)", "Dzień (np. 1 = start, 2 = kolejny dzień)": "Day (e.g., 1 = start, 2 = next day)",
        "Dodaj Trening do Planu": "Add Workout to Plan", "Zapisz Plan": "Save Plan", "Nazwa Planu (np. 4 tygodnie Baza)": "Plan Name (e.g., 4-week Base)",
        "Najpierw stwórz pojedyncze treningi (szablony) w zakładce Kreator.": "First, create individual workouts (templates) in the Builder tab.",
        "Komentarze do treningu": "Workout Comments", "Dodaj komentarz...": "Add a comment...", "Wyślij": "Send", "Interwały": "Intervals",
        "Mapa trasy GPS": "GPS Route Map", "Lista aktywności": "Activity List", "Czas w strefach": "Time in Zones"
    }
}

def tr(text): return text if st.session_state.lang == "PL" else TRANSLATIONS["EN"].get(text, text)

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        .stApp { background-color: #0A0D12; color: #E2E8F0; font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #11151C; border-right: 1px solid #1F2735; }
        h1, h2, h3, h4 { color: #00E5FF !important; font-weight: 800 !important; letter-spacing: -0.5px; }
        .login-header { text-align: center; margin-bottom: 40px; margin-top: 50px; }
        .login-title { font-size: 56px; font-weight: 900; color: #FFFFFF !important; letter-spacing: 2px; margin-bottom: 0px; text-transform: uppercase; }
        .login-subtitle { color: #00E5FF; font-size: 16px; letter-spacing: 4px; text-transform: uppercase; font-weight: 300; margin-top: -10px; }
        .metric-card { background: linear-gradient(145deg, #131821 0%, #0B0E14 100%); border: 1px solid #1F2735; border-top: 3px solid #00E5FF; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.4); margin-bottom: 15px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .metric-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,229,255,0.15); }
        .metric-val { font-size: 28px; font-weight: 800; color: #FFFFFF; }
        .metric-label { font-size: 11px; color: #8BA1B8; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 5px; font-weight: 600; }
        .race-card { background: linear-gradient(145deg, #2A1D00 0%, #1A1200 100%); border: 1px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 8px 24px rgba(255,215,0,0.15); margin-bottom: 20px; }
        .race-val { font-size: 32px; font-weight: 900; color: #FFD700; text-transform: uppercase; }
        .race-label { font-size: 14px; color: #E2E8F0; letter-spacing: 1px; margin-top: 5px; }
        .tp-summary-card { background: linear-gradient(145deg, #151A23 0%, #0E1218 100%); border: 1px solid #1F2735; border-left: 4px solid #00E5FF; border-radius: 10px; padding: 16px; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 0.9em; }
        .tp-week-title { color: #FFF; font-size: 1.15em; font-weight: 800; border-bottom: 1px solid #1F2735; margin-bottom: 12px; padding-bottom: 8px; }
        .tp-row { display: flex; justify-content: space-between; margin-bottom: 8px; color: #E2E8F0; font-weight: 600;}
        .tp-stat-line { display: flex; justify-content: space-between; color: #8BA1B8; font-size: 0.9em; margin-top: 4px; }
        div.stButton > button { background: linear-gradient(90deg, #00B4D8 0%, #00E5FF 100%); color: #05070A !important; border-radius: 8px; font-weight: 800; border: none; width: 100%; padding: 12px; text-transform: uppercase; letter-spacing: 0.5px; transition: all 0.3s ease; }
        div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,229,255,0.3); }
        div[data-testid="stFileUploader"] { border: 2px dashed #00E5FF; background-color: rgba(0,229,255,0.03); border-radius: 12px; }
        div[data-testid="stExpander"] { border: 1px solid #1F2735 !important; border-radius: 10px !important; background-color: #11151C !important; }
        div[data-testid="stNumberInput"] input:disabled { background-color: #1A202C; color: #64748B; }
        thead tr th { background-color: #00E5FF !important; color: #000 !important; font-weight: 800 !important; }
        tbody tr:nth-of-type(even) { background-color: #11151C; }
        tbody tr:nth-of-type(odd) { background-color: #161B22; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. STRUKTURA BAZY I UŻYTKOWNICY
# ==========================================
ZAWODNICY = ["Jan Kowalski", "Anna Nowak", "Piotr Triathlonista"]
USERS = {"admin": "trener123", "Jan Kowalski": "jan123", "Anna Nowak": "anna123", "Piotr Triathlonista": "piotr123"}
KOLORY_SPORT = {"Pływanie": "#2979FF", "Rower": "#FF1744", "Bieganie": "#00E676", "Siłownia": "#9E9E9E", "Inne": "#FF9100"}
KOLORY_BLOKOW = {"Rozgrzewka": "#558B2F", "Interwał": "#D32F2F", "Przerwa": "#1976D2", "Rozjazd": "#616161"}
ZONE_COLORS = ["#9E9E9E", "#2196F3", "#4CAF50", "#FFC107", "#FF5722", "#D50000", "#880E4F"]

for key in ["treningi", "strefy", "wyscigi", "biblioteka", "fizjologia", "power_profile", "run_records", "waga", "chat", "plany"]:
    if key not in db: db[key] = []
if isinstance(db["strefy"], list): db["strefy"] = {}
if "session_treningi" not in st.session_state: st.session_state.session_treningi = list(db["treningi"])

# ==========================================
# 3. FUNKCJE POMOCNICZE I ALGORYTMY
# ==========================================
def check_login(u, p): return True if u in USERS and USERS[u] == p else False
def format_czas(m):
    if m is None or m == 0: return "0h 00m"
    h, m = divmod(int(m), 60); return f"{h}h {m:02d}m"
def format_duration(seconds):
    if seconds == float('inf') or seconds is None or seconds == 0: return "-"
    s = int(seconds); h, rem = divmod(s, 3600); m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
def format_interval_time(seconds):
    m, s = divmod(int(seconds), 60); return f"{m}:{s:02d}"
def seconds_to_pace(speed_ms): return (1000 / speed_ms) / 60 if speed_ms > 0.5 else None
def format_pace_label(pace_float):
    if not pace_float or pd.isna(pace_float): return "-"
    return f"{int(pace_float)}:{int((pace_float - int(pace_float)) * 60):02d}"
def format_pace(pace_float): return format_pace_label(pace_float) if pace_float and pace_float <= 30 else "-"
def format_swim_pace(seconds, meters):
    if meters <= 0 or seconds <= 0: return "-"
    p = (seconds / meters) * 100; return f"{int(p // 60)}:{int(p % 60):02d}/100m"
def calculate_normalized_power(watts_stream):
    if not watts_stream or len(watts_stream) < 30: return 0
    return int((pd.Series(watts_stream).fillna(0).rolling(30).mean() ** 4).mean() ** 0.25)
def calculate_compliance(df):
    past = df[pd.to_datetime(df['data']).dt.date <= date.today()]
    if past.empty: return 0
    t = past[~past['wykonany']]['czas'].sum() + past[past['wykonany']]['czas'].sum()
    return int((past[past['wykonany']]['czas'].sum() / t) * 100) if t > 0 else 0

# Zabezpieczono rzutowaniem float(z["max"]) aby wykres stref zawsze się rysował
def calculate_time_in_zones_custom(stream, zone_defs, total_time_mins):
    if not stream or not zone_defs: return []
    zs = [{"label": z["Strefa"], "max": float(z["Max"]), "count": 0} for z in zone_defs]
    valid = [x for x in stream if x is not None]
    if not valid: return []
    for val in valid:
        for i, z in enumerate(zs):
            if val <= z["max"]: z["count"] += 1; break
            elif i == len(zs)-1: z["count"] += 1
    t = len(valid)
    return [{"label": z["label"], "mins": round((z["count"]/t) * total_time_mins, 1), "pct": (z["count"]/t)*100} for z in zs] if t > 0 else []

def pace_str_to_float(pace_str):
    try: p=pace_str.split(':'); return int(p[0])+int(p[1])/60.0
    except: return 0.0
def float_to_pace_str(val):
    m=int(val); return f"{m}:{int((val-m)*60):02d}"

def generuj_domyslne_strefy(ftp, lthr):
    p_zones = [{"Strefa": f"Z{i+1}", "Min": int(p_prev + (1 if i>0 else 0)), "Max": int(m*ftp)} for i, (m, p_prev) in enumerate(zip([0.55, 0.75, 0.90, 1.05, 1.20, 5.0], [0] + [int(x*ftp) for x in [0.55, 0.75, 0.90, 1.05, 1.20]]))]
    h_zones = [{"Strefa": f"Z{i+1}", "Min": int(h_prev + (1 if i>0 else 0)), "Max": int(m*lthr)} for i, (m, h_prev) in enumerate(zip([0.81, 0.89, 0.93, 0.99, 1.02, 1.2], [0] + [int(x*lthr) for x in [0.81, 0.89, 0.93, 0.99, 1.02]]))]
    return pd.DataFrame(p_zones), pd.DataFrame(h_zones)

# Nowa, super bezpieczna funkcja stref obsługująca DYSCYPLINY!
def get_user_zones(zawodnik, dyscyplina="Rower"):
    if isinstance(db["strefy"], list): db["strefy"] = {}
    all_zones = db["strefy"].get(zawodnik, {})
    
    if "ftp" in all_zones and "Rower" not in all_zones:
        old_ftp = all_zones.get("ftp", 250)
        old_lthr = all_zones.get("lthr", 170)
        old_zp = all_zones.get("zones_pwr")
        old_zh = all_zones.get("zones_hr")
        if not old_zp or not old_zh:
            zp, zh = generuj_domyslne_strefy(old_ftp, old_lthr)
            old_zp = zp.to_dict('records'); old_zh = zh.to_dict('records')
        
        migrated_zones = {
            "Rower": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp, "zones_hr": old_zh},
            "Bieganie": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp, "zones_hr": old_zh},
            "Pływanie": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp, "zones_hr": old_zh},
            "Siłownia": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp, "zones_hr": old_zh},
            "Inne": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp, "zones_hr": old_zh}
        }
        temp_db = db["strefy"]
        temp_db[zawodnik] = migrated_zones
        db["strefy"] = temp_db
        all_zones = migrated_zones
        
    disc_zones = all_zones.get(dyscyplina, {})
    if not disc_zones:
        zp, zh = generuj_domyslne_strefy(250, 170)
        disc_zones = {"ftp": 250, "lthr": 170, "zones_pwr": zp.to_dict('records'), "zones_hr": zh.to_dict('records')}
        
        temp_db = db["strefy"]
        if zawodnik not in temp_db: temp_db[zawodnik] = {}
        temp_db[zawodnik][dyscyplina] = disc_zones
        db["strefy"] = temp_db
        
    return disc_zones

def update_athlete_records(zawodnik, workout_data):
    if not workout_data.get('wykonany'): return
    if workout_data.get('peak_powers'):
        p_prof = next((x for x in db["power_profile"] if x['zawodnik'] == zawodnik), {"zawodnik": zawodnik})
        upd = False
        for k, v in workout_data['peak_powers'].items():
            if v > p_prof.get(k, 0): p_prof[k] = v; upd = True
        if upd: db["power_profile"] = [x for x in db["power_profile"] if x['zawodnik'] != zawodnik] + [p_prof]
    if workout_data.get('best_times'):
        r_prof = next((x for x in db["run_records"] if x['zawodnik'] == zawodnik), {"zawodnik": zawodnik})
        upd = False
        for k, v in workout_data['best_times'].items():
            if r_prof.get(k, 0) == 0 or v < r_prof[k]: r_prof[k] = v; upd = True
        if upd: db["run_records"] = [x for x in db["run_records"] if x['zawodnik'] != zawodnik] + [r_prof]

def save_data(new_entry):
    update_athlete_records(new_entry['zawodnik'], new_entry)
    st.session_state.session_treningi.append(new_entry)
    db["treningi"] = list(db["treningi"]) + [new_entry]

def add_comment_to_workout(zawodnik, data_str, tytul, dyscyplina, autor, tresc):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_comment = {"autor": autor, "data": now_str, "tresc": tresc}
    for w in st.session_state.session_treningi:
        if w.get('zawodnik') == zawodnik and str(w.get('data')) == str(data_str) and w.get('tytul') == tytul and w.get('dyscyplina') == dyscyplina:
            if 'komentarze_treningu' not in w: w['komentarze_treningu'] = []
            w['komentarze_treningu'].append(new_comment)
    temp_db = list(db["treningi"])
    for w in temp_db:
        if w.get('zawodnik') == zawodnik and str(w.get('data')) == str(data_str) and w.get('tytul') == tytul and w.get('dyscyplina') == dyscyplina:
            if 'komentarze_treningu' not in w: w['komentarze_treningu'] = []
            w['komentarze_treningu'].append(new_comment)
    db["treningi"] = temp_db

def get_df(zawodnik=None):
    data = st.session_state.session_treningi
    if not data: return pd.DataFrame()
    clean = []
    for d in data:
        if isinstance(d, dict) and 'zawodnik' in d:
            d.setdefault('dyscyplina','Inne'); d.setdefault('dystans',0.0); d.setdefault('czas',0); 
            d.setdefault('tss',0); d.setdefault('wykonany',False); d.setdefault('avg_power', 0)
            d.setdefault('streams', None); d.setdefault('laps', [])
            d.setdefault('rpe', 0); d.setdefault('feeling', '😐')
            d.setdefault('kroki', []); d.setdefault('peak_powers', {}); d.setdefault('best_times', {})
            d.setdefault('komentarze_treningu', [])
            clean.append(d)
    df = pd.DataFrame(clean)
    if df.empty: return df
    df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.date
    df = df.dropna(subset=['data'])
    return df if not zawodnik or zawodnik == tr("Wszyscy") else df[df['zawodnik'] == zawodnik]

def calculate_pmc(df):
    df_done = df[df['wykonany'] == True].copy() if not df.empty else pd.DataFrame()
    if df_done.empty: return pd.DataFrame()
    df_done['data'] = pd.to_datetime(df_done['data']).sort_values()
    dr = pd.date_range(start=df_done['data'].min(), end=pd.to_datetime(date.today()))
    daily = df_done.groupby('data')['tss'].sum().reindex(dr, fill_value=0).to_frame(name='tss')
    daily['CTL'] = daily['tss'].ewm(span=42, adjust=False).mean()
    daily['ATL'] = daily['tss'].ewm(span=7, adjust=False).mean()
    daily['TSB'] = daily['CTL'] - daily['ATL']
    return daily.reset_index().rename(columns={'index': 'date'})

def get_next_race(zawodnik):
    races = [w for w in db.get("wyscigi", []) if w['zawodnik'] == zawodnik]
    future_races = []
    for r in races:
        try:
            rd = datetime.strptime(r['data'], "%Y-%m-%d").date()
            if rd >= date.today(): future_races.append((r, (rd - date.today()).days))
        except: pass
    if not future_races: return None
    future_races.sort(key=lambda x: x[1])
    return future_races[0]

# --- NATIVE GARMIN FIT SDK ENGINE (NAPRAWIONY DLA FENIX 7 / EDGE) ---
class FitWriter:
    def __init__(self):
        self.data = bytearray()
        self.crc_table = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401, 0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]
    def compute_crc(self, payload, crc=0):
        for byte in payload:
            crc = (crc >> 4) & 0x0FFF ^ self.crc_table[crc & 0xF] ^ self.crc_table[byte & 0xF]
            crc = (crc >> 4) & 0x0FFF ^ self.crc_table[crc & 0xF] ^ self.crc_table[(byte >> 4) & 0xF]
        return crc
    def clean_ascii(self, text, length):
        text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
        return "".join([c for c in text if c.isalnum() or c in " -_()"]).encode('utf-8')[:length-1].ljust(length, b'\x00')
    def write_def(self, l_num, g_num, fields):
        self.data += bytearray([0x40 | (l_num & 0x0F), 0, 0]) + struct.pack('<H', g_num) + bytearray([len(fields)])
        for f in fields: self.data += bytearray(f)
    def write_data(self, l_num, data_bytes):
        self.data += bytearray([0x00 | (l_num & 0x0F)]) + data_bytes
    def generate(self, name, sport_enum, steps):
        self.data = bytearray()
        ts = int(time.time()) - 631065600 
        
        # 1. File ID Message
        self.write_def(0, 0, [(0, 1, 0x00), (1, 2, 0x84), (2, 2, 0x84), (3, 4, 0x8C), (4, 4, 0x86)])
        # manufacturer=1 (Garmin), product=0, serial=ts, time_created=ts
        self.write_data(0, struct.pack('<B H H I I', 5, 1, 0, ts, ts))
        
        # 2. Workout Header
        self.write_def(1, 26, [(8, 16, 0x07), (4, 2, 0x84), (5, 1, 0x00)])
        self.write_data(1, self.clean_ascii(name, 16) + struct.pack('<H B', len(steps), sport_enum))
        
        # 3. Workout Steps
        self.write_def(2, 27, [(254, 2, 0x84), (0, 16, 0x07), (1, 1, 0x00), (2, 4, 0x86), (3, 1, 0x00), (4, 4, 0x86), (5, 4, 0x86), (6, 4, 0x86), (7, 1, 0x00)])
        for idx, s in enumerate(steps):
            sd = struct.pack('<H', idx) + self.clean_ascii(s['name'], 16) + struct.pack('<B I B I I I B', s['d_type'], s['d_val'], s['t_type'], s['t_val'], s['t_low'], s['t_high'], s['intens'])
            self.write_data(2, sd)
            
        # Protokół 2.0 (0x20) - to to zmusza Fenixy 7 do akceptacji pliku
        header = struct.pack('<BBHI4s', 14, 0x20, 2141, len(self.data), b'.FIT')
        header += struct.pack('<H', self.compute_crc(header))
        ff = header + self.data
        return bytes(ff + struct.pack('<H', self.compute_crc(ff)))

def create_binary_fit(workout_data, ftp=250):
    writer = FitWriter()
    sport_enum = {"Bieganie": 1, "Rower": 2, "Pływanie": 5, "Siłownia": 3}.get(workout_data.get('dyscyplina', 'Bieganie'), 1)
    intens_map = {"Rozgrzewka": 2, "Interwał": 0, "Przerwa": 1, "Rozjazd": 3}
    name_map = {"Rozgrzewka": "Warmup", "Interwał": "Work", "Przerwa": "Rest", "Rozjazd": "Cooldown"}
    steps = []
    
    for k in workout_data.get('kroki', []):
        d_type = 1 if k.get('is_distance') else 0
        d_val = int(k.get('dystans_km', 0) * 100000) if d_type == 1 else int(k.get('czas_total_sec', 0) * 1000)
        d_val = max(d_val, 1000) # Zabezpieczenie przed zerowym czasem kroku
        
        mode = k.get('tryb', '')
        v_min = float(k.get('val_min', 0))
        v_max = float(k.get('val_max', 0))
        
        # Domyślnie: Open (brak określonego celu, np. krok na RPE)
        t_type = 2 
        t_val = 0  
        c_low = 0
        c_high = 0
        
        if v_min > 0 or v_max > 0:
            if "Waty" in mode: 
                t_type = 4 
                c_low = int(min(v_min, v_max)) + 1000
                c_high = int(max(v_min, v_max)) + 1000
            elif "%" in mode: 
                t_type = 4
                c_low = int((min(v_min, v_max) / 100) * ftp) + 1000
                c_high = int((max(v_min, v_max) / 100) * ftp) + 1000
            elif "Tętno" in mode: 
                t_type = 1
                c_low = int(min(v_min, v_max)) + 100
                c_high = int(max(v_min, v_max)) + 100
            elif "Tempo" in mode: 
                t_type = 0
                c_low = min(int(1000 / (v_min * 60) * 1000), int(1000 / (v_max * 60) * 1000))
                c_high = max(int(1000 / (v_min * 60) * 1000), int(1000 / (v_max * 60) * 1000))
            
        steps.append({'name': name_map.get(k.get('typ'), "Step"), 'd_type': d_type, 'd_val': d_val, 't_type': t_type, 't_val': t_val, 't_low': c_low, 't_high': c_high, 'intens': intens_map.get(k.get('typ'), 0)})
        
    return writer.generate(str(workout_data.get('tytul', 'Workout'))[:15], sport_enum, steps)

# --- ZWO GENERATOR ---
def generate_zwo_file(workout_data):
    xml = "<workout_file>\n<author>TriCoach Pro</author>\n"
    xml += f"<name>{workout_data['tytul']}</name>\n<description>{workout_data.get('komentarz','')}</description>\n<sportType>bike</sportType>\n<workout>\n"
    if workout_data.get('kroki'):
        for k in workout_data['kroki']:
            sec = k.get('czas_total_sec', 300)
            if sec == 0: sec = 300
            dur = int(sec); power = 0.5
            if "Waty" in k['tryb']: power = (k['val_min'] + k['val_max']) / 2 / 250
            elif "%" in k['tryb']: power = ((k['val_min'] + k['val_max']) / 2) / 100
            elif "RPE" in k['tryb']: power = k['val_min'] / 100
            xml += f'\t<SteadyState Duration="{dur}" Power="{max(0.3, min(power, 2.0)):.2f}"/>\n'
    return xml + "</workout>\n</workout_file>"

class PDFReport(FPDF):
    def header(self): self.set_font('Arial', 'B', 15); self.set_text_color(0, 229, 255); self.cell(0, 10, 'TriCoach Pro | Report', 0, 1, 'C'); self.ln(5)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_weekly_pdf(zawodnik, week_data, week_num, year, coach_note):
    pdf = PDFReport(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 12); pdf.set_text_color(0); pdf.cell(0, 10, f"Athlete: {zawodnik} | Week {week_num} / {year}", 0, 1, 'L'); pdf.ln(5)
    pdf.set_fill_color(240, 240, 240); pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 10, f"Time: {format_czas(week_data['czas'].sum())}", 1, 0, 'C', 1); pdf.cell(60, 10, f"Dist: {week_data['dystans'].sum()} km", 1, 0, 'C', 1); pdf.cell(60, 10, f"TSS: {int(week_data['tss'].sum())}", 1, 1, 'C', 1); pdf.ln(10)
    pdf.set_font('Arial', 'B', 11); pdf.cell(0, 10, "Log:", 0, 1, 'L'); pdf.set_font('Arial', '', 9); pdf.set_fill_color(0, 229, 255); pdf.set_text_color(255)
    pdf.cell(25, 8, "Date", 1, 0, 'C', 1); pdf.cell(25, 8, "Sport", 1, 0, 'C', 1); pdf.cell(85, 8, "Title", 1, 0, 'L', 1); pdf.cell(20, 8, "RPE", 1, 0, 'C', 1); pdf.cell(30, 8, "TSS", 1, 1, 'C', 1)
    pdf.set_text_color(0)
    for _, row in week_data.iterrows():
        pdf.cell(25, 8, str(row['data']), 1); pdf.cell(25, 8, tr(row['dyscyplina']), 1); pdf.cell(85, 8, row['tytul'][:45], 1); pdf.cell(20, 8, str(row.get('rpe', '-')) if row['wykonany'] else "-", 1, 0, 'C'); pdf.cell(30, 8, str(row['tss']), 1, 1, 'C')
    if coach_note: pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 150, 0); pdf.cell(0, 10, "Coach Note:", 0, 1, 'L'); pdf.set_font('Arial', 'I', 10); pdf.set_text_color(0); pdf.multi_cell(0, 8, coach_note)
    return pdf.output(dest='S').encode('latin-1')

def parse_tcx_pro(uploaded_file, athlete_all_zones):
    res = { "dist": 0.0, "tss": 0, "time": 0, "date": date.today(), "sport": "Inne", "avg_power": 0, "streams": {"time":[],"hr":[],"watts":[],"speed":[],"cadence":[],"lat":[],"lon":[]}, "laps": [], "peak_powers": {}, "best_times": {} }
    try:
        tree = ET.parse(uploaded_file); root = tree.getroot(); total_s = 0.0; total_m = 0.0; raw_real_s = []; raw_dist = []
        for elem in root.iter():
            if "Activity" in elem.tag and "Sport" in elem.attrib:
                s = elem.attrib["Sport"].lower()
                if "run" in s: res["sport"]="Bieganie"
                elif "bik" in s: res["sport"]="Rower"
                elif "swim" in s: res["sport"]="Pływanie"
            if elem.tag.endswith("Id"):
                try: res["date"] = datetime.strptime(elem.text.strip()[:10], "%Y-%m-%d").date()
                except: pass
                
        # Inteligentne pobieranie FTP i LTHR dla wykrytej dyscypliny
        disc_zones = athlete_all_zones.get(res["sport"], {})
        user_ftp = disc_zones.get("ftp", 250) if isinstance(disc_zones, dict) else 250
        user_lthr = disc_zones.get("lthr", 170) if isinstance(disc_zones, dict) else 170
        
        lap_c = 1; el_s = 0; hr_s = 0; hr_c = 0; pw_s = 0; pw_c = 0; active_time = 0; start_time_dt = None
        for lap in root.iter():
            if lap.tag.endswith("Lap"):
                lt=0.0; ld=0.0; lhr=None; lpw=None; lsp=None
                for c in lap:
                    if c.tag.endswith("TotalTimeSeconds"): lt=float(c.text); total_s+=lt
                    if c.tag.endswith("DistanceMeters"): ld=float(c.text); total_m+=ld
                    if c.tag.endswith("AverageHeartRateBpm"): 
                        for v in c: lhr=int(v.text)
                for e in lap.iter():
                    if e.tag.endswith("AvgWatts"): lpw=int(float(e.text))
                    if e.tag.endswith("AvgSpeed"): lsp=float(e.text)
                is_act = (ld>0) or (lhr and lhr>90) or (lpw and lpw>50)
                if is_act: active_time += lt
                lr = {"type":"work" if is_act else "rest", "nr":str(lap_c) if is_act else "", "czas":format_interval_time(lt), "hr":lhr, "moc":lpw}
                if res["sport"]=="Pływanie": lr["dystans"] = f"{int(ld)}m" if is_act else "Odpoczynek"; lr["tempo"] = format_swim_pace(lt,ld) if is_act else "-"
                else: lr["dystans"] = f"{round(ld/1000,2)}km"; lr["tempo"] = format_pace(seconds_to_pace(lsp)) if lsp else "-"
                res["laps"].append(lr)
                if is_act: lap_c+=1
                for tr_elem in lap.iter():
                    if tr_elem.tag.endswith("Track"):
                        for tp in tr_elem:
                            if tp.tag.endswith("Trackpoint"):
                                try:
                                    th=None; tw=None; ts=None; tc=None; tla=None; tlo=None; t_dist=None; pt_dt=None
                                    for tpc in tp.iter():
                                        if tpc.tag.endswith("HeartRateBpm"): 
                                            for v in tpc: th=int(v.text)
                                        if tpc.tag.endswith("Watts"): tw=int(tpc.text)
                                        if tpc.tag.endswith("Speed"): ts=float(tpc.text)
                                        if tpc.tag.endswith("Cadence") or tpc.tag.endswith("RunCadence"): 
                                            rc=int(tpc.text); tc=rc*2 if res["sport"]=="Bieganie" and 0<rc<125 else rc
                                        if tpc.tag.endswith("LatitudeDegrees"): tla=float(tpc.text)
                                        if tpc.tag.endswith("LongitudeDegrees"): tlo=float(tpc.text)
                                        if tpc.tag.endswith("DistanceMeters"): t_dist=float(tpc.text)
                                        if tpc.tag.endswith("Time"):
                                            try: pt_dt = datetime.strptime(tpc.text.strip()[:19], "%Y-%m-%dT%H:%M:%S")
                                            except: pass
                                    if start_time_dt is None and pt_dt is not None: start_time_dt = pt_dt
                                    current_real_sec = (pt_dt - start_time_dt).total_seconds() if start_time_dt and pt_dt else el_s 
                                    res["streams"]["time"].append(current_real_sec/60); res["streams"]["hr"].append(th); res["streams"]["watts"].append(tw)
                                    res["streams"]["speed"].append(ts); res["streams"]["cadence"].append(tc); res["streams"]["lat"].append(tla); res["streams"]["lon"].append(tlo)
                                    raw_real_s.append(current_real_sec); raw_dist.append(t_dist)
                                    if th: hr_s+=th; hr_c+=1
                                    if tw: pw_s+=tw; pw_c+=1
                                    el_s+=1
                                except: pass
        res["dist"] = round(total_m/1000, 2); res["time"] = int(total_s/60)
        if res["sport"] == "Rower" and len(res["streams"]["watts"]) > 0:
            w_series = pd.Series([w if w is not None else 0 for w in res["streams"]["watts"]])
            for k, v in {"5s": 5, "10s": 10, "20s": 20, "1m": 60, "5m": 300, "10m": 600, "20m": 1200, "60m": 3600}.items():
                res["peak_powers"][k] = int(w_series.rolling(v).mean().max()) if len(w_series) >= v else 0
        if res["sport"] == "Bieganie" and len(raw_real_s) > 0 and len(raw_dist) > 0:
            clean_dist = []; cumulative_d = 0; last_d = 0
            for d in raw_dist:
                if d is not None:
                    if d < last_d: cumulative_d += last_d
                    last_d = d
                clean_dist.append(cumulative_d + last_d)
            for k, target_dist in {"400m": 400, "1km": 1000, "5km": 5000, "10km": 10000, "Półmaraton": 21097, "Maraton": 42195}.items():
                min_t = float('inf'); left = 0
                for right in range(len(raw_real_s)):
                    while left < right and clean_dist[right] - clean_dist[left] >= target_dist:
                        d_diff = clean_dist[right] - clean_dist[left]; t_diff = raw_real_s[right] - raw_real_s[left]
                        if t_diff > 0 and d_diff > 0 and (d_diff / t_diff) < 8.5: 
                            exact_t = t_diff * (target_dist / d_diff)
                            if exact_t < min_t: min_t = exact_t
                        left += 1
                if min_t != float('inf'): res["best_times"][k] = int(min_t)
        if pw_c>0 and user_ftp>0: res["avg_power"] = int(pw_s/pw_c); np_val = calculate_normalized_power(res["streams"]["watts"]); res["tss"] = int(((active_time * (np_val if np_val>0 else res["avg_power"]) * ((np_val if np_val>0 else res["avg_power"])/user_ftp)) / (user_ftp*3600))*100)
        elif hr_c>0 and user_lthr>0: res["tss"] = int((active_time/3600)*100*((hr_s/hr_c/user_lthr)**3.5))
        if res["tss"]==0 and active_time>0: res["tss"] = int((active_time/3600)*60)
        if len(res["streams"]["time"]) > 600:
            step = len(res["streams"]["time"]) // 600
            for key in res["streams"]: res["streams"][key] = res["streams"][key][::step]
        return res
    except Exception: return res

def przygotuj_kalendarz(zawodnik):
    events = []; df = get_df(zawodnik if zawodnik != tr("Wszyscy") else None)
    for idx, t in df.iterrows():
        if t['wykonany']:
            if t.get('plan_czas', 0) > 0:
                pct = (t['czas'] / t['plan_czas']) * 100
                if 80 <= pct <= 120: col = "#00C853" 
                elif 60 <= pct < 80 or 120 < pct <= 150: col = "#FFD600" 
                else: col = "#D50000" 
            else:
                col = "#00C853" 
        else:
            col = "#1F2735" 

        border = KOLORY_SPORT.get(t['dyscyplina'], "#00E5FF")
        prefix = tr("Bieg") if t['dyscyplina']=="Bieganie" else tr("Rower") if t['dyscyplina']=="Rower" else tr("Pływanie")
        title = f"{prefix} | {t['dystans']}km" if t.get('dystans') else f"{prefix} | {t['czas']}min"
        if not t['wykonany']: title = f"[{tr('PLAN')}] {t['tytul']}"
        events.append({"title": title, "start": str(t['data']), "backgroundColor": col, "borderColor": border, "allDay": True, "extendedProps": {"type": "trening", "data_str": str(t['data']), "dyscyplina": t['dyscyplina'], "tytul": t['tytul']}})
    waga_data = list(db.get("waga", [])); wyscigi_data = list(db.get("wyscigi", []))
    if zawodnik and zawodnik != tr("Wszyscy"): 
        waga_data = [w for w in waga_data if w['zawodnik'] == zawodnik]; wyscigi_data = [r for r in wyscigi_data if r['zawodnik'] == zawodnik]
    for w in waga_data: events.append({"title": f"{tr('Waga')}: {w['waga']} kg", "start": w['data'], "backgroundColor": "#2D3748", "borderColor": "#4A5568", "textColor": "#FFFFFF", "allDay": True, "extendedProps": {"type": "waga", "data_str": w['data'], "waga": w['waga']}})
    for r in wyscigi_data: events.append({"title": f"🏆 {r['nazwa']}", "start": r['data'], "backgroundColor": "#FFD700", "borderColor": "#F57F17", "textColor": "#000000", "allDay": True})
    return events

def render_tp_weekly_list(df):
    if df.empty: 
        st.markdown(f"<div class='tp-summary-card'>{tr('Brak danych')}</div>", unsafe_allow_html=True); return
    df['iso_year'] = pd.to_datetime(df['data']).dt.isocalendar().year
    df['iso_week'] = pd.to_datetime(df['data']).dt.isocalendar().week
    unique_weeks = df[['iso_year', 'iso_week']].drop_duplicates().sort_values(['iso_year', 'iso_week'], ascending=False)
    for _, week_row in unique_weeks.iterrows():
        year = week_row['iso_year']; week = week_row['iso_week']; week_data = df[(df['iso_year'] == year) & (df['iso_week'] == week)]; comp_data = week_data[week_data['wykonany'] == True]
        html = f"""<div class="tp-summary-card"><div class="tp-week-title">{tr('Tydzień')} {week} <span style="font-size:0.7em; color:#8BA1B8; font-weight: 400;">({year})</span></div>
        <div class="tp-row"><span class="tp-val">{tr('Czas')}: {format_czas(comp_data['czas'].sum())} / {format_czas(week_data['czas'].sum())}</span><span class="tp-val">TSS: {int(comp_data['tss'].sum())} / {int(week_data['tss'].sum())}</span></div><hr style="border-color: #1F2735; margin: 8px 0;">"""
        for sport in ["Pływanie", "Rower", "Bieganie", "Siłownia"]:
            s_df = week_data[week_data['dyscyplina'] == sport]
            if not s_df.empty:
                s_comp = s_df[s_df['wykonany'] == True]
                color = KOLORY_SPORT.get(sport, "#8BA1B8")
                html += f"""<div style="border-left: 3px solid {color}; padding-left: 10px; margin-top: 10px;"><div style="font-weight:800; color:{color}; font-size:0.95em; letter-spacing: 0.5px;">{tr(sport).upper()}</div>
                <div class="tp-stat-line"><span>{format_czas(s_comp['czas'].sum())} / {format_czas(s_df['czas'].sum())}</span><span>{s_comp['dystans'].sum():.1f} km</span><span>{int(s_comp['tss'].sum())} / {int(s_df['tss'].sum())} TSS</span></div></div>"""
        st.markdown(html + "</div>", unsafe_allow_html=True)

def render_planned_workout_view(t, user_ftp=250):
    st.info(f"{tr('Zaplanowany Trening:')} {t['tytul']}")
    if t.get('komentarz'): st.markdown(f"{tr('Instrukcje Trenera:')}\n> {t['komentarz']}")
    if t.get('kroki'):
        fig = go.Figure(); ct = 0; steps_data = []
        for idx, k in enumerate(t['kroki']):
            v_desc = f"{k.get('dystans_km', 0)} km" if k.get('is_distance') else f"{int(k.get('czas_total_sec', 0)/60)} min"
            dur = k.get('czas_total_sec', 300)/60
            if dur == 0: dur = 5
            avg_val = (k.get('val_min', 0) + k.get('val_max', 0)) / 2
            if avg_val == 0: avg_val = 50 
            display_y = 100 / avg_val if "Tempo" in k.get('tryb', '') and avg_val > 0 else avg_val
            intensity_label = f"{float_to_pace_str(k['val_min'])} - {float_to_pace_str(k['val_max'])}" if "Tempo" in k.get('tryb', '') else f"{int(k.get('val_min',0))}-{int(k.get('val_max',0))}"
            fig.add_trace(go.Bar(x=[ct+dur/2], y=[display_y], width=[dur], name=f"{tr(k['typ'])}", marker_color=KOLORY_BLOKOW.get(k['typ']), text=f"{v_desc}<br>{intensity_label}", textposition="auto"))
            ct += dur
            steps_data.append({"#": idx+1, tr("Typ"): tr(k['typ']), tr("Czas/Dystans"): v_desc, "Task": f"{tr(k.get('tryb', ''))}: {intensity_label}"})

        fig.update_layout(template="plotly_dark", height=250, showlegend=False, xaxis_title=tr("Czas (min)"), yaxis=dict(showticklabels=False), margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        with st.expander(tr("Zobacz Rozpiskę")): st.table(pd.DataFrame(steps_data))

        c1_dl, c2_dl = st.columns(2)
        safe_fn = "".join([c for c in unicodedata.normalize('NFKD', str(t['tytul'])).encode('ASCII', 'ignore').decode('utf-8') if c.isalnum() or c in " -_"]).strip() or "Workout"
        c1_dl.download_button(tr("Pobierz plik .ZWO (Zwift)"), data=generate_zwo_file(t), file_name=f"{safe_fn}.zwo", mime="text/xml")
        c2_dl.markdown(f"<span style='font-size:0.85em; color:#8BA1B8;'>*{tr('Pobierz .FIT i wgraj go na zegarek do folderu GARMIN/NewFiles. Zegarek sam go przetworzy!')}*</span>", unsafe_allow_html=True)
        c2_dl.download_button(tr("Pobierz plik .FIT (Garmin)"), data=create_binary_fit(t, user_ftp), file_name=f"{safe_fn}.fit", mime="application/octet-stream")
    else: st.warning(tr("Tylko opis tekstowy."))

def render_analysis_dashboard(t, user_settings):
    if not t.get('wykonany'): render_planned_workout_view(t, user_settings.get('ftp', 250)); return

    if t.get('plan_czas', 0) > 0:
        comp_pct = int((t['czas'] / t['plan_czas']) * 100)
        col = "#00E676" if 80 <= comp_pct <= 120 else ("#FFD600" if 60 <= comp_pct < 80 or 120 < comp_pct <= 150 else "#FF1744")
        st.markdown(f"<div style='text-align:center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 15px;'><span style='color:#8BA1B8; text-transform:uppercase; font-size:0.8em;'>{tr('Zgodność z planem:')}</span> <strong style='color:{col}; font-size:1.2em;'>{comp_pct}%</strong></div>", unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(f"<div class='metric-card'><div class='metric-val'>{t.get('dystans')} km</div><div class='metric-label'>{tr('Dystans')}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><div class='metric-val'>{t.get('czas')} m</div><div class='metric-label'>{tr('Czas')}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><div class='metric-val'>{t.get('tss')}</div><div class='metric-label'>TSS</div></div>", unsafe_allow_html=True)
    np_val = calculate_normalized_power(t.get('streams', {}).get('watts', [])) if t.get('streams') and any(t['streams'].get('watts',[])) else 0
    k4.markdown(f"<div class='metric-card'><div class='metric-val'>{np_val} W</div><div class='metric-label'>{tr('NP (Moc)')}</div></div>", unsafe_allow_html=True)
    c7,c8=st.columns(2); c7.write(f"**{tr('RPE:')}** {t.get('rpe','-')}/10"); c8.write(f"**{tr('Samopoczucie:')}** {t.get('feeling','-')}")
    st.markdown("---")

    streams = t.get('streams')

    if streams and any(streams.get('lat', [])):
        lat_list = [l for l in streams.get('lat', []) if l is not None]
        lon_list = [l for l in streams.get('lon', []) if l is not None]
        if lat_list and lon_list:
            st.markdown(f"### 🗺️ {tr('Mapa trasy GPS')}")
            fig_map = go.Figure(go.Scattermapbox(mode="lines", lon=lon_list, lat=lat_list, line=dict(width=4, color='#00E5FF')))
            fig_map.update_layout(margin={'l':0, 't':0, 'b':0, 'r':0}, mapbox=dict(style="carto-darkmatter", center=dict(lat=np.mean(lat_list), lon=np.mean(lon_list)), zoom=12), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

    if t.get('laps'):
        st.markdown(f"### ⏱️ {tr('Interwały')}")
        ldf = pd.DataFrame(t['laps'])
        cols = ["nr","czas","dystans","tempo"] if t['dyscyplina']=="Pływanie" else ["nr","czas","dystans","hr","moc","tempo"]
        st.dataframe(ldf[[c for c in cols if c in ldf.columns]], hide_index=True, use_container_width=True)

    if streams and any(streams.get('time', [])):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=[tr("Tętno"),tr("Tempo/Moc"),tr("Kadencja")])
        row_idx = 1
        if any(streams.get('hr',[])): 
            fig.add_trace(go.Scatter(x=streams['time'], y=streams['hr'], name=tr("Tętno"), line=dict(color='#FF1744'), fill='tozeroy'), row=row_idx, col=1); row_idx+=1
        if t['dyscyplina']=="Bieganie" and any(streams.get('speed',[])):
            ps = [seconds_to_pace(s) if s else None for s in streams['speed']]
            fig.add_trace(go.Scatter(x=streams['time'], y=ps, name=tr("Tempo"), line=dict(color='#00E5FF'), fill='tozeroy', customdata=[format_pace_label(p) for p in ps], hovertemplate="Pace: %{customdata}/km"), row=row_idx, col=1)
            fig.update_yaxes(autorange="reversed", row=row_idx, col=1); row_idx+=1
        elif any(streams.get('watts',[])):
            fig.add_trace(go.Scatter(x=streams['time'], y=streams['watts'], name=tr("Moc"), line=dict(color='#FFD700'), fill='tozeroy'), row=row_idx, col=1); row_idx+=1
        if any(streams.get('cadence',[])): 
            fig.add_trace(go.Scatter(x=streams['time'], y=streams['cadence'], name=tr("Kadencja"), line=dict(color='#AA00FF')), row=row_idx, col=1)

        fig.update_layout(template="plotly_dark", height=500, showlegend=False, margin=dict(l=50,r=10,t=30,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        if streams and (any(streams.get('hr', [])) or any(streams.get('watts', []))):
            st.markdown(f"### 📊 {tr('Czas w strefach')}")
            cz1, cz2 = st.columns(2)
            
            if any(streams.get('watts', [])) and user_settings.get("zones_pwr"):
                z_pwr = calculate_time_in_zones_custom(streams['watts'], user_settings["zones_pwr"], t.get('czas', 0))
                if z_pwr:
                    df_zp = pd.DataFrame(z_pwr)
                    fig_zp = px.bar(df_zp, x='mins', y='label', orientation='h', title=tr("Moc"), text=df_zp['mins'].apply(lambda x: f"{x} min"), color='label', color_discrete_sequence=ZONE_COLORS)
                    fig_zp.update_layout(template="plotly_dark", showlegend=False, height=250, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    cz1.plotly_chart(fig_zp, use_container_width=True)
                    
            if any(streams.get('hr', [])) and user_settings.get("zones_hr"):
                z_hr = calculate_time_in_zones_custom(streams['hr'], user_settings["zones_hr"], t.get('czas', 0))
                if z_hr:
                    df_zh = pd.DataFrame(z_hr)
                    fig_zh = px.bar(df_zh, x='mins', y='label', orientation='h', title=tr("Tętno"), text=df_zh['mins'].apply(lambda x: f"{x} min"), color='label', color_discrete_sequence=ZONE_COLORS)
                    fig_zh.update_layout(template="plotly_dark", showlegend=False, height=250, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    cz2.plotly_chart(fig_zh, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 💬 {tr('Komentarze do treningu')}")
    komentarze = t.get('komentarze_treningu', [])
    for c in komentarze:
        is_me = (c['autor'] == st.session_state.username)
        bg_col = "rgba(0, 229, 255, 0.1)" if is_me else "rgba(255, 255, 255, 0.05)"
        align = "left"
        st.markdown(f"""
        <div style='background: {bg_col}; padding: 12px; border-radius: 8px; margin-bottom: 8px; text-align: {align}; border-left: {'3px solid #00E5FF' if is_me else '3px solid #FFD700'};'>
            <small style='color: #8BA1B8;'><b>{c['autor']}</b> • {c['data']}</small><br>
            <span style='color: #E2E8F0; font-size: 0.95em;'>{c['tresc']}</span>
        </div>
        """, unsafe_allow_html=True)

    safe_title = "".join([c for c in str(t.get('tytul','')) if c.isalnum()]).strip()
    with st.form(key=f"comment_form_{t.get('zawodnik')}_{t.get('data')}_{safe_title}"):
        new_comment = st.text_input(tr("Dodaj komentarz..."))
        if st.form_submit_button(tr("Wyślij")):
            if new_comment:
                add_comment_to_workout(t['zawodnik'], t['data'], t['tytul'], t['dyscyplina'], st.session_state.username, new_comment)
                st.rerun()

# ==========================================
# 4. LOGOWANIE
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.markdown("### Settings / Ustawienia")
    lang_sel = st.sidebar.radio("Language / Język", ["PL", "EN"], horizontal=True, index=0 if st.session_state.lang == 'PL' else 1)
    if lang_sel != st.session_state.lang: st.session_state.lang = lang_sel; st.rerun()

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
        st.markdown("""<div class="login-header"><h1 class="login-title">ENDURA IQ</h1><p class="login-subtitle">Science-Based Coaching Platform</p></div>""", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center; color: #8BA1B8;'>{tr('Zaloguj się')}</h4>", unsafe_allow_html=True)
        u = st.text_input(tr("Użytkownik"), placeholder="admin / Jan Kowalski")
        p = st.text_input(tr("Hasło"), type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(tr("Zaloguj")):
            if check_login(u, p): st.session_state.logged_in = True; st.session_state.username = u; st.session_state.role = "coach" if u=="admin" else "athlete"; st.rerun()
            else: st.error(tr("Nieprawidłowy login lub hasło."))
    st.stop()

# ==========================================
# 5. APLIKACJA MAIN
# ==========================================
ja = st.session_state.username
st.sidebar.markdown(f"<h3 style='color: #00E5FF; text-align: center; margin-bottom: 20px;'>{ja.upper()}</h3>", unsafe_allow_html=True)
lang_sel = st.sidebar.radio("Language / Język", ["PL", "EN"], horizontal=True, index=0 if st.session_state.lang == 'PL' else 1)
if lang_sel != st.session_state.lang: st.session_state.lang = lang_sel; st.rerun()

menu_opts = [tr("Dashboard"), tr("Kalendarz"), tr("Wiadomości"), tr("Statystyki"), tr("Raporty"), tr("Fizjologia"), tr("Strefy"), tr("Kreator"), tr("Plany"), tr("Baza")] if st.session_state.role == "coach" else [tr("Dodaj aktywność"), tr("Kalendarz"), tr("Wiadomości"), tr("Statystyki"), tr("Dane zawodnika")]
menu = st.sidebar.radio(tr("MENU"), menu_opts)
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button(tr("Wyloguj")): st.session_state.logged_in=False; st.rerun()

# --- 1. DODAJ AKTYWNOŚĆ (ZAWODNIK) ---
if menu == tr("Dodaj aktywność"):
    st.title(f"{tr('Cześć')} {ja.split(' ')[0]}!")
    next_race = get_next_race(ja)
    if next_race:
        r_data, d_left = next_race
        d_str = f"{d_left} {tr('dni do startu')}" if d_left > 0 else tr("dzisiaj!")
        st.markdown(f"<div class='race-card'><div class='race-val'>🏆 {r_data['nazwa']}</div><div class='race-label'><b>{d_str}</b> ({r_data['data']})</div></div>", unsafe_allow_html=True)

    df_pmc_ath = calculate_pmc(get_df(ja))
    c_ctl = int(df_pmc_ath.iloc[-1]['CTL']) if not df_pmc_ath.empty else 0
    c_atl = int(df_pmc_ath.iloc[-1]['ATL']) if not df_pmc_ath.empty else 0
    c_tsb = int(df_pmc_ath.iloc[-1]['TSB']) if not df_pmc_ath.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card' style='padding:15px;'><div class='metric-val' style='color:#00E5FF;'>{c_ctl}</div><div class='metric-label'>{tr('Fitness (CTL)')}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card' style='padding:15px;'><div class='metric-val' style='color:#FF1744;'>{c_atl}</div><div class='metric-label'>{tr('Zmęczenie (ATL)')}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='padding:15px;'><div class='metric-val' style='color:{'#00E676' if c_tsb >= 0 else '#FF9100'};'>{c_tsb}</div><div class='metric-label'>{tr('Forma (TSB)')}</div></div>", unsafe_allow_html=True)

    df_all_ath = get_df(ja)
    streak = len(df_all_ath[df_all_ath['wykonany'] == True]) if not df_all_ath.empty else 0
    c4.markdown(f"<div class='metric-card' style='padding:15px;'><div class='metric-val' style='color:#FFD700;'>🔥 {streak}</div><div class='metric-label'>{tr('Wykonane Treningi (Licznik)')}</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_main, col_side = st.columns([3, 1])
    with col_side: render_tp_weekly_list(get_df(ja))
    with col_main:
        with st.expander(tr("Zgłoś Trening (Upload TCX)"), expanded=True):
            up = st.file_uploader(tr("Wgraj plik z zegarka"), type=['tcx'])
            if 'form_data' not in st.session_state: st.session_state.form_data = {'date': date.today(), 'time': 45, 'dist': 5.0, 'tss': 30, 'sport': 'Bieganie', 'avg_power': 0, 'streams': None, 'laps': [], 'peak_powers': {}, 'best_times': {}}
            is_file_mode = False
            if up:
                is_file_mode = True
                parsed = parse_tcx_pro(up, db["strefy"].get(ja, {}))
                if parsed['time'] > 0: st.session_state.form_data = parsed; st.success(f"✅ {tr('Przetworzono:')} {parsed['dist']} km")

            curr = st.session_state.form_data
            with st.form("add_workout"):
                fc1, fc2 = st.columns(2)
                sport_options = ["Bieganie", "Rower", "Pływanie", "Siłownia", "Inne"]
                default_sport = curr.get('sport', 'Bieganie')
                s_idx = sport_options.index(default_sport) if default_sport in sport_options else 0
                f_sport = fc1.selectbox(tr("Dyscyplina"), sport_options, index=s_idx, format_func=tr)
                f_date = fc2.date_input(tr("Data"), curr['date'])

                unexecuted = [w for w in st.session_state.session_treningi if w.get('zawodnik')==ja and not w.get('wykonany') and w.get('dyscyplina')==f_sport]
                unexecuted_opts = {f"{w['data']} - {w['tytul']}": w for w in unexecuted}
                pair_choice = st.selectbox(tr("Powiąż z planowanym treningiem:"), [tr("Brak (dodaj jako nowy)")] + list(unexecuted_opts.keys()))

                fc3,fc4,fc5 = st.columns(3)
                f_time = fc3.number_input(tr("Czas (min)"), value=curr['time'], disabled=is_file_mode)
                f_dist = fc4.number_input(tr("Dystans (km)"), value=float(curr['dist']), disabled=is_file_mode)
                f_tss = fc5.number_input("TSS", value=int(curr['tss']), disabled=is_file_mode)
                st.markdown("---")
                c_rpe, c_feel = st.columns(2)
                f_rpe = c_rpe.slider("RPE", 1, 10, 5)
                f_feel = c_feel.select_slider(tr("Samopoczucie"), ["😫","😕","😐","🙂","🤩"], value="🙂")
                f_comm = st.text_area(tr("Notatka dla Trenera"))

                if st.form_submit_button(tr("ZAPISZ TRENING")):
                    new_entry = {"zawodnik": ja, "dyscyplina": f_sport, "data": str(f_date), "tytul": f"{tr(f_sport)}: {f_dist}km", "czas": f_time, "dystans": f_dist, "tss": f_tss, "avg_power": curr.get('avg_power',0), "wykonany": True, "komentarz": f_comm, "rpe": f_rpe, "feeling": f_feel, "streams": curr.get('streams'), "laps": curr.get('laps'), "peak_powers": curr.get('peak_powers', {}), "best_times": curr.get('best_times', {}), "komentarze_treningu": []}
                    if pair_choice != tr("Brak (dodaj jako nowy)"):
                        old_w = unexecuted_opts[pair_choice]
                        st.session_state.session_treningi = [w for w in st.session_state.session_treningi if w is not old_w]
                        db["treningi"] = [w for w in db["treningi"] if w != old_w]
                        new_entry['plan_czas'] = old_w.get('czas', 0)
                        new_entry['plan_tss'] = old_w.get('tss', 0)
                        new_entry['kroki'] = old_w.get('kroki', [])
                    save_data(new_entry); st.success(tr("Zapisano!")); st.session_state.pop('form_data', None); st.rerun()

        with st.expander(tr("Loguj Wagę Ciała")):
            with st.form("add_weight"):
                w_date = st.date_input(tr("Data ważenia"), date.today())
                w_val = st.number_input(tr("Waga (kg)"), min_value=30.0, max_value=200.0, value=75.0, step=0.1)
                if st.form_submit_button(tr("Zapisz Wagę")):
                    temp_waga = list(db["waga"])
                    existing = [x for x in temp_waga if x['zawodnik'] == ja and x['data'] == str(w_date)]
                    if existing: existing[0]['waga'] = w_val
                    else: temp_waga.append({"zawodnik": ja, "data": str(w_date), "waga": w_val})
                    db["waga"] = temp_waga; st.success(tr("Zapisano wagę!")); st.rerun()

        st.markdown(f"### {tr('Ostatnie Aktywności')}")
        df_plan = get_df(ja)
        for idx, row in df_plan.sort_values('data', ascending=False).iterrows():
            with st.expander(f"{'✅' if row['wykonany'] else '⬜'} {row['data']} | {tr(row['dyscyplina'])} - {row['tytul']}"):
                u_strefy_disc = get_user_zones(ja, row['dyscyplina'])
                if not row['wykonany']: render_planned_workout_view(row, u_strefy_disc.get('ftp', 250))
                else: 
                    if st.toggle(tr("Analiza"), key=f"tgl_{idx}"): render_analysis_dashboard(row.to_dict(), u_strefy_disc)

# --- 1.5 CZAT (WIADOMOŚCI) ---
elif menu == tr("Wiadomości"):
    st.title(f"💬 {tr('Wiadomości')}")
    chat_partner = "admin"
    if st.session_state.role == "coach": chat_partner = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY)
    st.markdown(f"#### {tr('Czat z')} {chat_partner}")
    st.markdown("---")
    msgs = db.get("chat", [])
    for m in msgs:
        if (m['od'] == ja and m['do'] == chat_partner) or (m['od'] == chat_partner and m['do'] == ja):
            is_me = (m['od'] == ja)
            with st.chat_message("user" if is_me else "assistant", avatar="👤" if is_me else ("👨‍🏫" if m['od'] == "admin" else "🏃")):
                st.caption(f"{m['data']}")
                st.write(m['tresc'])
    prompt = st.chat_input(tr("Napisz wiadomość..."))
    if prompt:
        db["chat"] = list(db.get("chat", [])) + [{"od": ja, "do": chat_partner, "data": datetime.now().strftime("%Y-%m-%d %H:%M"), "tresc": prompt}]
        st.rerun()

# --- 1.8 STATYSTYKI ---
elif menu == tr("Statystyki"):
    st.title(f"📊 {tr('Podsumowanie aktywności')}")
    target = ja if st.session_state.role != "coach" else st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY)
    df = get_df(target)
    df = df[df['wykonany'] == True]
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['year'] = df['data'].dt.year
        df['month'] = df['data'].dt.month
        years = sorted(df['year'].unique().tolist(), reverse=True)
        if not years: years = [date.today().year]
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox(tr("Wybierz rok"), years)
        months_pl = ["Cały rok", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
        months_en = ["Whole Year", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_opts = months_pl if st.session_state.lang == "PL" else months_en
        sel_month_str = c2.selectbox(tr("Wybierz miesiąc"), month_opts)
        df_filtered = df[df['year'] == sel_year]
        if sel_month_str != months_pl[0] and sel_month_str != months_en[0]: df_filtered = df_filtered[df_filtered['month'] == month_opts.index(sel_month_str)]

        if not df_filtered.empty:
            total_time = df_filtered['czas'].sum(); total_dist = df_filtered['dystans'].sum(); total_tss = df_filtered['tss'].sum()
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='metric-card'><div class='metric-val'>{format_czas(total_time)}</div><div class='metric-label'>{tr('Czas całkowity')}</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='metric-card'><div class='metric-val'>{total_dist:.1f} km</div><div class='metric-label'>{tr('Dystans całkowity')}</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='metric-card'><div class='metric-val'>{int(total_tss)}</div><div class='metric-label'>TSS</div></div>", unsafe_allow_html=True)
            agg_df = df_filtered.groupby('dyscyplina').agg({'czas': 'sum', 'dystans': 'sum'}).reset_index()
            st.markdown("---")
            c_pie, c_table = st.columns([1.5, 1])
            with c_pie:
                st.markdown(f"#### {tr('Proporcja czasu wg dyscyplin')}")
                fig = go.Figure(data=[go.Pie(labels=[tr(d) for d in agg_df['dyscyplina']], values=agg_df['czas'], hole=.4, marker=dict(colors=[KOLORY_SPORT.get(d, '#8BA1B8') for d in agg_df['dyscyplina']]))])
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            with c_table:
                st.markdown(f"#### {tr('Szczegóły dyscyplin')}")
                for idx, row in agg_df.iterrows():
                    sport = row['dyscyplina']; col_hex = KOLORY_SPORT.get(sport, "#8BA1B8")
                    st.markdown(f"<div style='border-left: 4px solid {col_hex}; padding-left: 15px; margin-bottom: 15px; background: rgba(255,255,255,0.05); padding-top: 10px; padding-bottom: 10px; border-radius: 0 8px 8px 0;'><strong style='color:{col_hex}; font-size: 1.1em;'>{tr(sport).upper()}</strong><br><span style='color: #E2E8F0;'>{tr('Czas')}: <b>{format_czas(row['czas'])}</b></span> | <span style='color: #E2E8F0;'>{tr('Dystans')}: <b>{row['dystans']:.1f} km</b></span></div>", unsafe_allow_html=True)
        else: st.info(tr("Brak danych w wybranym okresie."))
    else: st.info(tr("Brak wykonanych aktywności."))

# --- 2. KALENDARZ ---
elif menu == tr("Kalendarz"):
    st.title(tr("Kalendarz"))
    target = ja if st.session_state.role != "coach" else st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY)

    # --- ZAKŁADKI: KALENDARZ I LISTA KART ---
    tab_kalendarz, tab_lista = st.tabs([f"📅 {tr('Kalendarz')}", f"📋 {tr('Lista aktywności')}"])

    with tab_kalendarz:
        col_c, col_s = st.columns([3, 1])
        with col_c:
            with st.expander(tr("Dodaj zawody / cel")):
                with st.form("add_race_form"):
                    r_name = st.text_input(tr("Nazwa zawodów"), placeholder="Ironman Frankfurt")
                    r_date = st.date_input(tr("Data zawodów"), date.today() + timedelta(days=30))
                    if st.form_submit_button(tr("Dodaj Start")):
                        db["wyscigi"] = list(db.get("wyscigi", [])) + [{"zawodnik": target, "nazwa": r_name, "data": str(r_date)}]
                        st.success(tr("Dodano zawody!")); st.rerun()

            if st.session_state.role == "coach":
                with st.expander(tr("PANEL PLANOWANIA (TRENER)"), expanded=True):
                    with st.form("plan_workout"):
                        c1, c2 = st.columns(2)
                        def_date = date.today()
                        if 'cal_click_date' in st.session_state and st.session_state.cal_click_date:
                            try: def_date = datetime.strptime(st.session_state.cal_click_date, "%Y-%m-%d").date()
                            except: pass
                        p_date = c1.date_input(tr("Data"), def_date)
                        p_sport = c2.selectbox(tr("Dyscyplina"), ["Bieganie", "Rower", "Pływanie", "Siłownia"], format_func=tr)
                        opts = ["-- Własny --"] + [s['nazwa'] for s in db.get("biblioteka", [])]
                        p_temp = st.selectbox(tr("Wczytaj Szablon"), opts, format_func=tr)
                        def_title = f"{tr(p_sport)}"; def_time = 60; def_tss = 50; p_steps = []
                        if p_temp != "-- Własny --":
                            tmpl = next((x for x in db["biblioteka"] if x['nazwa']==p_temp), None)
                            if tmpl: def_title = tmpl['nazwa']; def_time = sum([k['czas_total_sec'] for k in tmpl['kroki']]) // 60; p_steps = tmpl['kroki']
                        p_title = st.text_input(tr("Tytuł"), value=def_title)
                        c3, c4 = st.columns(2); p_time = c3.number_input(tr("Czas (min)"), value=def_time); p_tss = c4.number_input("Plan TSS", value=def_tss)
                        p_desc = st.text_area(tr("Instrukcje dla zawodnika"))
                        if st.form_submit_button(tr("Dodaj do Planu")):
                            save_data({"zawodnik": target, "dyscyplina": p_sport, "data": str(p_date), "tytul": p_title, "komentarz": p_desc, "czas": p_time, "tss": p_tss, "wykonany": False, "kroki": p_steps})
                            st.success(tr("Zaplanowano!")); st.session_state.cal_click_date = None; st.rerun()

            events = przygotuj_kalendarz(target)
            cal = calendar(events=events, options={"initialView": "dayGridMonth", "initialDate": str(date.today()), "firstDay": 1, "selectable": True, "dateClick": True, "height": 700}, key=f'cal_view_{target}', callbacks=['dateClick', 'eventClick'])
            if cal.get("dateClick"):
                selected = cal["dateClick"]["dateStr"]
                if selected != st.session_state.get('cal_click_date'): st.session_state.cal_click_date = selected; st.rerun()
            if cal.get("eventClick"):
                props = cal["eventClick"]["event"].get("extendedProps", {})
                if props.get("type") == "waga": st.info(f"{tr('Ważenie z dnia')} {props.get('data_str')}: **{props.get('waga')} kg**")
                else:
                    df_c = get_df(target); match_df = df_c[(df_c['data'].astype(str) == props.get('data_str')) & (df_c['dyscyplina'] == props.get('dyscyplina')) & (df_c['tytul'] == props.get('tytul'))]
                    st.markdown("---")
                    if not match_df.empty: 
                        st.subheader(f"{tr('Szczegóły:')} {props.get('tytul')}")
                        t_dict = match_df.iloc[0].to_dict()
                        render_analysis_dashboard(t_dict, get_user_zones(target, t_dict['dyscyplina']))
                    else: st.info(tr("Nie znaleziono szczegółów. Sprawdź listę zadań."))

        with col_s: render_tp_weekly_list(get_df(target))

    with tab_lista:
        st.markdown(f"### 📋 {tr('Ostatnie Aktywności')}")
        st.markdown("""
        <style>
        .trening-karta {
            background-color: #11151C; 
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 5px solid #00E5FF; 
            border-top: 1px solid #1F2735;
            border-right: 1px solid #1F2735;
            border-bottom: 1px solid #1F2735;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .trening-naglowek {
            display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;
        }
        .trening-tytul {
            font-size: 18px; font-weight: 800; color: #FFFFFF; margin-bottom: 2px;
        }
        .trening-data {
            font-size: 13px; color: #8BA1B8;
        }
        .trening-trimp {
            background-color: rgba(0, 229, 255, 0.15); 
            color: #00E5FF; padding: 5px 12px; border-radius: 20px;
            font-weight: 800; font-size: 14px; border: 1px solid rgba(0, 229, 255, 0.3);
        }
        .trening-statystyki {
            display: flex; justify-content: space-between; font-size: 15px;
            color: #E2E8F0; font-weight: 600;
        }
        .stat-item {
            display: flex; flex-direction: column;
        }
        .stat-label {
            font-size: 11px; color: #8BA1B8; text-transform: uppercase;
            margin-bottom: 2px; font-weight: 600; letter-spacing: 0.5px;
        }
        </style>
        """, unsafe_allow_html=True)

        def narysuj_karte(sport, data, dystans, czas, tss_val, ty_color="#00E5FF"):
            html = f'''
            <div class="trening-karta" style="border-left-color: {ty_color};">
                <div class="trening-naglowek">
                    <div>
                        <div class="trening-tytul">{sport}</div>
                        <div class="trening-data">{data}</div>
                    </div>
                    <div class="trening-trimp" style="color: {ty_color}; border-color: {ty_color}; background-color: {ty_color}20;">{tss_val} TSS</div>
                </div>
                <div class="trening-statystyki">
                    <div class="stat-item"><span class="stat-label">{tr("Dystans")}</span><span>{dystans}</span></div>
                    <div class="stat-item"><span class="stat-label">{tr("Czas")}</span><span>{czas}</span></div>
                </div>
            </div>
            '''
            st.markdown(html, unsafe_allow_html=True)

        df_lista = get_df(target)
        if not df_lista.empty:
            df_lista = df_lista[df_lista['wykonany'] == True].sort_values('data', ascending=False)
            if df_lista.empty:
                st.info(tr("Brak wykonanych aktywności."))
            else:
                for idx, t_row in df_lista.iterrows():
                    ikona_sport = "🏃" if t_row['dyscyplina'] == "Bieganie" else "🚴" if t_row['dyscyplina'] == "Rower" else "🏊" if t_row['dyscyplina'] == "Pływanie" else "🏋️"
                    sport_txt = f"{ikona_sport} {tr(t_row['dyscyplina']).upper()}"
                    kolor_dyscypliny = KOLORY_SPORT.get(t_row['dyscyplina'], "#00E5FF")
                    dyst = f"{t_row.get('dystans', 0)} km"
                    czs = format_czas(t_row.get('czas', 0))
                    
                    narysuj_karte(sport_txt, str(t_row['data']), dyst, czs, int(t_row.get('tss', 0)), kolor_dyscypliny)
                    
                    with st.expander(f"🔍 {tr('Analiza')}: {t_row['tytul']}"):
                        render_analysis_dashboard(t_row.to_dict(), get_user_zones(target, t_row['dyscyplina']))
        else:
            st.info(tr("Brak wykonanych aktywności."))


# --- 3. DASHBOARD ---
elif menu == tr("Dashboard"):
    st.title(tr("Centrum Zarządzania")); cols = st.columns(3)
    for idx, z in enumerate(ZAWODNICY): cols[idx%3].metric(f"{z}", f"{calculate_compliance(get_df(z))}%", help=tr("Dyscyplina (Wykonanie Planu)"))
    st.markdown("---")

    target_pmc = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, key="pmc_sel")
    next_race = get_next_race(target_pmc)
    if next_race:
        r_data, d_left = next_race
        d_str = f"{d_left} {tr('dni do startu')}" if d_left > 0 else tr("dzisiaj!")
        st.markdown(f"<div class='race-card'><div class='race-val'>🏆 {r_data['nazwa']}</div><div class='race-label'><b>{d_str}</b> ({r_data['data']})</div></div>", unsafe_allow_html=True)

    st.subheader(tr("Wykres Formy (PMC)"))
    df_pmc = calculate_pmc(get_df(target_pmc))
    c_ctl = int(df_pmc.iloc[-1]['CTL']) if not df_pmc.empty else 0
    c_atl = int(df_pmc.iloc[-1]['ATL']) if not df_pmc.empty else 0
    c_tsb = int(df_pmc.iloc[-1]['TSB']) if not df_pmc.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><div class='metric-val' style='color:#00E5FF;'>{c_ctl}</div><div class='metric-label'>{tr('Fitness (CTL)')}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-val' style='color:#FF1744;'>{c_atl}</div><div class='metric-label'>{tr('Zmęczenie (ATL)')}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='metric-val' style='color:{'#00E676' if c_tsb >= 0 else '#FF9100'};'>{c_tsb}</div><div class='metric-label'>{tr('Forma (TSB)')}</div></div>", unsafe_allow_html=True)

    if not df_pmc.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_pmc['date'], y=df_pmc['TSB'], name='TSB', marker_color='gold', opacity=0.5))
        fig.add_trace(go.Scatter(x=df_pmc['date'], y=df_pmc['CTL'], name='CTL', line=dict(color='#00E5FF', width=3)))
        fig.add_trace(go.Scatter(x=df_pmc['date'], y=df_pmc['ATL'], name='ATL', line=dict(color='#FF1744', width=2)))
        fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)

# --- 4. DANE ZAWODNIKA / FIZJOLOGIA ---
elif menu in [tr("Fizjologia"), tr("Dane zawodnika")]:
    st.title(tr("Dane Zawodnika i Fizjologia"))
    sel_user = st.selectbox(tr("Zawodnik:"), ZAWODNICY) if st.session_state.role == "coach" else ja
    tab1, tab2, tab3, tab4 = st.tabs([tr("Profil Mocy (CP)"), tr("Rekordy Biegowe"), tr("Badania & Trendy"), tr("Waga")])

    with tab1:
        st.markdown(f"### {tr('Profil Mocy Rowerowej (Automatyczny)')}")
        df_all = get_df(sel_user)
        df_90 = df_all[(df_all['dyscyplina'] == 'Rower') & (df_all['wykonany'] == True)].copy()
        curve_90 = {"5s":0, "10s":0, "20s":0, "1m":0, "5m":0, "10m":0, "20m":0, "60m":0}
        if not df_90.empty:
            df_90['data'] = pd.to_datetime(df_90['data'])
            df_90 = df_90[df_90['data'] >= pd.to_datetime(date.today() - timedelta(days=90))]
            for _, r in df_90.iterrows():
                for k in curve_90.keys():
                    if r.get('peak_powers', {}).get(k, 0) > curve_90[k]: curve_90[k] = r['peak_powers'][k]

        p_prof = next((x for x in db["power_profile"] if x['zawodnik'] == sel_user), {"5s":0, "10s":0, "20s":0, "1m":0, "5m":0, "10m":0, "20m":0, "60m":0})
        fig_cp = go.Figure()
        x_vals = ["5s", "10s", "20s", "1m", "5m", "10m", "20m", "60m"]
        x_sec = [5, 10, 20, 60, 300, 600, 1200, 3600]
        fig_cp.add_trace(go.Scatter(x=x_sec, y=[p_prof.get(k, 0) for k in x_vals], mode='lines+markers', name=tr('Wszystkie czasy (All-time)'), line=dict(color='#8BA1B8', width=2, dash='dash')))
        fig_cp.add_trace(go.Scatter(x=x_sec, y=[curve_90.get(k, 0) for k in x_vals], mode='lines+markers', name=tr('Ostatnie 90 dni'), line=dict(color='#00E5FF', width=4), line_shape='spline', fill='tozeroy', fillcolor='rgba(0, 229, 255, 0.1)'))
        fig_cp.update_layout(title=tr("Krzywa Mocy (MMP)"), template="plotly_dark", yaxis_title="W", xaxis=dict(type="log", tickvals=x_sec, ticktext=x_vals), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        st.plotly_chart(fig_cp, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('5s',0)} W</div><div class='metric-label'>5s</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('10s',0)} W</div><div class='metric-label'>10s</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('20s',0)} W</div><div class='metric-label'>20s</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('1m',0)} W</div><div class='metric-label'>1m</div></div>", unsafe_allow_html=True)
        c5, c6, c7, c8 = st.columns(4)
        c5.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('5m',0)} W</div><div class='metric-label'>5m</div></div>", unsafe_allow_html=True)
        c6.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('10m',0)} W</div><div class='metric-label'>10m</div></div>", unsafe_allow_html=True)
        c7.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('20m',0)} W</div><div class='metric-label'>20m</div></div>", unsafe_allow_html=True)
        c8.markdown(f"<div class='metric-card'><div class='metric-val'>{p_prof.get('60m',0)} W</div><div class='metric-label'>60m</div></div>", unsafe_allow_html=True)

        if st.session_state.role == "coach":
            with st.expander(tr("Edytuj Ręcznie")):
                with st.form("cp_form"):
                    k1, k2, k3, k4 = st.columns(4)
                    cp5s = k1.number_input("5s", value=p_prof.get("5s",0)); cp10s = k2.number_input("10s", value=p_prof.get("10s",0)); cp20s = k3.number_input("20s", value=p_prof.get("20s",0)); cp1m = k4.number_input("1m", value=p_prof.get("1m",0))
                    k5, k6, k7, k8 = st.columns(4)
                    cp5m = k5.number_input("5m", value=p_prof.get("5m",0)); cp10m = k6.number_input("10m", value=p_prof.get("10m",0)); cp20m = k7.number_input("20m", value=p_prof.get("20m",0)); cp60m = k8.number_input("60m", value=p_prof.get("60m",0))
                    if st.form_submit_button(tr("Aktualizuj")):
                        db["power_profile"] = [x for x in db["power_profile"] if x['zawodnik'] != sel_user] + [{"zawodnik": sel_user, "5s":cp5s, "10s":cp10s, "20s":cp20s, "1m":cp1m, "5m":cp5m, "10m":cp10m, "20m":cp20m, "60m":cp60m}]
                        st.success(tr("Zapisano!")); st.rerun()

    with tab2:
        st.markdown(f"### {tr('Najlepsze Czasy Biegowe (Personal Bests)')}")
        r_prof = next((x for x in db["run_records"] if x['zawodnik'] == sel_user), {"400m":0, "1km":0, "5km":0, "10km":0, "Półmaraton":0, "Maraton":0})
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('400m', 0))}</div><div class='metric-label'>400m</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('1km', 0))}</div><div class='metric-label'>1km</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('5km', 0))}</div><div class='metric-label'>5km</div></div>", unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        c4.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('10km', 0))}</div><div class='metric-label'>10km</div></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('Półmaraton', 0))}</div><div class='metric-label'>21.1km</div></div>", unsafe_allow_html=True)
        c6.markdown(f"<div class='metric-card'><div class='metric-val'>{format_duration(r_prof.get('Maraton', 0))}</div><div class='metric-label'>42.2km</div></div>", unsafe_allow_html=True)

        if st.session_state.role == "coach":
            with st.expander(tr("Edytuj Ręcznie (w sekundach)")):
                with st.form("run_form"):
                    k1, k2, k3 = st.columns(3)
                    r400 = k1.number_input("400m", value=int(r_prof.get("400m",0))); r1 = k2.number_input("1km", value=int(r_prof.get("1km",0))); r5 = k3.number_input("5km", value=int(r_prof.get("5km",0)))
                    k4, k5, k6 = st.columns(3)
                    r10 = k4.number_input("10km", value=int(r_prof.get("10km",0))); r21 = k5.number_input("21.1km", value=int(r_prof.get("Półmaraton",0))); r42 = k6.number_input("42.2km", value=int(r_prof.get("Maraton",0)))
                    if st.form_submit_button(tr("Aktualizuj")):
                        db["run_records"] = [x for x in db["run_records"] if x['zawodnik'] != sel_user] + [{"zawodnik": sel_user, "400m":r400, "1km":r1, "5km":r5, "10km":r10, "Półmaraton":r21, "Maraton":r42}]
                        st.success(tr("Zapisano!")); st.rerun()

    with tab3:
        if st.session_state.role == "coach":
            with st.expander(tr("Dodaj Wynik Badań")):
                with st.form("add_phys"):
                    c1, c2 = st.columns(2); p_date = c1.date_input(tr("Data")); p_type = c2.selectbox(tr("Wskaźnik"), ["VO2max", "W/kg", "LT1", "LT2", "Tkanka %"])
                    p_val = st.number_input(tr("Wartość"), step=0.1)
                    if st.form_submit_button(tr("Zapisz")): db["fizjologia"].append({"zawodnik": sel_user, "data": str(p_date), "typ": p_type, "wartosc": p_val}); st.success(tr("Dodano!"))
        df_ph = pd.DataFrame(db["fizjologia"])
        if not df_ph.empty:
            df_ph = df_ph[df_ph['zawodnik'] == sel_user]
            if not df_ph.empty:
                sel_metric = st.selectbox(tr("Wybierz wskaźnik:"), df_ph['typ'].unique())
                fig_ph = px.line(df_ph[df_ph['typ'] == sel_metric].sort_values('data'), x='data', y='wartosc', markers=True, title=f"{tr('Historia:')} {sel_metric}")
                fig_ph.update_traces(line_color='#FF00E6', line_width=3); fig_ph.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig_ph, use_container_width=True)

    with tab4:
        st.markdown(f"### {tr('Historia Wagi')}")
        if st.session_state.role == "coach":
            with st.expander(tr("Dodaj Wagę Zawodnika")):
                with st.form("add_w_form_coach"):
                    w_date = st.date_input(tr("Data ważenia"))
                    w_val = st.number_input(tr("Waga (kg)"), min_value=30.0, max_value=200.0, value=75.0, step=0.1)
                    if st.form_submit_button(tr("Zapisz Wagę")):
                        temp_w = list(db["waga"])
                        existing = [x for x in temp_w if x['zawodnik'] == sel_user and x['data'] == str(w_date)]
                        if existing: existing[0]['waga'] = w_val
                        else: temp_w.append({"zawodnik": sel_user, "data": str(w_date), "waga": w_val})
                        db["waga"] = temp_w; st.success(tr("Dodano!")); st.rerun()

        waga_df = pd.DataFrame(list(db.get("waga", [])))
        if not waga_df.empty:
            waga_df = waga_df[waga_df['zawodnik'] == sel_user]
            if not waga_df.empty:
                waga_df['data'] = pd.to_datetime(waga_df['data']).dt.date
                waga_df = waga_df.sort_values('data')
                fig_w = px.line(waga_df, x='data', y='waga', markers=True, title=tr("Trend Wagi (kg)"))
                fig_w.update_traces(line_color='#00C853', line_width=3)
                fig_w.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_w, use_container_width=True)
            else: st.info(tr("Brak wpisów wagi dla tego zawodnika."))
        else: st.info(tr("Brak wpisów wagi w bazie."))

# --- 5. RAPORTY PDF ---
elif menu == tr("Raporty"):
    st.title(tr("Centrum Raportowania")); 
    if st.session_state.role != "coach": st.warning(tr("Dla trenera.")); st.stop()
    sel_user = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY)
    c1, c2 = st.columns(2); sel_year = c1.number_input(tr("Rok"), 2023, 2030, date.today().year); sel_week = c2.number_input(tr("Tydzień"), 1, 52, date.today().isocalendar().week - 1)
    coach_note = st.text_area(tr("Komentarz Trenera"))
    if st.button(tr("Generuj PDF")):
        df = get_df(sel_user); df['data'] = pd.to_datetime(df['data']); week_data = df[(df['data'].dt.isocalendar().year == sel_year) & (df['data'].dt.isocalendar().week == sel_week)].sort_values('data')
        if not week_data.empty:
            b64 = base64.b64encode(create_weekly_pdf(sel_user, week_data, sel_week, sel_year, coach_note)).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Report.pdf"><button style="width:100%;padding:10px;background:#00E5FF;border:none;">{tr("POBIERZ PDF")}</button></a>', unsafe_allow_html=True)
        else: st.error(tr("Brak danych."))

# --- 6. STREFY ---
elif menu == tr("Strefy"):
    st.title(tr("Strefy"))
    sel_user = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY) if st.session_state.role=="coach" else ja
    
    # Wybór dyscypliny dla stref
    sel_disc = st.selectbox(tr("Dyscyplina"), ["Rower", "Bieganie", "Pływanie", "Siłownia", "Inne"], format_func=tr)
    
    # Pobieramy konkretne strefy tylko dla wybranej dyscypliny zawodnika
    user_data = get_user_zones(sel_user, sel_disc)
    
    c1, c2, c3 = st.columns(3)
    new_ftp = c1.number_input("FTP (W)", value=int(user_data.get("ftp", 250)))
    new_lthr = c2.number_input("LTHR (BPM)", value=int(user_data.get("lthr", 170)))
    
    if c3.button(tr("Przelicz / Zresetuj")): 
        user_data["zones_pwr"] = generuj_domyslne_strefy(new_ftp, new_lthr)[0].to_dict('records')
        user_data["zones_hr"] = generuj_domyslne_strefy(new_ftp, new_lthr)[1].to_dict('records')
        user_data["ftp"] = new_ftp
        user_data["lthr"] = new_lthr
        
        # Bezpieczny zapis do bazy dla konkretnej dyscypliny
        temp_db = db["strefy"]
        if sel_user not in temp_db: temp_db[sel_user] = {}
        temp_db[sel_user][sel_disc] = user_data
        db["strefy"] = temp_db
        st.rerun()
        
    c1, c2 = st.columns(2)
    with c1: st.subheader(tr("Moc")); edited_pwr = st.data_editor(pd.DataFrame(user_data["zones_pwr"]), column_order=["Strefa", "Min", "Max"], hide_index=True, key=f"pwr_{sel_user}_{sel_disc}")
    with c2: st.subheader(tr("Tętno")); edited_hr = st.data_editor(pd.DataFrame(user_data["zones_hr"]), column_order=["Strefa", "Min", "Max"], hide_index=True, key=f"hr_{sel_user}_{sel_disc}")
    
    if st.button(tr("Zapisz Zmiany")): 
        user_data["zones_pwr"] = edited_pwr.to_dict('records')
        user_data["zones_hr"] = edited_hr.to_dict('records')
        user_data["ftp"] = new_ftp
        user_data["lthr"] = new_lthr
        
        temp_db = db["strefy"]
        if sel_user not in temp_db: temp_db[sel_user] = {}
        temp_db[sel_user][sel_disc] = user_data
        db["strefy"] = temp_db
        st.success(tr("Zapisano strefy!"))

# --- 7. KREATOR (POJEDYNCZE TRENINGI) ---
elif menu == tr("Kreator"):
    st.title(tr("Kreator")); sport_creator = st.selectbox(tr("Dyscyplina"), ["Rower", "Bieganie", "Pływanie"], format_func=tr)
    c1, c2 = st.columns([1, 2]); 
    if 'pro_steps' not in st.session_state: st.session_state['pro_steps'] = []
    with c1:
        opts = ["-- Własny --"] + [s.get('nazwa','Bez nazwy') for s in db.get("biblioteka", [])]
        load = st.selectbox(tr("Szablon"), opts, format_func=tr)
        if load != "-- Własny --" and st.button(tr("Załaduj")): st.session_state['pro_steps'] = list(next((x for x in db["biblioteka"] if x['nazwa']==load), None)['kroki']); st.rerun()
        st.markdown("---")
        tab_single, tab_set = st.tabs([tr("Pojedynczy Krok"), tr("Seria Interwałów")])
        with tab_single:
            typ = st.selectbox(tr("Typ"), ["Rozgrzewka", "Interwał", "Przerwa", "Rozjazd"], format_func=tr)
            jednostka = st.radio(tr("Jednostka"), [tr("Czas"), tr("Dystans")], horizontal=True, key="ts_jedn")
            if jednostka == tr("Czas"): v_time = st.number_input(tr("Czas (min)"), 0.5, 300.0, 10.0, step=0.5, key="ts_time"); v_dist = 0.0; is_dist = False
            else: v_time = 0.0; v_dist = st.number_input(tr("Dystans (km)"), 0.1, 200.0, 1.0, step=0.1, key="ts_dist"); is_dist = True
            mode = st.selectbox(tr("Intensywność"), ["Moc %FTP", "Waty", "Tętno", "Tempo", "RPE"], key="ts_mode")
            k1_s, k2_s = st.columns(2); v1, v2 = 0.0, 0.0
            if "Waty" in mode: v1=k1_s.number_input(tr("Od"),0,2000,150,5, key="ts_w1"); v2=k2_s.number_input(tr("Do"),0,2000,160,5, key="ts_w2")
            elif "%" in mode: v1=k1_s.number_input(tr("Od"),0,300,70,5, key="ts_p1"); v2=k2_s.number_input(tr("Do"),0,300,75,5, key="ts_p2")
            elif "Tętno" in mode: v1=k1_s.number_input(tr("Od"),0,220,140,1, key="ts_h1"); v2=k2_s.number_input(tr("Do"),0,220,150,1, key="ts_h2")
            elif "Tempo" in mode: t1=k1_s.text_input(tr("Od"),"5:00", key="ts_t1"); t2=k2_s.text_input(tr("Do"),"4:50", key="ts_t2"); v1=pace_str_to_float(t1); v2=pace_str_to_float(t2)
            else: v1=st.slider("RPE",1,10,5, key="ts_r1"); v2=v1
            if st.button(tr("Dodaj Krok")):
                sec = v_time * 60
                if is_dist: sec = int(v_dist * ((v1 + v2) / 2) * 60) if mode == "Tempo" and v1 > 0 else int(v_dist * (5.0 if sport_creator == "Bieganie" else 2.0 if sport_creator == "Rower" else 20.0) * 60)
                st.session_state['pro_steps'].append({"typ": typ, "tryb": mode, "val_min": v1, "val_max": v2, "is_distance": is_dist, "czas_total_sec": sec, "dystans_km": v_dist}); st.rerun()
        with tab_set:
            reps = st.number_input(tr("Liczba powtórzeń"), 2, 50, 5)
            st.markdown(f"<h4 style='color: #FF1744 !important; font-size: 1em;'>{tr('Praca')}</h4>", unsafe_allow_html=True)
            w_jedn = st.radio(tr("Jednostka")+" 1", [tr("Czas"), tr("Dystans")], horizontal=True, key="w_jedn", label_visibility="collapsed")
            if w_jedn == tr("Czas"): w_v_time = st.number_input(tr("Czas (min)"), 0.5, 300.0, 3.0, step=0.5, key="w_time"); w_v_dist=0.0; w_is_dist=False
            else: w_v_time=0.0; w_v_dist = st.number_input(tr("Dystans (km)"), 0.1, 50.0, 1.0, step=0.1, key="w_dist"); w_is_dist=True
            w_mode = st.selectbox(tr("Intensywność")+" 1", ["Moc %FTP", "Waty", "Tętno", "Tempo", "RPE"], key="w_mode", label_visibility="collapsed")
            wk1, wk2 = st.columns(2); wv1, wv2 = 0.0, 0.0
            if "Waty" in w_mode: wv1=wk1.number_input(tr("Od"),0,2000,250,5, key="ww1"); wv2=wk2.number_input(tr("Do"),0,2000,260,5, key="ww2")
            elif "%" in w_mode: wv1=wk1.number_input(tr("Od"),0,300,105,5, key="wp1"); wv2=wk2.number_input(tr("Do"),0,300,110,5, key="wp2")
            elif "Tętno" in w_mode: wv1=wk1.number_input(tr("Od"),0,220,170,1, key="wh1"); wv2=wk2.number_input(tr("Do"),0,220,180,1, key="wh2")
            elif "Tempo" in w_mode: t1=wk1.text_input(tr("Od"),"4:00", key="wt1"); t2=wk2.text_input(tr("Do"),"3:50", key="wt2"); wv1=pace_str_to_float(t1); wv2=pace_str_to_float(t2)
            else: wv1=st.slider("RPE",1,10,8, key="wr1"); wv2=wv1
            st.markdown(f"<h4 style='color: #1976D2 !important; font-size: 1em;'>{tr('Odpoczynek')}</h4>", unsafe_allow_html=True)
            r_jedn = st.radio(tr("Jednostka")+" 2", [tr("Czas"), tr("Dystans")], horizontal=True, key="r_jedn", label_visibility="collapsed")
            if r_jedn == tr("Czas"): r_v_time = st.number_input(tr("Czas (min)"), 0.5, 300.0, 2.0, step=0.5, key="r_time"); r_v_dist=0.0; r_is_dist=False
            else: r_v_time=0.0; r_v_dist = st.number_input(tr("Dystans (km)"), 0.1, 50.0, 0.5, step=0.1, key="r_dist"); r_is_dist=True
            r_mode = st.selectbox(tr("Intensywność")+" 2", ["Moc %FTP", "Waty", "Tętno", "Tempo", "RPE"], key="r_mode", label_visibility="collapsed")
            rk1, rk2 = st.columns(2); rv1, rv2 = 0.0, 0.0
            if "Waty" in r_mode: rv1=rk1.number_input(tr("Od"),0,2000,100,5, key="rw1"); rv2=rk2.number_input(tr("Do"),0,2000,110,5, key="rw2")
            elif "%" in r_mode: rv1=rk1.number_input(tr("Od"),0,300,50,5, key="rp1"); rv2=rk2.number_input(tr("Do"),0,300,55,5, key="rp2")
            elif "Tętno" in r_mode: rv1=rk1.number_input(tr("Od"),0,220,110,1, key="rh1"); rv2=rk2.number_input(tr("Do"),0,220,120,1, key="rh2")
            elif "Tempo" in r_mode: t1=rk1.text_input(tr("Od"),"6:00", key="rt1"); t2=rk2.text_input(tr("Do"),"5:50", key="rt2"); rv1=pace_str_to_float(t1); rv2=pace_str_to_float(t2)
            else: rv1=st.slider("RPE",1,10,3, key="rr1"); rv2=rv1
            if st.button(tr("Dodaj Serię")):
                for _ in range(int(reps)):
                    w_sec = w_v_time * 60
                    if w_is_dist: w_sec = int(w_v_dist * ((wv1+wv2)/2 if w_mode=="Tempo" and wv1>0 else (5.0 if sport_creator=="Bieganie" else 2.0)) * 60)
                    st.session_state['pro_steps'].append({"typ": "Interwał", "tryb": w_mode, "val_min": wv1, "val_max": wv2, "is_distance": w_is_dist, "czas_total_sec": w_sec, "dystans_km": w_v_dist})
                    r_sec = r_v_time * 60
                    if r_is_dist: r_sec = int(r_v_dist * ((rv1+rv2)/2 if r_mode=="Tempo" and rv1>0 else (5.0 if sport_creator=="Bieganie" else 2.0)) * 60)
                    st.session_state['pro_steps'].append({"typ": "Przerwa", "tryb": r_mode, "val_min": rv1, "val_max": rv2, "is_distance": r_is_dist, "czas_total_sec": r_sec, "dystans_km": r_v_dist})
                st.rerun()
        if st.session_state['pro_steps']:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(tr("Wyczyść Kreator")): st.session_state['pro_steps'] = []; st.rerun()
    with c2:
        if st.session_state['pro_steps']:
            fig = go.Figure(); ct=0
            for k in st.session_state['pro_steps']: 
                dur = k.get('czas_total_sec', 300)/60
                if dur == 0: dur = 5
                time_or_dist_label = f"{k.get('dystans_km', 0)} km" if k.get('is_distance') else f"{int(dur)} min"
                avg_val = (k.get('val_min',0)+k.get('val_max',0))/2
                if avg_val == 0: avg_val = 50
                display_y = 100 / avg_val if "Tempo" in k.get('tryb', '') and avg_val > 0 else avg_val
                intensity_label = f"{float_to_pace_str(k['val_min'])}-{float_to_pace_str(k['val_max'])}" if "Tempo" in k.get('tryb', '') else f"{int(k.get('val_min',0))}-{int(k.get('val_max',0))}"
                fig.add_trace(go.Bar(x=[ct+dur/2], y=[display_y], width=[dur], name=f"{tr(k['typ'])}", marker_color=KOLORY_BLOKOW.get(k['typ']), text=f"{time_or_dist_label}<br>{intensity_label}", textposition="auto"))
                ct+=dur
            fig.update_layout(template="plotly_dark", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)
            with st.form("sv"): 
                n=st.text_input(tr("Nazwa")); 
                if st.form_submit_button(tr("Zapisz")): 
                    db["biblioteka"] = list(db.get("biblioteka", [])) + [{"nazwa":n, "kroki":st.session_state['pro_steps'], "dyscyplina":sport_creator}]
                    st.success(tr("Dodano!")); st.session_state['pro_steps'] = []; st.rerun()

# --- 8. BIBLIOTEKA PLANÓW ---
elif menu == tr("Plany"):
    st.title(f"📚 {tr('Biblioteka Planów')}")
    if st.session_state.role != "coach":
        st.warning(tr("Dla trenera."))
        st.stop()

    tab1, tab2 = st.tabs([tr("Przypisz Plan"), tr("Kreator Planów")])

    with tab1:
        st.markdown(f"### {tr('Przypisz gotowy plan zawodnikowi')}")
        if not db.get("plany"):
            st.info(tr("Brak zapisanych planów w bazie."))
        else:
            with st.form("assign_plan_form"):
                c1, c2 = st.columns(2)
                p_athlete = c1.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY)
                p_plan_name = c2.selectbox(tr("Wybierz Plan"), [p['nazwa'] for p in db.get("plany", [])])
                p_start_date = st.date_input(tr("Data startu"), date.today())
                if st.form_submit_button(tr("Przypisz Plan")):
                    selected_plan = next((p for p in db["plany"] if p['nazwa'] == p_plan_name), None)
                    if selected_plan:
                        for item in selected_plan['treningi']:
                            target_date = p_start_date + timedelta(days=item['dzien'] - 1)
                            tmpl = next((x for x in db["biblioteka"] if x['nazwa'] == item['szablon']), None)
                            if tmpl:
                                t_time = sum([k.get('czas_total_sec', 0) for k in tmpl.get('kroki', [])]) // 60
                                plan_entry = {
                                    "zawodnik": p_athlete, "dyscyplina": tmpl.get('dyscyplina', 'Inne'), 
                                    "data": str(target_date), "tytul": tmpl['nazwa'], "komentarz": "", 
                                    "czas": t_time, "tss": 50, "wykonany": False, "kroki": tmpl.get('kroki', []),
                                    "komentarze_treningu": []
                                }
                                save_data(plan_entry)
                        st.success(tr("Plan przypisany!"))
                        st.rerun()

    with tab2:
        st.markdown(f"### {tr('Tworzenie Planu (Makro/Mikrocykl)')}")
        if "new_plan_steps" not in st.session_state: st.session_state.new_plan_steps = []
        opts = [s['nazwa'] for s in db.get("biblioteka", [])]

        if not opts:
            st.warning(tr("Najpierw stwórz pojedyncze treningi (szablony) w zakładce Kreator."))
        else:
            c3, c4 = st.columns(2)
            day_input = c3.number_input(tr("Dzień (np. 1 = start, 2 = kolejny dzień)"), min_value=1, value=1)
            tmpl_sel = c4.selectbox(tr("Szablon"), opts)

            if st.button(tr("Dodaj Trening do Planu")):
                st.session_state.new_plan_steps.append({"dzien": day_input, "szablon": tmpl_sel})
                st.session_state.new_plan_steps = sorted(st.session_state.new_plan_steps, key=lambda x: x['dzien'])
                st.rerun()

            if st.session_state.new_plan_steps:
                st.table(pd.DataFrame(st.session_state.new_plan_steps))
                with st.form("save_macro_plan"):
                    plan_name = st.text_input(tr("Nazwa Planu (np. 4 tygodnie Baza)"))
                    if st.form_submit_button(tr("Zapisz Plan")):
                        if plan_name:
                            db["plany"] = list(db.get("plany", [])) + [{"nazwa": plan_name, "treningi": st.session_state.new_plan_steps}]
                            st.session_state.new_plan_steps = []
                            st.success(tr("Zapisano!"))
                            st.rerun()

# --- 9. BAZA ---
elif menu == tr("Baza"): 
    if st.button(tr("RESET DANYCH")): db["treningi"]=[]; db["run_records"]=[]; db["power_profile"]=[]; db["waga"]=[]; db["chat"]=[]; db["wyscigi"]=[]; db["plany"]=[]; st.session_state.session_treningi=[]; st.rerun()
