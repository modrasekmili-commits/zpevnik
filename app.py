import streamlit as st
import requests
import logic
import streamlit.components.v1 as components
import re

# 1. Konfigurace
st.set_page_config(page_title="Zpěvník Online", layout="wide")

# 2. Vyladěné CSS pro perfektní zarovnání
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    .song-container {
        background-color: #1a1a1a;
        color: #e0e0e0;
        padding: 25px;
        border-radius: 8px;
        
        /* Absolutní vynucení neproporcionálního písma */
        font-family: 'Roboto Mono', 'Consolas', 'Monaco', monospace !important;
        
        height: 75vh;
        overflow-y: auto;
        overflow-x: auto; /* Důležité: řádek se nesmí zlomit, musí odjet doprava */
        
        /* Zásadní pro bílé znaky */
        white-space: pre !important; 
        word-wrap: normal !important;
        
        font-size: 18px;
        line-height: 1.3; /* Fixní výška řádku */
        border: 1px solid #333;
    }
    
    .stApp { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=600)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

with st.sidebar:
    st.title("🎸 Nastavení")
    search = st.text_input("Hledat:").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower() or search == str(p['id'])]
    
    if filtered:
        sel = st.selectbox("Píseň:", [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered])
        pisen = filtered[[f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered].index(sel)]
        
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        # Rychlost - ošetření starých hodnot z PC (2000ms -> 30px)
        raw_r = pisen.get('rychlost', 30)
        start_r = 30 if not raw_r or int(raw_r) > 200 else int(raw_r)
        spd = st.slider("Rychlost scrollu", 1, 100, start_r)
        
        if 'scrolling' not in st.session_state: st.session_state.scrolling = False
        if st.button("START / STOP", type="primary" if st.session_state.scrolling else "secondary"):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()

if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # ÚPRAVA TEXTU PŘED ZOBRAZENÍM
    raw_text = pisen['text_akordy']
    
    # 1. Sjednotíme konce řádků (odstraníme Windows \r)
    clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. Nahradíme tabulátory mezerami (Tabs ničí zarovnání na webu)
    clean_text = clean_text.expandtabs(4)
    
    # 3. Transpozice
    final_text = logic.transponuj_text(clean_text, trans)

    # Zobrazení
    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # JavaScript pro scroll
    if st.session_state.scrolling:
        components.html(f"""
            <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                window.parent.scrollInterval = setInterval(function() {{ b.scrollTop += 1; }}, {spd});
            }}
            </script>""", height=0)
    else:
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
