import streamlit as st
import requests
import logic

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# 2. CSS pro vzhled
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    /* Skrytí tlačítka kopírovat */
    button[title="Copy to clipboard"] { display: none !important; }

    /* Kontejner písně */
    .song-container {
        background-color: #1a1a1a !important;
        padding: 20px !important;
        border-radius: 10px;
        border: 1px solid #444;
        
        /* Maximální šířka písma, aby se text vešel a byl velký */
        /* 1.8vw je kompromis pro dlouhé řádky, aby byly čitelné a velké */
        font-size: 1.8vw !important; 
        font-family: 'Roboto Mono', monospace !important;
        color: #ffffff !important;
        
        white-space: pre !important;
        line-height: 1.3 !important;
        overflow-x: auto;
    }

    /* Vynucení bílé barvy pro název */
    .white-title {
        color: #ffffff !important;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0px;
    }

    .stApp { background-color: #0e1117; }
    
    /* Úprava bočního panelu pro list */
    [data-testid="stSidebar"] {
        min-width: 350px;
    }
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
    # Načítáme a řadíme podle názvu přímo v SQL dotazu
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json() if r.status_code == 200 else []

data = nacti_data()

# --- SIDEBAR (Seznam písniček jako LIST) ---
with st.sidebar:
    st.header("Seznam písní")
    search = st.text_input("🔍 Hledat:", "").lower()
    
    # Filtrace
    filtered = [p for p in data if search in p['nazev'].lower() or search in p['interpreti']['jmeno'].lower()]
    
    if filtered:
        # Formátování pro list: Název - Interpret
        seznam_zobrazeni = [f"{p['nazev']} - {p['interpreti']['jmeno']}" for p in filtered]
        
        # Zobrazení jako LIST (st.radio funguje jako vertikální seznam)
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
    # Bod 3: Bílý název a zobrazení čísla (ID)
    st.markdown(f'<p class="white-title">{pisen["nazev"]}</p>', unsafe_allow_html=True)
    st.caption(f"Interpret: {pisen['interpreti']['jmeno']} | Číslo písně: {pisen['id']}")
    
    # Transpozice (ponechána pro funkčnost akordů)
    trans = st.sidebar.number_input("Transpozice:", value=0, step=1)
    
    # Čištění textu
    text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
    finalni_text = logic.transponuj_text(text, trans)

    # Bod 4: Zobrazení v kontejneru s maximálním písmem
    st.markdown(f'<div class="song-container">{finalni_text}</div>', unsafe_allow_html=True)
else:
    st.info("Vyberte píseň v levém seznamu.")
