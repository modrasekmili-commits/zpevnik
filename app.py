import streamlit as st
import requests
import logic

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS pro mobilní optimalizaci a obří text
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

    /* Skrytí Streamlit prvků */
    button[title="Copy to clipboard"] { display: none !important; }
    [data-testid="stSidebar"] { min-width: 350px; }

    /* Kontejner pro text písně */
    .song-box {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        padding: 20px !important;
        border-radius: 10px;
        font-family: 'Roboto Mono', monospace !important;
        font-size: 2.5vw !important; /* Základ pro PC */
        white-space: pre !important;
        display: block !important;
        line-height: 1.3 !important;
        overflow-x: auto;
        border: 1px solid #444;
    }

    /* Responzivní písmo pro mobil (šířka pod 800px) */
    @media (max-width: 800px) {
        .song-box {
            font-size: 4.5vw !important; /* Větší písmo na mobilu */
            padding: 10px !important;
        }
        .huge-title {
            font-size: 2.5rem !important;
        }
    }

    .huge-title {
        color: #ffffff !important;
        font-size: 4rem !important;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    
    .meta-info {
        color: #aaaaaa;
        font-size: 1.5rem;
        margin-bottom: 15px;
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
        r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
        return r.json()
    except: return []

data = nacti_data()

# Inicializace stavu vybrané písně
if 'selected_song_id' not in st.session_state:
    st.session_state.selected_song_id = None

# --- LOGIKA ZOBRAZENÍ ---

# A. DETAIL PÍSNĚ (Pokud je vybraná)
if st.session_state.selected_song_id:
    # Najdeme data vybrané písně
    pisen = next((p for p in data if p['id'] == st.session_state.selected_song_id), None)
    
    if pisen:
        # Tlačítko Zpět
        if st.button("⬅ ZPĚT NA SEZNAM", use_container_width=True):
            st.session_state.selected_song_id = None
            st.rerun()

        # Hlavička
        st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
        
        # Transpozice v malém řádku
        trans = st.number_input("Transpozice:", value=0, step=1, key="trans_detail")

        # Text
        raw_text = pisen['text_akordy']
        clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        st.markdown(f'<div class="song-box">{finalni_text}</div>', unsafe_allow_html=True)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

# B. SEZNAM PÍSNÍ (Výchozí stav)
else:
    st.title("🎸 Zpěvník")
    search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    filtered = [p for p in data if search in str(p['id']) or search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower()]
    
    if filtered:
        # Formát pro seznam
        for p in filtered:
            # Každá píseň jako jedno velké tlačítko
            btn_label = f"{p['nazev']} — {p['interpreti']['jmeno']}"
            if st.button(btn_label, key=f"p-{p['id']}", use_container_width=True):
                st.session_state.selected_song_id = p['id']
                st.rerun()
    else:
        st.warning("Nic nenalezeno.")
