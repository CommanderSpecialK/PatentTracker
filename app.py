import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import random
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Patent Live Tracker", layout="wide")
st.title("🌐 Internationaler Patent-Live-Tracker")

# --- 1. ZENTRALE LÄNDER-KONFIGURATION ---
# Das Mapping nutzt jetzt die offiziellen 2-stelligen Ländercodes der Patentnummern
LAND_KONFIG = {
    "US": {"farbe": "blue", "lat": 39.8283, "lon": -98.5795},       # USA
    "DE": {"farbe": "red", "lat": 51.1657, "lon": 10.4515},        # Deutschland
    "JP": {"farbe": "darkpurple", "lat": 36.2048, "lon": 138.2529}, # Japan
    "CN": {"farbe": "orange", "lat": 35.8617, "lon": 104.1954},     # China
    "KR": {"farbe": "green", "lat": 35.9078, "lon": 127.7669},      # Südkorea
    "EP": {"farbe": "purple", "lat": 50.1109, "lon": 8.6821},       # Europäisches Patentamt
    "WO": {"farbe": "darkblue", "lat": 46.2044, "lon": 6.1432}      # Weltorganisation (WIPO / Genf)
}

# --- 2. DATEN AUS DER ECHTEN WOCHEN-CSV LADEN ---
@st.cache_data(ttl=60)
def load_patent_data():
    # Liest die CSV mit Semikolon-Trennung und entfernt eventuelle Leerzeichen im Header
    df = pd.read_csv("patente.csv", sep=";", skipinitialspace=True)
    
    # Spaltennamen bereinigen (Anführungszeichen entfernen, falls vorhanden)
    df.columns = df.columns.str.replace('"', '').str.strip()
    
    # Veröffentlichungsdatum ins richtige Datumsformat konvertieren
    df['Veröffentlichungsdatum'] = pd.to_datetime(df['Veröffentlichungsdatum'].str.replace('"', '').str.strip())
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
    # Nutzen der "Veröffentlichungsnummer" als eindeutige ID
    verfuegbare_patente = all_patents_df[~all_patents_df['Veröffentlichungsnummer'].isin(st.session_state.sichtbare_patent_ids)]
    
    if not verfuegbare_patente.empty:
        neues_patent = verfuegbare_patente.sample(n=1).iloc[0]
        st.session_state.sichtbare_patent_ids.append(neues_patent['Veröffentlichungsnummer'])
    
    st.session_state.naechster_intervall = random.randint(120, 600)
    st.session_state.letzter_zeitstempel = time.time()
    vergangene_zeit = 0

# --- 5. VERBLASSEN-LOGIK (ÄLTER ALS 2 TAGE) ---
jetzt = datetime.now()
zwei_tage_her = jetzt - timedelta(days=2)
sichtbare_patente_df = all_patents_df[all_patents_df['Veröffentlichungsnummer'].isin(st.session_state.sichtbare_patent_ids)]

# --- 6. FOLIUM KARTE ERSTELLEN (MIT WELT-BEGRENZUNG) ---
# no_wrap=True verhindert das Wiederholen der Weltkarte beim Zoomen
m = folium.Map(
    location=[20.0, 0.0], 
    zoom_start=2, 
    tiles="CartoDB positron",
    min_zoom=2,
    max_bounds=True
)

# Kachel-Layer mit no_wrap=True überschreiben, um die Endlos-Weltkarte zu stoppen
folium.TileLayer("CartoDB positron", no_wrap=True).add_to(m)

# Marker setzen
for idx, row in sichtbare_patente_df.iterrows():
    if row['Veröffentlichungsdatum'] < zwei_tage_her:
        continue
    
    pub_nr = str(row['Veröffentlichungsnummer']).replace('"', '').strip()
    titel = str(row['Titel']).replace('"', '').strip()
    anmelder = str(row['Anmelder']).replace('"', '').strip()
    
    # Extrahiere das Land aus den ersten zwei Buchstaben der Veröffentlichungsnummer (z.B. "WO" oder "EP")
    land_code = pub_nr[:2].upper()
    konfig = LAND_KONFIG.get(land_code, {"farbe": "gray", "lat": 20.0, "lon": 0.0})
    
    # Stabiler Jitter basierend auf der Patentnummer
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
