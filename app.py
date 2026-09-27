import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky - "wide" rozložení je nutností pro desktopový vzhled
st.set_page_config(page_title="Zpěvník", layout="wide", initial_sidebar_state="collapsed")

# Odstranění parametrů z URL
if st.query_params:
    st.query_params.clear()

# 2. CSS pro DESKTOPOVÝ VZHLED (Tmavé téma dle Tkinter předlohy)
st.markdown("""
    <style>
    /* Reset zbytečných mezer Streamlitu */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    header, footer {visibility: hidden;}

    /* Globální barvy podle Tmavého tématu z desktopu */
    .stApp {
        background-color: #1e1e1e; /* Hlavní pozadí */
        color: #ffffff;
    }

    /* Stylizace levého sloupce (Interpreti) */
    div[data-testid="column"]:nth-of-type(1) {
        background-color: #252526; /* Tmavší panel */
        padding: 10px;
        border-right: 1px solid #333333;
        height: 90vh;
        overflow-y: auto;
    }

    /* Vzhled tlačítek seznamu písní (bez oblých rohů, zarovnáno doleva) */
    .stButton button {
        width: 100%;
        text-align: left;
        border-radius: 0px !important;
        padding: 4px 10px;
        background-color: transparent;
        border: none;
        border-bottom: 1px solid #333;
        color: #cccccc;
        font-family: Arial, sans-serif;
        font-size: 14px;
    }
    
    .stButton button:hover {
        background-color: #007acc !important; /* Akcentní modrá z desktopu */
        color: white !important;
        border-color: #007acc;
    }

    /* Vyhledávací pole (kompaktní jako v desktopu) */
    div[data-testid="stTextInput"] input {
        background-color: #3c3c3c;
        color: white;
        border: 1px solid #555;
        border-radius: 0px;
        padding: 5px 10px;
    }

    /* Horní lišta filtru (barevná tlačítka z obrázku) */
    .filter-btn-group .stButton button {
        width: auto !important;
        display: inline-block;
        border: 1px solid #444 !important;
        padding: 2px 8px !important;
        font-size: 12px;
        margin-right: -5px;
    }

    /* Detail písně - hlavička */
    .viewer-header {
        background-color: #333333;
        padding: 10px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
        border-bottom: 2px solid #555;
    }
    .viewer-title {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    /* Vlastní radio button (pro seznam interpretů) aby vypadal jako Listbox */
    div[role="radiogroup"] label {
        padding: 5px !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #007acc !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Načtení dat (stejné jako předtím)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=300)
def nacti_data():
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "zpevnik"}
    try:
        r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
        if r.status_code == 200: return r.json()
    except: pass
    return []

data = nacti_data()

# Inicializace stavových proměnných
if 'selected_song_id' not in st.session_state:
    st.session_state.selected_song_id = None
if 'vybrany_interpret' not in st.session_state:
    st.session_state.vybrany_interpret = "--- Vše ---"
if 'hledani' not in st.session_state:
    st.session_state.hledani = ""

# --- HLAVNÍ LOGIKA ZOBRAZENÍ ---

if st.session_state.selected_song_id:
    # --- ZOBRAZENÍ DETAILU PÍSNĚ (VIEWER) ---
    pisen = next((p for p in data if p['id'] == st.session_state.selected_song_id), None)
    
    if pisen:
        # Simulace horní lišty z viewer.py
        col_back, col_title, col_trans = st.columns([1, 8, 3])
        with col_back:
            if st.button("⬅ Zpět"):
                st.session_state.selected_song_id = None
                st.rerun()
        with col_title:
            st.markdown(f'<div class="viewer-title">{pisen["interpreti"]["jmeno"]} - {pisen["nazev"]}</div>', unsafe_allow_html=True)
        with col_trans:
            trans = st.number_input("Transpozice:", value=0, step=1, key="trans", label_visibility="collapsed")

        clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        # HTML kontejner pro text s Consolas fontem (jako v desktopu)
        html_content = f"""
        <div id="zoom-container" style="
            background-color: #1e1e1e; 
            color: #ffffff; 
            padding: 20px; 
            font-family: 'Consolas', 'Roboto Mono', monospace; 
            font-size: 18px; 
            white-space: pre; 
            line-height: 1.5;
            touch-action: pan-y; 
        ">{finalni_text}</div>
        <script>
            // JS pro zoomování (stejný jako váš původní)
            const el = document.getElementById('zoom-container');
            let fontSize = 18;
            let initialDist = -1;
            el.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 2) {{
                    initialDist = Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY);
                }}
            }}, {{passive: false}});
            el.addEventListener('touchmove', (e) => {{
                if (e.touches.length === 2 && initialDist > 0) {{
                    e.preventDefault(); 
                    const currentDist = Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY);
                    const diff = currentDist - initialDist;
                    if (Math.abs(diff) > 5) {{
                        fontSize += diff > 0 ? 0.8 : -0.8;
                        fontSize = Math.min(Math.max(12, fontSize), 100); 
                        el.style.fontSize = fontSize + 'px';
                        initialDist = currentDist;
                    }}
                }}
            }}, {{passive: false}});
            el.addEventListener('touchend', (e) => {{
                if (e.touches.length < 2) {{ initialDist = -1; }}
            }});
        </script>
        """
        
        vyska = (len(finalni_text.split('\n')) * 30) + 100
        components.html(html_content, height=vyska, scrolling=False)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

else:
    # --- ZOBRAZENÍ SEZNAMU (ZPEVNIK.PYW) ---
    
    # Rozdělení na levý panel (interpreti) a pravý panel (seznam) - napodobuje Tkinter Frames
    col_left, col_right = st.columns([1, 4])
    
    with col_left:
        # Simulace levého Listboxu interpretů
        interpreti = sorted(list(set(p['interpreti']['jmeno'] for p in data if p['interpreti'])))
        interpreti.insert(0, "--- Vše ---")
        
        st.radio(
            "Interpreti", 
            interpreti, 
            key="vybrany_interpret",
            label_visibility="collapsed"
        )
        
    with col_right:
        # Horní vyhledávací lišta (napodobuje layout z obrázku)
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            hledani = st.text_input("Hledání (interpret, název, číslo)...", key="hledani_input", label_visibility="collapsed", placeholder="Hledání (interpret, název, číslo)...").lower()
        with s_col2:
            fulltext = st.text_input("Fulltext", key="fulltext_input", label_visibility="collapsed", placeholder="Fulltext (hledat v textech)...").lower()

        # Lišta tlačítek (Filtry) - napodobení barevných štítků z obrázku
        st.markdown("""
            <div class="filter-btn-group" style="margin-bottom: 10px;">
                <button style="background: white; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">VŠECHNY</button>
                <button style="background: #e8d0e8; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">🕒 HISTORIE</button>
                <button style="background: #cce5ff; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">📊 TOP PŘEHRANÉ</button>
                <button style="background: #ffcc99; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">? (Nehotové)</button>
                <button style="background: #c3e6cb; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">! (Hotové)</button>
                <button style="background: #f5c6cb; color: black; border: 1px solid #ccc; padding: 2px 5px; font-size: 11px;">♥ (Oblíbené)</button>
            </div>
        """, unsafe_allow_html=True)

        # Filtrování dat
        filtered = data
        
        # Filtr interpret
        if st.session_state.vybrany_interpret != "--- Vše ---":
            filtered = [p for p in filtered if p['interpreti']['jmeno'] == st.session_state.vybrany_interpret]
            
        # Filtr vyhledávání
        if hledani:
            filtered = [p for p in filtered if (hledani in str(p['id']) or 
                                                hledani in p['nazev'].lower() or 
                                                hledani in p['interpreti']['jmeno'].lower())]
        
        # Zobrazení výsledků (simulace Listboxu vpravo)
        if filtered:
            # Abychom simulovali čistý seznam, použijeme kontejner
            with st.container():
                for p in filtered:
                    # Prefixy jako v desktopu (? pro nehotové, ! pro hotové - zde natvrdo jako ukázka)
                    prefix = "? " 
                    titulek = f"{prefix}{p['nazev']} - {p['interpreti']['jmeno']}"
                    
                    if st.button(titulek, key=f"p-{p['id']}"):
                        st.session_state.selected_song_id = p['id']
                        st.rerun()
        else:
            st.markdown("<p style='color: #777;'>Nic nenalezeno.</p>", unsafe_allow_html=True)