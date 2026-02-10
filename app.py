import streamlit as st
import requests
import logic  # Použije tvůj stávající soubor logic.py

# Nastavení stránky
st.set_page_config(page_title="Můj Zpěvník", layout="wide")

# Načtení klíčů ze Secrets (to nastavíš v ovládacím panelu Streamlitu)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    # Načte písně i s jmény interpretů najednou
    r = requests.get(f"{URL}/rest/v1/pisne?select=*,interpreti(jmeno)", headers=headers)
    return r.json()

st.title("🎸 Online Zpěvník")

try:
    data = nacti_data()
    # Vytvoření seznamu pro výběr
    seznam_pisni = [f"{p['interpreti']['jmeno']} - {p['nazev']}" for p in data]
    vyber = st.selectbox("Vyber píseň:", seznam_pisni)

    if vyber:
        pisen = data[seznam_pisni.index(vyber)]
        
        col1, col2 = st.columns([1, 3])
        with col1:
            posun = st.number_input("Transpozice", value=0, step=1)
        
        # Použití tvé původní logiky z logic.py!
        transponovany_text = logic.transponuj_text(pisen['text_akordy'], posun)
        
        # Zobrazení textu (st.code zachová formátování akordů)
        st.code(transponovany_text, language="text")

except Exception as e:
    st.error(f"Chyba při načítání: {e}")
