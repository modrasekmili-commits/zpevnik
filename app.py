import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Online Zpěvník", layout="wide")

# 2. CSS: Skrytí clipboardu a základní styly
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    button[title="Copy to clipboard"] { display: none !important; }

    .song-container {
        background-color: #1a1a1a !important;
        padding: 30px;
        border-radius: 8px;
        height: 78vh;
        overflow-y: auto;
        overflow-x: auto;
        white-space: pre !important; 
        word-wrap: normal !important;
        line-height: 1.35; 
        border: 1px solid #333;
    }

    .stApp { background-color: #0e1117; }
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
    except: return []

data = nacti_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎸 Ovládání")
    search = st.text_input("🔍 Hledat:").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower() or search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Vyber píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        st.divider()
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        db_val = pisen.get('rychlost', 30)
        try: start_spd = 30 if int(db_val) > 200 else int(db_val)
        except: start_spd = 30
            
        spd = st.slider("Rychlost scrollu", 1, 100, start_spd)
        
        if 'scrolling' not in st.session_state: st.session_state.scrolling = False
        if st.button("🚀 START / STOP", use_container_width=True, type="primary" if st.session_state.scrolling else "secondary"):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # Čištění textu
    clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n')
    clean_text = clean_text.replace('\xa0', ' ')
    clean_text = clean_text.expandtabs(4)
    
    # Transpozice
    final_text = logic.transponuj_text(clean_text, trans)

    # VYNUCENÍ VELIKOSTI A BARVY PŘÍMO V HTML (Inline style)
    # Tady měníme velikost písma na 24px a barvu na světle šedou
    html_song = f"""
    <div id="song-box" class="song-container" 
         style="color: #e0e0e0 !important; 
                font-family: 'Roboto Mono', monospace !important; 
                font-size: 24px !important;">{final_text}</div>
    """
    st.markdown(html_song, unsafe_allow_html=True)

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
