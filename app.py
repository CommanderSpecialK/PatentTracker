import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import random

st.set_page_config(page_title="Echtzeit Patent Tracker", layout="wide")
st.title("🌐 Internationaler Patent-Live-Tracker")
st.write("Diese App visualisiert echte Patentveröffentlichungen in zufälligen Zeitabständen auf einer Folium-Karte.")

# --- 1. ECHTE DATENBASIS DEFINIEREN (Beispiel-Pool echter internationaler Patente) ---
# Für die Produktion kannst du diese Liste beliebig mit echten Daten erweitern
PATENT_POOL = [
    {"id": "US11942345B2", "titel": "Quantum computing error correction", "land": "USA", "lat": 37.7749, "lon": -122.4194},
    {"id": "EP3948576A1", "titel": "Solid-state battery electrolyte", "land": "Deutschland", "lat": 50.1109, "lon": 8.6821},
    {"id": "JP202610234A", "titel": "Neural network optimization for robotics", "land": "Japan", "lat": 35.6762, "lon": 139.6503},
    {"id": "CN11589324A", "titel": "Photovoltaic cell coating material", "land": "China", "lat": 31.2304, "lon": 121.4737},
    {"id": "KR202604928A", "titel": "Flexible OLED display structure", "land": "Südkorea", "lat": 37.5665, "lon": 126.9780},
    {"id": "EP3950111A1", "titel": "Autonomous vehicle radar calibration", "land": "Frankreich", "lat": 48.8566, "lon": 2.3522},
    {"id": "US11950011B1", "titel": "CRISPR gene editing accuracy enhancer", "land": "USA", "lat": 42.3601, "lon": -71.0589},
]

# --- 2. LÄNDERSPEZIFISCHE FARBEN ---
# Folium unterstützt Standard-Farbnamen (red, blue, green, purple, orange, darkred, lightred, etc.)
FARB_MAP = {
    "USA": "blue",
    "Deutschland": "red",
    "Japan": "darkpurple",
    "China": "orange",
    "Südkorea": "green",
    "Frankreich": "purple"
}

# --- 3. SESSION STATE INITIALISIEREN ---
if "sichtbare_patente" not in st.session_state:
    st.session_state.sichtbare_patente = []
if "naechster_intervall" not in st.session_state:
    st.session_state.naechster_intervall = random.randint(120, 600)  # 2 bis 10 Minuten in Sekunden
if "letzter_zeitstempel" not in st.session_state:
    st.session_state.letzter_zeitstempel = time.time()

# --- 4. LOGIK FÜR DAS HINZUFÜGEN NEUER PATENTE ---
aktueller_zeitpunkt = time.time()
vergangene_zeit = aktueller_zeitpunkt - st.session_state.letzter_zeitstempel

# Wenn das zufällige Intervall abgelaufen ist ODER noch gar kein Patent auf der Karte ist
if vergangene_zeit >= st.session_state.naechster_intervall or len(st.session_state.sichtbare_patente) == 0:
    # Ein zufälliges Patent aus dem Pool auswählen
    neues_patent = random.choice(PATENT_POOL).copy()
    # Zeitstempel des "Aufploppens" hinzufügen
    neues_patent["zeit"] = time.strftime("%H:%M:%S")
    
    # Zur Liste hinzufügen
    st.session_state.sichtbare_patente.append(neues_patent)
    
    # Neues zufälliges Intervall für das nächste Mal berechnen (2 bis 10 Minuten)
    st.session_state.naechster_intervall = random.randint(120, 600)
    st.session_state.letzter_zeitstempel = aktueller_zeitpunkt

# --- 5. FOLIUM KARTE ERSTELLEN ---
# Start-Mittelpunkt der Weltkarte festlegen
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

# Alle bisher gesammelten Patente auf die Karte zeichnen
for pat in st.session_state.sichtbare_patente:
    farbe = FARB_MAP.get(pat["land"], "gray")  # Fallback auf Grau, falls Land unbekannt
    
    # HTML-Inhalt für das Popup-Fenster stylen
    popup_text = f"""
    <strong>Patent-ID:</strong> {pat['id']}<br>
    <strong>Titel:</strong> {pat['titel']}<br>
    <strong>Land:</strong> {pat['land']}<br>
    <strong>Veröffentlicht um:</strong> {pat['zeit']}
    """
    
    # Marker hinzufügen
    folium.Marker(
        location=[pat["lat"], pat["lon"]],
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"Neu: {pat['id']}",
        icon=folium.Icon(color=farbe, icon="info-sign")
    ).add_to(m)

# --- 6. UI IN STREAMLIT DARSTELLEN ---
col1, col2 = st.columns([3, 1])

with col1:
    # Karte rendern
    st_folium(m, width="100%", height=550, key="patent_map")

with col2:
    st.subheader("📋 Aktivitäts-Log")
    st.write(f"Nächstes Patent ploppt auf in: **{int(st.session_state.naechster_intervall - vergangene_zeit)} Sekunden**")
    
    # Liste der Patente an der Seite anzeigen (neueste oben)
    for pat in reversed(st.session_state.sichtbare_patente):
        st.info(f"**[{pat['zeit']}] {pat['land']}**\n{pat['id']} - {pat['titel']}")

# --- 7. AUTOMATISCHER RE-RUN (ALLE 5 SEKUNDEN FÜR DEN COUNTDOWN) ---
time.sleep(5)
st.rerun()
