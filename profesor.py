import streamlit as st
from groq import Groq

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Spec. IT Vežbaonica - Bora Stanković", page_icon="🎓", layout="wide")

# --- CSS STILOVI ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stTextArea textarea { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #dcdcdc; }
    .chat-msg { padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6; }
    .user-msg { background-color: #2b3137; border-left: 4px solid #3b8ed0; }
    .bot-msg { background-color: #1c2329; border-left: 4px solid #f25a29; }
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #f25a29; margin-bottom: 20px; }
    /* Tabovi */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #f25a29; color: white; }
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ ---
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")

# --- SIDEBAR: PODEŠAVANJA ---
with st.sidebar:
    st.header("🏫 Podešavanje časa")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    
    if razred == "I Razred":
        tema = st.selectbox("Oblast:", ["Osnove (Tipovi, I/O)", "Grananja", "Petlje", "Nizovi (1D)", "Brojni sistemi"])
    else:
        tema = st.selectbox("Oblast:", ["Matrice (2D Nizovi)", "Stringovi", "Sortiranje/Pretraga", "Funkcije", "Rekurzija", "Strukture"])
    
    tezina = st.select_slider("Težina:", options=["Lak", "Srednji", "Takmičarski (Spec. IT)"])
    
    if st.button("🗑️ Obriši istoriju chata"):
        st.session_state.messages = []
        st.rerun()

# --- INICIJALIZACIJA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task" not in st.session_state:
    st.session_state.current_task = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković" (Niš), smer za učenike sa posebnim sposobnostima za informatiku (IT smer).
Radiš sa učenikom {razred}-og razreda. Tema: {tema}. Težina: {tezina}.

TVOJA ULOGA:
1. AKO UČENIK PITA TEORIJU: Objasni koncept jasno, koristi analogije, daj primer koda i objasni ga liniju po liniju.
2. AKO UČENIK POŠALJE KOD ZADATKA:
   - Proveri tačnost.
   - Proveri efikasnost (vreme izvršavanja, nepotrebne operacije).
   - Proveri "rubne slučajeve" (npr. šta ako je n=0).
   - Ne daj gotov kod odmah, navedi ga da sam ispravi grešku.

Jezik: Srpski. Kod: C++.
"""

# Ažuriranje prompta ako se promeni tema
if not st.session_state.messages or st.session_state.messages[0]["content"] != system_prompt:
    # Čuvamo stare poruke, ali ažuriramo sistemsku instrukciju na početku
    if len(st.session_state.messages) > 0:
         st.session_state.messages[0] = {"role": "system", "content": system_prompt}
    else:
         st.session_state.messages = [{"role": "system", "content": system_prompt}]

st.title(f"🎓 Profesor C++ ({razred})")

# --- GLAVNI DEO ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    # --- TABOVI: VEŽBANJE vs PITANJA ---
    tab_vezbanje, tab_pitanja = st.tabs(["📝 Rešavanje Zadatka", "🙋 Konsultacije (Pitanja)"])
    
    # === TAB 1: VEŽBANJE ===
    with tab_vezbanje:
        st.markdown("#### 1. Generisanje zad
