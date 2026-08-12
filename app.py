import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Patent Live Tracker", layout="wide")
st.title("🌐 Internationaler Patent-Live-Tracker")

# --- 1. ZENTRALE LÄNDER-KONFIGURATION ---
LAND_KONFIG = {
    "USA": {"farbe": "blue", "lat": 39.8283, "lon": -98.5795},
    "Deutschland": {"farbe": "red", "lat": 51.1657, "lon": 10.4515},
    "Japan": {"farbe": "darkpurple", "lat": 36.2048, "lon": 138.2529},
    "China": {"farbe": "orange", "lat": 35.8617, "lon": 104.1954},
    "Südkorea": {"farbe": "green", "lat": 35.9078, "lon": 127.7669},
    "Frankreich": {"farbe": "purple", "lat": 46.2276, "lon": 2.2137}
}

# --- 2. DATEN AUS CSV LADEN ---
@st.cache_data(ttl=60)
def load_patent_data():
    df = pd.read_csv("patente.csv")
    df['veroeffentlicht_am'] = pd.to_datetime(df['veroeffentlicht_am'])
    return df

try:
    all_patents_df = load_patent_data()
except Exception as e:
    st.error(f"Fehler beim Laden der patente.csv: {e}")
    st.stop()

# --- 3. SESSION STATE INITIALISIEREN ---
if "sichtbare_patent_ids" not in st.session_state:
    st.session_state.sichtbare_patent_ids = []
if "naechster_intervall" not in st.session_state:
    st.session_state.naechster_intervall = random.randint(120, 600)  # 2 bis 10 Minuten
if "letzter_zeitstempel" not in st.session_state:
    st.session_state.letzter_zeitstempel = time.time()

# --- 4. LOGIK FÜR DAS AUFPLOPPEN ---
aktueller_zeitpunkt = time.time()
vergangene_zeit = aktueller_zeitpunkt - st.session_state.letzter_zeitstempel

# Nur wenn die Wartezeit abgelaufen ist (oder noch gar kein Punkt da ist), wird gewürfelt
if vergangene_zeit >= st.session_state.naechster_intervall or len(st.session_state.sichtbare_patent_ids) == 0:
    verfuegbare_patente = all_patents_df[~all_patents_df['id'].isin(st.session_state.sichtbare_patent_ids)]
    
    if not verfuegbare_patente.empty:
        neues_patent = verfuegbare_patente.sample(n=1).iloc[0]
        st.session_state.sichtbare_patent_ids.append(neues_patent['id'])
    
    # Werte für die nächste Runde zurücksetzen
    st.session_state.naechster_intervall = random.randint(120, 600)
    st.session_state.letzter_zeitstempel = time.time()
    # Da ein neues Patent dazukam, müssen wir sofort neu zeichnen
    vergangene_zeit = 0 

# --- 5. VERBLASSEN-LOGIK ---
jetzt = datetime.now()
zwei_tage_gringo = jetzt - timedelta(days=2)
sichtbare_patente_df = all_patents_df[all_patents_df['id'].isin(st.session_state.sichtbare_patent_ids)]

# --- 6. FOLIUM KARTE ERSTELLEN ---
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

# Marker setzen
for idx, row in sichtbare_patente_df.iterrows():
    if row['veroeffentlicht_am'] < zwei_tage_gringo:
        continue
    
    land_name = row['land']
    konfig = LAND_KONFIG.get(land_name, {"farbe": "gray", "lat": 0.0, "lon": 0.0})
    
    # Jitter-Effekt (Nutzt die Patent-ID als Seed, damit der Punkt pro Patent stabil bleibt und nicht hin- und herspringt)
    random.seed(hash(row['id']))
    jitter_lat = konfig["lat"] + random.uniform(-1.5, 1.5)
    jitter_lon = konfig["lon"] + random.uniform(-1.5, 1.5)
    
    google_patents_url = f"https://google.com{row['id']}/en"
    
    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 13px;">
        <strong>Patent-ID:</strong> <a href="{google_patents_url}" target="_blank" style="color: #1A73E8; font-weight: bold;">{row['id']} ↗</a><br>
        <strong>Titel:</strong> {row['titel']}<br>
        <strong>Land:</strong> {land_name}<br>
        <strong>Veröffentlicht am:</strong> {row['veroeffentlicht_am'].strftime('%d.%m.%Y %H:%M')}
    </div>
    """
    
    folium.Marker(
        location=[jitter_lat, jitter_lon],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Patent: {row['id']}",
        icon=folium.Icon(color=konfig["farbe"], icon="info-sign")
    ).add_to(m)

# --- 7. UI DARSTELLUNG (Statisch ohne Flackern) ---
st_folium(m, width="100%", height=650, key="patent_map")

# --- 8. INTELLIGENTER TIMER ---
# Berechne exakt, wie viele Sekunden wir noch bis zum nächsten Aufploppen warten müssen
restliche_wartezeit = st.session_state.naechster_intervall - vergangene_zeit

if restliche_wartezeit > 0:
    # Die App schläft genau so lange, wie sie muss, anstatt alle 10 Sekunden neu zu laden
    time.sleep(restliche_wartezeit)
    st.rerun()
