import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import random
from datetime import datetime, timedelta
import csv

st.set_page_config(page_title="Patent Live Tracker", layout="wide")
st.title("🌐 Internationaler Patent-Live-Tracker")

# --- 1. ZENTRALE LÄNDER-KONFIGURATION ---
LAND_KONFIG = {
    "US": {"farbe": "blue", "lat": 39.8283, "lon": -98.5795},       
    "DE": {"farbe": "red", "lat": 51.1657, "lon": 10.4515},        
    "JP": {"farbe": "darkpurple", "lat": 36.2048, "lon": 138.2529}, 
    "CN": {"farbe": "orange", "lat": 35.8617, "lon": 104.1954},     
    "KR": {"farbe": "green", "lat": 35.9078, "lon": 127.7669},      
    "EP": {"farbe": "purple", "lat": 50.1109, "lon": 8.6821},       
    "WO": {"farbe": "darkblue", "lat": 46.2044, "lon": 6.1432}      
}

# --- 2. DATEN AUS DER ZERSTÜCKELTEN CSV ROBUST LADEN ---
@st.cache_data(ttl=60)
def load_patent_data():
    zeilen = []
    # UTF-8 mit BOM ('utf-8-sig') fängt ab, falls Excel die Datei codiert hat
    with open("patente.csv", mode="r", encoding="utf-8-sig") as f:
        # Der csv.reader erkennt automatisch, wenn Zeilenumbrüche INNERHALB von Anführungszeichen "..." stehen
        reader = csv.reader(f, delimiter=";", quotechar='"')
        
        # Header einlesen und säubern
        header = [spalte.strip() for spalte in next(reader)]
        
        for zeile in reader:
            if len(zeile) >= len(header):
                # Säubere alle Felder von ungewollten Zeilenumbrüchen im Text für die spätere Darstellung
                gesaeuberte_zeile = [feld.replace("\n", " ").strip() for feld in zeile]
                zeilen.append(gesaeuberte_zeile)
                
    # Erstelle den DataFrame aus den korrekt zusammengesetzten Zeilen
    df = pd.DataFrame(zeilen, columns=header)
    
    # Datumsspalte konvertieren
    df['Veröffentlichungsdatum'] = pd.to_datetime(df['Veröffentlichungsdatum'])
    return df

try:
    all_patents_df = load_patent_data()
except Exception as e:
    st.error(f"Fehler beim Laden der echten patente.csv: {e}")
    st.stop()

# --- 3. SESSION STATE INITIALISIEREN ---
if "sichtbare_patent_ids" not in st.session_state:
    st.session_state.sichtbare_patent_ids = []
if "naechster_intervall" not in st.session_state:
    st.session_state.naechster_intervall = random.randint(120, 600)
if "letzter_zeitstempel" not in st.session_state:
    st.session_state.letzter_zeitstempel = time.time()

# --- 4. LOGIK FÜR DAS AUFPLOPPEN ---
aktueller_zeitpunkt = time.time()
vergangene_zeit = aktueller_zeitpunkt - st.session_state.letzter_zeitstempel

if vergangene_zeit >= st.session_state.naechster_intervall or len(st.session_state.sichtbare_patent_ids) == 0:
    verfuegbare_patente = all_patents_df[~all_patents_df['Veröffentlichungsnummer'].isin(st.session_state.sichtbare_patent_ids)]
    
    if not verfuegbare_patente.empty:
        neues_patent = verfuegbare_patente.sample(n=1).iloc
        st.session_state.sichtbare_patent_ids.append(neues_patent['Veröffentlichungsnummer'])
    
    st.session_state.naechster_intervall = random.randint(120, 600)
    st.session_state.letzter_zeitstempel = time.time()
    vergangene_zeit = 0

# --- 5. VERBLASSEN-LOGIK (ÄLTER ALS 2 TAGE) ---
jetzt = datetime.now()
zwei_tage_her = jetzt - timedelta(days=2)
sichtbare_patente_df = all_patents_df[all_patents_df['Veröffentlichungsnummer'].isin(st.session_state.sichtbare_patent_ids)]

# --- 6. FOLIUM KARTE ERSTELLEN (WELT-BEGRENZUNG) ---
m = map = folium.Map(
    location=[20.0, 0.0], 
    zoom_start=2, 
    tiles="CartoDB positron",
    min_zoom=2,
    max_bounds=True
)
folium.TileLayer("CartoDB positron", no_wrap=True).add_to(m)

# Marker setzen
for idx, row in sichtbare_patente_df.iterrows():
    if row['Veröffentlichungsdatum'] < zwei_tage_her:
        continue
    
    pub_nr = str(row['Veröffentlichungsnummer'])
    titel = str(row['Titel'])
    anmelder = str(row['Anmelder'])
    
    land_code = pub_nr[:2].upper()
    konfig = LAND_KONFIG.get(land_code, {"farbe": "gray", "lat": 20.0, "lon": 0.0})
    
    random.seed(hash(pub_nr))
    jitter_lat = konfig["lat"] + random.uniform(-2.0, 2.0)
    jitter_lon = konfig["lon"] + random.uniform(-2.0, 2.0)
    
    google_patents_url = f"https://google.com{pub_nr}/en"
    
    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 13px; min-width: 200px;">
        <strong>Patent-ID:</strong> <a href="{google_patents_url}" target="_blank" style="color: #1A73E8; font-weight: bold;">{pub_nr} ↗</a><br>
        <p style="margin: 5px 0;"><strong>Titel:</strong> {titel[:100]}...</p>
        <strong>Anmelder:</strong> {anmelder[:50]}...<br>
        <strong>Veröffentlicht am:</strong> {row['Veröffentlichungsdatum'].strftime('%d.%m.%Y')}
    </div>
    """
    
    folium.Marker(
        location=[jitter_lat, jitter_lon],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Patent: {pub_nr}",
        icon=folium.Icon(color=konfig["farbe"], icon="info-sign")
    ).add_to(m)

# --- 7. UI DARSTELLUNG ---
st_folium(m, width="100%", height=650, key="patent_map")

# --- 8. INTELLIGENTER TIMER ---
restliche_wartezeit = st.session_state.naechster_intervall - vergangene_zeit
if restliche_wartezeit > 0:
    time.sleep(restliche_wartezeit)
    st.rerun()
