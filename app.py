import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import random
from datetime import datetime, timedelta
import openpyxl

st.set_page_config(page_title="Patent Live Tracker", layout="wide")
st.title("🌐 Internationaler Patent-Live-Tracker (Chronologisch)")

# --- 1. ZENTRALE LÄNDER-KONFIGURATION ---
LAND_KONFIG = {
    "US": {"farbe": "blue", "lat": 39.8283, "lon": -98.5795},       
    "DE": {"farbe": "red", "lat": 51.1657, "lon": 10.4515},        
    "AT": {"farbe": "lightred", "lat": 47.5162, "lon": 14.5501},   
    "FR": {"farbe": "purple", "lat": 46.2276, "lon": 2.2137},       
    "ES": {"farbe": "orange", "lat": 40.4637, "lon": -3.7492},      
    "PL": {"farbe": "darkgreen", "lat": 51.9194, "lon": 19.1451},   
    "RU": {"farbe": "darkred", "lat": 61.5240, "lon": 105.3188},    
    "JP": {"farbe": "darkpurple", "lat": 36.2048, "lon": 138.2529}, 
    "CN": {"farbe": "orange", "lat": 35.8617, "lon": 104.1954},     
    "KR": {"farbe": "green", "lat": 35.9078, "lon": 127.7669},      
    "CO": {"farbe": "cadetblue", "lat": 4.5709, "lon": -74.2973},   
    "EP": {"farbe": "purple", "lat": 50.1109, "lon": 8.6821},       
    "WO": {"farbe": "darkblue", "lat": 46.2044, "lon": 6.1432}      
}

# --- 2. EXCEL MIT HYPERLINKS DYNAMISCHES LADEN & SORTIEREN ---
@st.cache_data(ttl=60)
def load_patent_data():
    # 1. Header-Zeile ermitteln
    raw_df = pd.read_excel("patente.xlsx", header=None, engine="openpyxl")
    header_row_index = 0
    for idx, row in raw_df.iterrows():
        if row.astype(str).str.contains("Publication Number").any():
            header_row_index = idx
            break
            
    # 2. DataFrame normal laden
    df = pd.read_excel("patente.xlsx", skiprows=header_row_index, engine="openpyxl")
    df.columns = df.columns.str.strip()
    
    # 3. Native Hyperlinks mit openpyxl aus Spalte A ("Application ID") extrahieren
    wb = openpyxl.load_workbook("patente.xlsx", data_only=False)
    ws = wb.active
    
    extracted_urls = []
    # Datenzeilen beginnen im Excel direkt unter dem Header-Index (berücksichtige 1-basierte Excel-Indizierung)
    start_row = header_row_index + 2 
    
    for i in range(len(df)):
        cell = ws.cell(row=start_row + i, column=1) # Spalte 1 ist "Application ID"
        if cell.hyperlink and cell.hyperlink.target:
            extracted_urls.append(cell.hyperlink.target)
        else:
            # Fallback, falls in der Zeile mal kein Link hinterlegt sein sollte
            extracted_urls.append(None)
            
    df['Extracted_URL'] = extracted_urls
    
    # 4. Chronologisch sortieren (Älteste zuerst)
    df['Publication Date'] = pd.to_datetime(df['Publication Date'])
    df = df.sort_values(by='Publication Date', ascending=True)
    df['Publication Number'] = df['Publication Number'].astype(str).str.strip()
    return df

try:
    all_patents_df = load_patent_data()
except Exception as e:
    st.error(f"Fehler beim Laden der echten patente.xlsx: {e}")
    st.stop()

# --- 3. SESSION STATE INITIALISIEREN ---
if "sichtbare_patente_zeit" not in st.session_state:
    st.session_state.sichtbare_patente_zeit = {}
if "naechster_intervall" not in st.session_state:
    st.session_state.naechster_intervall = random.randint(120, 600)
if "letzter_zeitstempel" not in st.session_state:
    st.session_state.letzter_zeitstempel = time.time()

# --- 4. CHRONOLOGISCHE LOGIK FÜR DAS AUFPLOPPEN ---
aktueller_zeitpunkt = time.time()
vergangene_zeit = aktueller_zeitpunkt - st.session_state.letzter_zeitstempel

if vergangene_zeit >= st.session_state.naechster_intervall or len(st.session_state.sichtbare_patente_zeit) == 0:
    sichtbare_ids = list(st.session_state.sichtbare_patente_zeit.keys())
    verfuegbare_patente = all_patents_df[~all_patents_df['Publication Number'].isin(sichtbare_ids)]
    
    if not verfuegbare_patente.empty:
        naechstes_patent = verfuegbare_patente.iloc
        neue_id = str(naechstes_patent['Publication Number'])
        st.session_state.sichtbare_patente_zeit[neue_id] = datetime.now()
    
    st.session_state.naechster_intervall = random.randint(120, 600)
    st.session_state.letzter_zeitstempel = time.time()
    vergangene_zeit = 0

# --- 5. VERBLASSEN-LOGIK (Nach 2 Tagen ausblenden) ---
jetzt = datetime.now()
zwei_tage_her = jetzt - timedelta(days=2)

aktive_ids = [
    pid for pid, aufplopp_zeit in st.session_state.sichtbare_patente_zeit.items()
    if aufplopp_zeit >= zwei_tage_her
]

sichtbare_patente_df = all_patents_df[all_patents_df['Publication Number'].isin(aktive_ids)]

# --- 6. FOLIUM KARTE ERSTELLEN ---
m = folium.Map(
    location=[20.0, 0.0], 
    zoom_start=2, 
    tiles="CartoDB positron",
    min_zoom=2,
    max_bounds=True
)
folium.TileLayer("CartoDB positron", no_wrap=True).add_to(m)

# Marker setzen
for idx, row in sichtbare_patente_df.iterrows():
    pub_nr = str(row['Publication Number'])
    titel = str(row['Title']).replace('\n', ' ')
    anmelder = str(row['Applicants']).replace('\n', ' ')
    land_code = str(row['Country']).strip().upper()
    v_datum = row['Publication Date'].strftime('%d.%m.%Y')
    
    # --- ABFANGEN NICHT GELISTETER LÄNDER (Fallback) ---
    # Falls ein Land fehlt, wird 'gray' und die Koordinate [0.0, 0.0] (Nullinsel am Äquator) gewählt
    konfig = LAND_KONFIG.get(land_code, {"farbe": "gray", "lat": 0.0, "lon": 0.0})
    
    random.seed(hash(pub_nr))
    jitter_lat = konfig["lat"] + random.uniform(-2.0, 2.0)
    jitter_lon = konfig["lon"] + random.uniform(-2.0, 2.0)
    
    # --- HYPERLINK NUTZEN ---
    # Nutzt die aus Excel extrahierte URL. Falls leer, wird als Fallback Google Patents generiert
    excel_url = row['Extracted_URL']
    if pd.isna(excel_url) or not excel_url:
        clean_url_id = pub_nr.replace("/", "").replace(" ", "").replace("-", "")
        patent_url = f"https://google.com/{clean_url_id}/en"
    else:
        patent_url = str(excel_url)
    
    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 13px; min-width: 200px;">
        <strong>Patent-ID:</strong> <a href="{patent_url}" target="_blank" style="color: #1A73E8; font-weight: bold; text-decoration: underline;">{pub_nr} ↗</a><br>
        <p style="margin: 5px 0;"><strong>Titel:</strong> {titel[:100]}...</p>
        <strong>Anmelder:</strong> {anmelder[:50]}...<br>
        <strong>Veröffentlicht am:</strong> {v_datum}
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
