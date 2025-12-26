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
    .chat-msg { padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6; }
    .user-msg { background-color: #2b3137; border-left: 4px solid #3b8ed0; }
    .bot-msg { background-color: #1c2329; border-left: 4px solid #f25a29; }
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #f25a29; margin-bottom: 20px; }
    
    /* Stilovi za Tabove */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 10px 15px; font-size: 0.9em;}
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

# --- SIDEBAR: PODEŠAVANJA ---
with st.sidebar:
    st.header("🏫 Dnevnik rada")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    
    if razred == "I Razred":
        tema_options = ["Osnove (Tipovi, I/O)", "Grananja", "Petlje", "Nizovi (1D)", "Brojni sistemi"]
    else:
        tema_options = ["Matrice (2D Nizovi)", "Stringovi", "Sortiranje/Pretraga", "Funkcije", "Rekurzija"]
    
    tema = st.selectbox("Trenutna oblast u školi:", tema_options)
    tezina = st.select_slider("Nivo znanja:", options=["Početnik", "Srednji", "Napredni (Takmičar)"])
    
    st.markdown("---")
    if st.button("🔄 Restartuj čas"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- INICIJALIZACIJA STANJA ---
# Ovde definišemo "Proaktivnog profesora" koji odmah postavlja pitanja
welcome_msg = (
    f"Zdravo! Ja sam tvoj mentor za programiranje.\n\n"
    f"Vidim da si u **{razred}u** i da radite **{tema}**.\n\n"
    "Pre nego što počnemo sa zadacima, reci mi:\n"
    "1. **Šta ste tačno radili na poslednjem času?**\n"
    "2. **Da li ti je nešto ostalo nejasno ili teško?** (npr. ne razumeš petlje, muče te nizovi...)\n\n"
    "Piši mi ovde u chatu, pa ćemo napraviti plan."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "buggy_code" not in st.session_state: st.session_state.buggy_code = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si iskusni profesor informatike u gimnaziji "Bora Stanković" (Niš), IT smer.
Radiš sa učenikom {razred}-og razreda. Tema: {tema}.

TVOJA METODOLOGIJA:
1. **DIJAGNOSTIKA:** Na početku saznaj šta učenik ne zna. Ako kaže da mu "petlje nisu jasne", objasni ih pre zadavanja zadataka.
2. **SPIRALNO UČENJE:** Iako vežbate trenutnu temu ({tema}), povremeno ubaci pitanje iz prethodnih lekcija da ne zaboravi.
3. **PODRŠKA:** Budi ohrabrujući, ali traži preciznost (kao pravi C++ kompajler).
4. **VIZUELIZACIJA:** Ako učenik traži dijagram, generiši Graphviz DOT kod u ```dot bloku.

Jezik: Srpski.
"""

# Ubacivanje sistemskog prompta (ali ne brišemo istoriju razgovora)
messages_for_api = [{"role": "system", "content": system_prompt}] + st.session_state.messages

st.title(f"🎓 Profesor C++ ({razred})")

# --- GLAVNI DEO ---
col_left, col_right = st.columns([1.3, 1])

with col_left:
    # --- 4 TABA: SADA JE RAZGOVOR PRVI ---
    tab_chat, tab_vezba, tab_viz, tab_lov = st.tabs(["💬 Razgovor", "📝 Zadaci", "📊 Dijagrami", "🐛 Lov na greške"])
    
    # === TAB 1: RAZGOVOR (KONSULTACIJE) ===
    with tab_chat:
        st.markdown("#### 🗣️ Konsultacije")
        st.caption("Ovde odgovaraš profesoru na pitanja ili tražiš objašnjenja.")
        
        chat_input = st.text_area("Tvoj odgovor / pitanje:", height=100, key="chat_input_main", placeholder="Npr: Učili smo while petlju, ali me buni kad se koristi ona, a kad for...")
        
        if st.button("Pošalji poruku", key="btn_chat_send"):
            if api_key and chat_input:
                # 1. Dodajemo user poruku u istoriju
                st.session_state.messages.append({"role": "user", "content": chat_input})
                
                # 2. Šaljemo API-ju
                client = Groq(api_key=api_key)
                with st.spinner("Profesor kuca..."):
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 2: ZADACI (ISTO KAO PRE) ===
    with tab_vezba:
        st.markdown("#### 📝 Vežbanje")
        if st.button("🎲 Daj mi zadatak", key="btn_gen"):
            if api_key:
                client = Groq(api_key=api_key)
                # Prompt traži zadatak na osnovu onoga što je učenik rekao u chatu
                context_summary = "Uzmi u obzir prethodni razgovor sa učenikom o tome šta mu nije jasno."
                p = f"{context_summary} Zadaj jedan {tezina} zadatak iz oblasti {tema}. Format: Tekst, Ulaz, Izlaz. Bez rešenja."
                
                with st.spinner("Smišljam zadatak prilagođen tebi..."):
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt}] + st.session_state.messages + [{"role":"user", "content": p}])
                    st.session_state.current_task = resp.choices[0].message.content
        
        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)

        student_code = st.text_area("C++ Editor:", height=300, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", key="code_main")
        
        if st.button("🚀 Predaj rešenje", key="btn_code_sub"):
            if api_key:
                msg = f"Zadatak: {st.session_state.current_task}\nEvo mog koda:\n```cpp\n{student_code}\n```\nPregledaj ga."
                st.session_state.messages.append({"role": "user", "content": msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram kod..."):
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 3: VIZUELIZACIJA ===
    with tab_viz:
        st.info("Zalepi kod ovde da vidiš kako izgleda njegova logika (Dijagram toka).")
        viz_code = st.text_area("Kod za dijagram:", height=150, key="viz_editor")
        if st.button("🎨 Nacrtaj", key="btn_viz"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                viz_p = f"Pretvori ovaj C++ kod u Graphviz DOT format. Vrati SAMO kod unutar ```dot``` bloka.\nKod:\n{viz_code}"
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
                match = re.search(r'```dot(.*?)```', resp.choices[0].message.content, re.DOTALL)
                if match:
                    st.graphviz_chart(match.group(1).strip())
                else:
                    st.error("Nisam uspeo da nacrtam.")

    # === TAB 4: LOV NA GREŠKE ===
    with tab_lov:
        if st.button("🐛 Generiši kod sa greškom"):
            if api_key:
                client = Groq(api_key=api_key)
                bug_p = f"Napravi C++ kod sa logičkom greškom iz oblasti {tema}. Vrati samo kod."
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":bug_p}])
                st.session_state.buggy_code = resp.choices[0].message.content
        
        if st.session_state.buggy_code:
            st.code(st.session_state.buggy_code, language="cpp")
            guess = st.text_input("Gde je greška?")
            if st.button("Proveri odgovor"):
                st.session_state.messages.append({"role": "user", "content": f"U kodu:\n{st.session_state.buggy_code}\nMislim da je greška: {guess}"})
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

# --- DESNI PANEL (CHAT ISTORIJA) ---
with col_right:
    st.markdown("### 💬 Istorija Razgovora")
    chat_container = st.container(height=700)
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user":
                # Skraćeni prikaz za korisnika da ne guši chat
                display = msg["content"]
                if "Evo mog koda" in display: display = "📝 *Predao rešenje zadatka...*"
                if "Mislim da je greška" in display: display = "🐛 *Pokušaj detekcije greške...*"
                st.markdown(f'<div class="chat-msg user-msg"><b>Ti:</b><br>{display}</div>', unsafe_allow_html=True)
