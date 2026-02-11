import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky
st.set_page_config(page_title="Zpěvník", layout="wide")

# Odstranění FBCLID a jiných parametrů z adresy hned při startu
if st.query_params:
    st.query_params.clear()

# 2. CSS pro PC vzhled a obří titulky
st.markdown("""
    <style>
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    #MainMenu, footer, header {visibility: hidden;}
    
    div[data-testid="stTextInput"] label {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }

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
        if r.status_code == 200: return r.json()
    except: pass
    return []

data = nacti_data()

if 'selected_song_id' not in st.session_state:
    st.session_state.selected_song_id = None

# --- HLAVNÍ LOGIKA ---

if st.session_state.selected_song_id:
    # DETAIL PÍSNĚ
    pisen = next((p for p in data if p['id'] == st.session_state.selected_song_id), None)
    
    if pisen:
        if st.button("⬅ ZPĚT"):
            st.session_state.selected_song_id = None
            st.rerun()

        st.markdown(f'<div class="huge-title">{pisen["id"]}. {pisen["nazev"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta-info">{pisen["interpreti"]["jmeno"]}</div>', unsafe_allow_html=True)
        
        trans = st.number_input("Transpozice:", value=0, step=1, key="trans")

        clean_text = pisen['text_akordy'].replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').expandtabs(4)
        finalni_text = logic.transponuj_text(clean_text, trans)

        # HTML s JavaScriptem pro ZOOM (2 prsty) a SCROLL (1 prst)
        html_content = f"""
        <div id="zoom-container" style="
            background-color: #1a1a1a; 
            color: #ffffff; 
            padding: 25px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 24px; 
            white-space: pre; 
            line-height: 1.4;
            border-radius: 12px;
            border: 1px solid #444;
            touch-action: pan-y; 
            user-select: none;
            -webkit-user-select: none;
        ">{finalni_text}</div>

        <script>
            const el = document.getElementById('zoom-container');
            let fontSize = 24;
            let initialDist = -1;

            el.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 2) {{
                    initialDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
                }}
            }}, {{passive: false}});

            el.addEventListener('touchmove', (e) => {{
                if (e.touches.length === 2 && initialDist > 0) {{
                    e.preventDefault(); // Zablokuje scroll jen při zoomování
                    const currentDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
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
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
        """
        
        # Výpočet výšky okna
        vyska = (len(finalni_text.split('\n')) * 60) + 300
        components.html(html_content, height=vyska, scrolling=False)
    else:
        st.session_state.selected_song_id = None
        st.rerun()

else:
    # SEZNAM PÍSNÍ
    st.markdown("<h1 style='color: white; margin-bottom: 0;'>🎸 Zpěvník</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 Hledat (ID, název, interpret):", "").lower()
    
    filtered = [p for p in data if (search in str(p['id']) or 
                                    search in p['nazev'].lower() or 
                                    search in p['interpreti']['jmeno'].lower())]
    
    if filtered:
        st.write("") 
        for p in filtered:
            if st.button(f"{p['nazev']} — {p['interpreti']['jmeno']}", key=f"p-{p['id']}", use_container_width=True):
                st.session_state.selected_song_id = p['id']
                st.rerun()
    else:
        st.warning("Nic nenalezeno.")
