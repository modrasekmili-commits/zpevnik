import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

st.set_page_config(page_title="Zpěvník Responzivní", layout="wide")

# Inicializace stavů
if 'scrolling' not in st.session_state: st.session_state.scrolling = False
if 'font_scale' not in st.session_state: st.session_state.font_scale = 2.5 # Základní měřítko v 'vw'
if 'scroll_mod' not in st.session_state: st.session_state.scroll_mod = "normal"

# 1. CSS s DYNAMICKOU šířkou písma (vw = % šířky okna)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    button[title="Copy to clipboard"] {{ display: none !important; }}

    .song-container {{
        background-color: #1a1a1a !important;
        padding: 15px !important;
        border-radius: 10px;
        height: 80vh;
        overflow-y: auto;
        overflow-x: auto;
        white-space: pre !important; 
        word-wrap: normal !important;
        line-height: 1.3 !important; 
        border: 2px solid #444;
    }}

    #song-box, #song-box * {{
        color: #ffffff !important;
        /* TADY JE TO KOUZLO: Písmo tvoří X % šířky displeje */
        font-size: {st.session_state.font_scale}vw !important;
        font-family: 'Roboto Mono', monospace !important;
        background-color: transparent !important;
    }}
    
    /* Na mobilu (šířka pod 600px) písmo trochu zvětšíme, aby bylo čitelné */
    @media (max-width: 600px) {{
        #song-box, #song-box * {{
            font-size: {st.session_state.font_scale * 1.5}vw !important;
        }}
    }}

    .stApp {{ background-color: #0e1117; }}
    </style>
    """, unsafe_allow_html=True)

# 2. Načtení dat
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = { "apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik" }
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

with st.sidebar:
    st.title("🎸 Ovládání")
    search = st.text_input("🔍 Hledat:").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower() or search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        st.divider()
        # Slider pro doladění velikosti, pokud by se text nevešel
        st.session_state.font_scale = st.slider("Velikost písma (% šířky)", 1.0, 5.0, st.session_state.font_scale, 0.1)
        
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        st.divider()
        db_val = pisen.get('rychlost', 30)
        try: start_spd = 30 if int(db_val) > 200 else int(db_val)
        except: start_spd = 30
        spd = st.slider("Základní rychlost", 1, 100, start_spd)
        
        if st.button("🚀 START / STOP", use_container_width=True, type="primary" if st.session_state.scrolling else "secondary"):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()

if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # Tlačítka pod názvem
    c1, c2, c3 = st.columns(3)
    if c1.button("⏸️ PAUZA (8ř)", use_container_width=True): st.session_state.scroll_mod = "pause"
    if c2.button("⏩ RYCHLE (2x)", use_container_width=True): st.session_state.scroll_mod = "fast"
    if c3.button("🔄 RESET", use_container_width=True): st.session_state.scroll_mod = "normal"

    clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
    final_text = logic.transponuj_text(clean_text, trans)

    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # JavaScript logic
    if st.session_state.scrolling:
        current_spd = spd
        if st.session_state.scroll_mod == "pause":
            js_logic = "var mod_spd = 999999; setTimeout(() => { window.parent.location.reload(); }, 8000);"
        elif st.session_state.scroll_mod == "fast":
            current_spd = max(1, spd // 2)
            js_logic = f"var mod_spd = {current_spd}; setTimeout(() => {{ window.parent.location.reload(); }}, 4000);"
        else:
            js_logic = f"var mod_spd = {spd};"

        components.html(f"""
            <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                {js_logic}
                if (window.parent.scrollInterval) {{ clearInterval(window.parent.scrollInterval); }}
                window.parent.scrollInterval = setInterval(function() {{ b.scrollTop += 1; }}, mod_spd);
            }}
            </script>""", height=0)
    else:
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
