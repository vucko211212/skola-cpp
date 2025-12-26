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
    
    /* Elementi */
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4a4a4a; margin-bottom: 20px; }
    .solution-box { background-color: #1e2620; padding: 15px; border-radius: 10px; border: 1px solid #28a745; margin-top: 15px; }
    .knowledge-box { background-color: #1c2329; border: 1px solid #4a4a4a; padding: 20px; border-radius: 5px; }
    
    /* Tabovi */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 8px 12px; font-size: 0.85em; }
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
    st.header("🏫 Dnevnik rada (1. Polugodište)")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    
    # Fokusiramo teme na 1. polugodište
    if razred == "I Razred":
        tema_options = [
            "Uvod u C++ (Sintaksa)",
            "Promenljive i Tipovi podataka",
            "Ulaz i Izlaz (cin/cout)",
            "Aritmetički operatori (+, -, %, /)",
            "Relacijski i Logički operatori",
            "Grananja (if-else)",
            "Switch naredba",
            "Brojni sistemi (Bin, Oct, Hex)"
        ]
    else:
        tema_options = ["Matrice", "Stringovi", "Strukture", "Sortiranje"]
    
    tema = st.selectbox("Oblast vežbanja:", tema_options)
    tezina = st.select_slider("Nivo znanja:", options=["Početnik", "Srednji", "Napredni (Takmičar)"])
    
    st.markdown("---")
    if st.button("🔄 Restartuj čas"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- INICIJALIZACIJA STANJA ---
welcome_msg = (
    f"Zdravo! Fokusirani smo na **prvo polugodište**.\n\n"
    f"Tema: **{tema}**.\n\n"
    "**Pre zadataka:**\n"
    "1. Šta ti je najteže iz ove oblasti?\n"
    "2. Da li ti treba kratko objašnjenje pre nego što krenemo?\n\n"
    "Piši dole 👇"
)

if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""
if "buggy_code" not in st.session_state: st.session_state.buggy_code = ""
if "quiz_code" not in st.session_state: st.session_state.quiz_code = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković" (Niš), IT smer.
Radiš sa učenikom {razred}-og razreda. Fokus je PRVO POLUGODIŠTE.
Trenutna tema: {tema}.

PRAVILA:
1. **ISKLJUČIVO C++**.
2. Zadaci moraju biti prilagođeni prvom polugodištu (nema nizova ni funkcija ako se rade if-ovi).
3. Ako je tema "Brojni sistemi", zadaj zadatke konverzije ili sabiranja u binarnom sistemu.
4. Koristi srpski jezik (ekavica).
"""

st.title(f"🎓 Profesor C++ ({razred})")

# --- GLAVNI DEO ---
col_workspace, col_chat = st.columns([1.5, 1])

# LEVA KOLONA: RADNI PROSTOR
with col_workspace:
    # DODAT TAB "BAZA ZNANJA"
    tab_znanje, tab_vezba, tab_sim, tab_kviz, tab_viz = st.tabs(["📖 Baza Znanja", "📝 Zadaci", "🔍 Simulacija", "❓ Kviz", "📊 Dijagrami"])
    
    # === TAB 1: BAZA ZNANJA (NOVO!) ===
    with tab_znanje:
        st.markdown("### 📚 Teorija za 1. polugodište")
        lekcija = st.selectbox("Izaberi lekciju:", [
            "Tipovi podataka u C++", 
            "Operator deljenja i ostatka (%)", 
            "Logički operatori (&&, ||, !)",
            "IF-ELSE Grananja",
            "Switch Naredba",
            "Brojni sistemi (Konverzije)",
            "Drugi komplement (Negativni brojevi)"
        ])
        
        with st.container(border=True):
            if lekcija == "Tipovi podataka u C++":
                st.markdown("""
                - `int` : Celi brojevi (4 bajta). Primer: `int a = 5;`
                - `float` / `double` : Realni brojevi. Primer: `double pi = 3.14159;`
                - `char` : Jedan znak. Primer: `char slovo = 'A';`
                - `bool` : Logička vrednost (`true` ili `false`).
                
                ⚠️ **Pazi:** `5 / 2` je `2` (celobrojno), a `5.0 / 2` je `2.5` (realno)!
                """)
            elif lekcija == "Operator deljenja i ostatka (%)":
                st.markdown("""
                Operator `%` (moduo) vraća **ostatak** pri deljenju.
                
                Primeri:
                - `10 % 3 = 1` (jer je 10 = 3*3 + **1**)
                - `4 % 2 = 0` (broj je paran ako je `x % 2 == 0`)
                - `123 % 10 = 3` (daje poslednju cifru broja)
                - `123 / 10 = 12` (odseca poslednju cifru)
                """)
            elif lekcija == "Logički operatori (&&, ||, !)":
                st.markdown("""
                - `&&` (**I**): Oba izraza moraju biti tačna. 
                  - `(5 > 2 && 3 < 4)` -> **TRUE**
                - `||` (**ILI**): Bar jedan mora biti tačan.
                  - `(5 > 2 || 3 > 100)` -> **TRUE**
                - `!` (**NE**): Obrće vrednost.
                  - `!(5 > 2)` -> **FALSE**
                """)
            elif lekcija == "IF-ELSE Grananja":
                st.code("""
if (uslov) {
    // Radi se ako je uslov TAČAN
} else if (drugi_uslov) {
    // Radi se ako je drugi uslov TAČAN
} else {
    // Radi se ako NIŠTA nije tačno
}
                """, language="cpp")
            elif lekcija == "Brojni sistemi (Konverzije)":
                st.markdown("""
                **Binarni u Dekadni:**
                $101_2 = 1 \cdot 2^2 + 0 \cdot 2^1 + 1 \cdot 2^0 = 4+0+1 = 5$
                
                **Heksadekadni (Baza 16):**
                Cifre: 0-9 i A(10), B(11), C(12), D(13), E(14), F(15).
                
                **Binarni -> Heksadekadni:**
                Grupisati po 4 bita s desna na levo.
                $110110_2 \rightarrow 0011 \quad 0110 \rightarrow 3 \quad 6 \rightarrow 36_{16}$
                """)
            elif lekcija == "Drugi komplement (Negativni brojevi)":
                st.markdown("""
                Kako zapisati **-5** u 4 bita?
                1. Zapiši +5 binarno: `0101`
                2. Invertuj bitove (0->1, 1->0): `1010` (Ovo je Prvi komplement)
                3. Dodaj 1: `1010 + 1 = 1011`
                
                Rezultat: **1011** je -5.
                """)
            elif lekcija == "Switch Naredba":
                 st.code("""
switch (x) {
    case 1:
        cout << "Jedan";
        break; // Obavezno break!
    case 2:
        cout << "Dva";
        break;
    default:
        cout << "Nepoznat broj";
}
                """, language="cpp")

    # === TAB 2: ZADACI ===
    with tab_vezba:
        st.markdown("#### Generator Zadataka (1. Polugodište)")
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🎲 Daj mi zadatak", type="primary"):
                if api_key:
                    st.session_state.current_solution = "" 
                    client = Groq(api_key=api_key)
                    # Eksplicitno tražimo zadatke iz 1. polugodišta
                    p = f"Zadaj jedan {tezina} zadatak iz oblasti {tema}. Fokus: 1. polugodište (bez nizova ako nije tema). Tekst, Ulaz, Izlaz."
                    with st.spinner("Smišljam zadatak..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": p}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_task = resp.choices[0].message.content
                    st.rerun()
        with col_btn2:
            if st.button("👀 Reši mi zadatak"):
                if not st.session_state.current_task: st.warning("Prvo generiši zadatak!")
                elif api_key:
                    client = Groq(api_key=api_key)
                    sol_prompt = f"Zadatak: {st.session_state.current_task}\n\nDaj DETALJNO objašnjenje i C++ rešenje. Objasni korak po korak."
                    with st.spinner("Pišem rešenje..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": sol_prompt}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_solution = resp.choices[0].message.content
                    st.rerun()

        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
        if st.session_state.current_solution:
            st.markdown(f'<div class="solution-box"><b>💡 Rešenje profesora:</b><br>{st.session_state.current_solution}</div>', unsafe_allow_html=True)

        st.markdown("---")
        student_code = st.text_area("Tvoj C++ kod:", height=200, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", label_visibility="collapsed")
        if st.button("🚀 Predaj rešenje"):
            if api_key:
                msg = f"Zadatak: {st.session_state.current_task}\nKod:\n```cpp\n{student_code}\n```\nPregledaj moj kod."
                st.session_state.messages.append({"role": "user", "content": msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram..."):
                    full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                st.rerun()

    # === TAB 3: SIMULACIJA ===
    with tab_sim:
        st.info("Ubaci kod i ja ću napraviti **Trace Table**.")
        sim_code = st.text_area("Kod za simulaciju:", height=150, placeholder="int a = 5; if (a > 3)...")
        if st.button("📉 Simuliraj"):
            if api_key and sim_code:
                client = Groq(api_key=api_key)
                sim_prompt = f"Napravi Trace Table za ovaj C++ kod. Kod:\n{sim_code}"
                with st.spinner("Simuliram..."):
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":sim_prompt}])
                    st.markdown(resp.choices[0].message.content)

    # === TAB 4: KVIZ ===
    with tab_kviz:
        st.markdown("#### 🤔 Šta će ispisati ovaj kod?")
        if st.button("🎲 Generiši trik pitanje"):
            if api_key:
                client = Groq(api_key=api_key)
                quiz_prompt = f"Daj mi kratak C++ snippet iz oblasti {tema} sa trik pitanjem 'Šta je ispis?'. Bez rešenja."
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":quiz_prompt}])
                st.session_state.quiz_code = resp.choices[0].message.content
        
        if st.session_state.quiz_code:
            st.code(st.session_state.quiz_code, language="cpp")
            user_guess = st.text_input("Tvoj odgovor:")
            if st.button("Proveri odgovor"):
                if api_key:
                    client = Groq(api_key=api_key)
                    chk_prompt = f"Kod:\n{st.session_state.quiz_code}\nUčenik kaže: '{user_guess}'. Da li je tačno?"
                    with st.spinner("Proveravam..."):
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":chk_prompt}])
                        st.markdown(resp.choices[0].message.content)

    # === TAB 5: VIZUELIZACIJA ===
    with tab_viz:
        st.info("Zalepi C++ kod da vidiš dijagram toka.")
        viz_code = st.text_area("Kod za dijagram:", height=150)
        if st.button("🎨 Nacrtaj"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                viz_p = f"Pretvori ovaj C++ kod u Graphviz DOT format. Vrati SAMO kod u ```dot``` bloku.\n{viz_code}"
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
                match = re.search(r'```dot(.*?)```', resp.choices[0].message.content, re.DOTALL)
                if match: st.graphviz_chart(match.group(1).strip())
                else: st.error("Greška pri crtanju.")

# DESNA KOLONA: CHAT
with col_chat:
    st.markdown("### 💬 Mentor")
    chat_container = st.container(height=600)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user":
                text = msg["content"]
                if "Zadatak:" in text: text = "📝 *Predao sam rešenje zadatka...*"
                st.markdown(f'<div class="chat-msg user-msg">{text}</div>', unsafe_allow_html=True)

    st.markdown("---")
    chat_input = st.text_area("Piši profesoru ovde:", height=80, placeholder="Pitaj me o gradivu...", label_visibility="collapsed")
    if st.button("Pošalji poruku"):
        if api_key and chat_input:
            st.session_state.messages.append({"role": "user", "content": chat_input})
            client = Groq(api_key=api_key)
            with st.spinner("..."):
                full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
            st.rerun()
