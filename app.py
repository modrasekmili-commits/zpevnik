import streamlit as st
import requests
import logic
import streamlit.components.v1 as components

# 1. Konfigurace stránky (musí být jako první)
st.set_page_config(page_title="Online Zpěvník", layout="wide")

# 2. Vyladěné CSS pro perfektní vzhled a potlačení rušivých prvků
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

    /* SKRYTÍ TLAČÍTKA KOPÍROVAT (Clipboard) */
    button[title="Copy to clipboard"] {
        display: none !important;
    }

    /* Hlavní kontejner písně */
    .song-container {
        background-color: #1a1a1a !important;
        color: #e0e0e0 !important;
        padding: 25px;
        border-radius: 8px;
        
        /* Absolutní vynucení neproporcionálního písma pro zarovnání akordů */
        font-family: 'Roboto Mono', 'Consolas', 'Monaco', monospace !important;
        
        height: 78vh;
        overflow-y: auto;
        overflow-x: auto;
        
        /* Zachování mezer a konců řádků */
        white-space: pre !important; 
        word-wrap: normal !important;
        
        font-size: 18px;
        line-height: 1.25; 
        border: 1px solid #333;
    }

    /* Vynucení barvy pozadí pro vše uvnitř kontejneru (řeší bílé pruhy) */
    .song-container * {
        background-color: transparent !important;
    }
    
    /* Úprava scrollovací lišty */
    .song-container::-webkit-scrollbar { width: 10px; height: 10px; }
    .song-container::-webkit-scrollbar-thumb { background: #444; border-radius: 5px; }

    /* Pozadí celé aplikace */
    .stApp { background-color: #0e1117; }
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
    try:
        r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,rychlost,interpreti(jmeno)&order=nazev", headers=headers)
        return r.json()
    except:
        return []

data = nacti_data()

# --- BOČNÍ PANEL (SIDEBAR) ---
with st.sidebar:
    st.title("🎸 Ovládání")
    search = st.text_input("🔍 Hledat (ID, název, autor):").lower()
    
    # Filtrace seznamu
    filtered = [p for p in data if search in p['nazev'].lower() or 
                search in p['interpreti']['jmeno'].lower() or 
                search == str(p['id'])]
    
    if filtered:
        sel_list = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtered]
        sel = st.selectbox("Vyber píseň:", sel_list)
        pisen = filtered[sel_list.index(sel)]
        
        st.divider()
        trans = st.number_input("Transpozice:", value=0, step=1)
        
        # Ošetření rychlosti z databáze (převod z ms na webový interval)
        db_val = pisen.get('rychlost', 30)
        try:
            start_spd = 30 if int(db_val) > 200 else int(db_val)
        except:
            start_spd = 30
            
        spd = st.slider("Rychlost scrollu (1=max, 100=min)", 1, 100, start_spd)
        
        # Logika Start/Stop tlačítka
        if 'scrolling' not in st.session_state: 
            st.session_state.scrolling = False

        def toggle_scroll():
            st.session_state.scrolling = not st.session_state.scrolling

        st.button("🚀 START / STOP", on_click=toggle_scroll, use_container_width=True, 
                  type="primary" if st.session_state.scrolling else "secondary")
    else:
        st.warning("Píseň nenalezena.")

# --- HLAVNÍ PLOCHA ---
if 'pisen' in locals():
    st.title(pisen['nazev'])
    st.caption(f"Interpret: {pisen['interpreti']['jmeno']} | ID: {pisen['id']}")
    
    # --- ČIŠTĚNÍ TEXTU ---
    raw_text = pisen['text_akordy']
    
    # 1. Odstranění Windows konců řádků (\r)
    clean_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. KLÍČOVÉ: Nahrazení nezlomitelných mezer (\xa0) obyčejnými mezerami (oprava bílých pruhů)
    clean_text = clean_text.replace('\xa0', ' ')
    
    # 3. Nahrazení tabulátorů mezerami
    clean_text = clean_text.expandtabs(4)
    
    # 4. Transpozice pomocí tvého logic.py
    final_text = logic.transponuj_text(clean_text, trans)

    # 5. Zobrazení v HTML kontejneru
    st.markdown(f'<div id="song-box" class="song-container">{final_text}</div>', unsafe_allow_html=True)

    # --- JAVASCRIPT PRO SCROLL ---
    if st.session_state.scrolling:
        js_scroll = f"""
        <script>
            var b = window.parent.document.getElementById('song-box');
            if (b) {{
                // Vyčištění předchozích intervalů
                if (window.parent.scrollInterval) {{ clearInterval(window.parent.scrollInterval); }}
                // Nastavení nového posunu
                window.parent.scrollInterval = setInterval(function() {{ 
                    b.scrollTop += 1; 
                }}, {spd});
            }}
        </script>
        """
        components.html(js_scroll, height=0)
    else:
        # Zastavení posunu
        components.html("<script>clearInterval(window.parent.scrollInterval);</script>", height=0)
else:
    st.info("Vyber píseň v bočním panelu.")
