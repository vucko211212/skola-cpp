import streamlit as st
from groq import Groq

# --- KONFIGURACIJA ---
st.set_page_config(
    page_title="C++ Vežbaonica - Specijalno IT odeljenje",
    page_icon="💻",
    layout="wide"
)

# --- CSS STILOVI ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stTextArea textarea { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #dcdcdc; }
    .chat-msg { padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6; }
    .user-msg { background-color: #2b3137; border-left: 4px solid #3b8ed0; }
    .bot-msg { background-color: #1c2329; border-left: 4px solid #f25a29; } /* Groq narandžasta boja */
    /* Stil za tabove */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1c2329; border-radius: 5px 5px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #f25a29; color: white; }
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ (GROQ) ---
api_key = None
# Tražimo GROQ_API_KEY u tajnama
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 Groq API Ključ:", type="password")

# --- INICIJALIZACIJA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # --- SISTEMSKI PROMPT ---
    st.session_state.messages.append({
        "role": "system", 
        "content": """
        Ti si iskusni i metodični profesor informatike u specijalizovanom IT odeljenju gimnazije. Predaješ C++.
        
        KADA UČENIK PITA TEORIJSKO PITANJE:
        1. NE DAJ SAMO KOD. Daj strukturirano objašnjenje.
        2. STRUKTURA: Koncept (Logika) -> Postupak -> Primer koda -> Objašnjenje.
        
        KADA UČENIK POŠALJE KOD:
        1. Koristi Sokratovski metod. Postavi pitanje koje ukazuje na grešku.
        2. Analiziraj logiku i sintaksu.
        
        Opšta pravila:
        - Budi strpljiv.
        - Fokus na gradivo 1. razreda (tipovi, if/else, petlje, nizovi).
        - Koristi srpski jezik.
        """
    })

st.title("💻 Virtuelni Profesor (Powered by Llama 3)")

# --- UI STRUKTURA ---
col_input, col_chat = st.columns([1.1, 1])

with col_input:
    tab_code, tab_ask = st.tabs(["📝 Piši Kod (Vežbanje)", "❓ Pitaj Profesora (Teorija)"])
    
    # --- TAB 1: EDITOR ---
    with tab_code:
        st.caption("Ovde vežbaš zadatke. Napiši kod i profesor će ga pregledati.")
        default_code = """#include <iostream>
using namespace std;

int main() {
    // Tvoj kod ovde
    return 0;
}"""
        student_code = st.text_area("Editor", height=400, value=default_code)
        code_question = st.text_input("Imaš li konkretno pitanje u vezi ovog koda?", placeholder="Npr: Gde sam pogrešio?")
        btn_analyze = st.button("🔍 Pregledaj moj kod")

    # --- TAB 2: TEORIJA ---
    with tab_ask:
        st.caption("Pitaj bilo šta bez pisanja koda.")
        theory_question = st.text_area("Tvoje pitanje:", height=150, placeholder="Npr: Kako radi for petlja?")
        btn_ask = st.button("🙋 Postavi pitanje")

# --- LOGIKA SLANJA ---
prompt_to_send = None

if btn_analyze and api_key:
    prompt_to_send = f"Analiziraj moj kod:\n```cpp\n{student_code}\n```\nPitanje uz kod: {code_question}"

if btn_ask and api_key and theory_question:
    prompt_to_send = theory_question

# --- KOMUNIKACIJA SA GROQ ---
with col_chat:
    st.subheader("Razgovor")
    chat_container = st.container(height=600)
    
    if prompt_to_send:
        st.session_state.messages.append({"role": "user", "content": prompt_to_send})
        
        # Inicijalizacija Groq klijenta
        client = Groq(api_key=api_key)
        
        try:
            with st.spinner("Profesor razmišlja..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Najnoviji i najpametniji besplatan model
                    messages=st.session_state.messages,
                    temperature=0.5
                )
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.error(f"Greška: {e}")

    # Prikaz istorije
    with chat_container:
        if len(st.session_state.messages) == 1:
            st.info("Zdravo! Ja sam tvoj AI profesor. Koristim brzi Llama 3 model.")
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                display_text = msg["content"]
                if "Analiziraj moj kod" in display_text:
                    display_text = "📝 *Poslao sam kod na pregled...*"
                st.markdown(f'<div class="chat-msg user-msg"><b>Učenik:</b><br>{display_text}</div>', unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
