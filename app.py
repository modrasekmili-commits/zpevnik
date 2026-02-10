import streamlit as st
import requests
import logic  # tvůj logic.py

# 1. Roztažení na celou obrazovku
st.set_page_config(page_title="Zpěvník Online", layout="wide")

# CSS pro hezčí zobrazení (volitelné)
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stCode { background-color: #ffffff !important; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

def nacti_data():
    headers = {
        "apikey": KEY, 
        "Authorization": f"Bearer {KEY}",
        "Accept-Profile": "zpevnik"
    }
    r = requests.get(f"{URL}/rest/v1/pisne?select=*,interpreti(jmeno)&order=nazev", headers=headers)
    return r.json()

st.title("🎸 Můj Online Zpěvník")

try:
    data = nacti_data()
    
    # Horní panel s ovládáním
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        seznam = [f"{p['interpreti']['jmeno']} - {p['nazev']}" for p in data]
        vyber = st.selectbox("Vyber píseň:", seznam)
    
    with col2:
        posun = st.number_input("Transpozice", value=0, step=1)
        
    if vyber:
        pisen = data[seznam.index(vyber)]
        
        # Zobrazení názvu velkým písmem
        st.subheader(f"{pisen['nazev']} ({pisen['interpreti']['jmeno']})")
        
        # Logika transpozice
        text_k_zobrazeni = logic.transponuj_text(pisen['text_akordy'], posun)
        
        # Zobrazení - language="text" vypne barevné zvýrazňování kódu
        st.code(text_k_zobrazeni, language="text")

except Exception as e:
    st.error(f"Něco se nepovedlo: {e}")
