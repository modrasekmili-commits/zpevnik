import streamlit as st
import requests
import logic

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# 2. CSS pro čistý vzhled, obří název a správné zobrazení textu
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

    /* Skrytí Streamlit prvků */
    button[title="Copy to clipboard"] { display: none !important; }
    
    /* Kontejner pro text písně */
    .song-box {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        padding: 30px !important;
        border-radius: 10px;
        font-family: 'Roboto Mono', monospace !important;
        
        /* Velikost písma - pokud je to pořád malé, změň 2.2vw na vyšší */
        font-size: 2.2vw !important; 
        
        /* Zásadní pro zachování konců řádků a mezer */
        white-space: pre !important;
        display: block !important;
        line-height: 1.35 !important;
        
        overflow-x: auto;
        border: 1px solid #444;
        margin-top: 20px;
    }

    /* Vynucení bílé barvy pro vše uvnitř boxu (proti bílým pruhům) */
    .song-box * {
        color: #ffffff !important;
        background-color: transparent !important;
    }

    /* Obří název */
    .huge-title {
        color: #ffffff !important;
        font-size: 4.5rem !important;
        font-weight: 800;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    
    .meta-info {
        color: #aaaaaa;
        font-size: 1.8rem;
        margin-bottom: 10px;
    }

    .stApp { background-color: #0e1117; }
    
    /* Sidebar šířka */
    [data-testid="stSidebar"] { min-width: 400px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Načtení dat
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Seznam písní")
    search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    filtered = [p for p in data if search in str(p['id']) or search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower()]
    
    if filtered:
        seznam_zobrazeni = [f"{p['nazev']} - {p['interpreti']['jmeno']}" for p in filtered]
        vyber_label = st.radio("Výběr:", seznam_zobrazeni, label_visibility="collapsed")
        pisen = filtered[seznam_zobrazeni.index(vyber_label)]
        
        st.divider()
        trans = st.number_input("Transpozice:", value=0, step=1)
    else:
        st.warning("Nic nenalezeno.")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    # Obří název s ID a Interpret
    st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
    
    # Příprava textu
    raw_text = pisen['text_akordy']
    clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
    finalni_text = logic.transponuj_text(clean_text, trans)

    # Zobrazení textu v DIVu s agresivním zachováním formátu
    st.markdown(f'<div class="song-box">{finalni_text}</div>', unsafe_allow_html=True)
else:
    st.info("Vyberte píseň vlevo.")
