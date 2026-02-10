import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky - musí být jako první
st.set_page_config(page_title="Zpěvník Online", layout="wide")

# 2. CSS pro vzhled a FIXNÍ ŠÍŘKU PÍSMA (aby akordy seděly)
st.markdown("""
    <style>
    /* Hlavní kontejner pro píseň */
    .song-container {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 30px;
        border-radius: 10px;
        /* Zásadní pro zarovnání akordů: */
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        height: 75vh;
        overflow-y: auto;
        overflow-x: auto;
        white-space: pre !important; /* Zachová mezery a konce řádků */
        font-size: 18px;
        line-height: 1.2; /* Menší řádkování pro lepší spojení akordů s textem */
        border: 2px solid #444;
        tab-size: 4;
    }
    
    /* Úprava bočního panelu */
    .stSidebar {
        background-color: #f8f9fa;
    }
    
    /* Styl pro nadpis písně */
    .song-title {
        color: #ff4b4b;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Načtení dat ze Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=600)
def nacti_data():
    headers = {
        "apikey": KEY, 
        "Authorization": f"Bearer {KEY}", 
        "Accept-Profile": "zpevnik"
    }
    # Načítáme ID, název, text, rychlost a jméno interpreta
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    if r.status_code != 200:
        st.error(f"Chyba databáze: {r.text}")
        return []
    return r.json()

data = nacti_data()

# --- SIDEBAR (Ovládání) ---
with st.sidebar:
    st.title("🎸 Ovládání")
    search_query = st.text_input("🔍 Hledat (ID, název, autor):", "").lower()
    
    # Filtrace
    filtrovana_data = [p for p in data if search_query in p['nazev'].lower() or 
                        search_query in p['interpreti']['jmeno'].lower() or 
                        search_query == str(p['id'])]
    
    if filtrovana_data:
        seznam = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtrovana_data]
        vyber = st.selectbox("Vyber píseň:", seznam)
        pisen = filtrovana_data[seznam.index(vyber)]
        
        st.divider()
        posun = st.number_input("Transpozice:", value=0, step=1)
        
        st.subheader("⏱️ Autoscroll")
        # Ošetření rychlosti (převod z ms na webový slider 1-100)
        try:
            val = int(pisen.get('rychlost', 30))
            db_rychlost = 30 if val > 200 else val
        except:
            db_rychlost = 30
            
        rychlost_scroll = st.slider("Rychlost (1=max, 100=min)", 1, 100, db_rychlost)
        
        if 'scroll_active' not in st.session_state:
            st.session_state.scroll_active = False

        def toggle_scroll():
            st.session_state.scroll_active = not st.session_state.scroll_active

        st.button("🚀 START / STOP", on_click=toggle_scroll, use_container_width=True, 
                  type="primary" if st.session_state.scroll_active else "secondary")
    else:
        st.warning("Píseň nenalezena")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    # Hlavička písně
    st.markdown(f"<h1 class='song-title'>{pisen['nazev']}</h1>", unsafe_allow_html=True)
    st.markdown(f"**{pisen['interpreti']['jmeno']}** (ID: {pisen['id']})")

    # Transpozice pomocí logic.py
    # DŮLEŽITÉ: Používáme .replace('\r\n', '\n'), aby nedocházelo k dvojitým řádkům
    čisty_text = pisen['text_akordy'].replace('\r\n', '\n')
    finalni_text = logic.transponuj_text(čisty_text, posun)

    # Zobrazení v kontejneru
    # HTML wrap zajistí, že se text nebude hroutit
    st.markdown(f'<div id="song-box" class="song-container">{finalni_text}</div>', unsafe_allow_html=True)

    # --- JAVASCRIPT PRO SCROLL ---
    if st.session_state.scroll_active:
        js_scroll = f"""
        <script>
            var scrollBox = window.parent.document.getElementById('song-box');
            if (scrollBox) {{
                if (window.scrollInterval) {{ clearInterval(window.scrollInterval); }}
                window.scrollInterval = setInterval(function() {{
                    scrollBox.scrollTop += 1;
                }}, {rychlost_scroll});
            }}
        </script>
        """
        components.html(js_scroll, height=0)
    else:
        # Zastavení scrollu
        components.html("<script>if (window.scrollInterval) { clearInterval(window.scrollInterval); }</script>", height=0)

else:
    st.info("Vyber píseň v levém panelu pro zobrazení.")
