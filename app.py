import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Online Zpěvník", layout="wide")

# 2. Vyladěné CSS: Vynucení barvy a velikosti pro VŠECHEN text
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    /* Skrytí tlačítka kopírování */
    button[title="Copy to clipboard"] {
        display: none !important;
    }

    /* Hlavní kontejner písně */
    .song-container {
        background-color: #1a1a1a !important;
        /* VYNUCENÍ BARVY A VELIKOSTI PRO VŠECHNO UVNITŘ */
        color: #e0e0e0 !important;
        font-size: 20px !important; 
        
        padding: 25px;
        border-radius: 8px;
        font-family: 'Roboto Mono', 'Consolas', 'Monaco', monospace !important;
        
        height: 78vh;
        overflow-y: auto;
        overflow-x: auto;
        
        white-space: pre !important; 
        word-wrap: normal !important;
        line-height: 1.3; 
        border: 1px solid #333;
    }

    /* Fix pro jakékoli vnořené prvky (odstraní černé/malé písmo) */
    .song-container, .song-container * {
        color: #e0e0e0 !important;
        background-color: transparent !important;
        font-family: 'Roboto Mono', 'Consolas', 'Monaco', monospace !important;
    }
    
    .stApp { background-color: #0e1117; }
    
    /* Úprava scrollovací lišty */
    .song-container::-webkit-scrollbar { width: 10px; height: 10px; }
    .song-container::-webkit-scrollbar-thumb { background: #444; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Načtení dat
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    try:
        r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
        return r.json()
    except:
        return []

data = nacti_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎸 Ovládání")
    search = st.text_input("🔍 Hledat (ID, název, autor):").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or 
                search in p['interpreti']['jmeno'].lower() or 
                search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Vyber píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        st.divider()
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        db_val = pisen.get('rychlost', 30)
        try:
            start_spd = 30 if int(db_val) > 200 else int(db_val)
        except:
            start_spd = 30
            
        spd = st.slider("Rychlost scrollu", 1, 100, start_spd)
        
        if 'scrolling' not in st.session_state: st.session_state.scrolling = False
        if st.button("🚀 START / STOP", use_container_width=True, type="primary" if st.session_state.scrolling else "secondary"):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()
    else:
        st.warning("Nic nenalezeno.")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # ČIŠTĚNÍ TEXTU
    clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n')
    clean_text = clean_text.replace('\xa0', ' ')
    clean_text = clean_text.expandtabs(4)
    
    # Transpozice
    final_text = logic.transponuj_text(clean_text, trans)

    # Zobrazení v DIVu
    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # JavaScript pro scroll
    if st.session_state.scrolling:
        components.html(f"""
            <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                if (window.parent.scrollInterval) {{ clearInterval(window.parent.scrollInterval); }}
                window.parent.scrollInterval = setInterval(function() {{ b.scrollTop += 1; }}, {spd});
            }}
            </script>""", height=0)
    else:
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
