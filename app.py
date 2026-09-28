import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky - "wide" rozložení je nutností pro desktopový vzhled
st.set_page_config(page_title="Zpěvník", layout="wide", initial_sidebar_state="collapsed")

# Odstranění parametrů z adresy hned při startu
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

# 3. Načtení dat
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

# --- HLAVNÍ LOGIKA ---

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
            st.markdown(f'<div class="viewer-title">{pisen["id"]}. {pisen["interpreti"]["jmeno"]} - {pisen["nazev"]}</div>', unsafe_allow_html=True)
        with col_trans:
            trans = st.number_input("Transpozice:", value=0, step=1, key="trans", label_visibility="collapsed")

        clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        # HTML kontejner pro text s Consolas fontem a novým plovoucím panelem
        html_content = f"""
        <style>
            body, html {{
                margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: #1e1e1e;
            }}
            #zoom-container {{
                height: 100vh;
                overflow-y: auto;
                padding: 20px;
                padding-bottom: 120px; /* Místo pro plovoucí panel dole */
                background-color: #1e1e1e; 
                color: #ffffff; 
                font-family: 'Consolas', 'Roboto Mono', monospace; 
                font-size: 18px; 
                white-space: pre; 
                line-height: 1.5;
                touch-action: pan-y; 
                user-select: none;
                -webkit-user-select: none;
            }}
            
            /* Plovoucí panel s tlačítky */
            #controls {{
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(40, 40, 40, 0.95);
                padding: 10px;
                border: 1px solid #555;
                border-radius: 10px;
                display: flex;
                gap: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.6);
                z-index: 1000;
            }}
            .ctrl-btn {{
                background: #444; 
                color: white; 
                border: 1px solid #666; 
                padding: 10px 20px; 
                cursor: pointer; 
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: bold; 
                border-radius: 5px; 
                transition: 0.2s;
            }}
            .ctrl-btn:active {{ background: #666; }}
            
            /* Třída pro aktivní stav přehrávání - napodobuje oranžový stav z desktopu */
            #btnScroll.playing {{
                background: #ffc107; 
                color: black;
                border-color: #d39e00;
            }}
        </style>

        <div id="zoom-container">{finalni_text}</div>
        
        <div id="controls">
            <button class="ctrl-btn" id="btnSlower">🐢 Zpomalit</button>
            <button class="ctrl-btn" id="btnScroll">▶ PLAY</button>
            <button class="ctrl-btn" id="btnFaster">🐇 Zrychlit</button>
        </div>

        <script>
            const container = document.getElementById('zoom-container');
            
            // --- ZOOMOVÁNÍ ---
            let fontSize = 18;
            let initialDist = -1;

            container.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 2) {{
                    initialDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
                }}
            }}, {{passive: false}});

            container.addEventListener('touchmove', (e) => {{
                if (e.touches.length === 2 && initialDist > 0) {{
                    e.preventDefault(); 
                    const currentDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
                    const diff = currentDist - initialDist;
                    if (Math.abs(diff) > 5) {{
                        fontSize += diff > 0 ? 0.8 : -0.8;
                        fontSize = Math.min(Math.max(12, fontSize), 100); 
                        container.style.fontSize = fontSize + 'px';
                        initialDist = currentDist;
                    }}
                }}
            }}, {{passive: false}});

            container.addEventListener('touchend', (e) => {{
                if (e.touches.length < 2) {{ initialDist = -1; }}
            }});

            // --- AUTOMATICKÉ ROLOVÁNÍ ---
            let isScrolling = false;
            let scrollInterval;
            let speed = 40; // Rychlost (čím menší číslo, tím rychleji)

            const btnScroll = document.getElementById('btnScroll');
            const btnSlower = document.getElementById('btnSlower');
            const btnFaster = document.getElementById('btnFaster');

            function toggleScroll() {{
                isScrolling = !isScrolling;
                if (isScrolling) {{
                    btnScroll.innerText = '⏸ STOP';
                    btnScroll.classList.add('playing');
                    startScrolling();
                }} else {{
                    btnScroll.innerText = '▶ PLAY';
                    btnScroll.classList.remove('playing');
                    stopScrolling();
                }}
            }}

            function startScrolling() {{
                clearInterval(scrollInterval);
                scrollInterval = setInterval(() => {{
                    container.scrollBy(0, 1);
                }}, speed);
            }}

            function stopScrolling() {{
                clearInterval(scrollInterval);
            }}

            // Obsluha tlačítek
            btnScroll.addEventListener('click', toggleScroll);
            
            btnSlower.addEventListener('click', () => {{
                speed = Math.min(speed + 15, 150);
                if (isScrolling) startScrolling();
            }});

            btnFaster.addEventListener('click', () => {{
                speed = Math.max(speed - 15, 10);
                if (isScrolling) startScrolling();
            }});

            // Mezerník spouští rolování (stejně jako v desktopové aplikaci)
            document.addEventListener('keydown', (e) => {{
                if (e.code === 'Space') {{
                    e.preventDefault(); // Zabrání výchozímu poskoku stránky
                    toggleScroll();
                }}
            }});
        </script>
        """
        
        # Pevná výška okna (750px), aby vnitřní skript mohl rolovat obsahem uvnitř něj
        components.html(html_content, height=750, scrolling=False)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

else:
    # --- ZOBRAZENÍ SEZNAMU (HLAVNÍ MENU) ---
    
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
        # Horní vyhledávací lišta
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            hledani = st.text_input("Hledání (interpret, název, číslo)...", key="hledani_input", label_visibility="collapsed", placeholder="Hledání (interpret, název, číslo)...").lower()
        with s_col2:
            fulltext = st.text_input("Fulltext", key="fulltext_input", label_visibility="collapsed", placeholder="Fulltext (hledat v textech)...").lower()

        # Filtrování dat
        filtered = data
        
        # 1. Filtr interpret
        if st.session_state.vybrany_interpret != "--- Vše ---":
            filtered = [p for p in filtered if p['interpreti']['jmeno'] == st.session_state.vybrany_interpret]
            
        # 2. Běžné vyhledávání (ID, název, interpret)
        if hledani:
            filtered = [p for p in filtered if (hledani in str(p['id']) or 
                                                hledani in p['nazev'].lower() or 
                                                hledani in p['interpreti']['jmeno'].lower())]
        
        # 3. FULLTEXTOVÉ vyhledávání
        if fulltext:
            slova = fulltext.split() 
            filtered = [
                p for p in filtered 
                if p.get('text_akordy') and all(slovo in p['text_akordy'].lower() for slovo in slova)
            ]
        
        # Zobrazení výsledků (čistý titulek bez příznaků ! a ?)
        if filtered:
            with st.container():
                for p in filtered:
                    titulek = f"{p['nazev']} - {p['interpreti']['jmeno']}"
                    
                    if st.button(titulek, key=f"p-{p['id']}"):
                        st.session_state.selected_song_id = p['id']
                        st.rerun()
        else:
            st.markdown("<p style='color: #777;'>Nic nenalezeno.</p>", unsafe_allow_html=True)