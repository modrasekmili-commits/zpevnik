import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# 2. CSS pro vzhled, barvy a šířku
st.markdown("""
    <style>
    /* Omezení šířky na PC a vycentrování */
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    
    /* Skrytí Streamlit prvků */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Větší a bílý popis vyhledávání */
    div[data-testid="stTextInput"] label {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* Styl tlačítek v seznamu */
    .stButton button {
        text-align: left;
        padding: 12px;
        font-size: 1.2rem;
        background-color: #262730;
        border: 1px solid #444;
        color: white;
    }

    .huge-title {
        color: #ffffff !important;
        font-size: clamp(2.5rem, 6vw, 4.5rem);
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 5px;
    }
    
    .meta-info {
        color: #aaaaaa;
        font-size: 1.5rem;
        margin-bottom: 25px;
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
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

data = nacti_data()

if 'selected_song_id' not in st.session_state:
    st.session_state.selected_song_id = None

# --- LOGIKA ---

if st.session_state.selected_song_id:
    # --- DETAIL PÍSNĚ ---
    pisen = next((p for p in data if p['id'] == st.session_state.selected_song_id), None)
    
    if pisen:
        if st.button("⬅ ZPĚT"):
            st.session_state.selected_song_id = None
            st.rerun()

        st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
        
        trans = st.number_input("Transpozice:", value=0, step=1, key="trans")

        raw_text = pisen['text_akordy']
        clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        # Izolované zobrazení textu
        html_content = f"""
        <div style="
            background-color: #1a1a1a; 
            color: #ffffff; 
            padding: 25px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 24px; 
            white-space: pre; 
            line-height: 1.4;
            border-radius: 12px;
            border: 1px solid #444;
        ">{finalni_text}</div>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
        """
        # Výpočet výšky (34px na řádek + rezerva)
        vyska = (len(finalni_text.split('\n')) * 34) + 100
        components.html(html_content, height=vyska, scrolling=False)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

else:
    # --- SEZNAM PÍSNÍ ---
    st.markdown("<h1 style='color: white; margin-bottom: 0;'>🎸 Zpěvník</h1>", unsafe_allow_html=True)
    
    search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    # Filtrace dat
    filtered = [p for p in data if (search in str(p['id']) or 
                                    search in p['nazev'].lower() or 
                                    search in p['interpreti']['jmeno'].lower())]
    
    if filtered:
        st.write("") 
        for p in filtered:
            btn_label = f"{p['nazev']} — {p['interpreti']['jmeno']}"
            if st.button(btn_label, key=f"p-{p['id']}", use_container_width=True):
                st.session_state.selected_song_id = p['id']
                st.rerun()
    else:
        st.warning("Nic nenalezeno.")
