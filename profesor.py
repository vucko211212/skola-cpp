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
    .success-box { background-color: #1e3a23; padding: 15px; border-radius: 10px; border: 1px solid #28a745; margin-bottom: 10px; }
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
        tema = st.selectbox("Oblast:", ["Matrice (2D Nizovi)", "Stringovi", "Sortiranje/Pretraga", "Funkcije", "Rekurzija"])
    
    tezina = st.select_slider("Težina:", options=["Lak", "Srednji", "Takmičarski"])
    
    st.markdown("---")
    if st.button("🗑️ Obriši istoriju"):
        st.session_state.messages = []
        st.session_state.buggy_code = ""
        st.rerun()

# --- INICIJALIZACIJA ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "buggy_code" not in st.session_state: st.session_state.buggy_code = ""

# --- SISTEMSKI PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković". Učenik: {razred}. Tema: {tema}.
1. OBJAŠNJAVANJE: Koristi analogije. Budi precizan.
2. VIZUELIZACIJA: Ako učenik traži dijagram toka, generiši ISKLJUČIVO validan Graphviz DOT kod unutar ```dot blokova.
3. LOV NA GREŠKE: Ako tražiš da nađe grešku, daj kod koji se kompajlira ali logički ne radi (npr. petlja ide do <= umesto <).
Jezik: Srpski.
"""
if not st.session_state.messages or st.session_state.messages[0]["content"] != system_prompt:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

st.title(f"🎓 Profesor C++ ({razred})")

col_left, col_right = st.columns([1.2, 1])

with col_left:
    # --- NOVI TABOVI ---
    tab_vezba, tab_vizuelizacija, tab_lov = st.tabs(["📝 Zadaci", "📊 Dijagram Toka", "🐛 Lov na Greške"])
    
    # === TAB 1: ZADACI ===
    with tab_vezba:
        if st.button("🎲 Daj mi zadatak", key="btn_gen"):
            if api_key:
                client = Groq(api_key=api_key)
                p = f"Zadaj {tezina} zadatak iz {tema}. Format: Tekst, Ulaz, Izlaz. Bez rešenja."
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":p}])
                st.session_state.current_task = resp.choices[0].message.content
        
        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)

        student_code = st.text_area("Tvoj kod:", height=300, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", key="editor_main")
        btn_submit = st.button("🚀 Predaj rešenje", key="btn_sub")

    # === TAB 2: VIZUELIZACIJA (NOVO!) ===
    with tab_vizuelizacija:
        st.info("Zalepi svoj C++ kod ovde i ja ću ti nacrtati dijagram toka (algoritam).")
        viz_code = st.text_area("Kod za vizuelizaciju:", height=200, placeholder="Ovde stavi npr. if-else ili while petlju...", key="editor_viz")
        btn_draw = st.button("🎨 Nacrtaj Dijagram", key="btn_draw")
        
        if btn_draw and api_key and viz_code:
            client = Groq(api_key=api_key)
            # Prompt koji tera AI da vrati samo Graphviz kod
            viz_prompt = f"Pretvori ovaj C++ kod u Graphviz DOT format za dijagram toka. Koristi oblike: dijamant za uslove, pravougaonik za procese, paralelogram za ulaz/izlaz. Vrati SAMO kod unutar ```dot``` bloka.\nKod:\n{viz_code}"
            
            with st.spinner("Crtam..."):
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_prompt}])
                full_response = resp.choices[0].message.content
                
                # Izvlačenje DOT koda pomoću Regex-a
                match = re.search(r'```dot(.*?)```', full_response, re.DOTALL)
                if match:
                    dot_code = match.group(1).strip()
                    st.graphviz_chart(dot_code)
                else:
                    st.error("Nisam uspeo da generišem sliku. Pokušaj sa jednostavnijim kodom.")

    # === TAB 3: LOV NA GREŠKE (NOVO!) ===
    with tab_lov:
        st.markdown("#### 🐛 Pronađi uljeza!")
        if st.button("Generiši pokvaren kod"):
            if api_key:
                client = Groq(api_key=api_key)
                bug_prompt = f"Napravi kratak C++ kod (10-15 linija) iz oblasti {tema} koji ima jednu podmuklu logičku grešku (ne sintaksnu). Reci mi samo kod, ne govori gde je greška."
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":bug_prompt}])
                st.session_state.buggy_code = resp.choices[0].message.content
        
        if st.session_state.buggy_code:
            st.code(st.session_state.buggy_code, language="cpp")
            user_guess = st.text_input("Šta misliš, gde je greška?")
            if st.button("Proveri moj odgovor"):
                if api_key:
                    check_prompt = f"Kod:\n{st.session_state.buggy_code}\n\nUčenik kaže da je greška: {user_guess}. Da li je u pravu? Objasni rešenje."
                    client = Groq(api_key=api_key)
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":system_prompt},{"role":"user","content":check_prompt}])
                    st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})

# --- DESNI PANEL (CHAT) ---
with col_right:
    st.markdown("### 💬 Mentor")
    chat_box = st.container(height=650)
    
    # Logika za slanje koda iz prvog taba
    if btn_submit and api_key:
        msg = f"Zadatak: {st.session_state.current_task}\nKod:\n```cpp\n{student_code}\n```\nPregledaj."
        st.session_state.messages.append({"role": "user", "content": msg})
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})

    with chat_box:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user":
                preview = "📝 *Poslao rešenje/pitanje...*"
                st.markdown(f'<div class="chat-msg user-msg"><b>Ti:</b><br>{preview}</div>', unsafe_allow_html=True)
