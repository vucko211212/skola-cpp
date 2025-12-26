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
    
    /* Kontejneri */
    .lesson-box { background-color: #1e202e; padding: 25px; border-radius: 10px; border-left: 5px solid #3b8ed0; margin-bottom: 20px; }
    .exam-box { background-color: #2b1c1c; padding: 25px; border-radius: 10px; border: 1px dashed #f25a29; margin-bottom: 20px; }
    .task-box { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4a4a4a; margin-bottom: 20px; }
    .solution-box { background-color: #1e2620; padding: 15px; border-radius: 10px; border: 1px solid #28a745; margin-top: 15px; }
    
    /* Tabovi */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 8px 12px; font-size: 0.9em; }
    .stTabs [aria-selected="true"] { background-color: #f25a29; color: white; border-top: 2px solid white;}
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ (ZAŠTIĆEN) ---
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")

if api_key:
    api_key = api_key.strip()

MODEL_NAZIV = "llama-3.3-70b-versatile" 

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏫 Dnevnik rada")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    
    if razred == "I Razred":
        tema_options = [
            "1. Uvod u C++ (Struktura, iostream)",
            "2. Promenljive i Tipovi (int, float, char, bool)",
            "3. Operatori (Aritmetički, Relacijski, Logički)",
            "4. Grananja (IF-ELSE)",
            "5. Switch Naredba",
            "6. Petlje (FOR, WHILE, DO-WHILE) - Napredno",
            "7. Brojni sistemi (Bin, Oct, Hex, 2K)"
        ]
    else:
        tema_options = ["Matrice", "Stringovi", "Sortiranje", "Strukture"]
    
    tema = st.selectbox("Oblast rada:", tema_options)
    tezina = st.select_slider("Težina zadataka:", options=["Dvojka", "Trojka/Četvorka", "Petica (Takmičarski)"])
    
    st.markdown("---")
    if st.button("🔄 Restartuj čas"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- STANJE APLIKACIJE ---
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Zdravo! Spreman sam za rad."}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""
if "lesson_content" not in st.session_state: st.session_state.lesson_content = ""
if "exam_content" not in st.session_state: st.session_state.exam_content = ""

# --- SYSTEM PROMPT ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković" (Niš), IT smer.
Radiš sa učenikom {razred}-og razreda.
Tema: {tema}.

ULOGE:
1. U tabu "Baza Znanja": Ti si AUTOR UDŽBENIKA. Pišeš detaljne lekcije.
2. U tabu "Zadaci": Ti si ISPITIVAČ. Zadaješ zadatke.
3. U tabu "Dijagrami": Ti si SYSTEM ZA VIZUELIZACIJU. Pretvaraš C++ u DOT jezik.

PRAVILA:
- ISKLJUČIVO C++ (Zabranjen Python).
- Jezik komunikacije: Srpski (ekavica).
"""

st.title(f"🎓 Spec. IT Vežbaonica ({razred})")

# --- GLAVNI PROSTOR ---
col_workspace, col_chat = st.columns([1.6, 1])

with col_workspace:
    tab_znanje, tab_vezba, tab_ispit, tab_sim, tab_viz = st.tabs([
        "📖 Baza Znanja (Udžbenik)", 
        "📝 Pojedinačni Zadaci", 
        "📜 Probni Kontrolni", 
        "🔍 Simulacija", 
        "📊 Dijagrami"
    ])
    
    # === TAB 1: BAZA ZNANJA ===
    with tab_znanje:
        st.markdown(f"### 📘 Lekcija: {tema}")
        st.caption("Ovde AI generiše kompletnu lekciju sa primerima, kao iz knjige.")
        
        col_les1, col_les2 = st.columns([1, 1])
        with col_les1:
            specific_topic = st.text_input("Šta te konkretno zanima?", placeholder="npr. Ugnježdeni IF, Break naredba...")
        with col_les2:
            st.write("") 
            st.write("") 
            if st.button("Generiši lekciju", type="primary"):
                if api_key:
                    client = Groq(api_key=api_key)
                    topic_full = f"{tema} - {specific_topic}" if specific_topic else tema
                    lesson_p = f"""
                    Napiši DETALJNU lekciju za srednjoškolce o temi: '{topic_full}'.
                    Struktura lekcije:
                    1. Definicija (Šta je to i čemu služi).
                    2. Sintaksa u C++ (Opšta formula).
                    3. Rešen Primer (Kod + Objašnjenje).
                    4. "Pazi se!" (Najčešće greške učenika).
                    5. Mali trik (Best practice).
                    Koristi Markdown formatiranje.
                    """
                    with st.spinner("Pišem lekciju..."):
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":lesson_p}])
                        st.session_state.lesson_content = resp.choices[0].message.content
        
        if st.session_state.lesson_content:
            st.markdown(f'<div class="lesson-box">{st.session_state.lesson_content}</div>', unsafe_allow_html=True)

    # === TAB 2: ZADACI ===
    with tab_vezba:
        st.markdown("#### Vežbaonica")
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🎲 Novi zadatak"):
                if api_key:
                    st.session_state.current_solution = "" 
                    client = Groq(api_key=api_key)
                    p = f"Zadaj jedan {tezina} zadatak iz oblasti {tema}. Tekst, Ulaz, Izlaz. Bez rešenja."
                    with st.spinner("Tražim zadatak..."):
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":p}])
                        st.session_state.current_task = resp.choices[0].message.content
                    st.rerun()
        with col_btn2:
            if st.button("👀 Prikaži rešenje"):
                if not st.session_state.current_task: st.warning("Nema zadatka!")
                elif api_key:
                    client = Groq(api_key=api_key)
                    sol_p = f"Zadatak: {st.session_state.current_task}\n\nDaj detaljno C++ rešenje sa objašnjenjem."
                    with st.spinner("Rešavam..."):
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":sol_p}])
                        st.session_state.current_solution = resp.choices[0].message.content
                    st.rerun()

        if st.session_state.current_task:
            st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
        if st.session_state.current_solution:
            st.markdown(f'<div class="solution-box">{st.session_state.current_solution}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        code_input = st.text_area("Tvoj kod:", height=150)
        if st.button("Proveri kod"):
            if api_key:
                msg = f"Zadatak: {st.session_state.current_task}\nKod:\n{code_input}\nAnaliziraj kod kao profesor."
                st.session_state.messages.append({"role":"user", "content":msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram..."):
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                    st.session_state.messages.append({"role":"assistant", "content":resp.choices[0].message.content})
                st.rerun()

    # === TAB 3: KONTROLNI ===
    with tab_ispit:
        st.markdown("### 📜 Generator Kontrolnih Zadataka")
        if st.button("Generiši Probni Kontrolni (Grupa A)", type="primary"):
            if api_key:
                client = Groq(api_key=api_key)
                exam_p = f"""
                Sastavi PROBNI KONTROLNI ZADATAK iz oblasti {tema}.
                3 zadatka: Lak, Srednji, Težak.
                Ispiši samo tekstove zadataka.
                """
                with st.spinner("Štampam kontrolni..."):
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":exam_p}])
                    st.session_state.exam_content = resp.choices[0].message.content
        
        if st.session_state.exam_content:
            st.markdown(f'<div class="exam-box">{st.session_state.exam_content}</div>', unsafe_allow_html=True)

    # === TAB 4: SIMULACIJA ===
    with tab_sim:
        sim_code = st.text_area("Kod za Trace Table:", height=150, placeholder="int a=5; while(a>0)...")
        if st.button("📉 Napravi tabelu"):
            if api_key and sim_code:
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":f"Napravi detaljan Trace Table (tabelu praćenja) za ovaj C++ kod:\n{sim_code}"}])
                st.markdown(resp.choices[0].message.content)

    # === TAB 5: VIZUELIZACIJA (POPRAVLJENO!) ===
    with tab_viz:
        st.info("Zalepi C++ kod da vidiš dijagram toka.")
        viz_code = st.text_area("Kod za dijagram:", height=150, placeholder="if (a > b) { cout << a; } else { cout << b; }")
        
        if st.button("🎨 Crtaj Dijagram"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                # --- STROŽI PROMPT ZA VIZUELIZACIJU ---
                viz_p = f"""
                Ti si mašina za konverziju koda. Tvoj jedini zadatak je da pretvoriš dati C++ kod u validan Graphviz DOT jezik.
                PRAVILA:
                1. Vrati ISKLJUČIVO DOT kod unutar ```dot i ``` blokova.
                2. NE PIŠI NIKAKAV UVODNI NI ZAVRŠNI TEKST. Nema "Evo dijagrama". Samo kod.
                
                C++ Kod:
                {viz_code}
                """
                with st.spinner("Crtam... (Ovo može potrajati par sekundi)"):
                    try:
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
                        full_response = resp.choices[0].message.content
                        
                        # --- PAMETNIJE HVATANJE KODA ---
