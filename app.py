import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# 2. CSS pro PC a mobil
st.markdown("""
    <style>
    /* Omezení šířky na PC pro lepší vzhled */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
    
    /* Skrytí Streamlit prvků */
    #MainMenu, footer, header {visibility: hidden;}
    
    .stButton button {
        text-align: left;
        padding: 10px;
        font-size: 1.1rem;
    }

    .huge-title {
        color: #ffffff !important;
        font-size: clamp(2rem, 5vw, 4rem);
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 5px;
    }
    
    .meta-info {
        color: #aaaaaa;
        font-size: 1.2rem;
        margin-bottom: 20px;
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

if 'selected_song_id' not in st.session_state:
    st.session_state.selected_song_id = None

# --- LOGIKA ---

if st.session_state.selected_song_id:
    pisen = next((p for p in data if p['id'] == st.session_state.selected_song_id), None)
    
    if pisen:
        if st.button("⬅ ZPĚT"):
            st.session_state.selected_song_id = None
            st.rerun()

        st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
        
        trans = st.number_input("Transpozice:", value=0, step=1, key="trans")

        # Příprava textu
        raw_text = pisen['text_akordy']
        clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        # Totální izolace textu přes Iframe (řeší bílé řádky 100%)
        html_content = f"""
        <div style="
            background-color: #1a1a1a; 
            color: #ffffff; 
            padding: 20px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 22px; 
            white-space: pre; 
            line-height: 1.35;
            border-radius: 10px;
            border: 1px solid #444;
        ">{finalni_text}</div>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
        """
        # Automatický výpočet výšky podle počtu řádků
        vyska = len(finalni_text.split('\n')) * 32 
        components.html(html_content, height=max(vyska, 500), scrolling=False)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

else:
    st.title("🎸 Zpěvník")
    
    # Omezení šířky vyhledávání na PC
    col1, _ = st.columns([2, 1])
    with col1:
        search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    filtered = [p for p in data if search in str(p['id']) or search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower()]
    
    if filtered:
        # Seznam tlačítek v omezené šířce
        col_list, _ = st.columns([2, 1])
        with col_list:
            for p in filtered:
                if st.button(f"{p['nazev']} — {p['interpreti']['jmeno']}", key=f"p-{p['id']}", use_container_width=True):
                    st.session_state.selected_song_id = p['id']
                    st.rerun()
