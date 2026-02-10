import streamlit as st
import requests
import logic

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# 2. CSS pro čistý vzhled bez bílých řádků
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

    /* Skrytí Streamlit prvků */
    button[title="Copy to clipboard"] { display: none !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Styl pro hlavní text písně - čistý blok bez pozadí Streamlitu */
    .song-text-area {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1.8vw !important; /* Dynamická velikost */
        line-height: 1.3;
        white-space: pre;
        overflow-x: auto;
        border: 1px solid #444;
    }

    /* Styl pro obří název písně */
    .huge-title {
        color: #ffffff !important;
        font-size: 4rem !important; /* Obří velikost */
        font-weight: 800;
        margin-bottom: 5px;
        line-height: 1.1;
    }
    
    .meta-info {
        color: #aaaaaa;
        font-size: 1.5rem;
        margin-bottom: 20px;
    }

    .stApp { background-color: #0e1117; }
    
    /* Sidebar úpravy */
    [data-testid="stSidebar"] { min-width: 400px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Načtení dat ze Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = {
        "apikey": KEY, 
        "Authorization": f"Bearer {KEY}", 
        "Accept-Profile": "zpevnik"
    }
    # Načítáme vše a řadíme abecedně
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

# --- SIDEBAR (Vyhledávání a Seznam) ---
with st.sidebar:
    st.title("Seznam písní")
    search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    # Bod 4: Vyhledávání podle ID, názvu i interpreta
    filtered = []
    for p in data:
        id_str = str(p['id'])
        nazev = p['nazev'].lower()
        interpret = p['interpreti']['jmeno'].lower()
        
        if search in id_str or search in nazev or search in interpret:
            filtered.append(p)
    
    if filtered:
        # Bod 2: Výpis v seznamu bez ID (jen Název - Interpret)
        seznam_zobrazeni = [f"{p['nazev']} - {p['interpreti']['jmeno']}" for p in filtered]
        
        vyber_label = st.radio(
            "Vyberte píseň:",
            seznam_zobrazeni,
            label_visibility="collapsed"
        )
        
        index = seznam_zobrazeni.index(vyber_label)
        pisen = filtered[index]
    else:
        st.warning("Nic nenalezeno.")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    # Bod 1 a 2: Obří název s číslem a interpretem
    st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
    
    # Transpozice v sidebaru
    trans = st.sidebar.number_input("Transpozice:", value=0, step=1)
    
    # Bod 3: Čištění textu (náhrada všech problematických znaků)
    # Odstraníme nezlomitelné mezery a sjednotíme konce řádků
    text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
    finalni_text = logic.transponuj_text(text, trans)

    # Zobrazení textu jako čisté HTML bez Streamlit obalů (řeší bílé řádky)
    st.markdown(f'<pre class="song-text-area">{finalni_text}</pre>', unsafe_allow_html=True)
else:
    st.info("Vyberte píseň v levém seznamu.")
