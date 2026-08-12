import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Patent Live Tracker Simulation", layout="wide")
st.title("🌐 Live Patent Veröffentlichungen (Simulation)")
st.write("Diese App simuliert das weltweite Aufploppen von Patenten in Echtzeit.")

# Session State initialisieren, um die Punkte über Rerenders hinweg zu speichern
if "patent_data" not in st.session_state:
    # Wir starten mit einer leeren Liste/Datenrahmen
    st.session_state.patent_data = pd.DataFrame(columns=["lat", "lon", "titel"])

# Platzhalter für die Karte, damit sie an derselben Stelle aktualisiert wird
map_placeholder = st.empty()

# Button zum Starten/Stoppen der Simulation
start_sim = st.checkbox("Simulation starten", value=True)

# Endlosschleife für die Live-Aktualisierung
while start_sim:
    # 1. Zufällige neue Koordinaten generieren (Simulation eines neuen Patents)
    # Normale Zufallszahlen zentriert um typische Ballungsräume (z.B. USA, Europa, Asien)
    new_lat = np.random.uniform(-40, 60)
    new_lon = np.random.uniform(-120, 140)
    new_title = f"Patent Nr. {np.random.randint(100000, 999999)}"
    
    new_row = pd.DataFrame([{"lat": new_lat, "lon": new_lon, "titel": new_title}])
    
    # 2. Zum bestehenden Datensatz in der Session hinzufügen
    st.session_state.patent_data = pd.concat([st.session_state.patent_data, new_row], ignore_index=True)
    
    # Optional: Begrenzen auf die letzten 50 Punkte, damit die Karte nicht überlädt
    if len(st.session_state.patent_data) > 50:
        st.session_state.patent_data = st.session_state.patent_data.tail(50)
    
    # 3. Karte im Platzhalter neu zeichnen
    with map_placeholder.container():
        st.map(st.session_state.patent_data, latitude="lat", longitude="lon", size=20)
        st.caption(f"Letztes veröffentlichtes Patent: {new_title} bei [{new_lat:.2f}, {new_lon:.2f}]")
    
    # 4. Wartezeit bis zum nächsten "Aufploppen" (z. B. 1.5 Sekunden)
    time.sleep(1.5)
    
    # Rerender erzwingen
    st.rerun()
