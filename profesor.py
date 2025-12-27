import streamlit as st
from groq import Groq
import re

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Spec. IT Mentor - Bora Stanković", page_icon="🎓", layout="wide")

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
# Koristimo brži model da izbegnemo RateLimit greške
MODEL_NAZIV = "llama-3.1-8b-instant"

api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")
if api_key: api_key = api_key.strip()

# --- POMOĆNA FUNKCIJA ZA API ---
def pozovi_ai(messages, temp=0.5):
    if not api_key:
        return "Unesi API ključ u sidebar-u."
    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=messages, temperature=temp)
        return resp.choices[0].message.content
    except Exception as e:
        if "rate_limit" in str(e).lower():
            return "⚠️ SERVER ZAUZET: Sačekaj 30 sekundi (Rate Limit)."
        return f"Greška: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏫 Opcije")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    if st.button("🔄 Restartuj aplikaciju"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- INICIJALIZACIJA STANJA ---
if "messages" not in st.session_state: 
    st.session_state.messages = [{"role": "assistant", "content": "Zdravo! Ja sam tvoj mentor. Popuni anketu 'Moje Znanje' da počnemo."}]
if "user_profile" not in st.session_state: st.session_state.user_profile = "Nije popunjeno."
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković". Radiš sa IT odeljenjem ({razred}).
PROFIL UČENIKA: {st.session_state.user_profile}

TVOJA METODOLOGIJA:
1. Obavezno koristi vizuelne opise: tabele za memoriju (Ime | Adresa | Vrednost).
2. Ako učenik kaže 'nismo radili', testiraj ga jednim blic pitanjem.
3. Piši ISKLJUČIVO u C++ i koristi srpski jezik (ekavica).
"""

st.title(f"🎓 Spec. IT Mentor ({razred})")

# --- DEFINICIJA KOLONA (Ovde je bila greška!) ---
col_workspace, col_chat = st.columns([1.6, 1])

# === LEVA KOLONA: RADNI PROSTOR ===
with col_workspace:
    tab_profil, tab_vezba, tab_znanje, tab_sim, tab_viz = st.tabs([
        "🧠 Moje Znanje", "📝 Zadaci", "📖 Baza Znanja", "🔍 Simulacija", "📊 Dijagrami"
    ])

    with tab_profil:
        st.subheader("📊 Dijagnostika")
        with st.form("anketa"):
            q1 = st.radio("Brojni sistemi i Drugi komplement?", ["Znam", "Treba pomoć", "Nismo radili"], index=2, horizontal=True)
            q2 = st.radio("Tipovi podataka i memorija (int, double, char)?", ["Znam", "Treba pomoć", "Nismo radili"], index=2, horizontal=True)
            q3 = st.radio("Grananja (IF-ELSE, Switch)?", ["Znam", "Treba pomoć", "Nismo radili"], index=2, horizontal=True)
            q4 = st.radio("Petlje (FOR, WHILE)?", ["Znam", "Treba pomoć", "Nismo radili"], index=2, horizontal=True)
            
            if st.form_submit_button("Sačuvaj i Analiziraj"):
                izvestaj = f"Sistemi: {q1}, Tipovi: {q2}, Grananja: {q3}, Petlje: {q4}"
                st.session_state.user_profile = izvestaj
                odgovor = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Napravi plan rada za danas na osnovu ovoga: {izvestaj}"}])
                st.session_state.plan_rada = odgovor
                st.rerun()
        
        if "plan_rada" in st.session_state:
            st.markdown(f'<div class="analysis-box"><b>Tvoj plan:</b><br>{st.session_state.plan_rada}</div>', unsafe_allow_html=True)

    with tab_vezba:
        c1, c2 = st.columns(2)
        if c1.button("🎲 Novi zadatak"):
            st.session_state.current_task = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":"Zadaj mi zadatak prilagođen mom profilu."}])
            st.session_state.current_solution = ""
            st.rerun()
        if c2.button("👀 Reši zadatak"):
            if st.session_state.current_task:
                st.session_state.current_solution = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Reši ovaj zadatak:\n{st.session_state.current_task}"}])
                st.rerun()
        
        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
        if st.session_state.current_solution:
            st.markdown(f'<div class="solution-box">{st.session_state.current_solution}</div>', unsafe_allow_html=True)

    with tab_znanje:
        st.subheader("📖 AI Udžbenik")
        tema_lekcije = st.text_input("Unesi temu (npr. 'Drugi komplement' ili 'Switch'):")
        if st.button("Generiši lekciju") and tema_lekcije:
            lekcija = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Napiši lekciju o {tema_lekcije} sa tabelama memorije i 3 primera."}])
            st.session_state.poslednja_lekcija = lekcija
        
        if "poslednja_lekcija" in st.session_state:
            st.markdown(st.session_state.poslednja_lekcija)

    with tab_sim:
        sim_code = st.text_area("Kod za Trace Table:", height=150)
        if st.button("📉 Tabelarni prikaz"):
            if api_key and sim_code:
                st.markdown(pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Napravi Trace Table za:\n{sim_code}"}]))

    with tab_viz:
        viz_code = st.text_area("Kod za Dijagram:", height=150)
        if st.button("🎨 Nacrtaj"):
            if api_key and viz_code:
                resp = pozovi_ai([{"role":"system","content":system_prompt}, {"role":"user","content":f"Pretvori u DOT kod (samo ```dot``` blok):\n{viz_code}"}])
                match = re.search(r'```dot(.*?)```', resp, re.DOTALL)
                if match: st.graphviz_chart(match.group(1).strip())

# === DESNA KOLONA: MENTOR (CHAT) ===
with col_chat:
    st.subheader("💬 Razgovor")
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        role = "bot-msg" if m["role"]=="assistant" else "user-msg"
        chat_container.markdown(f'<div class="chat-msg {role}">{m["content"]}</div>', unsafe_allow_html=True)
    
    if upit := st.chat_input("Pitaj me bilo šta..."):
        st.session_state.messages.append({"role":"user", "content":upit})
        odgovor = pozovi_ai([{"role":"system","content":system_prompt}] + st.session_state.messages)
        st.session_state.messages.append({"role":"assistant", "content":odgovor})
        st.rerun()
