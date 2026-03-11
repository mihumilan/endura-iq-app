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
import io
import zipfile
from streamlit_calendar import calendar

# --- KRYPTOGRAFIA (BEZPIECZEŃSTWO RODO) ---
import bcrypt
from cryptography.fernet import Fernet

# Bezpieczne ładowanie klucza z sejfu Streamlit (Secrets)
FERNET_KEY = st.secrets["FERNET_KEY"].encode('utf-8')
cipher_suite = Fernet(FERNET_KEY)

st.set_page_config(page_title="Endura IQ", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- MODUŁ BAZY DANYCH MONGODB (CLOUD) ---
import pymongo

@st.cache_resource
def get_database_client():
    # Bezpieczne ładowanie hasła z sejfu Streamlit
    uri = st.secrets["MONGO_URI"]
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

# Inicjalizacja profesjonalnej bazy w chmurze
mongo_client = get_database_client()
db = MongoDBWrapper(mongo_client)

# ==========================================
# 1. KONFIGURACJA, TŁUMACZENIA I CSS GŁÓWNY
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
        "Ocena Treningu (RPE i Samopoczucie)": "Workout Rating (RPE & Feeling)",
        "Szablon / Fragment": "Template / Fragment",
        "🔄 Pobierz automatycznie z Garmin Connect": "🔄 Auto-Sync from Garmin Connect",
        "Aplikacja sama znajdzie Twoje ostatnie treningi w chmurze Garmina, pobierze ich ukryte pliki TCX i dokona pełnej analizy.": "The app will automatically find your recent workouts in the Garmin cloud, download their hidden TCX files, and perform a full analysis.",
        "Ile ostatnich aktywności sprawdzić?": "How many recent activities to check?",
        "📥 Pobierz teraz": "📥 Download now",
        "Łączenie z Garmin Connect i pobieranie": "Connecting to Garmin Connect and downloading",
        "aktywności... (to potrwa kilkanaście sekund)": "activities... (this will take a few seconds)",
        "Zakończono! Pomyślnie pobrano i zanalizowano": "Finished! Successfully downloaded and analyzed",
        "nowych treningów.": "new workouts.",
        "Wszystkie treningi z wybranego okresu są już w Twojej bazie Endura IQ. Nie znaleziono nowych.": "All workouts from the selected period are already in your Endura IQ database. No new ones found.",
        "Błąd synchronizacji:": "Synchronization error:",
        "⚠️ Zanim pobierzesz treningi, musisz podać dane logowania do Garmina w zakładce 'Dane zawodnika' -> 'Integracje 🔗'": "⚠️ Before downloading workouts, you must provide your Garmin login credentials in the 'Athlete Data' -> 'Integrations 🔗' tab.",
        "📂 Ręczne wgranie pliku (TCX)": "📂 Manual file upload (TCX)",
        "Pełna Analiza (Wykresy i Mapa)": "Full Analysis (Charts & Map)",
        "Szczegóły:": "Details:",
        "❌ Zamknij panel dnia": "❌ Close day panel",
        "🗓️ Zarządzaj Dniem": "🗓️ Manage Day",
        "Wybierz datę (kliknij w kalendarzu u góry lub wpisz ręcznie):": "Select a date (click on the calendar above or enter manually):",
        "📌 Zostaw notatkę na dzień": "📌 Leave a note for",
        "(np. ograniczony czas, wyjazd):": "(e.g., limited time, travel):",
        "Komentarz do dnia": "Day comment",
        "Zapisz Notatkę": "Save Note",
        "Notatka przypięta do kalendarza!": "Note pinned to calendar!",
        "🏆 Dodaj Zawody w dniu": "🏆 Add Race on",
        "⚡ Zaplanuj Trening (Trener) -": "⚡ Plan Workout (Coach) -",
        "-- Własny --": "-- Custom --",
        "Bez nazwy": "Unnamed",
        "💾 Zapisz / Aktualizuj": "💾 Save / Update",
        "🔄 Zastąp": "🔄 Replace",
        "➕ Doklej": "➕ Append",
        "🗑️ Usuń": "🗑️ Delete",
        "Usunięto!": "Deleted!",
        "Zaktualizowano istniejący szablon!": "Existing template updated!",
        "Zapisano nowy szablon!": "New template saved!",
        "🗺️ Mapa trasy GPS": "🗺️ GPS Route Map",
        "⏱️ Interwały": "⏱️ Intervals",
        "📊 Czas w strefach": "📊 Time in Zones",
        "💬 Komentarze do rozmowy": "💬 Conversation comments",
        "Dodaj szybką wiadomość...": "Add a quick message...",
        "Wyślij": "Send",
        "Integracje 🔗": "Integrations 🔗",
        "📝 Ankieta Profilowa": "📝 Profile Survey",
        "🔵 Autoryzacja Garmin Connect": "🔵 Garmin Connect Authorization",
        "Podaj dane logowania, aby aplikacja Endura IQ mogła automatycznie wysyłać zaplanowane treningi prosto do Twojego kalendarza w zegarku.": "Provide login details so the Endura IQ app can automatically send planned workouts straight to your watch calendar.",
        "E-mail Garmin": "Garmin Email",
        "Hasło Garmin": "Garmin Password",
        "Zapisz połączenie z chmurą": "Save cloud connection",
        "Zapisano dane. Od teraz możesz wysyłać treningi prosto z kalendarza!": "Data saved. From now on, you can send workouts straight from the calendar!",
        "Profil Startowy (Ankieta):": "Initial Profile (Survey):",
        "Data wypełnienia:": "Fill date:",
        "Wzrost:": "Height:",
        "Tętno spoczynkowe:": "Resting Heart Rate:",
        "Zdrowie i Urazy": "Health and Injuries",
        "Cukrzyca:": "Diabetes:",
        "Astma:": "Asthma:",
        "Choroby serca:": "Heart diseases:",
        "Problemy z kręgosłupem/stawami:": "Spine/joint problems:",
        "Urazy/Kontuzje:": "Injuries:",
        "Brak": "None",
        "Styl życia": "Lifestyle",
        "Praca:": "Work:",
        "Średni sen:": "Average sleep:",
        "Harmonogram dostępności (godziny:minuty/dzień)": "Availability schedule (hours:minutes/day)",
        "Cele i Doświadczenie": "Goals and Experience",
        "Staż w sportach:": "Sports experience:",
        "Cel główny:": "Main goal:",
        "Główne zawody (Kategoria A):": "Main race (A Race):",
        "Najsłabsze strony:": "Weaknesses:",
        "Dostępny Sprzęt": "Available Equipment",
        "Basen/Wody otwarte:": "Pool/Open water:",
        "Siłownia:": "Gym:",
        "Trenażer Smart:": "Smart Trainer:",
        "Pomiar mocy:": "Power meter:",
        "Profil Psychologiczny (1-5)": "Psychological Profile (1-5)",
        "Odporność na ból:": "Pain tolerance:",
        "Koncentracja w stresie:": "Focus under stress:",
        "Dyscyplina treningowa:": "Training discipline:",
        "Zdolność do odpoczynku:": "Ability to rest:",
        "Ten zawodnik nie wypełnił jeszcze ankiety startowej.": "This athlete hasn't filled out the initial survey yet.",
        "✏️ Edytuj ocenę": "✏️ Edit rating",
        "RPE (Odczuwany wysiłek)": "RPE (Perceived Exertion)",
        "Zrobione! Trening jest gotowy. Twój zegarek będzie pilnował intensywności.": "Done! Workout is ready. Your watch will monitor the intensity.",
        "Błąd po stronie serwerów Garmin:": "Garmin servers error:",
        "Brak danych logowania do Garmin Connect. Uzupełnij je najpierw w zakładce 'Dane Zawodnika' -> 'Integracje 🔗'.": "No Garmin Connect login credentials. Fill them in the 'Athlete Data' -> 'Integrations 🔗' tab first.",
        "⚠️ Błąd logowania! Sprawdź czy e-mail/hasło są poprawne. Upewnij się też, że na koncie Garmin masz wyłączoną weryfikację dwuetapową (2FA).": "⚠️ Login error! Check if email/password are correct. Make sure 2FA is disabled on your Garmin account.",
        "⚠️ Błąd integracji:": "⚠️ Integration error:",
        "Logowanie": "Log In",
        "Rejestracja": "Sign Up",
        "Dołącz do Endura IQ i rozpocznij swoją profesjonalną drogę.": "Join Endura IQ and start your professional journey.",
        "Twój Login / Nick (musi być unikalny)": "Your Username (must be unique)",
        "Adres E-mail": "Email Address",
        "Imię i Nazwisko": "Full Name",
        "Utwórz konto": "Create Account",
        "Użytkownik o takim loginie już istnieje. Wybierz inny!": "Username already exists. Choose another!",
        "Wypełnij poprawnie wszystkie pola (Login i Imię min. 3 znaki, Hasło min. 4, poprawny email).": "Fill all fields correctly (Username and Name min 3 chars, Password min 4 chars, valid email).",
        "Konto utworzone! Możesz się teraz zalogować w zakładce obok.": "Account created! You can now log in on the adjacent tab.",
        "Próg Tempo (MM:SS/km)": "Threshold Pace (MM:SS/km)",
        "Próg Tempo (MM:SS/100m)": "Threshold Pace (MM:SS/100m)",
        "📊 Historia": "📊 History",
        "Historia treningowa": "Training History",
        "Średnia objętość (ostatnie 3 miesiące) [godz/tydz]:": "Average volume (last 3 months) [hours/week]:",
        "Aktualne / Szacowane Wartości (wpisz 0 jeśli nie znasz)": "Current / Estimated Values (enter 0 if unknown)",
        "Szacowane FTP (W):": "Estimated FTP (W):",
        "Próg Mleczanowy - LTHR (BPM):": "Lactate Threshold - LTHR (BPM):",
        "Tętno Maksymalne (BPM):": "Max HR (BPM):",
        "Gotowość na Tydzień Testowy:": "Readiness for Testing Week:",
        "Testy wyznaczające dokładne strefy i krzywą profilu mocy (m.in. sprint 5s, 1min, 5min, 20min).": "Tests to determine precise zones and power profile curve (e.g., 5s sprint, 1m, 5m, 20m).",
        "Tak, zróbmy pełne testy (Profil Mocy: 5s, 1m, 5m, 20m + bieganie)": "Yes, let's do full tests (Power Profile: 5s, 1m, 5m, 20m + run)",
        "Nie, mam aktualne badania/wyniki": "No, I have recent test results/baselines",
        "Zdam się na decyzję trenera": "I'll leave it to the coach",
        "Oczekiwania wobec trenera": "Expectations from Coach",
        "Preferowany styl komunikacji:": "Preferred communication style:",
        "Zbalansowany (dane + wsparcie)": "Balanced (data + support)",
        "Tylko suche dane i analiza": "Strictly data and analysis",
        "Dużo motywacji i wsparcia mentalnego": "High motivation & mental support",
        "Historia i Parametry Wyjściowe": "History & Baseline Metrics",
        "Tydzień Testowy:": "Testing Week:",
        "Komunikacja:": "Communication:",
        "Średnia objętość:": "Avg Volume:",
        "Godz.": "Hrs",
        "Min.": "Mins",
        "Priorytet treningu (1-10):": "Training Priority (1-10):",
        "1 = Życie prywatne, 10 = Trening 100%": "1 = Personal life, 10 = Training 100%",
        "Ze względów bezpieczeństwa i prywatności, tylko zawodnik ma dostęp do swoich danych logowania Garmin Connect.": "For security and privacy reasons, only the athlete has access to their Garmin Connect login credentials.",
        "⚙️ Konto": "⚙️ Account",
        "Usuwanie Konta": "Account Deletion",
        "Uwaga: Ta operacja jest nieodwracalna. Zostaną usunięte wszystkie Twoje treningi, statystyki, wiadomości i integracje.": "Warning: This operation is irreversible. All your workouts, stats, messages, and integrations will be deleted.",
        "Wpisz 'USUŃ' aby potwierdzić:": "Type 'DELETE' to confirm:",
        "Trwale usuń moje konto": "Permanently delete my account",
        "Wpisz słowo USUŃ poprawnie.": "Type the word correctly.",
        "USUŃ": "DELETE",
        "Automatyczna synchronizacja w tle...": "Automatic background sync...",
        "Pobrano automatycznie nowych treningów:": "Automatically downloaded new workouts:",
        "📤 Wyślij nadchodzące treningi na zegarek (7 dni)": "📤 Send upcoming workouts to watch (7 days)",
        "Wyślij wszystkie zaplanowane treningi na najbliższe 7 dni jednym kliknięciem.": "Send all planned workouts for the next 7 days with one click.",
        "🚀 Wyślij zaplanowany tydzień": "🚀 Send planned week",
        "Brak zaplanowanych treningów strukturalnych na najbliższe 7 dni.": "No structured workouts planned for the next 7 days.",
        "Wysyłanie treningów...": "Sending workouts...",
        "Pomyślnie wysłano": "Successfully sent",
        "treningów na zegarek!": "workouts to watch!",
        "Napotkano błąd przy części treningów:": "Encountered an error with some workouts:",
        "Wyrażam zgodę na przetwarzanie moich danych dotyczących zdrowia (tętno, waga, informacje o kontuzjach) w celu realizacji planu treningowego.": "I explicitly consent to the processing of my health data (heart rate, weight, injury information) for the purpose of executing the training plan.",
        "Musisz wyrazić zgodę na przetwarzanie danych medycznych (wymóg prawny RODO).": "You must consent to the processing of medical data (GDPR legal requirement)."
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
        
        section[data-testid="stSidebar"] div.stButton > button {
            background: transparent !important;
            color: #8BA1B8 !important;
            border: 1px solid #1F2735 !important;
            padding: 8px !important;
            font-size: 12px !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            box-shadow: none !important;
            margin-top: 40px !important;
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            color: #FF5252 !important;
            border-color: #FF5252 !important;
            background: #11151C !important;
        }
        
        div[data-testid="stFileUploader"] { border: 2px dashed #00E5FF; background-color: rgba(0,229,255,0.03); border-radius: 12px; }
        div[data-testid="stExpander"] { border: 1px solid #1F2735 !important; border-radius: 10px !important; background-color: #11151C !important; }
        div[data-testid="stNumberInput"] input:disabled { background-color: #1A202C; color: #64748B; }
        thead tr th { background-color: #00E5FF !important; color: #000 !important; font-weight: 800 !important; }
        tbody tr:nth-of-type(even) { background-color: #11151C; }
        tbody tr:nth-of-type(odd) { background-color: #161B22; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

cal_css = """
    .fc-theme-standard td, .fc-theme-standard th { border-color: #1F2735 !important; }
    .fc-daygrid-day { background-color: #0A0D12 !important; }
    .fc-day-today { background-color: #161B22 !important; }
    .fc-col-header-cell { background-color: #11151C !important; color: #8BA1B8 !important; padding: 10px 0 !important; text-transform: uppercase; font-size: 0.85rem;}
    .fc-daygrid-day-number { color: #E2E8F0 !important; font-weight: 600; font-size: 1.1rem; padding: 8px !important; text-decoration: none !important; }
    .fc-toolbar-title { color: #00E5FF !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 1px; font-size: 1.4rem !important;}
    .fc-button-primary { background-color: #11151C !important; border: 1px solid #00E5FF !important; color: #00E5FF !important; text-transform: uppercase; font-weight: bold !important; border-radius: 6px !important; padding: 6px 12px !important;}
    .fc-button-primary:hover { background-color: #00E5FF !important; color: #000 !important; }
    
    .fc-event {
        border-radius: 6px !important;
        padding: 5px 8px !important;
        margin: 3px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
        cursor: pointer !important;
        transition: transform 0.2s ease, filter 0.2s ease !important;
    }
    .fc-event:hover {
        transform: translateY(-2px) scale(1.02) !important;
        filter: brightness(1.2) !important;
        z-index: 10 !important;
    }
    
    .completed-workout-green { background: linear-gradient(135deg, #00C853 0%, #009624 100%) !important; border-left: 4px solid #00FF66 !important; color: #FFF !important; }
    .completed-workout-yellow { background: linear-gradient(135deg, #FFD600 0%, #F57F17 100%) !important; border-left: 4px solid #FFFF00 !important; color: #000 !important; }
    .completed-workout-red { background: linear-gradient(135deg, #D50000 0%, #8E0000 100%) !important; border-left: 4px solid #FF5252 !important; color: #FFF !important; }
    .planned-workout { background: #11151C !important; border: 2px dashed #00E5FF !important; color: #00E5FF !important; }
    
    .weight-event { background: #2D3748 !important; color: #A0AEC0 !important; border-radius: 20px !important; font-size: 0.8rem !important; padding: 2px 8px !important; text-align: center;}
    .race-event { background: linear-gradient(135deg, #FFD700 0%, #F57F17 100%) !important; color: #000 !important; font-weight: 900 !important; text-transform: uppercase;}
    .day-note-event { background: transparent !important; color: #FFD700 !important; font-style: italic !important; font-weight: 500 !important; box-shadow: none !important; text-align: right; }
"""

inject_custom_css()

# ==========================================
# 2. DYNAMICZNA STRUKTURA UŻYTKOWNIKÓW 
# ==========================================
KOLORY_SPORT = {"Pływanie": "#2979FF", "Rower": "#FF1744", "Bieganie": "#00E676", "Siłownia": "#9E9E9E", "Inne": "#FF9100"}
KOLORY_BLOKOW = {"Rozgrzewka": "#558B2F", "Interwał": "#D32F2F", "Przerwa": "#1976D2", "Rozjazd": "#616161"}
ZONE_COLORS = ["#9E9E9E", "#2196F3", "#4CAF50", "#FFC107", "#FF5722", "#D50000", "#880E4F"]

if "users_db" not in db or not isinstance(db.get("users_db"), dict): 
    # Dla bezpieczeństwa RODO - przy resecie bazy nowe hasło admina od razu jest hashowane
    db["users_db"] = {"admin": {"password": bcrypt.hashpw("trener123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "coach", "fullname": "Administrator (Trener)"}}
if "zawodnicy_list" not in db or not isinstance(db.get("zawodnicy_list"), list):
    db["zawodnicy_list"] = []

ZAWODNICY = db.get("zawodnicy_list", [])

for key in ["treningi", "strefy", "wyscigi", "biblioteka", "fizjologia", "power_profile", "run_records", "waga", "chat", "plany", "garmin_creds", "zawodnicy_info", "day_notes"]:
    if key not in db: db[key] = {} if key in ["strefy", "garmin_creds", "zawodnicy_info"] else []
if isinstance(db["strefy"], list): db["strefy"] = {}
if isinstance(db["garmin_creds"], list): db["garmin_creds"] = {}
if isinstance(db["zawodnicy_info"], list): db["zawodnicy_info"] = {}

# --- AUTO-HEALER BAZY DANYCH (KONSOLIDACJA TRENINGÓW) ---
if "session_treningi" not in st.session_state: 
    st.session_state.session_treningi = list(db["treningi"])

def consolidate_workouts():
    db_treningi = list(db.get("treningi", []))
    unexecuted = []
    executed = []
    
    for w in db_treningi:
        if w.get("wykonany"):
            executed.append(w)
        else:
            unexecuted.append(w)
            
    modified = False
    new_db = []
    
    for ew in executed:
        matching_plan = next((p for p in unexecuted if p.get("zawodnik") == ew.get("zawodnik") and str(p.get("data")) == str(ew.get("data")) and p.get("dyscyplina") == ew.get("dyscyplina")), None)
        
        if matching_plan:
            if not ew.get("plan_czas"):
                ew["plan_czas"] = matching_plan.get("czas", 0)
                ew["plan_tss"] = matching_plan.get("tss", 0)
                ew["kroki"] = matching_plan.get("kroki", [])
            
            if matching_plan.get("tytul"):
                ew["tytul"] = matching_plan.get("tytul")
                
            unexecuted = [p for p in unexecuted if p != matching_plan]
            modified = True
            
        new_db.append(ew)
        
    new_db.extend(unexecuted)
    
    if modified:
        db["treningi"] = new_db
        st.session_state.session_treningi = new_db

consolidate_workouts()

# ==========================================
# 3. FUNKCJE POMOCNICZE I ALGORYTMY
# ==========================================
def check_login(u, p):
    users = db.get("users_db", {})
    user_data = users.get(u)
    if not user_data: return False, None
    
    stored_pw = user_data.get("password", "")
    
    # Obsługa starych haseł (zanim wprowadziliśmy szyfrowanie bcrypt) i nowych
    if stored_pw.startswith("$2b$"):
        if bcrypt.checkpw(p.encode('utf-8'), stored_pw.encode('utf-8')):
            return True, user_data.get("role", "athlete")
    else:
        if p == stored_pw:
            return True, user_data.get("role", "athlete")
            
    return False, None

def get_display_name(login):
    users = db.get("users_db", {})
    if not isinstance(users, dict): return login
    fullname = users.get(login, {}).get("fullname", login)
    if fullname and fullname != login:
        return f"{fullname} ({login})"
    return login

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

def calculate_time_in_zones_custom(stream, zone_defs, total_time_mins):
    if not stream or not zone_defs: return []
    try:
        zs = [{"label": str(z.get("Strefa", "")), "max": float(z.get("Max", 0)), "count": 0} for z in zone_defs]
    except ValueError:
        return []
        
    valid = []
    for x in stream:
        if x is not None:
            try:
                v = float(x)
                if not np.isnan(v): valid.append(v)
            except: pass
            
    if not valid: return []
    
    for val in valid:
        for i, z in enumerate(zs):
            if val <= z["max"]:
                z["count"] += 1
                break
            elif i == len(zs)-1:
                z["count"] += 1
                
    t = len(valid)
    try:
        ttm = float(total_time_mins)
        if ttm <= 0: ttm = t / 60.0
    except:
        ttm = t / 60.0
        
    return [{"label": z["label"], "mins": round((z["count"]/t) * ttm, 1), "pct": (z["count"]/t)*100} for z in zs]

def render_zone_chart_robust(df_z, title):
    max_v = df_z['mins'].max()
    max_v = float(max_v) if pd.notna(max_v) else 0.0
    if max_v <= 0: max_v = 1.0 
    
    fig = go.Figure(go.Bar(
        x=df_z['mins'].astype(float),
        y=df_z['label'].astype(str),
        orientation='h',
        text=df_z['mins'].apply(lambda x: f"{float(x):.1f}m"),
        textposition='auto',
        marker_color=ZONE_COLORS[:len(df_z)]
    ))
    
    fig.update_layout(
        title=title,
        yaxis=dict(categoryorder='array', categoryarray=df_z['label'].astype(str).tolist()[::-1]),
        xaxis=dict(range=[0, max_v * 1.15]), 
        template="plotly_dark",
        showlegend=False,
        height=250,
        margin=dict(l=0,r=10,t=30,b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def pace_str_to_float(pace_str):
    try: p=pace_str.split(':'); return int(p[0])+int(p[1])/60.0
    except: return 0.0
def float_to_pace_str(val):
    m=int(val); return f"{m}:{int((val-m)*60):02d}"

def pace_to_sec(p):
    try:
        parts = str(p).replace(',', ':').replace('.', ':').split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(p)
    except: return 240

def sec_to_pace(s):
    s = max(0, int(s))
    m = s // 60
    sec = s % 60
    return f"{m}:{sec:02d}"

def generuj_domyslne_strefy(ftp_val, lthr, is_pace=False):
    h_zones = [{"Strefa": f"Z{i+1}", "Min": int(h_prev + (1 if i>0 else 0)), "Max": int(m*lthr)} for i, (m, h_prev) in enumerate(zip([0.81, 0.89, 0.93, 0.99, 1.02, 1.2], [0] + [int(x*lthr) for x in [0.81, 0.89, 0.93, 0.99, 1.02]]))]
    
    if is_pace:
        t_sec = pace_to_sec(ftp_val)
        muls = [(1.50, 1.29), (1.28, 1.14), (1.13, 1.06), (1.05, 0.99), (0.98, 0.90), (0.89, 0.50)]
        p_zones = [{"Strefa": f"Z{i+1}", "Min": sec_to_pace(t_sec * m_slow), "Max": sec_to_pace(t_sec * m_fast)} for i, (m_slow, m_fast) in enumerate(muls)]
        return pd.DataFrame(p_zones), pd.DataFrame(h_zones)
        
    ftp = int(ftp_val) if ftp_val else 250
    p_zones = [{"Strefa": f"Z{i+1}", "Min": int(p_prev + (1 if i>0 else 0)), "Max": int(m*ftp)} for i, (m, p_prev) in enumerate(zip([0.55, 0.75, 0.90, 1.05, 1.20, 5.0], [0] + [int(x*ftp) for x in [0.55, 0.75, 0.90, 1.05, 1.20]]))]
    return pd.DataFrame(p_zones), pd.DataFrame(h_zones)

def get_user_zones(zawodnik, dyscyplina="Rower"):
    if isinstance(db["strefy"], list): db["strefy"] = {}
    all_zones = db["strefy"].get(zawodnik, {})
    
    if "ftp" in all_zones and "Rower" not in all_zones:
        old_ftp = all_zones.get("ftp", 250)
        old_lthr = all_zones.get("lthr", 170)
        old_zp, old_zh = generuj_domyslne_strefy(old_ftp, old_lthr)
        zp_run, _ = generuj_domyslne_strefy("4:30", old_lthr, is_pace=True)
        zp_swim, _ = generuj_domyslne_strefy("1:45", old_lthr, is_pace=True)
        
        migrated_zones = {
            "Rower": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp.to_dict('records'), "zones_hr": old_zh.to_dict('records')},
            "Bieganie": {"ftp": "4:30", "lthr": old_lthr, "zones_pwr": zp_run.to_dict('records'), "zones_hr": old_zh.to_dict('records')},
            "Pływanie": {"ftp": "1:45", "lthr": old_lthr, "zones_pwr": zp_swim.to_dict('records'), "zones_hr": old_zh.to_dict('records')},
            "Siłownia": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp.to_dict('records'), "zones_hr": old_zh.to_dict('records')},
            "Inne": {"ftp": old_ftp, "lthr": old_lthr, "zones_pwr": old_zp.to_dict('records'), "zones_hr": old_zh.to_dict('records')}
        }
        temp_db = db["strefy"]
        temp_db[zawodnik] = migrated_zones
        db["strefy"] = temp_db
        all_zones = migrated_zones
        
    disc_zones = all_zones.get(dyscyplina, {})
    is_pace = dyscyplina in ["Bieganie", "Pływanie"]
    
    if not disc_zones or (is_pace and isinstance(disc_zones.get("ftp", 250), (int, float))):
        def_ftp = "4:30" if dyscyplina == "Bieganie" else ("1:45" if dyscyplina == "Pływanie" else 250)
        zp, zh = generuj_domyslne_strefy(def_ftp, 170, is_pace=is_pace)
        disc_zones = {"ftp": def_ftp, "lthr": 170, "zones_pwr": zp.to_dict('records'), "zones_hr": zh.to_dict('records')}
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
            d.setdefault('rpe', 5); d.setdefault('feeling', '🙂')
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

def send_workout_to_garmin_connect(email, password, workout_data):
    import garminconnect
    
    try:
        decrypted_password = cipher_suite.decrypt(password.encode('utf-8')).decode('utf-8')
    except Exception:
        decrypted_password = password
        
    client = garminconnect.Garmin(email, decrypted_password)
    client.login()
    
    sport_str = workout_data.get('dyscyplina', 'Bieganie')
    sport_id, sport_key = (2, "cycling") if sport_str == "Rower" else ((4, "swimming") if sport_str == "Pływanie" else (1, "running"))
    
    zawodnik = workout_data.get('zawodnik')
    user_zones = db["strefy"].get(zawodnik, {}).get(sport_str, {})
    
    raw_ftp = user_zones.get('ftp', 250)
    try: ftp = float(raw_ftp)
    except: ftp = 250
    
    steps = []
    total_intervals = sum(1 for k in workout_data.get('kroki', []) if k.get('typ') == 'Interwał')
    interval_count = 1
    
    for i, k in enumerate(workout_data.get('kroki', [])):
        typ_str = k.get('typ', 'Interwał')
        s_id, s_key = (1, "warmup") if typ_str == "Rozgrzewka" else ((2, "cooldown") if typ_str == "Rozjazd" else ((4, "rest") if typ_str == "Przerwa" else (3, "active")))
        
        tryb = k.get('tryb', '')
        v1 = float(k.get('val_min', 0))
        v2 = float(k.get('val_max', 0))
        
        t_type_id = 1
        t_type_key = "no.target"
        t_val1 = None
        t_val2 = None
        
        if "Waty" in tryb and v1 > 0 and v2 > 0:
            t_type_id = 2
            t_type_key = "power.custom"
            t_val1 = int(min(v1, v2))
            t_val2 = int(max(v1, v2))
        elif "%" in tryb and v1 > 0 and v2 > 0:
            t_type_id = 2
            t_type_key = "power.custom"
            t_val1 = int((min(v1, v2) / 100.0) * ftp)
            t_val2 = int((max(v1, v2) / 100.0) * ftp)
        elif "Tętno" in tryb and v1 > 0 and v2 > 0:
            t_type_id = 4
            t_type_key = "heart.rate.custom"
            t_val1 = int(min(v1, v2))
            t_val2 = int(max(v1, v2))
        elif "Tempo" in tryb and v1 > 0 and v2 > 0:
            t_type_id = 6
            t_type_key = "pace.custom"
            speed1 = 1000.0 / (v1 * 60.0)
            speed2 = 1000.0 / (v2 * 60.0)
            t_val1 = round(min(speed1, speed2), 3)
            t_val2 = round(max(speed1, speed2), 3)
            
        prefix = ""
        if typ_str == "Interwał" and total_intervals > 1:
            prefix = f"[{interval_count}/{total_intervals}] "
            interval_count += 1
            
        desc_str = f"{prefix}{tryb} {float_to_pace_str(v1) if 'Tempo' in tryb else int(v1)}-{float_to_pace_str(v2) if 'Tempo' in tryb else int(v2)}"
        
        step_dict = {
            "type": "ExecutableStepDTO",
            "stepId": i+1,
            "stepOrder": i+1,
            "description": desc_str[:50],
            "stepType": {"stepTypeId": s_id, "stepTypeKey": s_key},
            "targetType": {"workoutTargetTypeId": t_type_id, "workoutTargetTypeKey": t_type_key},
            "targetValueOne": t_val1,
            "targetValueTwo": t_val2
        }
        
        if k.get('is_distance'):
            step_dict["endCondition"] = {"conditionTypeId": 3, "conditionTypeKey": "distance"}
            step_dict["endConditionValue"] = int(k.get('dystans_km', 0) * 1000)
        else:
            step_dict["endCondition"] = {"conditionTypeId": 2, "conditionTypeKey": "time"}
            val_sec = int(k.get('czas_total_sec', 0))
            step_dict["endConditionValue"] = val_sec if val_sec > 0 else 60
            
        steps.append(step_dict)
        
    payload = {
        "workoutName": "".join([c for c in str(workout_data.get('tytul', 'Workout')) if c.isalnum() or c in " -_"])[:15],
        "description": str(workout_data.get('komentarz', 'Wygenerowano przez Endura IQ'))[:200],
        "sportType": {"sportTypeId": sport_id, "sportTypeKey": sport_key},
        "workoutSegments": [{"segmentOrder": 1, "sportType": {"sportTypeId": sport_id, "sportTypeKey": sport_key}, "workoutSteps": steps}]
    }
    
    res = client.garth.post("connectapi", "/workout-service/workout", json=payload)
    res_dict = res.json() if hasattr(res, "json") else (res if isinstance(res, dict) else {})
    
    if isinstance(res_dict, dict) and res_dict.get("workoutId"):
        w_id = res_dict["workoutId"]
        w_date = str(workout_data.get('data', date.today()))
        client.garth.post("connectapi", f"/workout-service/schedule/{w_id}", json={"date": w_date})
        return True, tr("Zrobione! Trening jest gotowy. Twój zegarek będzie pilnował intensywności.")
    else:
        return False, f"{tr('Błąd po stronie serwerów Garmin:')} {str(res_dict)[:150]}"

def parse_tcx_pro(file_obj, user_zones, expected_sport=None):
    try:
        tree = ET.parse(file_obj)
        root = tree.getroot()
    except Exception:
        if isinstance(file_obj, bytes):
            root = ET.fromstring(file_obj)
        elif isinstance(file_obj, str):
            root = ET.fromstring(file_obj.encode('utf-8'))
        else:
            file_obj.seek(0)
            root = ET.fromstring(file_obj.read())
            
    ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
          'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'}
          
    act = root.find('.//tcx:Activity', ns)
    sport_attr = act.attrib.get('Sport', 'Other') if act is not None else 'Other'
    
    if expected_sport:
        sport = expected_sport
    else:
        if sport_attr == 'Running': sport = 'Bieganie'
        elif sport_attr == 'Biking': sport = 'Rower'
        elif 'Swim' in sport_attr: sport = 'Pływanie'
        else: sport = 'Inne'

    streams = {'time': [], 'hr': [], 'watts': [], 'speed': [], 'cadence': [], 'lat': [], 'lon': []}
    laps_data = []
    total_time_sec = 0.0
    total_dist_m = 0.0

    for lap_idx, lap in enumerate(root.findall('.//tcx:Lap', ns)):
        l_time = float(lap.find('tcx:TotalTimeSeconds', ns).text) if lap.find('tcx:TotalTimeSeconds', ns) is not None else 0
        l_dist = float(lap.find('tcx:DistanceMeters', ns).text) if lap.find('tcx:DistanceMeters', ns) is not None else 0
        total_time_sec += l_time
        total_dist_m += l_dist
        
        hr_elem = lap.find('tcx:AverageHeartRateBpm/tcx:Value', ns)
        l_hr = int(hr_elem.text) if hr_elem is not None else 0
        
        if sport == 'Pływanie':
            tempo_str = format_swim_pace(l_time, l_dist)
        else:
            tempo_str = format_pace(seconds_to_pace(l_dist/l_time)) if l_time>0 and l_dist>0 else "-"
        
        laps_data.append({
            "nr": lap_idx + 1, 
            "czas": format_duration(l_time), 
            "dystans": f"{l_dist/1000:.2f}km", 
            "hr": l_hr, 
            "moc": 0, 
            "tempo": tempo_str
        })
        
        for trkpt in lap.findall('.//tcx:Trackpoint', ns):
            streams['time'].append(len(streams['time']))
            hr = trkpt.find('tcx:HeartRateBpm/tcx:Value', ns)
            streams['hr'].append(int(hr.text) if hr is not None else None)
            lat = trkpt.find('tcx:Position/tcx:LatitudeDegrees', ns)
            lon = trkpt.find('tcx:Position/tcx:LongitudeDegrees', ns)
            streams['lat'].append(float(lat.text) if lat is not None else None)
            streams['lon'].append(float(lon.text) if lon is not None else None)
            
            cad_val = None
            cad = trkpt.find('tcx:Cadence', ns)
            if cad is not None:
                cad_val = int(cad.text)
                
            ext = trkpt.find('tcx:Extensions/ns3:TPX', ns)
            if ext is not None:
                speed = ext.find('ns3:Speed', ns)
                streams['speed'].append(float(speed.text) if speed is not None else None)
                watts = ext.find('ns3:Watts', ns)
                streams['watts'].append(int(watts.text) if watts is not None else None)
                
                run_cad = ext.find('ns3:RunCadence', ns)
                if run_cad is not None:
                    rc_val = int(run_cad.text)
                    cad_val = rc_val * 2 if rc_val < 130 else rc_val
            else:
                streams['speed'].append(None)
                streams['watts'].append(None)
                
            streams['cadence'].append(cad_val)

    avg_pwr = int(np.nanmean([x for x in streams['watts'] if x is not None])) if any(x is not None for x in streams['watts']) else 0
    np_val = calculate_normalized_power(streams['watts'])
    
    raw_ftp = user_zones.get(sport, {}).get('ftp', 250)
    try: ftp = float(raw_ftp)
    except: ftp = 250
    
    tss_val = 0
    if np_val > 0 and ftp > 0:
        if_val = np_val / ftp
        tss_val = int((total_time_sec * np_val * if_val) / (ftp * 3600) * 100)
    elif total_time_sec > 0:
        tss_val = int((total_time_sec/60) * (50/60))

    return {
        "dist": round(total_dist_m/1000, 2),
        "time": int(total_time_sec/60),
        "tss": tss_val,
        "sport": sport,
        "avg_power": avg_pwr,
        "streams": streams,
        "laps": laps_data,
        "peak_powers": {},
        "best_times": {}
    }

def sync_from_garmin(zawodnik, email, password, limit=10):
    import garminconnect
    
    try:
        decrypted_password = cipher_suite.decrypt(password.encode('utf-8')).decode('utf-8')
    except Exception:
        decrypted_password = password
        
    client = garminconnect.Garmin(email, decrypted_password)
    client.login()
    
    activities = client.get_activities(0, limit)
    added_count = 0
    
    existing_ids = [str(w.get("garmin_id")) for w in st.session_state.session_treningi if w.get("zawodnik") == zawodnik and w.get("garmin_id")]
    athlete_zones = db["strefy"].get(zawodnik, {})
    
    for act in activities:
        a_id = str(act.get('activityId'))
        if not a_id or a_id in existing_ids:
            continue
            
        garmin_type = act.get('activityType', {}).get('typeKey', '')
        if "run" in garmin_type: sport = "Bieganie"
        elif "cycling" in garmin_type: sport = "Rower"
        elif "swim" in garmin_type: sport = "Pływanie"
        elif "strength" in garmin_type: sport = "Siłownia"
        else: sport = "Inne"
        
        start_time_local = act.get('startTimeLocal', '') 
        act_date = start_time_local.split(" ")[0] if start_time_local else str(date.today())
        
        dist_km = round(act.get('distance', 0) / 1000, 2) if act.get('distance') else 0.0
        duration_min = int(act.get('duration', 0) / 60) if act.get('duration') else 0
        
        tytul = act.get('activityName', 'Trening')
        if not tytul or tytul == 'Bez nazwy' or tytul == 'Untitled':
            tytul = f"{tr(sport)}: {dist_km}km"
            
        parsed = {
            "dist": dist_km, "tss": 0, "time": duration_min, "date": act_date, 
            "sport": sport, "avg_power": 0, "streams": None, "laps": [], 
            "peak_powers": {}, "best_times": {}
        }
        
        try:
            try:
                dl_fmt = client.ActivityDownloadFormat.TCX
            except AttributeError:
                dl_fmt = "tcx"
                
            tcx_data = client.download_activity(act['activityId'], dl_fmt=dl_fmt)
            
            if tcx_data:
                if isinstance(tcx_data, bytes) and tcx_data.startswith(b'PK'):
                    with zipfile.ZipFile(io.BytesIO(tcx_data)) as z:
                        first_file = z.namelist()[0]
                        tcx_data = z.read(first_file)
                        
                if isinstance(tcx_data, str): tcx_data = tcx_data.encode('utf-8')
                
                tcx_file = io.BytesIO(tcx_data)
                parsed_tcx = parse_tcx_pro(tcx_file, athlete_zones, expected_sport=sport)
                
                if parsed_tcx['time'] > 0:
                    parsed = parsed_tcx
                    if parsed['sport'] == "Inne": parsed['sport'] = sport
        except Exception:
            pass 
            
        tss_val = parsed.get('tss', 0)
        if tss_val == 0 and duration_min > 0:
            tss_val = int((duration_min/60)*50)
            
        new_entry = {
            "zawodnik": zawodnik,
            "garmin_id": a_id, 
            "dyscyplina": parsed['sport'],
            "data": act_date,
            "tytul": tytul,
            "czas": parsed['time'] if parsed['time'] > 0 else duration_min,
            "dystans": parsed['dist'] if parsed['dist'] > 0 else dist_km,
            "tss": tss_val,
            "avg_power": parsed.get('avg_power', 0),
            "wykonany": True,
            "komentarz": "Trening pobrany z Garmin Connect.",
            "rpe": 5, 
            "feeling": "🙂", 
            "streams": parsed.get('streams'),
            "laps": parsed.get('laps', []),
            "peak_powers": parsed.get('peak_powers', {}),
            "best_times": parsed.get('best_times', {}),
            "komentarze_treningu": []
        }
        
        unexecuted_matches = [w for w in st.session_state.session_treningi 
                              if w.get("zawodnik") == zawodnik 
                              and not w.get("wykonany") 
                              and w.get("dyscyplina") == parsed['sport']
                              and str(w.get("data")) == act_date]
                              
        if unexecuted_matches:
            old_w = unexecuted_matches[0]
            new_session = [w for w in st.session_state.session_treningi if w is not old_w]
            st.session_state.session_treningi = new_session
            
            new_db = []
            for w in db.get("treningi", []):
                if (w.get("zawodnik") == old_w.get("zawodnik") and
                    str(w.get("data")) == str(old_w.get("data")) and
                    w.get("tytul") == old_w.get("tytul") and
                    w.get("dyscyplina") == old_w.get("dyscyplina") and
                    not w.get("wykonany")):
                    continue
                new_db.append(w)
            db["treningi"] = new_db
            
            new_entry['plan_czas'] = old_w.get('czas', 0)
            new_entry['plan_tss'] = old_w.get('tss', 0)
            new_entry['kroki'] = old_w.get('kroki', [])
            if old_w.get('tytul') and old_w.get('tytul') != tr(parsed['sport']):
                new_entry['tytul'] = old_w.get('tytul')
                
        save_data(new_entry)
        added_count += 1
        
    return added_count

def przygotuj_kalendarz(zawodnik):
    events = []; df = get_df(zawodnik if zawodnik != tr("Wszyscy") else None)
    today_str = str(date.today())
    
    for idx, t in df.iterrows():
        ikona = "🏃" if t['dyscyplina'] == "Bieganie" else "🚴" if t['dyscyplina'] == "Rower" else "🏊" if t['dyscyplina'] == "Pływanie" else "🏋️"
        
        if t['wykonany']:
            if t.get('plan_czas', 0) > 0:
                pct = (t['czas'] / t['plan_czas']) * 100
                if 80 <= pct <= 120: c_class = "completed-workout-green" 
                elif 50 <= pct < 80 or 120 < pct <= 150: c_class = "completed-workout-yellow" 
                else: c_class = "completed-workout-red" 
            else:
                c_class = "completed-workout-green"
                
            title_text = f"{ikona} {t['dystans']}km / {t['czas']}m" if t.get('dystans') else f"{ikona} {t['czas']}m"
            events.append({
                "title": title_text, 
                "start": str(t['data']), 
                "className": c_class, 
                "allDay": True, 
                "extendedProps": {"type": "trening", "data_str": str(t['data']), "dyscyplina": t['dyscyplina'], "tytul": t['tytul']}
            })
        else:
            if str(t['data']) < today_str:
                c_class = "completed-workout-red"
                title_text = f"{ikona} {t['tytul']}"
            else:
                c_class = "planned-workout"
                title_text = f"{ikona} [PLAN] {t['tytul']}"
                
            events.append({
                "title": title_text, 
                "start": str(t['data']), 
                "className": c_class, 
                "allDay": True, 
                "extendedProps": {"type": "trening", "data_str": str(t['data']), "dyscyplina": t['dyscyplina'], "tytul": t['tytul']}
            })

    waga_data = list(db.get("waga", [])); wyscigi_data = list(db.get("wyscigi", []))
    if zawodnik and zawodnik != tr("Wszyscy"): 
        waga_data = [w for w in waga_data if w['zawodnik'] == zawodnik]
        wyscigi_data = [r for r in wyscigi_data if r['zawodnik'] == zawodnik]
        
    for w in waga_data: 
        events.append({"title": f"⚖️ {w['waga']} kg", "start": w['data'], "className": "weight-event", "allDay": True, "extendedProps": {"type": "waga", "data_str": w['data'], "waga": w['waga']}})
    
    for r in wyscigi_data: 
        events.append({"title": f"🏆 {r['nazwa']}", "start": r['data'], "className": "race-event", "allDay": True})
        
    notes_data = list(db.get("day_notes", []))
    if zawodnik and zawodnik != tr("Wszyscy"):
        notes_data = [n for n in notes_data if n['zawodnik'] == zawodnik]
    for n in notes_data:
        events.append({"title": f"💬 {n['note']}", "start": n['data'], "className": "day-note-event", "allDay": True})

    return events

class PDFReport(FPDF):
    def header(self): self.set_font('Arial', 'B', 15); self.set_text_color(0, 229, 255); self.cell(0, 10, 'TriCoach Pro | Report', 0, 1, 'C'); self.ln(5)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_weekly_pdf(zawodnik, week_data, week_num, year, coach_note):
    pdf = PDFReport(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 12); pdf.set_text_color(0); pdf.cell(0, 10, f"Athlete: {get_display_name(zawodnik)} | Week {week_num} / {year}", 0, 1, 'L'); pdf.ln(5)
    pdf.set_fill_color(240, 240, 240); pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 10, f"Time: {format_czas(week_data['czas'].sum())}", 1, 0, 'C', 1); pdf.cell(60, 10, f"Dist: {week_data['dystans'].sum()} km", 1, 0, 'C', 1); pdf.cell(60, 10, f"TSS: {int(week_data['tss'].sum())}", 1, 1, 'C', 1); pdf.ln(10)
    pdf.set_font('Arial', 'B', 11); pdf.cell(0, 10, "Log:", 0, 1, 'L'); pdf.set_font('Arial', '', 9); pdf.set_fill_color(0, 229, 255); pdf.set_text_color(255)
    pdf.cell(25, 8, "Date", 1, 0, 'C', 1); pdf.cell(25, 8, "Sport", 1, 0, 'C', 1); pdf.cell(85, 8, "Title", 1, 0, 'L', 1); pdf.cell(20, 8, "RPE", 1, 0, 'C', 1); pdf.cell(30, 8, "TSS", 1, 1, 'C', 1)
    pdf.set_text_color(0)
    for _, row in week_data.iterrows():
        pdf.cell(25, 8, str(row['data']), 1); pdf.cell(25, 8, tr(row['dyscyplina']), 1); pdf.cell(85, 8, row['tytul'][:45], 1); pdf.cell(20, 8, str(row.get('rpe', '-')) if row['wykonany'] else "-", 1, 0, 'C'); pdf.cell(30, 8, str(row['tss']), 1, 1, 'C')
    if coach_note: pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 150, 0); pdf.cell(0, 10, "Coach Note:", 0, 1, 'L'); pdf.set_font('Arial', 'I', 10); pdf.set_text_color(0); pdf.multi_cell(0, 8, coach_note)
    return pdf.output(dest='S').encode('latin-1')

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

def render_planned_workout_view(t, user_ftp=250, unique_key=""):
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
        
        if st.toggle(tr("Zobacz Rozpiskę"), key=f"gc_tog_rozp_plan_{t.get('tytul')}_{t.get('data')}_{unique_key}"):
            st.table(pd.DataFrame(steps_data))
        
        st.markdown("---")
        st.markdown(f"### ☁️ {tr('Synchronizacja')}")
        
        if st.button("🚀 Wyślij prosto do Garmin Connect (WiFi / Bluetooth)", key=f"gc_{t['tytul']}_{t['data']}_{unique_key}"):
            with st.spinner(f"{tr('Łączenie z Garmin Connect i pobieranie')} 1 {tr('aktywności... (to potrwa kilkanaście sekund)')}"):
                zawodnik = t.get('zawodnik')
                g_creds = db["garmin_creds"].get(zawodnik, {})
                if not g_creds.get("email") or not g_creds.get("password"):
                    st.error(tr("Brak danych logowania do Garmin Connect. Uzupełnij je najpierw w zakładce 'Dane Zawodnika' -> 'Integracje 🔗'."))
                else:
                    try:
                        ok, msg = send_workout_to_garmin_connect(g_creds["email"], g_creds["password"], t)
                        if ok: 
                            st.success(msg)
                            st.balloons()
                        else: st.error(msg)
                    except Exception as e:
                        if "Authentication" in str(e) or "Login" in str(e) or "401" in str(e) or "403" in str(e):
                            st.error(tr("⚠️ Błąd logowania! Sprawdź czy e-mail/hasło są poprawne. Upewnij się też, że na koncie Garmin masz wyłączoną weryfikację dwuetapową (2FA)."))
                        else:
                            st.error(f"{tr('⚠️ Błąd integracji:')} {str(e)}")

    else: st.warning(tr("Tylko opis tekstowy."))

def render_analysis_dashboard(t, user_settings, unique_key=""):
    if not t.get('wykonany'): return

    streams = t.get('streams')
    
    has_pwr = streams and streams.get('watts') and any(x is not None for x in streams.get('watts'))
    has_hr = streams and streams.get('hr') and any(x is not None for x in streams.get('hr'))

    if streams and any(streams.get('lat', [])):
        lat_list = [l for l in streams.get('lat', []) if l is not None]
        lon_list = [l for l in streams.get('lon', []) if l is not None]
        if lat_list and lon_list:
            st.markdown(f"### {tr('🗺️ Mapa trasy GPS')}")
            fig_map = go.Figure(go.Scattermapbox(mode="lines", lon=lon_list, lat=lat_list, line=dict(width=4, color='#00E5FF')))
            fig_map.update_layout(margin={'l':0, 't':0, 'b':0, 'r':0}, mapbox=dict(style="carto-darkmatter", center=dict(lat=np.mean(lat_list), lon=np.mean(lon_list)), zoom=12), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

    if t.get('laps'):
        st.markdown(f"### {tr('⏱️ Interwały')}")
        ldf = pd.DataFrame(t['laps'])
        
        # DYNAMICZNY PRZELICZNIK TEMPA DLA PŁYWANIA (Wsteczna kompatybilność)
        if 'czas' in ldf.columns and 'dystans' in ldf.columns:
            new_tempos = []
            for _, row in ldf.iterrows():
                try:
                    c_str = str(row['czas'])
                    parts = c_str.split(':')
                    sec = 0
                    if len(parts) == 3: sec = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
                    elif len(parts) == 2: sec = int(parts[0])*60 + int(parts[1])
                    
                    d_str = str(row['dystans']).replace('km', '').strip()
                    meters = float(d_str) * 1000
                    
                    if sec > 0 and meters > 0:
                        if t.get('dyscyplina') == 'Pływanie':
                            p = (sec / meters) * 100
                            new_tempos.append(f"{int(p // 60)}:{int(p % 60):02d}/100m")
                        else:
                            speed_ms = meters / sec
                            p_float = (1000 / speed_ms) / 60 if speed_ms > 0.5 else None
                            if p_float and p_float <= 30:
                                new_tempos.append(f"{int(p_float)}:{int((p_float - int(p_float)) * 60):02d}")
                            else:
                                new_tempos.append("-")
                    else:
                        new_tempos.append("-")
                except:
                    new_tempos.append(row.get('tempo', '-'))
            ldf['tempo'] = new_tempos
            
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

        if has_pwr or has_hr:
            st.markdown(f"### {tr('📊 Czas w strefach')}")
            cz1, cz2 = st.columns(2)
            
            valid_pwr_zones = True
            if user_settings.get("zones_pwr") and len(user_settings["zones_pwr"]) > 0:
                try:
                    float(user_settings["zones_pwr"][0].get("Max", 0))
                except:
                    valid_pwr_zones = False
                    
            if has_pwr and user_settings.get("zones_pwr") and valid_pwr_zones:
                z_pwr = calculate_time_in_zones_custom(streams['watts'], user_settings["zones_pwr"], t.get('czas', 0))
                if z_pwr:
                    df_zp = pd.DataFrame(z_pwr)
                    fig_zp = render_zone_chart_robust(df_zp, tr("Moc"))
                    cz1.plotly_chart(fig_zp, use_container_width=True)
                    
            if has_hr and user_settings.get("zones_hr"):
                z_hr = calculate_time_in_zones_custom(streams['hr'], user_settings["zones_hr"], t.get('czas', 0))
                if z_hr:
                    df_zh = pd.DataFrame(z_hr)
                    fig_zh = render_zone_chart_robust(df_zh, tr("Tętno"))
                    cz2.plotly_chart(fig_zh, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### {tr('💬 Komentarze do rozmowy')}")
    komentarze = t.get('komentarze_treningu', [])
    for c in komentarze:
        is_me = (c['autor'] == st.session_state.username)
        bg_col = "rgba(0, 229, 255, 0.1)" if is_me else "rgba(255, 255, 255, 0.05)"
        align = "left"
        autor_disp = get_display_name(c['autor'])
        st.markdown(f"""
        <div style='background: {bg_col}; padding: 12px; border-radius: 8px; margin-bottom: 8px; text-align: {align}; border-left: {'3px solid #00E5FF' if is_me else '3px solid #FFD700'};'>
            <small style='color: #8BA1B8;'><b>{autor_disp}</b> • {c['data']}</small><br>
            <span style='color: #E2E8F0; font-size: 0.95em;'>{c['tresc']}</span>
        </div>
        """, unsafe_allow_html=True)

    safe_title = "".join([c for c in str(t.get('tytul','')) if c.isalnum()]).strip()
    form_key = f"comment_chat_form_{t.get('zawodnik')}_{t.get('data')}_{safe_title}_{unique_key}"
    
    with st.form(key=form_key):
        new_comment = st.text_input(tr("Dodaj szybką wiadomość..."))
        if st.form_submit_button(tr("Wyślij")):
            if new_comment:
                add_comment_to_workout(t['zawodnik'], t['data'], t['tytul'], t['dyscyplina'], st.session_state.username, new_comment)
                st.rerun()

def render_workout_expander(row, idx, ja, is_coach=False):
    t_dict = row.to_dict()
    u_strefy_disc = get_user_zones(t_dict['zawodnik'], t_dict['dyscyplina'])
    
    with st.expander(f"{'✅' if t_dict['wykonany'] else '⬜'} {t_dict['data']} | {tr(t_dict['dyscyplina'])} - {t_dict['tytul']}"):
        if not t_dict['wykonany']:
            render_planned_workout_view(t_dict, u_strefy_disc.get('ftp', 250), unique_key=f"pln_{idx}")
        else:
            if t_dict.get('plan_czas', 0) > 0:
                comp_pct = int((t_dict['czas'] / t_dict['plan_czas']) * 100)
                col = "#00E676" if 80 <= comp_pct <= 120 else ("#FFD600" if 50 <= comp_pct < 80 or 120 < comp_pct <= 150 else "#FF1744")
                st.markdown(f"<div style='text-align:center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 15px;'><span style='color:#8BA1B8; text-transform:uppercase; font-size:0.8em;'>{tr('Zgodność z planem:')}</span> <strong style='color:{col}; font-size:1.2em;'>{comp_pct}%</strong></div>", unsafe_allow_html=True)

            k1,k2,k3,k4 = st.columns(4)
            k1.markdown(f"<div class='metric-card'><div class='metric-val'>{t_dict.get('dystans')} km</div><div class='metric-label'>{tr('Dystans')}</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='metric-card'><div class='metric-val'>{t_dict.get('czas')} m</div><div class='metric-label'>{tr('Czas')}</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='metric-card'><div class='metric-val'>{t_dict.get('tss')}</div><div class='metric-label'>TSS</div></div>", unsafe_allow_html=True)
            
            has_valid_watts = t_dict.get('streams') and t_dict['streams'].get('watts') and any(x is not None for x in t_dict['streams'].get('watts'))
            np_val = calculate_normalized_power(t_dict['streams']['watts']) if has_valid_watts else 0
            k4.markdown(f"<div class='metric-card'><div class='metric-val'>{np_val} W</div><div class='metric-label'>{tr('NP (Moc)')}</div></div>", unsafe_allow_html=True)

            if t_dict.get('kroki'):
                st.markdown(f"### 🎯 {tr('Zaplanowany Trening:')}")
                fig_plan = go.Figure()
                ct = 0
                steps_data = []
                for idx_step, k in enumerate(t_dict['kroki']):
                    v_desc = f"{k.get('dystans_km', 0)} km" if k.get('is_distance') else f"{int(k.get('czas_total_sec', 0)/60)} min"
                    dur = k.get('czas_total_sec', 300)/60
                    if dur == 0: dur = 5
                    avg_val = (k.get('val_min', 0) + k.get('val_max', 0)) / 2
                    if avg_val == 0: avg_val = 50 
                    display_y = 100 / avg_val if "Tempo" in k.get('tryb', '') and avg_val > 0 else avg_val
                    intensity_label = f"{float_to_pace_str(k['val_min'])} - {float_to_pace_str(k['val_max'])}" if "Tempo" in k.get('tryb', '') else f"{int(k.get('val_min',0))}-{int(k.get('val_max',0))}"
                    fig_plan.add_trace(go.Bar(x=[ct+dur/2], y=[display_y], width=[dur], name=f"{tr(k['typ'])}", marker_color=KOLORY_BLOKOW.get(k['typ']), text=f"{v_desc}<br>{intensity_label}", textposition="auto"))
                    ct += dur
                    steps_data.append({"#": idx_step+1, tr("Typ"): tr(k['typ']), tr("Czas/Dystans"): v_desc, "Task": f"{tr(k.get('tryb', ''))}: {intensity_label}"})

                fig_plan.update_layout(template="plotly_dark", height=200, showlegend=False, xaxis_title=tr("Czas (min)"), yaxis=dict(showticklabels=False), margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_plan, use_container_width=True)
                
                if st.toggle(tr("Zobacz Rozpiskę"), key=f"tog_rozp_comp_{idx}_{t_dict['data']}"):
                    st.table(pd.DataFrame(steps_data))
                    
                st.markdown("---")

            st.markdown(f"### 📋 {tr('Ocena Treningu (RPE i Samopoczucie)')}")
            col_rpe1, col_rpe2 = st.columns([3, 1])
            col_rpe1.markdown(f"**RPE:** {t_dict.get('rpe', 5)}/10 | **Samopoczucie:** {t_dict.get('feeling', '🙂')}")
            if t_dict.get('komentarz'):
                col_rpe1.markdown(f"*{t_dict.get('komentarz')}*")
                
            if not is_coach:
                if col_rpe2.button(tr("✏️ Edytuj ocenę"), key=f"btn_edit_{idx}_{t_dict['data']}"):
                    st.session_state[f"edit_rating_{idx}_{t_dict['data']}"] = not st.session_state.get(f"edit_rating_{idx}_{t_dict['data']}", False)
                    
                if st.session_state.get(f"edit_rating_{idx}_{t_dict['data']}", False):
                    with st.form(key=f"form_rating_{idx}_{t_dict['data']}"):
                        n_rpe = st.slider(tr("RPE (Odczuwany wysiłek)"), 1, 10, int(t_dict.get('rpe', 5)))
                        n_feel = st.select_slider(tr("Samopoczucie"), ["😫","😕","😐","🙂","🤩"], value=t_dict.get('feeling', '🙂'))
                        n_kom = st.text_area(tr("Notatka dla trenera"), value=t_dict.get('komentarz', ''))
                        if st.form_submit_button(tr("Zapisz")):
                            temp_db = list(db["treningi"])
                            for w in temp_db:
                                if w.get('zawodnik') == t_dict['zawodnik'] and str(w.get('data')) == str(t_dict['data']) and w.get('tytul') == t_dict['tytul'] and w.get('dyscyplina') == t_dict['dyscyplina']:
                                    w['rpe'] = n_rpe
                                    w['feeling'] = n_feel
                                    w['komentarz'] = n_kom
                            db["treningi"] = temp_db
                            st.session_state.session_treningi = temp_db
                            st.session_state[f"edit_rating_{idx}_{t_dict['data']}"] = False
                            st.rerun()

            if st.toggle(tr("Pełna Analiza (Wykresy i Mapa)"), key=f"tgl_{idx}_{t_dict['data']}"):
                render_analysis_dashboard(t_dict, u_strefy_disc, unique_key=str(idx))

def render_onboarding_view(zawodnik):
    fullname = db.get("users_db", {}).get(zawodnik, {}).get("fullname", zawodnik)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00E5FF;'>{tr('Witaj w Endura IQ, ')}{fullname.split(' ')[0]}! 🚀</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align:center; color:#8BA1B8; margin-bottom: 30px;'>{tr('Zanim ułożymy Twój pierwszy plan, musimy się lepiej poznać. Przejdź przez krótki formularz, a my zajmiemy się resztą.')}</h4>", unsafe_allow_html=True)
    
    with st.form("onboarding_wizard"):
        t1, t2, t3, t4, t5, t6 = st.tabs([tr("❤️ Zdrowie"), tr("⏱️ Styl Życia"), tr("🎯 Cele"), tr("🚴 Sprzęt"), tr("📊 Historia"), tr("🧠 Psychologia")])
        
        with t1:
            st.markdown(f"### {tr('Podstawowe parametry')}")
            c1, c2, c3 = st.columns(3)
            wzrost = c1.number_input(tr("Wzrost:"), 100, 250, 175)
            waga = c2.number_input(tr("Waga:"), 30.0, 200.0, 70.0)
            hr_rest = c3.number_input(tr("Tętno spoczynkowe:"), 30, 120, 50)
            
            st.markdown(f"### {tr('Profil medyczny')}")
            st.markdown(tr("Czy cierpisz na:"))
            ch1, ch2, ch3, ch4 = st.columns(4)
            cukrzyca = ch1.checkbox(tr("Cukrzyca:"))
            astma = ch2.checkbox(tr("Astma:"))
            serce = ch3.checkbox(tr("Choroby serca:"))
            plecy = ch4.checkbox(tr("Problemy z kręgosłupem/stawami:"))
            
            urazy = st.text_area(tr("Urazy/Kontuzje:"))
            
        with t2:
            st.markdown(f"### {tr('Styl życia')}")
            c1, c2 = st.columns(2)
            praca = c1.selectbox(tr("Praca:"), ["Siedząca (biuro)", "Fizyczna", "Mieszana", "Wymagająca stania"])
            sen = c2.number_input(tr("Średnia ilość snu (h)"), 4.0, 12.0, 7.5)
            
            st.markdown(f"### {tr('Harmonogram dostępności (godziny:minuty/dzień)')}")
            d1, d2, d3, d4, d5, d6, d7 = st.columns(7)
            for d, day_name in zip([d1,d2,d3,d4,d5,d6,d7], ["PN", "WT", "SR", "CZ", "PT", "SO", "ND"]):
                with d:
                    st.markdown(f"**{day_name}**")
                    st.number_input(tr("Godz."), 0, 24, 1 if day_name not in ["SO", "ND"] else 2, key=f"h_{day_name}")
                    st.number_input(tr("Min."), 0, 59, 0, key=f"m_{day_name}")
            
        with t3:
            st.markdown(f"### {tr('Cele i Doświadczenie')}")
            lata_sport = st.number_input(tr("Staż w sportach:"), 0, 50, 2)
            cel_glowny = st.text_area(tr("Cel główny:"))
            zawody_a = st.text_input(tr("Główne zawody (Kategoria A):"))
            
        with t4:
            st.markdown(f"### {tr('Dostępny Sprzęt')}")
            c_s1, c_s2 = st.columns(2)
            basen = c_s1.checkbox(f"🏊 {tr('Basen/Wody otwarte:')}")
            silownia = c_s2.checkbox(f"🏋️ {tr('Siłownia:')}")
            trenazer = c_s1.checkbox(f"🚴 {tr('Trenażer Smart:')}")
            pomiar_mocy = c_s2.checkbox(f"⚡ {tr('Pomiar mocy:')}")
            
            slabe_strony = st.text_area(tr("Najsłabsze strony:"))
            
        with t5:
            st.markdown(f"### {tr('Historia treningowa')}")
            avg_vol = st.number_input(tr("Średnia objętość (ostatnie 3 miesiące) [godz/tydz]:"), 0.0, 40.0, 5.0, 0.5)
            
            st.markdown(f"### {tr('Aktualne / Szacowane Wartości (wpisz 0 jeśli nie znasz)')}")
            c_hist1, c_hist2, c_hist3 = st.columns(3)
            est_ftp = c_hist1.number_input(tr("Szacowane FTP (W):"), 0, 500, 0)
            est_lthr = c_hist2.number_input(tr("Próg Mleczanowy - LTHR (BPM):"), 0, 220, 0)
            est_maxhr = c_hist3.number_input(tr("Tętno Maksymalne (BPM):"), 0, 250, 0)
            
            st.markdown("---")
            st.markdown(f"### {tr('Gotowość na Tydzień Testowy:')}")
            st.markdown(f"<span style='color:#8BA1B8; font-size:0.9em;'>{tr('Testy wyznaczające dokładne strefy i krzywą profilu mocy (m.in. sprint 5s, 1min, 5min, 20min).')}</span>", unsafe_allow_html=True)
            test_week = st.selectbox("", [
                tr("Tak, zróbmy pełne testy (Profil Mocy: 5s, 1m, 5m, 20m + bieganie)"),
                tr("Nie, mam aktualne badania/wyniki"),
                tr("Zdam się na decyzję trenera")
            ], label_visibility="collapsed")
            
        with t6:
            st.markdown(f"### {tr('Profil Psychologiczny (1-5)')}")
            st.markdown(f"<span style='color:#8BA1B8;'>{tr('Oceń siebie w skali od 1 (Słabo) do 5 (Doskonale)')}</span>", unsafe_allow_html=True)
            p1 = st.slider(tr("Odporność na ból:"), 1, 5, 3)
            p2 = st.slider(tr("Koncentracja w stresie:"), 1, 5, 3)
            p3 = st.slider(tr("Dyscyplina treningowa:"), 1, 5, 3)
            p4 = st.slider(tr("Zdolność do odpoczynku:"), 1, 5, 3)
            
            st.markdown("---")
            st.markdown(f"### {tr('Priorytet')}")
            p5 = st.slider(tr("Priorytet treningu (1-10):"), 1, 10, 5, help=tr("1 = Życie prywatne, 10 = Trening 100%"))
            
            st.markdown("---")
            st.markdown(f"### {tr('Oczekiwania wobec trenera')}")
            comm_style = st.selectbox(tr("Preferowany styl komunikacji:"), [
                tr("Zbalansowany (dane + wsparcie)"),
                tr("Tylko suche dane i analiza"),
                tr("Dużo motywacji i wsparcia mentalnego")
            ])
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit_onboarding = st.form_submit_button("ZAPISZ MÓJ PROFIL I WEJDŹ DO APLIKACJI 🚀")
        
        if submit_onboarding:
            profil = {
                "onboarded": True,
                "wzrost": wzrost, "waga": waga, "hr_rest": hr_rest,
                "choroby": {"cukrzyca": cukrzyca, "astma": astma, "serce": serce, "plecy": plecy},
                "urazy": urazy,
                "praca": praca, "sen": sen,
                "czas_trening": {
                    "PN": f"{st.session_state.h_PN}h {st.session_state.m_PN}m",
                    "WT": f"{st.session_state.h_WT}h {st.session_state.m_WT}m",
                    "SR": f"{st.session_state.h_SR}h {st.session_state.m_SR}m",
                    "CZ": f"{st.session_state.h_CZ}h {st.session_state.m_CZ}m",
                    "PT": f"{st.session_state.h_PT}h {st.session_state.m_PT}m",
                    "SO": f"{st.session_state.h_SO}h {st.session_state.m_SO}m",
                    "ND": f"{st.session_state.h_ND}h {st.session_state.m_ND}m"
                },
                "lata_sport": lata_sport, "cel_glowny": cel_glowny, "zawody_a": zawody_a,
                "sprzet": {"basen": basen, "trenazer": trenazer, "pomiar_mocy": pomiar_mocy, "silownia": silownia},
                "slabe_strony": slabe_strony,
                "psychologia": {"bol": p1, "stres": p2, "dyscyplina": p3, "odpoczynek": p4, "priorytet": p5},
                "historia": {"avg_vol": avg_vol, "est_ftp": est_ftp, "est_lthr": est_lthr, "est_maxhr": est_maxhr, "test_week": test_week},
                "komunikacja": comm_style,
                "data_wypelnienia": str(date.today())
            }
            
            temp_info = db["zawodnicy_info"]
            temp_info[zawodnik] = profil
            db["zawodnicy_info"] = temp_info
            
            st.success("Profil zapisany! Trwa ładowanie Twojego konta...")
            time.sleep(2)
            st.rerun()

# ==========================================
# 4. LOGOWANIE I REJESTRACJA
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.markdown("### Settings / Ustawienia")
    lang_sel = st.sidebar.radio("Language / Język", ["PL", "EN"], horizontal=True, index=0 if st.session_state.lang == 'PL' else 1)
    if lang_sel != st.session_state.lang: st.session_state.lang = lang_sel; st.rerun()

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
        st.markdown("""<div class="login-header"><h1 class="login-title">ENDURA IQ</h1><p class="login-subtitle">Science-Based Coaching Platform</p></div>""", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs([tr("Logowanie"), tr("Rejestracja")])
        
        with tab_log:
            u = st.text_input(tr("Użytkownik"), placeholder="admin / Twój Login", key="log_u")
            p = st.text_input(tr("Hasło"), type="password", placeholder="••••••••", key="log_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(tr("Zaloguj")):
                is_valid, rola = check_login(u, p)
                if is_valid: 
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.role = rola
                    st.rerun()
                else: 
                    st.error(tr("Nieprawidłowy login lub hasło."))
                    
        with tab_reg:
            st.markdown(f"<span style='color:#8BA1B8; font-size: 0.9em;'>{tr('Dołącz do Endura IQ i rozpocznij swoją profesjonalną drogę.')}</span>", unsafe_allow_html=True)
            reg_login = st.text_input(tr("Twój Login / Nick (musi być unikalny)"))
            reg_email = st.text_input(tr("Adres E-mail"))
            reg_name = st.text_input(tr("Imię i Nazwisko"))
            reg_pass = st.text_input(tr("Hasło"), type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            rodo_consent = st.checkbox(tr("Wyrażam zgodę na przetwarzanie moich danych dotyczących zdrowia (tętno, waga, informacje o kontuzjach) w celu realizacji planu treningowego."))
            
            if st.button(tr("Utwórz konto")):
                users = db.get("users_db", {})
                if reg_login in users:
                    st.error(tr("Użytkownik o takim loginie już istnieje. Wybierz inny!"))
                elif len(reg_login) < 3 or len(reg_name) < 3 or len(reg_pass) < 4 or "@" not in reg_email:
                    st.error(tr("Wypełnij poprawnie wszystkie pola (Login i Imię min. 3 znaki, Hasło min. 4, poprawny email)."))
                elif not rodo_consent:
                    st.error(tr("Musisz wyrazić zgodę na przetwarzanie danych medycznych (wymóg prawny RODO)."))
                else:
                    hashed_pw = bcrypt.hashpw(reg_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    users[reg_login] = {"password": hashed_pw, "role": "athlete", "fullname": reg_name, "email": reg_email}
                    db["users_db"] = users
                    
                    zaw_list = db.get("zawodnicy_list", [])
                    if reg_login not in zaw_list:
                        zaw_list.append(reg_login)
                        db["zawodnicy_list"] = zaw_list
                        
                    st.success(tr("Konto utworzone! Możesz się teraz zalogować w zakładce obok."))
                    time.sleep(2)
                    st.rerun()
    st.stop()

# ==========================================
# 5. APLIKACJA MAIN
# ==========================================
ja = st.session_state.username

if st.session_state.role == "athlete":
    athlete_info = db["zawodnicy_info"].get(ja, {})
    if not athlete_info.get("onboarded", False):
        render_onboarding_view(ja)
        st.stop()

ja_disp = get_display_name(ja)
st.sidebar.markdown(f"<h3 style='color: #00E5FF; text-align: center; margin-bottom: 20px;'>{ja_disp.split(' ')[0].upper()}</h3>", unsafe_allow_html=True)
lang_sel = st.sidebar.radio("Language / Język", ["PL", "EN"], horizontal=True, index=0 if st.session_state.lang == 'PL' else 1)
if lang_sel != st.session_state.lang: st.session_state.lang = lang_sel; st.rerun()

# --- SYSTEM POWIADOMIEŃ W MENU ---
unread_count = sum(1 for m in db.get("chat", []) if m.get("do") == ja and m.get("read", True) is False)

def format_menu(opt):
    if opt == tr("Wiadomości") and unread_count > 0:
        return f"{opt} 🔴 ({unread_count})"
    return opt

menu_opts = [tr("Dashboard"), tr("Kalendarz"), tr("Wiadomości"), tr("Statystyki"), tr("Raporty"), tr("Fizjologia"), tr("Strefy"), tr("Kreator"), tr("Plany"), tr("Baza")] if st.session_state.role == "coach" else [tr("Dodaj aktywność"), tr("Kalendarz"), tr("Wiadomości"), tr("Statystyki"), tr("Dane zawodnika")]
menu = st.sidebar.radio(tr("MENU"), menu_opts, format_func=format_menu)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button(tr("Wyloguj")): st.session_state.logged_in=False; st.rerun()

# --- AUTO-SYNC W TLE (DLA ZAWODNIKA) ---
if menu == tr("Dodaj aktywność"):
    
    if "auto_synced" not in st.session_state:
        st.session_state.auto_synced = False
        
    if not st.session_state.auto_synced:
        g_creds = db["garmin_creds"].get(ja, {})
        if g_creds.get("email") and g_creds.get("password"):
            with st.spinner(tr("Automatyczna synchronizacja w tle...")):
                try:
                    added = sync_from_garmin(ja, g_creds["email"], g_creds["password"], 5)
                    st.session_state.auto_synced = True
                    if added > 0:
                        consolidate_workouts()
                        st.toast(f"{tr('Pobrano automatycznie nowych treningów:')} {added}")
                        time.sleep(1)
                        st.rerun()
                except Exception:
                    st.session_state.auto_synced = True
        else:
            st.session_state.auto_synced = True

    st.title(f"{tr('Cześć')} {ja_disp.split(' ')[0]}!")
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
        
        # --- ZBIORCZE WYSYŁANIE PLANU NA ZEGAREK (7 DNI) ---
        with st.expander(tr("📤 Wyślij nadchodzące treningi na zegarek (7 dni)"), expanded=False):
            st.markdown(f"<span style='color:#8BA1B8; font-size:0.9em;'>{tr('Wyślij wszystkie zaplanowane treningi na najbliższe 7 dni jednym kliknięciem.')}</span>", unsafe_allow_html=True)
            if st.button(tr("🚀 Wyślij zaplanowany tydzień")):
                g_creds = db["garmin_creds"].get(ja, {})
                if not g_creds.get("email") or not g_creds.get("password"):
                    st.warning(tr("Brak danych logowania do Garmin Connect. Uzupełnij je w zakładce 'Dane Zawodnika' -> 'Integracje 🔗'."))
                else:
                    today = date.today()
                    next_week = today + timedelta(days=7)
                    
                    to_send = []
                    for w in st.session_state.session_treningi:
                        if w.get("zawodnik") == ja and not w.get("wykonany"):
                            try:
                                w_date = pd.to_datetime(w["data"]).date()
                                if today <= w_date <= next_week and w.get("kroki"):
                                    to_send.append(w)
                            except:
                                pass
                                
                    if not to_send:
                        st.info(tr("Brak zaplanowanych treningów strukturalnych na najbliższe 7 dni."))
                    else:
                        progress_text = tr("Wysyłanie treningów...")
                        my_bar = st.progress(0, text=progress_text)
                        
                        success_count = 0
                        error_msg = ""
                        
                        for i, w in enumerate(to_send):
                            try:
                                ok, msg = send_workout_to_garmin_connect(g_creds["email"], g_creds["password"], w)
                                if ok: success_count += 1
                                else: error_msg = msg
                            except Exception as e:
                                error_msg = str(e)
                                
                            my_bar.progress((i + 1) / len(to_send), text=f"{progress_text} ({i+1}/{len(to_send)})")
                            time.sleep(3) # Bezpieczeństwo - blokada Garmina
                            
                        if success_count > 0:
                            st.success(f"{tr('Pomyślnie wysłano')} {success_count} {tr('treningów na zegarek!')}")
                            st.balloons()
                        if error_msg:
                            st.error(f"{tr('Napotkano błąd przy części treningów:')} {error_msg}")
                            
        with st.expander(tr("🔄 Pobierz automatycznie z Garmin Connect"), expanded=False):
            st.markdown(f"<span style='color:#8BA1B8; font-size:0.9em;'>{tr('Aplikacja sama znajdzie Twoje ostatnie treningi w chmurze Garmina, pobierze ich ukryte pliki TCX i dokona pełnej analizy.')}</span>", unsafe_allow_html=True)
            g_creds = db["garmin_creds"].get(ja, {})
            
            if g_creds.get("email") and g_creds.get("password"):
                c_sync1, c_sync2 = st.columns([2, 1])
                sync_limit = c_sync1.selectbox(tr("Ile ostatnich aktywności sprawdzić?"), [10, 30, 90])
                if c_sync2.button(tr("📥 Pobierz teraz")):
                    with st.spinner(f"{tr('Łączenie z Garmin Connect i pobieranie')} {sync_limit} {tr('aktywności... (to potrwa kilkanaście sekund)')}"):
                        try:
                            added = sync_from_garmin(ja, g_creds["email"], g_creds["password"], sync_limit)
                            if added > 0:
                                consolidate_workouts()
                                st.success(f"{tr('Zakończono! Pomyślnie pobrano i zanalizowano')} {added} {tr('nowych treningów.')}")
                                st.balloons()
                            else:
                                st.info(tr("Wszystkie treningi z wybranego okresu są już w Twojej bazie Endura IQ. Nie znaleziono nowych."))
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"{tr('Błąd synchronizacji:')} {str(e)}")
            else:
                st.warning(tr("⚠️ Zanim pobierzesz treningi, musisz podać dane logowania do Garmina w zakładce 'Dane zawodnika' -> 'Integracje 🔗'"))

        with st.expander(tr("📂 Ręczne wgranie pliku (TCX)"), expanded=False):
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
                st.markdown(f"### {tr('Ocena Treningu (RPE i Samopoczucie)')}")
                c_rpe, c_feel = st.columns(2)
                f_rpe = c_rpe.slider(tr("RPE (Odczuwany wysiłek)"), 1, 10, 5)
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
                        new_entry['tytul'] = old_w.get('tytul', new_entry['tytul'])
                    save_data(new_entry); st.success(tr("Zapisano!")); st.session_state.pop('form_data', None); st.rerun()

        st.markdown(f"### {tr('Ostatnie Aktywności')}")
        df_plan = get_df(ja)
        for idx, row in df_plan.sort_values('data', ascending=False).iterrows():
            render_workout_expander(row, idx, ja, is_coach=False)

# --- 1.5 CZAT (WIADOMOŚCI) ---
elif menu == tr("Wiadomości"):
    st.title(f"💬 {tr('Wiadomości')}")
    chat_partner = "admin"
    if st.session_state.role == "coach": 
        def format_coach_chat_partner(z):
            z_unread = sum(1 for m in db.get("chat", []) if m.get("do") == ja and m.get("od") == z and m.get("read", True) is False)
            name = get_display_name(z)
            return f"🔴 {name}" if z_unread > 0 else name
        chat_partner = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=format_coach_chat_partner)
    
    # OZNACZANIE WIADOMOŚCI JAKO PRZECZYTANE W TLE
    chat_db = list(db.get("chat", []))
    has_unread_now = False
    for m in chat_db:
        if m.get("do") == ja and m.get("od") == chat_partner and m.get("read", True) is False:
            m["read"] = True
            has_unread_now = True
    if has_unread_now:
        db["chat"] = chat_db
        st.rerun()
    
    partner_disp = get_display_name(chat_partner)
    st.markdown(f"#### {tr('Czat z')} {partner_disp}")
    st.markdown("---")
    msgs = db.get("chat", [])
    for m in msgs:
        if (m['od'] == ja and m['do'] == chat_partner) or (m['od'] == chat_partner and m['do'] == ja):
            is_me = (m['od'] == ja)
            with st.chat_message("user" if is_me else "assistant", avatar="👤" if is_me else ("👨‍🏫" if m['od'] == "admin" else "🏃")):
                autor_disp = get_display_name(m['od'])
                st.caption(f"{autor_disp} • {m['data']}")
                st.write(m['tresc'])
    prompt = st.chat_input(tr("Napisz wiadomość..."))
    if prompt:
        db["chat"] = list(db.get("chat", [])) + [{"od": ja, "do": chat_partner, "data": datetime.now().strftime("%Y-%m-%d %H:%M"), "tresc": prompt, "read": False}]
        st.rerun()

# --- 1.8 STATYSTYKI ---
elif menu == tr("Statystyki"):
    st.title(f"📊 {tr('Podsumowanie aktywności')}")
    target = ja if st.session_state.role != "coach" else st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=get_display_name)
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
            df_filtered['czas'] = pd.to_numeric(df_filtered['czas'], errors='coerce').fillna(0)
            df_filtered['dystans'] = pd.to_numeric(df_filtered['dystans'], errors='coerce').fillna(0)
            
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
                fig = go.Figure(data=[go.Pie(
                    labels=[tr(d) for d in agg_df['dyscyplina']], 
                    values=agg_df['czas'].astype(float).tolist(), 
                    hole=.4, 
                    marker=dict(colors=[KOLORY_SPORT.get(d, '#8BA1B8') for d in agg_df['dyscyplina']])
                )])
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
    target = ja if st.session_state.role != "coach" else st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=get_display_name)

    tab_kalendarz, tab_lista = st.tabs([f"📅 {tr('Kalendarz')}", f"📋 {tr('Lista aktywności')}"])

    with tab_kalendarz:
        col_c, col_s = st.columns([3, 1])
        with col_c:
            events = przygotuj_kalendarz(target)
            
            if 'cal_click_date' not in st.session_state:
                st.session_state.cal_click_date = str(date.today())
                
            cal_options = {
                "initialView": "dayGridMonth",
                "initialDate": st.session_state.cal_click_date,
                "firstDay": 1,
                "selectable": True,
                "height": 800,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,listWeek"
                },
                "eventDisplay": "block"
            }
            
            cal = calendar(events=events, options=cal_options, custom_css=cal_css, key=f'cal_view_{target}', callbacks=['dateClick', 'eventClick', 'select'])
            
            if cal and isinstance(cal, dict):
                if cal.get("callback") == "dateClick":
                    clicked_date = cal.get("dateClick", {}).get("dateStr")
                    if clicked_date and clicked_date != st.session_state.get('cal_click_date'):
                        st.session_state.cal_click_date = clicked_date
                        st.rerun()
                elif cal.get("callback") == "select":
                    clicked_date = cal.get("select", {}).get("startStr")
                    if clicked_date and clicked_date[:10] != st.session_state.get('cal_click_date'):
                        st.session_state.cal_click_date = clicked_date[:10]
                        st.rerun()
            
            st.markdown("---")
            st.markdown(f"### {tr('🗓️ Zarządzaj Dniem')}")
            
            try:
                def_d = datetime.strptime(st.session_state.cal_click_date, "%Y-%m-%d").date()
            except:
                def_d = date.today()
                
            c_date_obj = st.date_input(tr("Wybierz datę (kliknij w kalendarzu u góry lub wpisz ręcznie):"), value=def_d)
            c_date = str(c_date_obj)
            st.session_state.cal_click_date = c_date
            
            curr_notes = [n for n in db.get("day_notes", []) if n['zawodnik'] == target and n['data'] == c_date]
            curr_note_text = curr_notes[0]['note'] if curr_notes else ""
            
            with st.form(key=f"note_form_{c_date}"):
                st.markdown(f"<span style='color:#8BA1B8; font-size:0.9em;'>{tr('📌 Zostaw notatkę na dzień')} <b>{c_date}</b> {tr('(np. ograniczony czas, wyjazd):')}</span>", unsafe_allow_html=True)
                note_input = st.text_input(tr("Komentarz do dnia"), value=curr_note_text)
                if st.form_submit_button(tr("Zapisz Notatkę")):
                    all_notes = list(db.get("day_notes", []))
                    all_notes = [n for n in all_notes if not (n['zawodnik'] == target and n['data'] == c_date)]
                    if note_input.strip():
                        all_notes.append({"zawodnik": target, "data": c_date, "note": note_input})
                    db["day_notes"] = all_notes
                    st.success(tr("Notatka przypięta do kalendarza!"))
                    st.rerun()
            
            with st.expander(f"{tr('🏆 Dodaj Zawody w dniu')} {c_date}"):
                with st.form("add_race_form_click"):
                    r_name = st.text_input(tr("Nazwa zawodów"), placeholder="Ironman Frankfurt")
                    if st.form_submit_button(tr("Zapisz")):
                        db["wyscigi"] = list(db.get("wyscigi", [])) + [{"zawodnik": target, "nazwa": r_name, "data": c_date}]
                        st.success(tr("Dodano zawody!")); st.rerun()

            if st.session_state.role == "coach":
                with st.expander(f"{tr('⚡ Zaplanuj Trening (Trener) -')} {c_date}"):
                    with st.form("plan_workout_click"):
                        p_sport = st.selectbox(tr("Dyscyplina"), ["Bieganie", "Rower", "Pływanie", "Siłownia"], format_func=tr)
                        opts = [tr("-- Własny --")] + [s.get('nazwa',tr('Bez nazwy')) for s in db.get("biblioteka", [])]
                        p_temp = st.selectbox(tr("Wczytaj Szablon"), opts)
                        def_title = f"{tr(p_sport)}"; def_time = 60; def_tss = 50; p_steps = []
                        if p_temp != tr("-- Własny --"):
                            tmpl = next((x for x in db["biblioteka"] if x.get('nazwa')==p_temp), None)
                            if tmpl: def_title = tmpl['nazwa']; def_time = sum([k['czas_total_sec'] for k in tmpl['kroki']]) // 60; p_steps = tmpl['kroki']
                        p_title = st.text_input(tr("Tytuł"), value=def_title)
                        c3, c4 = st.columns(2); p_time = c3.number_input(tr("Czas (min)"), value=def_time); p_tss = c4.number_input("Plan TSS", value=def_tss)
                        p_desc = st.text_area(tr("Instrukcje dla zawodnika"))
                        if st.form_submit_button(tr("Dodaj do Planu")):
                            save_data({"zawodnik": target, "dyscyplina": p_sport, "data": c_date, "tytul": p_title, "komentarz": p_desc, "czas": p_time, "tss": p_tss, "wykonany": False, "kroki": p_steps})
                            st.success(tr("Zaplanowano!")); st.session_state.cal_click_date = None; st.rerun()

            if cal and isinstance(cal, dict) and cal.get("callback") == "eventClick":
                props = cal.get("eventClick", {}).get("event", {}).get("extendedProps", {})
                if props.get("type") == "waga": 
                    st.info(f"{tr('Ważenie z dnia')} {props.get('data_str')}: **{props.get('waga')} kg**")
                elif props.get("type") == "trening":
                    df_c = get_df(target); match_df = df_c[(df_c['data'].astype(str) == props.get('data_str')) & (df_c['dyscyplina'] == props.get('dyscyplina')) & (df_c['tytul'] == props.get('tytul'))]
                    st.markdown("---")
                    if not match_df.empty: 
                        st.subheader(f"📊 {tr('Szczegóły:')} {props.get('tytul')}")
                        t_dict = match_df.iloc[0].to_dict()
                        
                        if t_dict.get('wykonany'):
                            if st.session_state.role == "coach":
                                st.markdown(f"**RPE:** {t_dict.get('rpe', 5)}/10 | **Samopoczucie:** {t_dict.get('feeling', '🙂')}")
                                if t_dict.get('komentarz'):
                                    st.markdown(f"*{t_dict.get('komentarz')}*")
                            render_analysis_dashboard(t_dict, get_user_zones(target, t_dict['dyscyplina']), unique_key="cal")
                        else:
                            render_planned_workout_view(t_dict, get_user_zones(target, t_dict['dyscyplina']).get('ftp', 250), unique_key="cal_modal")
                            
                    else: st.info(tr("Nie znaleziono szczegółów. Sprawdź listę zadań."))

        with col_s: render_tp_weekly_list(get_df(target))

    with tab_lista:
        st.markdown(f"### 📋 {tr('Ostatnie Aktywności')}")
        df_lista = get_df(target)
        if not df_lista.empty:
            df_lista = df_lista[df_lista['wykonany'] == True].sort_values('data', ascending=False)
            if df_lista.empty:
                st.info(tr("Brak wykonanych aktywności."))
            else:
                for idx, t_row in df_lista.iterrows():
                    render_workout_expander(t_row, idx, ja, is_coach=(st.session_state.role=="coach"))
        else:
            st.info(tr("Brak wykonanych aktywności."))

# --- 3. DASHBOARD ---
elif menu == tr("Dashboard"):
    st.title(tr("Centrum Zarządzania")); cols = st.columns(3)
    for idx, z in enumerate(ZAWODNICY): 
        z_disp = get_display_name(z)
        cols[idx%3].metric(f"{z_disp}", f"{calculate_compliance(get_df(z))}%", help=tr("Dyscyplina (Wykonanie Planu)"))
    st.markdown("---")

    target_pmc = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, key="pmc_sel", format_func=get_display_name)
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
    sel_user = st.selectbox(tr("Zawodnik:"), ZAWODNICY, format_func=get_display_name) if st.session_state.role == "coach" else ja
    
    tabs = st.tabs([tr("Profil Mocy (CP)"), tr("Rekordy Biegowe"), tr("Badania & Trendy"), tr("Waga"), tr("Integracje 🔗"), tr("📝 Ankieta Profilowa")] + ([tr("⚙️ Konto")] if st.session_state.role == "athlete" else []))

    with tabs[0]:
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

    with tabs[1]:
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

    with tabs[2]:
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

    with tabs[3]:
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
        
    with tabs[4]:
        st.markdown(f"### {tr('🔵 Autoryzacja Garmin Connect')}")
        if st.session_state.role == "coach":
            st.info(tr("Ze względów bezpieczeństwa i prywatności, tylko zawodnik ma dostęp do swoich danych logowania Garmin Connect."))
        else:
            st.markdown(f"<span style='color:#8BA1B8;'>{tr('Podaj dane logowania, aby aplikacja Endura IQ mogła automatycznie wysyłać zaplanowane treningi prosto do Twojego kalendarza w zegarku.')}</span>", unsafe_allow_html=True)
            creds = db["garmin_creds"].get(sel_user, {})
            with st.form("garmin_form"):
                g_email = st.text_input(tr("E-mail Garmin"), value=creds.get("email", ""))
                has_pass_saved = True if creds.get("password") else False
                pass_ph = "********" if has_pass_saved else ""
                
                g_pass = st.text_input(tr("Hasło Garmin"), value="", placeholder=pass_ph, type="password")
                if st.form_submit_button(tr("Zapisz połączenie z chmurą")):
                    temp_gc = db["garmin_creds"]
                    if g_pass:
                        encrypted_pass = cipher_suite.encrypt(g_pass.encode('utf-8')).decode('utf-8')
                        temp_gc[sel_user] = {"email": g_email, "password": encrypted_pass}
                        db["garmin_creds"] = temp_gc
                        st.success(tr("Zapisano dane. Od teraz możesz wysyłać treningi prosto z kalendarza!"))
                    elif has_pass_saved and not g_pass:
                        temp_gc[sel_user]["email"] = g_email
                        db["garmin_creds"] = temp_gc
                        st.success(tr("Zapisano dane (hasło pozostało bez zmian)."))
                    else:
                        st.error("Podaj hasło.")
                
    with tabs[5]:
        sel_user_disp = get_display_name(sel_user)
        st.markdown(f"### {tr('Profil Startowy (Ankieta):')} {sel_user_disp}")
        info = db["zawodnicy_info"].get(sel_user, {})
        
        if info and info.get("onboarded"):
            st.markdown(f"<span style='color:#00E5FF; font-weight:bold;'>{tr('Data wypełnienia:')}</span> {info.get('data_wypelnienia')}", unsafe_allow_html=True)
            st.markdown("---")
            
            c_p1, c_p2, c_p3 = st.columns(3)
            c_p1.markdown(f"**{tr('Wzrost:')}** {info.get('wzrost')} cm")
            c_p2.markdown(f"**{tr('Waga:')}** {info.get('waga')} kg")
            c_p3.markdown(f"**{tr('Tętno spoczynkowe:')}** {info.get('hr_rest')} BPM")
            
            st.markdown(f"#### {tr('Historia i Parametry Wyjściowe')}")
            hist = info.get("historia", {})
            st.write(f"- {tr('Średnia objętość:')} **{hist.get('avg_vol', 0)} h/tydz**")
            st.write(f"- {tr('Szacowane FTP:')} **{hist.get('est_ftp', 0)} W** | LTHR: **{hist.get('est_lthr', 0)} BPM** | Max HR: **{hist.get('est_maxhr', 0)} BPM**")
            st.write(f"- {tr('Tydzień Testowy:')} **{hist.get('test_week', tr('Brak'))}**")
            
            st.markdown(f"#### {tr('Zdrowie i Urazy')}")
            choroby = info.get("choroby", {})
            st.write(f"- {tr('Cukrzyca:')} {'✅' if choroby.get('cukrzyca') else '❌'}")
            st.write(f"- {tr('Astma:')} {'✅' if choroby.get('astma') else '❌'}")
            st.write(f"- {tr('Choroby serca:')} {'✅' if choroby.get('serce') else '❌'}")
            st.write(f"- {tr('Problemy z kręgosłupem/stawami:')} {'✅' if choroby.get('plecy') else '❌'}")
            st.markdown(f"**{tr('Urazy/Kontuzje:')}** {info.get('urazy', tr('Brak'))}")
            
            st.markdown(f"#### {tr('Styl życia')}")
            st.write(f"**{tr('Praca:')}** {info.get('praca')} | **{tr('Średni sen:')}** {info.get('sen')} h")
            
            st.markdown(f"#### {tr('Harmonogram dostępności (godziny:minuty/dzień)')}")
            ct = info.get("czas_trening", {})
            
            def fmt_ct(val):
                if isinstance(val, (int, float)):
                    h = int(val)
                    m = int((val - h) * 60)
                    return f"{h}h {m}m"
                return val
                
            st.write(f"PN: {fmt_ct(ct.get('PN'))} | WT: {fmt_ct(ct.get('WT'))} | ŚR: {fmt_ct(ct.get('SR'))} | CZ: {fmt_ct(ct.get('CZ'))} | PT: {fmt_ct(ct.get('PT'))} | SO: {fmt_ct(ct.get('SO'))} | ND: {fmt_ct(ct.get('ND'))}")
            
            st.markdown(f"#### {tr('Cele i Doświadczenie')}")
            st.write(f"**{tr('Staż w sportach:')}** {info.get('lata_sport')} lat")
            st.write(f"**{tr('Cel główny:')}** {info.get('cel_glowny')}")
            st.write(f"**{tr('Główne zawody (Kategoria A):')}** {info.get('zawody_a')}")
            st.write(f"**{tr('Najsłabsze strony:')}** {info.get('slabe_strony')}")
            
            st.markdown(f"#### {tr('Dostępny Sprzęt')}")
            sprzet = info.get("sprzet", {})
            st.write(f"- {tr('Basen/Wody otwarte:')} {'✅' if sprzet.get('basen') else '❌'}")
            st.write(f"- {tr('Siłownia:')} {'✅' if sprzet.get('silownia') else '❌'}")
            st.write(f"- {tr('Trenażer Smart:')} {'✅' if sprzet.get('trenazer') else '❌'}")
            st.write(f"- {tr('Pomiar mocy:')} {'✅' if sprzet.get('pomiar_mocy') else '❌'}")
            
            st.markdown(f"#### {tr('Profil Psychologiczny (1-5)')}")
            psy = info.get("psychologia", {})
            st.write(f"- {tr('Odporność na ból:')} **{psy.get('bol')}/5**")
            st.write(f"- {tr('Koncentracja w stresie:')} **{psy.get('stres')}/5**")
            st.write(f"- {tr('Dyscyplina treningowa:')} **{psy.get('dyscyplina')}/5**")
            st.write(f"- {tr('Zdolność do odpoczynku:')} **{psy.get('odpoczynek')}/5**")
            st.write(f"- {tr('Priorytet treningu (1-10):')} **{psy.get('priorytet', '-')}**")
            st.write(f"- {tr('Komunikacja:')} **{info.get('komunikacja', tr('Zbalansowany (dane + wsparcie)'))}**")

        else:
            st.info(tr("Ten zawodnik nie wypełnił jeszcze ankiety startowej."))

    # --- ZAKŁADKA USUWANIA KONTA (TYLKO DLA ZAWODNIKA) ---
    if st.session_state.role == "athlete":
        with tabs[6]:
            st.markdown(f"### 🛑 {tr('Usuwanie Konta')}")
            st.warning(tr("Uwaga: Ta operacja jest nieodwracalna. Zostaną usunięte wszystkie Twoje treningi, statystyki, wiadomości i integracje."))
            
            del_confirm = st.text_input(tr("Wpisz 'USUŃ' aby potwierdzić:"))
            
            if st.button(tr("Trwale usuń moje konto"), type="primary"):
                if del_confirm == tr("USUŃ"):
                    # 1. Usuwanie z listy zawodników
                    db["zawodnicy_list"] = [z for z in db.get("zawodnicy_list", []) if z != ja]
                    
                    # 2. Usuwanie konta (loginu)
                    users_temp = db.get("users_db", {})
                    if ja in users_temp: 
                        del users_temp[ja]
                        db["users_db"] = users_temp
                        
                    # 3. Usuwanie powiązanych danych z list
                    db["treningi"] = [w for w in db.get("treningi", []) if w.get("zawodnik") != ja]
                    db["wyscigi"] = [w for w in db.get("wyscigi", []) if w.get("zawodnik") != ja]
                    db["fizjologia"] = [w for w in db.get("fizjologia", []) if w.get("zawodnik") != ja]
                    db["power_profile"] = [w for w in db.get("power_profile", []) if w.get("zawodnik") != ja]
                    db["run_records"] = [w for w in db.get("run_records", []) if w.get("zawodnik") != ja]
                    db["waga"] = [w for w in db.get("waga", []) if w.get("zawodnik") != ja]
                    db["day_notes"] = [w for w in db.get("day_notes", []) if w.get("zawodnik") != ja]
                    db["chat"] = [m for m in db.get("chat", []) if m.get("od") != ja and m.get("do") != ja]
                    
                    # 4. Usuwanie danych ze słowników
                    for dict_key in ["strefy", "garmin_creds", "zawodnicy_info"]:
                        temp_d = db.get(dict_key, {})
                        if ja in temp_d:
                            del temp_d[ja]
                            db[dict_key] = temp_d
                            
                    st.success("Konto usunięte bezpowrotnie.")
                    time.sleep(2)
                    st.session_state.logged_in = False
                    st.rerun()
                else:
                    st.error(tr("Wpisz słowo USUŃ poprawnie."))

# --- 5. RAPORTY PDF ---
elif menu == tr("Raporty"):
    st.title(tr("Centrum Raportowania")); 
    if st.session_state.role != "coach": st.warning(tr("Dla trenera.")); st.stop()
    sel_user = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=get_display_name)
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
    sel_user = st.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=get_display_name) if st.session_state.role=="coach" else ja
    
    sel_disc = st.selectbox(tr("Dyscyplina"), ["Rower", "Bieganie", "Pływanie", "Siłownia", "Inne"], format_func=tr)
    user_data = get_user_zones(sel_user, sel_disc)
    is_pace = sel_disc in ["Bieganie", "Pływanie"]
    
    c1, c2, c3 = st.columns(3)
    if is_pace:
        label = tr("Próg Tempo (MM:SS/km)") if sel_disc == "Bieganie" else tr("Próg Tempo (MM:SS/100m)")
        new_ftp = c1.text_input(label, value=str(user_data.get("ftp", "4:30" if sel_disc == "Bieganie" else "1:45")))
    else:
        new_ftp = c1.number_input("FTP (W)", value=int(user_data.get("ftp", 250)))
        
    new_lthr = c2.number_input("LTHR (BPM)", value=int(user_data.get("lthr", 170)))
    
    if c3.button(tr("Przelicz / Zresetuj")): 
        zp, zh = generuj_domyslne_strefy(new_ftp, new_lthr, is_pace=is_pace)
        user_data["zones_pwr"] = zp.to_dict('records')
        user_data["zones_hr"] = zh.to_dict('records')
        user_data["ftp"] = new_ftp
        user_data["lthr"] = new_lthr
        
        temp_db = db["strefy"]
        if sel_user not in temp_db: temp_db[sel_user] = {}
        temp_db[sel_user][sel_disc] = user_data
        db["strefy"] = temp_db
        st.rerun()
        
    c1, c2 = st.columns(2)
    with c1: 
        st.subheader(tr("Tempo") if is_pace else tr("Moc"))
        edited_pwr = st.data_editor(pd.DataFrame(user_data["zones_pwr"]), column_order=["Strefa", "Min", "Max"], hide_index=True, key=f"pwr_{sel_user}_{sel_disc}")
    with c2: 
        st.subheader(tr("Tętno"))
        edited_hr = st.data_editor(pd.DataFrame(user_data["zones_hr"]), column_order=["Strefa", "Min", "Max"], hide_index=True, key=f"hr_{sel_user}_{sel_disc}")
    
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
    if 'loaded_template_name' not in st.session_state: st.session_state['loaded_template_name'] = ""
    
    with c1:
        opts = [tr("-- Własny --")] + [s.get('nazwa',tr('Bez nazwy')) for s in db.get("biblioteka", [])]
        load = st.selectbox(tr("Szablon / Fragment"), opts)
        
        if load != tr("-- Własny --"):
            col_l1, col_l2, col_l3 = st.columns(3)
            if col_l1.button(tr("🔄 Zastąp")): 
                tmpl = next((x for x in db["biblioteka"] if x['nazwa']==load), None)
                if tmpl:
                    st.session_state['pro_steps'] = list(tmpl['kroki'])
                    st.session_state['loaded_template_name'] = tmpl['nazwa']
                    st.rerun()
            if col_l2.button(tr("➕ Doklej")):
                tmpl = next((x for x in db["biblioteka"] if x['nazwa']==load), None)
                if tmpl:
                    st.session_state['pro_steps'].extend(list(tmpl['kroki']))
                    st.rerun()
            if col_l3.button(tr("🗑️ Usuń")):
                db["biblioteka"] = [x for x in db.get("biblioteka", []) if x['nazwa'] != load]
                if st.session_state['loaded_template_name'] == load:
                    st.session_state['loaded_template_name'] = ""
                st.success(tr("Usunięto!"))
                time.sleep(1)
                st.rerun()
                
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
            if st.button(tr("Wyczyść Kreator")): 
                st.session_state['pro_steps'] = []
                st.session_state['loaded_template_name'] = ""
                st.rerun()
                
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
                n = st.text_input(tr("Nazwa"), value=st.session_state['loaded_template_name'])
                if st.form_submit_button(tr("💾 Zapisz / Aktualizuj")): 
                    if n:
                        lib = list(db.get("biblioteka", []))
                        existing_idx = next((i for i, x in enumerate(lib) if x['nazwa'] == n), -1)
                        if existing_idx >= 0:
                            lib[existing_idx] = {"nazwa": n, "kroki": st.session_state['pro_steps'], "dyscyplina": sport_creator}
                            msg = tr("Zaktualizowano istniejący szablon!")
                        else:
                            lib.append({"nazwa": n, "kroki": st.session_state['pro_steps'], "dyscyplina": sport_creator})
                            msg = tr("Zapisano nowy szablon!")
                        
                        db["biblioteka"] = lib
                        st.success(msg)
                        st.session_state['pro_steps'] = []
                        st.session_state['loaded_template_name'] = ""
                        time.sleep(1)
                        st.rerun()

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
                p_athlete = c1.selectbox(tr("Wybierz zawodnika:"), ZAWODNICY, format_func=get_display_name)
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
    if st.button(tr("RESET DANYCH")): db["treningi"]=[]; db["run_records"]=[]; db["power_profile"]=[]; db["waga"]=[]; db["chat"]=[]; db["wyscigi"]=[]; db["plany"]=[]; db["day_notes"]=[]; st.session_state.session_treningi=[]; st.rerun()
