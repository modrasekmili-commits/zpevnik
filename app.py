import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

st.set_page_config(page_title="Zpěvník Online", layout="wide")

# --- JAVASCRIPT PRO POSOUVÁNÍ ---
def autoscroll_js(rychlost, running):
    if not running:
        return "<script>clearInterval(window.scrollInterval);</script>"
    
    # Rychlost v milisekundách (čím nižší číslo, tím rychleji to jede)
    # Převádíme tvou 'rychlost' na rozumný interval
    js_code = f"""
    <script>
    if (window.scrollInterval) {{ clearInterval(window.scrollInterval); }}
    window.scrollInterval = setInterval(function() {{
        window.scrollBy(0, 1);
    }}, {rychlost});
    </script>
    """
    return js_code

# --- NAČTENÍ DAT ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=600)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json()

data = nacti_data()

# --- SIDEBAR (Ovládání) ---
with st.sidebar:
    st.header("Nastavení")
    search_query = st.text_input("🔍 Hledat:", "").lower()
    
    # Filtrace
    filtrovana_data = [p for p in data if search_query in p['nazev'].lower() or search_query in p['interpreti']['jmeno'].lower() or search_query == str(p['id'])]
    
    if filtrovana_data:
        seznam = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtrovana_data]
        vyber = st.selectbox("Vyber píseň:", seznam)
        pisen = filtrovana_data[seznam.index(vyber)]
        
        st.divider()
        posun = st.number_input("Transpozice:", value=0, step=1)
        
        # --- AUTOSCROLL OVLÁDÁNÍ ---
        st.subheader("Autoscroll")
        # Načteme výchozí rychlost z DB, nebo dáme 50 (čím menší, tím rychlejší)
        rychlost_scrolling = st.slider("Rychlost (menší = rychlejší)", 1, 100, 30)
        
        if 'scroll_running' not in st.session_state:
            st.session_state.scroll_running = False

        def toggle_scroll():
            st.session_state.scroll_running = not st.session_state.scroll_running

        st.button("🚀 START / STOP", on_click=toggle_scroll, use_container_width=True)

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.subheader(f"{pisen['nazev']} — {pisen['interpreti']['jmeno']}")
    
    # Výpočet textu
    finalni_text = logic.transponuj_text(pisen['text_akordy'], posun)
    
    # Zobrazení textu
    st.code(finalni_text, language="text")
    
    # Vložení JavaScriptu pro scroll
    components.html(autoscroll_js(rychlost_scrolling, st.session_state.scroll_running), height=0)

# --- KLÁVESOVÉ ZKRATKY (INFO) ---
# Webové prohlížeče bohužel neumožňují snadno zachytit šipky pro ovládání scrollu 
# bez přebití výchozího chování prohlížeče, ale pomocí slideru vlevo to můžeš ladit v reálném čase.
