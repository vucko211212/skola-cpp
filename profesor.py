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
    
    /* Upozorenje za rešenje */
    .warning-box { border: 1px solid #ff4b4b; background-color: #3d0c0c; padding: 10px; border-radius: 5px; color: #ffcccc; }
    
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
    "Hajde prvo da vidimo gde "
    "zapinje. **Postaviću ti par pitanja da procenim tvoje znanje.**\n\n"
    "Za početak: Kako bi ocenio svoje razumevanje ove teme od 1 do 5 i šta ti je najteže kod nje?"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = "" # Za čuvanje rešenja
if "buggy_code" not in st.session_state: st.session_state.buggy_code = ""

# --- SISTEMSKI PROMPT (AŽURIRAN ZA DIJAGNOSTIKU) ---
system_prompt = f"""
Ti si iskusni profesor informatike u gimnaziji "Bora Stanković" (Niš).
Radiš sa učenikom {razred}-og razreda. Tema: {tema}.

FAZA 1: DIJAGNOSTIKA (Razgovor)
- Ne kreći odmah sa zadacima. Kroz razgovor postavi 2-3 ciljana pitanja da proveriš da li učenik razume osnovne koncepte (npr. sintaksu, logiku).
- Ako vidiš rupu u znanju, objasni to pre nego što pređete na zadatke.

FAZA 2: ZADACI
- Kada daješ rešenje zadatka (na eksplicitan zahtev), ono MORA biti detaljno.
- Prvo objasni logiku (algoritam).
- Zatim napiši kod sa komentarima uz svaku važnu liniju.

JEZIK:
- Standardni srpski jezik. Budi ohrabrujući ali strog oko preciznosti koda.
"""

st.title(f"🎓 Profesor C++ ({razred})")

# --- GLAVNI DEO ---
col_left, col_right = st.columns([1.3, 1])

with col_left:
    tab_chat, tab_vezba, tab_viz, tab_lov = st.tabs(["💬 Razgovor (Dijagnostika)", "📝 Zadaci & Rešenja", "📊 Dijagrami", "🐛 Lov na greške"])
    
    # === TAB 1: RAZGOVOR ===
    with tab_chat:
        st.markdown("#### 🗣️ Konsultacije i Provera znanja")
        chat_input = st.text_area("Tvoj odgovor / pitanje:", height=100, key="chat_input_main", placeholder="Ovde kucaj...")
        
        if st.button("Pošalji poruku", key="btn_chat_send"):
            if api_key and chat_input:
                st.session_state.messages.append({"role": "user", "content": chat_input})
                client = Groq(api_key=api_key)
                with st.spinner("Profesor razmišlja..."):
                    full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 2: ZADACI I REŠENJA ===
    with tab_vezba:
        st.markdown("#### 📝 Generator Zadataka")
        
        col_btns = st.columns([1, 1])
        with col_btns[0]:
            if st.button("🎲 Daj mi NOVI zadatak", key="btn_gen"):
                if api_key:
                    st.session_state.current_solution = "" # Brišemo staro rešenje kad traži novi zadatak
                    client = Groq(api_key=api_key)
                    # Uzimamo kontekst iz chata da bi zadatak bio prilagođen
                    p = f"Na osnovu onoga što smo pričali u chatu o mom znanju, zadaj mi jedan {tezina} zadatak iz oblasti {tema}. Samo Tekst, Ulaz, Izlaz."
                    with st.spinner("Smišljam zadatak prilagođen tebi..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": p}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_task = resp.choices[0].message.content
                    st.rerun()

        # Prikaz zadatka
        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
            
            # --- DUGME ZA REŠENJE (NOVO) ---
            with col_btns[1]:
                if st.button("👀 Prikaži rešenje sa objašnjenjem"):
                    if api_key:
                        client = Groq(api_key=api_key)
                        sol_prompt = f"Zadatak je: {st.session_state.current_task}\n\nUčenik traži rešenje. Napiši DETALJNO objašnjenje postupka, korak po korak, i zatim tačan C++ kod sa komentarima. Objasni kao da predaješ lekciju."
                        with st.spinner("Pišem detaljno objašnjenje..."):
                            resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt}, {"role":"user", "content": sol_prompt}])
                            st.session_state.current_solution = resp.choices[0].message.content
                            st.rerun()

            # Prikaz rešenja u Expanderu (skriveno dok se ne klikne ili ako je već generisano)
            if st.session_state.current_solution:
                with st.expander("⚠️ REŠENJE ZADATKA (Otvori samo ako si se zaglavio!)", expanded=True):
                    st.markdown('<div class="warning-box"><b>Pedagoška napomena:</b> Ako samo prepišeš ovo rešenje, nećeš naučiti. Pokušaj prvo sam, pa koristi ovo za proveru.</div>', unsafe_allow_html=True)
                    st.markdown(st.session_state.current_solution)

        st.markdown("---")
        st.markdown("#### Tvoj prostor za rad")
        student_code = st.text_area("C++ Editor:", height=300, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", key="code_main")
        
        if st.button("🚀 Predaj moje rešenje na pregled", key="btn_code_sub"):
            if api_key:
                msg = f"Zadatak: {st.session_state.current_task}\nKod:\n```cpp\n{student_code}\n```\nPregledaj."
                st.session_state.messages.append({"role": "user", "content": msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram kod..."):
                    full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 3: VIZUELIZACIJA ===
    with tab_viz:
        st.info("Zalepi kod ovde da vidiš dijagram toka.")
        viz_code = st.text_area("Kod za dijagram:", height=150, key="viz_editor")
        if st.button("🎨 Nacrtaj", key="btn_viz"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                viz_p = f"Pretvori ovaj C++ kod u Graphviz DOT format. Vrati SAMO kod unutar ```dot``` bloka. Kod:\n{viz_code}"
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
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
                bug_p = f"Napravi C++ kod sa logičkom greškom ({tema}). Vrati samo kod."
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":bug_p}])
                st.session_state.buggy_code = resp.choices[0].message.content
        
        if st.session_state.buggy_code:
            st.code(st.session_state.buggy_code, language="cpp")
            guess = st.text_input("Gde je greška?")
            if st.button("Proveri odgovor"):
                st.session_state.messages.append({"role": "user", "content": f"U kodu:\n{st.session_state.buggy_code}\nMislim da je greška: {guess}"})
                client = Groq(api_key=api_key)
                full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

# --- DESNI PANEL (CHAT ISTORIJA) ---
with col_right:
    st.markdown("### 💬 Mentor")
    chat_container = st.container(height=800)
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user":
                preview = msg["content"]
                if "Evo mog koda" in preview: preview = "📝 *Predao rešenje zadatka...*"
                if "Mislim da je greška" in preview: preview = "🐛 *Lov na greške...*"
                st.markdown(f'<div class="chat-msg user-msg"><b>Ti:</b><br>{preview}</div>', unsafe_allow_html=True)
