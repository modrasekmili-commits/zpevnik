import streamlit as st
import requests
import logic  # tvůj logic.py

st.set_page_config(page_title="Zpěvník Online", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=600) # Data si pamatuje 10 minut, pak je načte znovu
def nacti_data():
    headers = {
        "apikey": KEY, 
        "Authorization": f"Bearer {KEY}",
        "Accept-Profile": "zpevnik"
    }
    # Načteme ID, název, text a jméno interpreta
    r = requests.get(f"{URL}/rest/v1/pisne?select=id,nazev,text_akordy,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json()

st.title("🎸 Online Zpěvník")

try:
    data = nacti_data()
    
    # --- VYHLEDÁVÁNÍ ---
    search_query = st.text_input("🔍 Hledej (název, interpret nebo číslo písně):", "").lower()

    # Filtrování dat na základě hledání
    filtrovana_data = []
    for p in data:
        id_str = str(p['id'])
        nazev = p['nazev'].lower()
        interpret = p['interpreti']['jmeno'].lower()
        
        if search_query in nazev or search_query in interpret or search_query == id_str:
            filtrovana_data.append(p)

    # --- VÝBĚR PÍSNĚ ---
    if filtrovana_data:
        seznam_pro_selectbox = [f"{p['id']}. {p['interpreti']['jmeno']} - {p['nazev']}" for p in filtrovana_data]
        vyber_label = st.selectbox(f"Nalezeno písní: {len(filtrovana_data)}", seznam_pro_selectbox)
        
        index_vybrane = seznam_pro_selectbox.index(vyber_label)
        pisen = filtrovana_data[index_vybrane]

        # --- OVLÁDÁNÍ ---
        st.divider()
        c1, c2 = st.columns([1, 4])
        with c1:
            posun = st.number_input("Transpozice:", value=0, step=1)
            st.write(f"**ID písně:** {pisen['id']}")
        
        with c2:
            st.subheader(f"{pisen['nazev']} — {pisen['interpreti']['jmeno']}")
            
        # Transpozice a zobrazení
        finalni_text = logic.transponuj_text(pisen['text_akordy'], posun)
        st.code(finalni_text, language="text")
        
    else:
        st.warning("Žádná píseň neodpovídá vyhledávání.")

except Exception as e:
    st.error(f"Chyba: {e}")
