import streamlit as st
from openai import OpenAI

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
    .bot-msg { background-color: #1c2329; border-left: 4px solid #28a745; }
    /* Stil za tabove */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1c2329; border-radius: 5px 5px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #28a745; color: white; }
</style>
""", unsafe_allow_html=True)

# --- API KLJUČ ---
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("🔑 API Ključ:", type="password")

# --- INICIJALIZACIJA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # --- SISTEMSKI PROMPT (MOZAK PROFESORA) ---
    st.session_state.messages.append({
        "role": "system", 
        "content": """
        Ti si iskusni i metodični profesor informatike u specijalizovanom IT odeljenju gimnazije. Predaješ C++.
        
        KADA UČENIK PITA TEORIJSKO PITANJE (npr. "Kako da sortiram niz?", "Šta je for petlja?"):
        1. NE DAJ SAMO KOD. Daj strukturirano objašnjenje.
        2. STRUKTURA ODGOVORA:
           - **Koncept (Logika):** Objasni rečima šta radimo (npr. "Zamisli da ređaš karte...").
           - **Postupak:** Taksativno navedi korake algoritma.
           - **Primer koda:** Kratak, jasan C++ primer (koristi Markdown).
           - **Objašnjenje koda:** Šta radi koja linija.
           - **Savet/Trik:** Neka česta greška ili "best practice".
        
        KADA UČENIK POŠALJE SVOJ KOD NA PREGLED:
        1. Koristi Sokratovski metod. Ne ispravljaj odmah, nego postavi pitanje koje ukazuje na grešku.
        2. Ako je kod dobar, pohvali ga i predloži malu optimizaciju.
        
        Opšta pravila:
        - Budi strpljiv i ohrabrujući.
        - Fokus na gradivo 1. razreda (nema pointera, klasa, vektora osim ako se ne traži).
        - Koristi srpski jezik.
        """
    })

st.title("💻 Virtuelni Profesor Programiranja")

# --- UI STRUKTURA ---
# Delimo ekran na levi deo (Interakcija) i desni deo (Chat)
col_input, col_chat = st.columns([1.1, 1])

with col_input:
    # --- TABOVI ---
    tab_code, tab_ask = st.tabs(["📝 Piši Kod (Vežbanje)", "❓ Pitaj Profesora (Teorija)"])
    
    # --- TAB 1: EDITOR KODA ---
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

    # --- TAB 2: TEORIJSKA PITANJA ---
    with tab_ask:
        st.caption("Ovde možeš pitati bilo šta što ti nije jasno, bez pisanja koda.")
        theory_question = st.text_area("Tvoje pitanje:", height=150, placeholder="Npr: Kako da napravim program koji sortira brojeve? Nije mi jasna while petlja...")
        st.info("💡 Savet: Pitaj za primere, objašnjenja postupaka ili kako funkcionišu određene naredbe.")
        btn_ask = st.button("🙋 Postavi pitanje")

# --- LOGIKA SLANJA ---
prompt_to_send = None

# Ako je kliknuto dugme u prvom tabu
if btn_analyze and api_key:
    prompt_to_send = f"Analiziraj moj kod:\n```cpp\n{student_code}\n```\nPitanje uz kod: {code_question}"

# Ako je kliknuto dugme u drugom tabu
if btn_ask and api_key and theory_question:
    prompt_to_send = theory_question

# --- OBRADA I PRIKAZ CHATA ---
with col_chat:
    st.subheader("Razgovor")
    chat_container = st.container(height=600)
    
    # Slanje zahteva AI-u
    if prompt_to_send:
        # Dodajemo korisnikovu poruku
        st.session_state.messages.append({"role": "user", "content": prompt_to_send})
        
        client = OpenAI(api_key=api_key)
        
        try:
            with st.spinner("Profesor kuca odgovor..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages,
                    temperature=0.5
                )
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.error(f"Došlo je do greške: {e}")

    # Prikaz istorije poruka
    with chat_container:
        if len(st.session_state.messages) == 1:
            st.markdown('<div class="chat-msg bot-msg"><b>Profesor:</b><br>Zdravo! Izaberi tab levo: "Piši Kod" ako vežbaš zadatke, ili "Pitaj Profesora" ako ti treba objašnjenje lekcije.</div>', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                # Skraćujemo prikaz ako je korisnik poslao ogroman kod, da ne guši chat
                display_text = msg["content"]
                if "Analiziraj moj kod" in display_text:
                    display_text = "📝 <i>Poslao sam kod na pregled...</i>"
                st.markdown(f'<div class="chat-msg user-msg"><b>Učenik:</b><br>{display_text}</div>', unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
