import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

st.set_page_config(page_title="Zpěvník PRO", layout="wide")

# Inicializace stavů, pokud neexistují
if 'scrolling' not in st.session_state: st.session_state.scrolling = False
if 'font_size' not in st.session_state: st.session_state.font_size = 24
if 'scroll_mod' not in st.session_state: st.session_state.scroll_mod = "normal" # normal, pause, fast

# 1. CSS s dynamickou velikostí písma
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    button[title="Copy to clipboard"] {{ display: none !important; }}

    .song-container {{
        background-color: #1a1a1a !important;
        padding: 25px !important;
        border-radius: 10px;
        height: 75vh;
        overflow-y: auto;
        white-space: pre !important; 
        word-wrap: normal !important;
        line-height: 1.4 !important; 
        border: 2px solid #444;
    }}

    #song-box, #song-box * {{
        color: #ffffff !important;
        font-size: {st.session_state.font_size}px !important;
        font-family: 'Roboto Mono', monospace !important;
        background-color: transparent !important;
    }}
    
    .stApp {{ background-color: #0e1117; }}
    </style>
    """, unsafe_allow_html=True)

# 2. Načtení dat
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎸 Ovládání")
    search = st.text_input("🔍 Hledat:").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower() or search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        st.divider()
        
        # OVLÁDÁNÍ PÍSMA (pro dotykovky)
        st.subheader("🔎 Velikost písma")
        col_f1, col_f2 = st.columns(2)
        if col_f1.button("➖ Menší", use_container_width=True):
            st.session_state.font_size = max(12, st.session_state.font_size - 2)
            st.rerun()
        if col_f2.button("➕ Větší", use_container_width=True):
            st.session_state.font_size = min(60, st.session_state.font_size + 2)
            st.rerun()

        st.divider()
        
        # OVLÁDÁNÍ SCROLLU
        st.subheader("⏱️ Posun")
        db_val = pisen.get('rychlost', 30)
        try: start_spd = 30 if int(db_val) > 200 else int(db_val)
        except: start_spd = 30
        spd = st.slider("Základní rychlost", 1, 100, start_spd)
        
        if st.button("🚀 START / STOP", use_container_width=True, type="primary" if st.session_state.scrolling else "secondary"):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()

# --- HLAVNÍ PLOCHA - AKČNÍ TLAČÍTKA ---
if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # Rychlá tlačítka pro hraní
    c1, c2, c3 = st.columns(3)
    if c1.button("⏸️ PAUZA (8 řádků)", use_container_width=True):
        st.session_state.scroll_mod = "pause"
    if c2.button("⏩ RYCHLE (2x)", use_container_width=True):
        st.session_state.scroll_mod = "fast"
    if c3.button("🔄 OBNOVIT", use_container_width=True):
        st.session_state.scroll_mod = "normal"

    # Příprava textu
    clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
    final_text = logic.transponuj_text(clean_text, st.sidebar.number_input("Transpozice:", value=0, step=1))

    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # VÝPOČET RYCHLOSTI PRO JAVASCRIPT
    # 8 řádků při line-height 1.4 a písmu Xpx je cca 8 * X * 1.4 pixelů.
    # Pro jednoduchost budeme pauzovat/zrychlovat na časový interval.
    
    current_spd = spd
    js_mod_logic = ""
    
    if st.session_state.scrolling:
        if st.session_state.scroll_mod == "pause":
            # JavaScript zastaví scroll na cca 10 sekund (odpovídá zhruba 8 řádkům pomalého čtení)
            js_mod_logic = "var mod_spd = 999999; setTimeout(() => { window.parent.location.reload(); }, 10000);"
        elif st.session_state.scroll_mod == "fast":
            # Dvojnásobná rychlost (poloviční interval)
            current_spd = max(1, spd // 2)
            js_mod_logic = f"var mod_spd = {current_spd}; setTimeout(() => {{ window.parent.location.reload(); }}, 5000);"
        else:
            js_mod_logic = f"var mod_spd = {spd};"

        components.html(f"""
            <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                {js_mod_logic}
                if (window.parent.scrollInterval) {{ clearInterval(window.parent.scrollInterval); }}
                window.parent.scrollInterval = setInterval(function() {{ b.scrollTop += 1; }}, mod_spd);
            }}
            </script>""", height=0)
    else:
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
