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
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ ---
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")

# --- SIDEBAR: PODEŠAVANJA ČASA ---
with st.sidebar:
    st.header("🏫 Podešavanje časa")
    razred = st.radio("Izaberi razred:", ["I Razred", "II Razred"])
    
    if razred == "I Razred":
        tema = st.selectbox("Oblast vežbanja:", 
            ["Osnove (Tipovi, Ulaz/Izlaz)", "Grananja (if/switch)", "Petlje (for/while)", "Nizovi (1D)", "Brojni sistemi"])
    else:
        tema = st.selectbox("Oblast vežbanja:", 
            ["Matrice (2D Nizovi)", "Stringovi", "Sortiranje i Pretraga", "Funkcije", "Rekurzija", "Strukture"])
    
    tezina = st.select_slider("Težina zadatka:", options=["Lak (Za dvojku)", "Srednji (Standardan)", "Takmičarski (Spec. IT)"])

# --- INICIJALIZACIJA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task" not in st.session_state:
    st.session_state.current_task = ""

# --- SISTEMSKI PROMPT (PEDAGOGIJA ZA SPEC. ODELJENJA) ---
system_prompt = f"""
Ti si strogi ali pravičan profesor u gimnaziji "Bora Stanković" (Niš), smer za učenike sa posebnim sposobnostima za informatiku.
Trenutno radiš sa učenikom {razred}-og razreda. Tema je: {tema}. Težina: {tezina}.

TVOJA METODOLOGIJA (SPEC. IT STANDARD):
1. **Insistiraj na optimizaciji:** Ako je zadatak "Takmičarski", nije dovoljno da kod radi. Mora biti efikasan (npr. izbegavati nepotrebne petlje).
2. **Rubni slučajevi (Edge cases):** Uvek pitaj "Šta ako je unet negativan broj?", "Šta ako je niz prazan?". Na to se u ovom smeru gube poeni.
3. **Stil:** Traži da kod bude čitak, promenljive smisleno imenovane.
4. **Gradivo II razreda:** Ako je tema Matrice, insistiraj na pravilnom indeksiranju. Ako je Sortiranje, pitaj za Bubble vs Selection sort.
5. **Jezik:** Srpski. Kod piši u C++.

KADA GENERIŠEŠ ZADATAK:
Daj jasan tekst zadatka, primer ulaza i primer izlaza (kao na Petlji ili BubbleBee).
"""

# Ako je lista prazna ili se promenio razred/tema, ažuriraj system prompt
if not st.session_state.messages or st.session_state.messages[0]["content"] != system_prompt:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

st.title(f"🎓 Profesor C++ ({razred})")
st.caption(f"Fokus: {tema} | Nivo: {tezina}")

# --- GLAVNI INTERFEJS ---
col_left, col_right = st.columns([1, 1])

with col_left:
    # SEKCIJA ZA GENERISANJE ZADATKA
    st.markdown("### 1. Zadatak")
    if st.button("🎲 Zadaj mi novi zadatak"):
        if api_key:
            client = Groq(api_key=api_key)
            prompt_task = f"Daj mi jedan {tezina} zadatak iz oblasti {tema} za {razred}. Navedi Tekst zadatka, Primer Ulaza i Primer Izlaza. Ne piši rešenje."
            
            with st.spinner("Profesor smišlja zadatak..."):
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_task}])
                st.session_state.current_task = resp.choices[0].message.content
    
    if st.session_state.current_task:
        st.markdown(f'<div class="task-box">{st.session_state.current_task}</div>', unsafe_allow_html=True)
    else:
        st.info("Klikni na dugme iznad da dobiješ zadatak za vežbanje.")

    # SEKCIJA ZA KODIRANJE
    st.markdown("### 2. Tvoje rešenje")
    student_code = st.text_area("C++ Editor", height=300, value="#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}")
    
    student_question = st.text_input("Pitanje ili komentar (opciono):")
    btn_check = st.button("🚀 Predaj rešenje profesoru")

# --- LOGIKA ODGOVORA ---
with col_right:
    st.markdown("### 3. Analiza Profesora")
    chat_container = st.container(height=600)

    if btn_check and api_key:
        msg_content = f"Ovo je tekst zadatka koji radim:\n{st.session_state.current_task}\n\nOvo je moj kod:\n```cpp\n{student_code}\n```\n\n{student_question}"
        st.session_state.messages.append({"role": "user", "content": msg_content})
        
        client = Groq(api_key=api_key)
        with st.spinner("Profesor testira tvoj kod na rubnim slučajevima..."):
            try:
                resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages, temperature=0.4)
                bot_reply = resp.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                st.error(str(e))

    # Prikaz istorije
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                 st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "user" and "Ovo je tekst zadatka" not in msg["content"]: 
                # Prikazujemo user poruke samo ako nisu one ogromne sa kodom (radi preglednosti)
                st.markdown(f'<div class="chat-msg user-msg"><b>Učenik:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
