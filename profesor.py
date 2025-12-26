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
    
    /* Poruke u chatu */
    .chat-msg { padding: 12px 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.5; font-size: 0.95em; }
    .user-msg { background-color: #2b3137; border-left: 4px solid #3b8ed0; text-align: right; }
    .bot-msg { background-color: #1c2329; border-left: 4px solid #f25a29; }
    
    /* Zadaci i Rešenja */
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4a4a4a; margin-bottom: 20px; }
    .solution-box { background-color: #1e2620; padding: 15px; border-radius: 10px; border: 1px solid #28a745; margin-top: 15px; }
    
    /* Dugmići */
    .stButton button { width: 100%; border-radius: 5px; }
    
    /* Tabovi */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 10px 15px; }
    .stTabs [aria-selected="true"] { background-color: #f25a29; color: white; border-top: 2px solid white;}
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ ---
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")

MODEL_NAZIV = "llama-3.3-70b-versatile" 

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏫 Dnevnik rada")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    
    if razred == "I Razred":
        tema_options = ["Osnove (Tipovi, I/O)", "Grananja", "Petlje", "Nizovi (1D)", "Brojni sistemi"]
    else:
        tema_options = ["Matrice (2D Nizovi)", "Stringovi", "Sortiranje/Pretraga", "Funkcije", "Rekurzija"]
    
    tema = st.selectbox("Trenutna oblast:", tema_options)
    tezina = st.select_slider("Nivo znanja:", options=["Početnik", "Srednji", "Napredni (Takmičar)"])
    
    st.markdown("---")
    if st.button("🔄 Restartuj čas"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- INICIJALIZACIJA STANJA ---
welcome_msg = (
    f"Zdravo! Ja sam tvoj mentor za programiranje.\n\n"
    f"Vidim da si u **{razred}u** i da radite **{tema}**.\n\n"
    "**Pre nego što krenemo na zadatke:**\n"
    "1. Šta ste radili na poslednjem času?\n"
    "2. Da li ti je nešto ostalo nejasno?\n\n"
    "Odgovori mi dole u polju za unos 👇"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""
if "buggy_code" not in st.session_state: st.session_state.buggy_code = ""

# --- SISTEMSKI PROMPT (AŽURIRAN: ZABRANA PYTHON-A) ---
system_prompt = f"""
Ti si iskusni profesor informatike u gimnaziji "Bora Stanković" (Niš), specijalno IT odeljenje.
Radiš sa učenikom {razred}-og razreda. Tema: {tema}.

STROGA PRAVILA ZA KODIRANJE:
1. **ISKLJUČIVO C++**. ZABRANJENO JE KORISTITI PYTHON.
2. Ako učenik pošalje Python kod, upozori ga da u ovoj školi radimo samo C++ i prevedi kod u C++.
3. Koristi `cin`, `cout` i standardne biblioteke (`<iostream>`, `<vector>` itd.).

TVOJA PEDAGOGIJA:
1. Prvo dijagnostika kroz razgovor.
2. Kada daješ rešenje zadatka: MORAŠ prvo objasniti logiku (algoritam), pa tek onda kod.
3. Budi ohrabrujući ali traži preciznost.
4. Jezik komunikacije: Standardni srpski (ekavica).

Zapamti: Ti si profesor C++ jezika. Python ne postoji u tvojoj učionici.
"""

st.title(f"🎓 Profesor C++ ({razred})")

# --- GLAVNI DEO ---
col_workspace, col_chat = st.columns([1.4, 1])

# ==========================================
# LEVA KOLONA: RADNI PROSTOR (ALATI)
# ==========================================
with col_workspace:
    tab_vezba, tab_viz, tab_lov = st.tabs(["📝 Zadaci", "📊 Dijagrami", "🐛 Lov na greške"])
    
    # === TAB 1: ZADACI ===
    with tab_vezba:
        st.markdown("#### Generator Zadataka")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            if st.button("🎲 Daj mi zadatak", type="primary"):
                if api_key:
                    st.session_state.current_solution = "" 
                    client = Groq(api_key=api_key)
                    # Eksplicitno naglašavamo C++ i u promptu za zadatak
                    context_p = "Na osnovu onoga što smo pričali, "
                    p = f"{context_p} zadaj mi jedan {tezina} zadatak iz oblasti {tema} u jeziku C++. Samo Tekst, Ulaz, Izlaz."
                    with st.spinner("Smišljam C++ zadatak..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": p}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_task = resp.choices[0].message.content
                    st.rerun()

        with col_btn2:
            if st.button("👀 Reši mi zadatak"):
                if not st.session_state.current_task:
                    st.warning("Prvo generiši zadatak!")
                elif api_key:
                    client = Groq(api_key=api_key)
                    # Eksplicitno tražimo C++ rešenje
                    sol_prompt = f"Zadatak: {st.session_state.current_task}\n\nUčenik se zaglavio. Daj DETALJNO objašnjenje i rešenje ISKLJUČIVO u C++ jeziku. Objasni korak po korak."
                    with st.spinner("Pišem C++ rešenje..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": sol_prompt}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_solution = resp.choices[0].message.content
                    st.rerun()

        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
        
        if st.session_state.current_solution:
            st.markdown(f'<div class="solution-box"><b>💡 Rešenje profesora (C++):</b><br>{st.session_state.current_solution}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("Tvoj C++ Editor:")
        student_code = st.text_area("Kod", height=300, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", label_visibility="collapsed")
        
        if st.button("🚀 Predaj moje rešenje"):
            if api_key:
                msg = f"Zadatak: {st.session_state.current_task}\nKod:\n```cpp\n{student_code}\n```\nPregledaj moj C++ kod."
                st.session_state.messages.append({"role": "user", "content": msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram C++..."):
                    full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 2: VIZUELIZACIJA ===
    with tab_viz:
        st.info("Zalepi C++ kod da vidiš dijagram toka.")
        viz_code = st.text_area("Kod za dijagram:", height=150)
        if st.button("🎨 Nacrtaj"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                viz_p = f"Pretvori ovaj C++ kod u Graphviz DOT format. Vrati SAMO kod unutar ```dot``` bloka.\n{viz_code}"
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
                match = re.search(r'```dot(.*?)```', resp.choices[0].message.content, re.DOTALL)
                if match: st.graphviz_chart(match.group(1).strip())
                else: st.error("Greška pri crtanju.")

    # === TAB 3: LOV NA GREŠKE ===
    with tab_lov:
        if st.button("🐛 Generiši kod sa greškom"):
            if api_key:
                client = Groq(api_key=api_key)
                bug_p = f"Daj C++ kod sa logičkom greškom ({tema}). Samo kod."
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":bug_p}])
                st.session_state.buggy_code = resp.choices[0].message.content
        
        if st.session_state.buggy_code:
            st.code(st.session_state.buggy_code, language="cpp")
            guess = st.text_input("Gde je greška?")
            if st.button("Proveri"):
                st.session_state.messages.append({"role": "user", "content": f"U kodu:\n{st.session_state.buggy_code}\nMislim da je greška: {guess}"})
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

# ==========================================
# DESNA KOLONA: KOMUNIKACIJA (CHAT)
# ==========================================
with col_chat:
    st.markdown("### 💬 Razgovor sa mentorom")
    
    chat_container = st.container(height=600)
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user":
                text = msg["content"]
                if "Zadatak:" in text and "Kod:" in text: text = "📝 *Predao sam rešenje zadatka...*"
                st.markdown(f'<div class="chat-msg user-msg">{text}</div>', unsafe_allow_html=True)

    st.markdown("---")
    chat_input = st.text_area("Piši profesoru ovde:", height=80, placeholder="Npr: Nije mi jasan prethodni korak...", label_visibility="collapsed")
    
    if st.button("Pošalji poruku"):
        if api_key and chat_input:
            st.session_state.messages.append({"role": "user", "content": chat_input})
            client = Groq(api_key=api_key)
            with st.spinner("..."):
                full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
            st.rerun()
