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
    .exam-box { background-color: #2b1c1c; padding: 25px; border-radius: 10px; border: 1px dashed #f25a29; margin-bottom: 20px; }
    .detective-box { background-color: #2e2e1e; padding: 15px; border: 1px solid #ebd834; border-radius: 8px; margin-top: 10px; color: #ebd834; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2329; border-radius: 5px 5px 0 0; padding: 8px 12px; font-size: 0.9em; }
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
if api_key: api_key = api_key.strip()

MODEL_NAZIV = "llama-3.3-70b-versatile" 

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏫 Dnevnik rada")
    razred = st.radio("Razred:", ["I Razred", "II Razred"])
    st.info("💡 Savet: Ako nisi siguran šta ste radili, koristi opciju 'Detektiv' u prvom tabu!")
    
    st.markdown("---")
    if st.button("🔄 Restartuj aplikaciju"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- STANJE APLIKACIJE ---
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Zdravo! Prvo popuni profil znanja. Ako za nešto nisi siguran da li ste radili, označi 'Ne prepoznajem' pa ćemo proveriti zajedno."}]
if "current_task" not in st.session_state: st.session_state.current_task = ""
if "current_solution" not in st.session_state: st.session_state.current_solution = ""
if "user_profile" not in st.session_state: st.session_state.user_profile = "Nije popunjen."
if "detective_result" not in st.session_state: st.session_state.detective_result = "" 

# --- SYSTEM PROMPT (AŽURIRAN ZA DETEKCIJU) ---
system_prompt = f"""
Ti si profesor informatike u gimnaziji "Bora Stanković" (Niš), IT smer.
Radiš sa učenikom {razred}-og razreda.

PROFIL UČENIKA:
{st.session_state.user_profile}

VAŽNO PRAVILO O ZNANJU:
Učenici često zaboravljaju nazive lekcija. Ako u profilu piše "Ne prepoznajem pojam" ili "Nismo radili":
1. NEMOJ to trajno isključiti.
2. Povremeno ponudi: "Hej, vidim da si rekao da niste radili X. Da li želiš da ti pokažem primer koda, možda prepoznaš?"
3. Ako učenik potvrdi da prepoznaje kod, tretiraj to kao "Treba vežbanje".

TEHNIČKA PRAVILA:
- ISKLJUČIVO C++ (Zabranjen Python).
- Jezik: Srpski (ekavica).
"""

st.title(f"🎓 Spec. IT Vežbaonica ({razred})")

# --- PITANJA ZA ANKETU ---
questions_db = {
    "Algoritmi": ["Dijagrami toka (romb, pravougaonik)", "Binarni sistem i konverzije", "Drugi komplement (Negativni brojevi)"],
    "C++ Osnove": ["Tipovi podataka (int, float, char)", "Ulaz i izlaz (cin, cout)", "Aritmetički operatori (+, -, /, %)"],
    "Grananja": ["IF-ELSE naredbe", "Ugnježdeni IF", "SWITCH naredba"],
    "Petlje": ["FOR petlja", "WHILE petlja", "DO-WHILE petlja"]
}

# Promenjene opcije da budu manje "definitivne"
opcije = ["Znam (Siguran sam)", "Treba mi pomoć (Nesiguran)", "Ne prepoznajem pojam (Možda nismo radili)"]

# --- GLAVNI DEO ---
col_workspace, col_chat = st.columns([1.6, 1])

with col_workspace:
    tab_profil, tab_vezba, tab_ispit, tab_sim, tab_viz, tab_znanje = st.tabs([
        "🧠 Moje Znanje", "📝 Zadaci", "📜 Kontrolni", "🔍 Simulacija", "📊 Dijagrami", "📖 Baza Znanja"
    ])
    
    # === TAB 1: MOJE ZNANJE (SA DETEKTIVOM) ===
    with tab_profil:
        st.markdown("### 📊 Profilisanje")
        
        # 1. SEKCIJA: ANKETA
        with st.expander("📝 Popuni anketu (Klikni ovde)", expanded=True):
            with st.form("knowledge_form"):
                results = {}
                for category, questions in questions_db.items():
                    st.markdown(f"**{category}**")
                    for q in questions:
                        results[q] = st.radio(q, opcije, index=2, horizontal=True)
                    st.markdown("---")
                submit_profil = st.form_submit_button("✅ Sačuvaj moj profil")
            
            if submit_profil:
                profile_text = "Status znanja:\n"
                for q, answer in results.items():
                    profile_text += f"- {q}: {answer}\n"
                st.session_state.user_profile = profile_text
                st.success("Profil je ažuriran! Profesor sada zna šta (misliš da) znaš.")

        # 2. SEKCIJA: DETEKTIV (NOVO!)
        st.markdown("---")
        st.markdown("### 🕵️ Detektiv: Nisi siguran da li ste nešto radili?")
        st.caption("Izaberi pojam koji ti zvuči nepoznato. Ja ću ti pokazati KOD. Ako prepoznaš kod, znači da ste radili!")
        
        col_det1, col_det2 = st.columns([1, 1])
        with col_det1:
            unknown_topic = st.selectbox("Izaberi sumnjiv pojam:", 
                ["Drugi komplement", "Switch naredba", "Modulo (%) operator", "Do-While petlja", "Ugnježdeni IF"])
        with col_det2:
            st.write("")
            st.write("")
            if st.button("🔍 Pokaži mi primer koda"):
                if api_key:
                    client = Groq(api_key=api_key)
                    # Prompt traži samo vizuelni primer, bez teške teorije
                    det_prompt = f"""
                    Učenik ne zna da li su radili pojam: '{unknown_topic}'.
                    Daj kratak, jasan C++ kod (snippet) koji to ilustruje.
                    Zatim pitaj: "Da li si viđao ovakav kod na tabli?"
                    Ne objašnjavaj definicije, samo pokaži primer.
                    """
                    with st.spinner("Tražim u arhivi..."):
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":det_prompt}])
                        st.session_state.detective_result = resp.choices[0].message.content
        
        if st.session_state.detective_result:
            st.markdown(f'<div class="detective-box">{st.session_state.detective_result}</div>', unsafe_allow_html=True)
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Da, viđao sam ovo!"):
                    st.success(f"Odlično! Znači radili ste '{unknown_topic}'. Dodajem to u listu za vežbanje.")
                    st.session_state.user_profile += f"\n- {unknown_topic}: Ipak smo radili (Prepoznao vizuelno)."
            with col_no:
                if st.button("Ne, prvi put vidim"):
                    st.info(f"U redu. Onda verovatno još niste stigli do toga. Preskačemo '{unknown_topic}'.")

    # === TAB 2: ZADACI ===
    with tab_vezba:
        st.markdown("#### Vežbaonica")
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🎲 Daj mi zadatak"):
                if api_key:
                    st.session_state.current_solution = "" 
                    client = Groq(api_key=api_key)
                    # Prompt koristi profil, ali je otvoren za "meko" testiranje
                    p = "Zadaj mi zadatak. Ako u profilu imam 'Ne prepoznajem', zadaj nešto VRLO JEDNOSTAVNO iz te oblasti da proverimo da li ću se snaći."
                    with st.spinner("Biram zadatak..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": p}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                        st.session_state.current_task = resp.choices[0].message.content
                    st.rerun()
        with col_btn2:
            if st.button("👀 Prikaži rešenje"):
                if not st.session_state.current_task: st.warning("Prvo generiši zadatak!")
                elif api_key:
                    client = Groq(api_key=api_key)
                    sol_p = f"Zadatak: {st.session_state.current_task}\n\nDaj detaljno C++ rešenje."
                    with st.spinner("Pišem rešenje..."):
                        full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role":"user", "content": sol_p}]
                        resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
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
                msg = f"Zadatak: {st.session_state.current_task}\nKod:\n{code_input}\nAnaliziraj."
                st.session_state.messages.append({"role":"user", "content":msg})
                client = Groq(api_key=api_key)
                with st.spinner("Analiziram..."):
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
                    st.session_state.messages.append({"role":"assistant", "content":resp.choices[0].message.content})
                st.rerun()

    # === TAB 3: KONTROLNI ===
    with tab_ispit:
        if st.button("Generiši Probni Kontrolni", type="primary"):
            if api_key:
                client = Groq(api_key=api_key)
                exam_p = "Sastavi PROBNI KONTROLNI (3 zadatka) prilagođen onome što učenik PREPOZNAJE."
                with st.spinner("Štampam..."):
                    resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":exam_p}])
                    st.markdown(f'<div class="exam-box">{resp.choices[0].message.content}</div>', unsafe_allow_html=True)

    # === TAB 4, 5, 6 (Simulacija, Vizuelizacija, Baza) ===
    # (Ostali tabovi su isti kao pre, samo ih kopiram da kod bude kompletan)
    with tab_sim:
        sim_code = st.text_area("Kod za Trace Table:", height=150)
        if st.button("📉 Tabeliraj"):
            if api_key and sim_code:
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":f"Trace Table za:\n{sim_code}"}])
                st.markdown(resp.choices[0].message.content)
    
    with tab_viz:
        viz_code = st.text_area("Kod za dijagram:", height=150)
        if st.button("🎨 Crtaj"):
            if api_key and viz_code:
                client = Groq(api_key=api_key)
                viz_p = f"Pretvori u DOT kod. Samo kod u ```dot```.\n{viz_code}"
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":viz_p}])
                match = re.search(r'```dot(.*?)```', resp.choices[0].message.content, re.DOTALL)
                if match: st.graphviz_chart(match.group(1).strip())

    with tab_znanje:
        topic = st.text_input("Tema za lekciju:", placeholder="npr. While petlja...")
        if st.button("Napiši lekciju") and api_key and topic:
            client = Groq(api_key=api_key)
            with st.spinner("Pišem..."):
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=[{"role":"system","content":system_prompt},{"role":"user","content":f"Napiši lekciju o: {topic}"}])
                st.markdown(resp.choices[0].message.content)

# DESNA KOLONA: CHAT
with col_chat:
    st.markdown("### 💬 Mentor")
    chat_box = st.container(height=550)
    with chat_box:
        for msg in st.session_state.messages:
            role_class = "bot-msg" if msg["role"]=="assistant" else "user-msg"
            st.markdown(f'<div class="chat-msg {role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
            
    st.markdown("---")
    c_in = st.text_area("Chat:", height=80, label_visibility="collapsed", placeholder="Pitaj profesora...")
    if st.button("Pošalji"):
        if api_key and c_in:
            st.session_state.messages.append({"role":"user", "content":c_in})
            client = Groq(api_key=api_key)
            with st.spinner("..."):
                full_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                resp = client.chat.completions.create(model=MODEL_NAZIV, messages=full_msgs)
                st.session_state.messages.append({"role":"assistant", "content":resp.choices[0].message.content})
            st.rerun()
