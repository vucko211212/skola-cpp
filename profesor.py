import streamlit as st
from groq import Groq
import re

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Spec. IT Vežbaonica - Bora Stanković", page_icon="🎓", layout="wide")

# --- CSS STILOVI ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stTextArea textarea { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #dcdcdc; }
    .analysis-box { background-color: #1a2634; padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff; margin-bottom: 20px; }
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4a4a4a; margin-bottom: 20px; }
    .solution-box { background-color: #1e2620; padding: 15px; border-radius: 10px; border: 1px solid #28a745; margin-top: 15px; }
    .chat-msg { padding: 12px 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.5; font-size: 0.95em; }
    .bot-msg { background-color: #1c2329; border-left: 4px solid #f25a29; }
    .user-msg { background-color: #2b3137; border-left: 4px solid #3b8ed0; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- API I MODEL ---
# Menjamo model na brži '8b' kako bismo izbegli RateLimitError
MODEL_NAZIV = "llama-3.1-8b-instant"

api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")
if api_key: api_key = api_key.strip()

# --- POMOĆNA FUNKCIJA ZA API (SA KEŠIRANJEM) ---
def pozovi_ai(messages, temp=0.5):
    if not api_key:
        return "Unesi API ključ u sidebar-u."
    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=messages, temperature=temp)
        return resp.choices[0].message.content
    except Exception as e:
        if "rate_limit" in str(e).lower():
            return "⚠️ SERVER JE PREOPTEREĆEN: Sačekaj 30 sekundi pa pokušaj ponovo. (Rate Limit)"
        return f"Greška: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏫 Opcije")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    if st.button("🔄 Restartuj aplikaciju"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- STANJE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_profile" not in st.session_state: st.session_state.user_profile = "Nije popunjeno."
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković". Učenik: {razred}.
PROFIL ZNANJA: {st.session_state.user_profile}

PEDAGOŠKA UPUTSTVA:
1. Kada objašnjavaš promenljive, koristi vizuelne tabele memorije (Ime | Adresa | Vrednost).
2. Ako učenik kaže da nešto nije radio, prvo mu daj 'blic proveru' (jedno pitanje) da potvrdiš.
3. ISKLJUČIVO C++ (ekavica).
"""

st.title(f"🎓 Spec. IT Mentor ({razred})")

# --- PITANJA ZA ANKETU ---
questions_db = {
    "Osnove": ["Dijagrami toka?", "Binarni sistem?", "Tipovi podataka (int, double)?", "Ulaz/Izlaz (cin/cout)?"],
    "Logika": ["Ostatak deljenja (%)?", "Logički operatori (&&, ||)?", "IF-ELSE grananja?", "SWITCH naredba?"],
    "Napredno": ["FOR petlja?", "WHILE petlja?", "Nizovi?", "Funkcije?"]
}

# --- TABOVI ---
tab_profil, tab_vezba, tab_sim, tab_viz, tab_znanje = st.tabs([
    "🧠 Moje Znanje", "📝 Zadaci", "🔍 Simulacija", "📊 Dijagrami", "📖 Baza Znanja"
])

# === TAB 1: MOJE ZNANJE ===
with tab_profil:
    st.subheader("📊 Dijagnostika znanja")
    with st.form("anketa"):
        results = {}
        for cat, qs in questions_db.items():
            st.write(f"**{cat}**")
            for q in qs:
                results[q] = st.radio(q, ["Znam", "Treba pomoć", "Nismo radili"], index=2, horizontal=True)
        
        if st.form_submit_button("Analiziraj"):
            izvestaj = "\n".join([f"{k}: {v}" for k, v in results.items()])
            st.session_state.user_profile = izvestaj
            plan = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Analiziraj ovo i napravi plan rada:\n{izvestaj}"}])
            st.session_state.plan = plan
            st.rerun()
    
    if "plan" in st.session_state:
        st.markdown(f'<div class="analysis-box">{st.session_state.plan}</div>', unsafe_allow_html=True)

# === TAB 2: ZADACI ===
with tab_vezba:
    col1, col2 = st.columns(2)
    if col1.button("🎲 Daj zadatak"):
        q = "Zadaj mi zadatak na osnovu mog profila znanja. Kratak tekst, ulaz i izlaz."
        st.session_state.current_task = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":q}])
        st.session_state.current_solution = ""
        st.rerun()
    
    if col2.button("👀 Reši zadatak"):
        if st.session_state.current_task:
            q = f"Reši detaljno ovaj zadatak u C++ uz objašnjenje koraka:\n{st.session_state.current_task}"
            st.session_state.current_solution = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":q}])
            st.rerun()

    if st.session_state.current_task:
        st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
    if st.session_state.current_solution:
        st.markdown(f'<div class="solution-box">{st.session_state.current_solution}</div>', unsafe_allow_html=True)

# === TAB 5: BAZA ZNANJA (AI UDŽBENIK) ===
with tab_znanje:
    st.subheader("📖 AI Udžbenik")
    tema_lekcije = st.text_input("Koju lekciju želiš da ti objasnim?")
    if st.button("Generiši lekciju") and tema_lekcije:
        prompt = f"Napiši lekciju o {tema_lekcije}. Koristi tabele za prikaz memorije i navedi 3 primera zadataka koji dolaze na kontrolnom."
        lekcija = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":prompt}])
        st.markdown(lekcija)

# --- CHAT DESNO ---
with col_chat:
    st.subheader("💬 Mentor")
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        cl = "bot-msg" if m["role"]=="assistant" else "user-msg"
        chat_container.markdown(f'<div class="chat-msg {cl}">{m["content"]}</div>', unsafe_allow_html=True)
    
    if upit := st.chat_input("Pitaj profesora..."):
        st.session_state.messages.append({"role":"user", "content":upit})
        odgovor = pozovi_ai([{"role":"system","content":system_prompt}] + st.session_state.messages)
        st.session_state.messages.append({"role":"assistant", "content":odgovor})
        st.rerun()
