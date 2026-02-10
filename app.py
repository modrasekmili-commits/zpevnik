import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník Online", layout="wide")

# 2. Vyladěné CSS: Skrytí tlačítka kopírování a fixace písma
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    /* SKRYTÍ TLAČÍTKA KOPÍROVAT (Clipboard) */
    button[title="Copy to clipboard"] {
        display: none !important;
    }

    .song-container {
        background-color: #1a1a1a;
        color: #e0e0e0;
        padding: 25px;
        border-radius: 8px;
        
        /* Absolutní vynucení neproporcionálního písma */
        font-family: 'Roboto Mono', 'Consolas', 'Monaco', monospace !important;
        
        height: 78vh;
        overflow-y: auto;
        overflow-x: auto;
        
        /* Zásadní pro bílé znaky a zarovnání */
        white-space: pre !important; 
        word-wrap: normal !important;
        
        font-size: 18px;
        line-height: 1.25; 
        border: 1px solid #333;
    }
    
    /* Úprava scrollovací lišty pro song-box */
    .song-container::-webkit-scrollbar { width: 10px; height: 10px; }
    .song-container::-webkit-scrollbar-thumb { background: #444; border-radius: 5px; }

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
    except:
        return []

data = nacti_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎸 Nastavení")
    search = st.text_input("🔍 Hledat (ID, název, autor):").lower()
    
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower() or search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Vyber píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        # Rychlost: pokud je v DB hodnota z Windows (např. 2000), nastavíme 30
        db_val = pisen.get('rychlost', 30)
        try:
            start_spd = 30 if int(db_val) > 200 else int(db_val)
        except:
            start_spd = 30
            
        spd = st.slider("Rychlost scrollu", 1, 100, start_spd)
        
        if 'scrolling' not in st.session_state: st.session_state.scrolling = False
        if st.button("🚀 START / STOP", type="primary" if st.session_state.scrolling else "secondary", use_container_width=True):
            st.session_state.scrolling = not st.session_state.scrolling
            st.rerun()
    else:
        st.warning("Nic nenalezeno.")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.title(pisen['nazev'])
    
    # 1. Vyčištění textu (náhrada Windows konců řádků a tabulátorů)
    clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n')
    clean_text = clean_text.expandtabs(4)
    
    # 2. Transpozice pomocí tvého logic.py
    final_text = logic.transponuj_text(clean_text, trans)

    # 3. Zobrazení v DIVu (místo st.code, aby se dalo CSS lépe ovládat)
    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # 4. JavaScript pro plynulý scroll
    if st.session_state.scrolling:
        components.html(f"""
            <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                if (window.parent.scrollInterval) {{ clearInterval(window.parent.scrollInterval); }}
                window.parent.scrollInterval = setInterval(function() {{ 
                    b.scrollTop += 1; 
                }}, {spd});
            }}
            </script>""", height=0)
    else:
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
else:
    st.info("Vyber píseň vlevo.")
