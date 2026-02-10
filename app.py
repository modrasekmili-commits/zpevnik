import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník Online", layout="wide")

# 2. CSS pro vzhled a fixní výšku textu (aby bylo kam rolovat)
st.markdown("""
    <style>
    .song-container {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Consolas', 'Monaco', monospace;
        height: 70vh;
        overflow-y: auto;
        white-space: pre;
        font-size: 18px;
        line-height: 1.4;
        border: 1px solid #444;
    }
    /* Skrytí scrollbaru pro čistší vzhled */
    .song-container::-webkit-scrollbar { width: 8px; }
    .song-container::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Načtení klíčů a dat
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=600)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    # Načítáme vše potřebné včetně rychlosti
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json()

try:
    data = nacti_data()
except Exception as e:
    st.error(f"Chyba při připojení k Supabase: {e}")
    data = []

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

# Ošetření rychlosti z databáze (pokud je tam 2000, převedeme to na rozumných 30)
raw_rychlost = pisen.get('rychlost')
try:
    db_rychlost = int(raw_rychlost)
    if db_rychlost > 200: # Pokud je to číslo z PC aplikace (např. 2000)
        db_rychlost = 30  # Nastavíme rozumný střed pro web
except:
    db_rychlost = 30

# Slider nyní bude mít rozsah 1 až 100
rychlost = st.slider("Rychlost (1=blesk, 100=hlemýžď)", 1, 100, db_rychlost)
        
        if 'scroll_active' not in st.session_state:
            st.session_state.scroll_active = False

        def toggle_scroll():
            st.session_state.scroll_active = not st.session_state.scroll_active

        st.button("START / STOP", on_click=toggle_scroll, use_container_width=True, 
                  type="primary" if st.session_state.scroll_active else "secondary")
    else:
        st.warning("Píseň nenalezena")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.title(f"{pisen['nazev']}")
    st.caption(f"Interpret: {pisen['interpreti']['jmeno']} | ID: {pisen['id']}")

    # Transpozice pomocí tvého logic.py
    finalni_text = logic.transponuj_text(pisen['text_akordy'], posun)

    # Zobrazení textu v kontejneru s ID pro JavaScript
    st.markdown(f'<div id="song-box" class="song-container">{finalni_text}</div>', unsafe_allow_html=True)

    # --- JAVASCRIPT PRO POSOUVÁNÍ KONKRÉTNÍHO DIVU ---
    if st.session_state.scroll_active:
        js_scroll = f"""
        <script>
            // Najdeme prvek v nadřazeném okně (Streamlit)
            const scrollBox = window.parent.document.getElementById('song-box');
            if (scrollBox) {{
                if (window.scrollInterval) {{ clearInterval(window.scrollInterval); }}
                window.scrollInterval = setInterval(function() {{
                    scrollBox.scrollTop += 1;
                }}, {rychlost});
            }}
        </script>
        """
        components.html(js_scroll, height=0)
    else:
        components.html("<script>if (window.scrollInterval) { clearInterval(window.scrollInterval); }</script>", height=0)

else:
    st.info("Vyber píseň v levém panelu.")
