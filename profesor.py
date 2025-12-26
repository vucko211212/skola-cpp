import streamlit as st
from openai import OpenAI

# --- KONFIGURACIJA STRANICE ---
st.set_page_config(
    page_title="C++ Vežbaonica - Specijalno IT odeljenje",
    page_icon="💻",
    layout="wide"
)

# --- CSS STILOVI (Tamna tema i lepši chat) ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stTextArea textarea {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #1e1e1e;
        color: #dcdcdc;
        border: 1px solid #4a4a4a;
    }
    .chat-msg {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        line-height: 1.5;
    }
    .user-msg {
        background-color: #2b3137;
        border-left: 4px solid #3b8ed0;
    }
    .bot-msg {
        background-color: #1c2329;
        border-left: 4px solid #28a745;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA ZA API KLJUČ (SIGURNOST) ---
api_key = None

# 1. Provera da li je ključ u tajnim podešavanjima (za Web)
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
# 2. Ako nije, traži ga ručno (za lokalno testiranje)
else:
    with st.sidebar:
        api_key = st.text_input("🔑 API Ključ (Nije podešen u Secrets):", type="password")
        if not api_key:
            st.warning("⚠️ Da bi aplikacija radila, potreban je API ključ.")

# --- INICIJALIZACIJA CHATA I PROFESORA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # SISTEMSKI PROMPT - OVDE DEFINIŠEMO PONAŠANJE PROFESORA
    st.session_state.messages.append({
        "role": "system", 
        "content": """
        Ti si iskusni profesor informatike u gimnaziji (specijalno IT odeljenje).
        Predaješ predmet "Programiranje" (C++) učenicima prvog razreda.
        
        TVOJ PEDAGOŠKI PRISTUP:
        1. SOKRATOVSKI METOD: Nikada ne piši ceo tačan kod odmah. Umesto toga, postavljaj pitanja koja navode učenika da sam uoči grešku.
        2. TEME PRVOG RAZREDA: Fokusiraj se isključivo na:
           - Tipove podataka (int, float, char, bool)
           - Ulaz/izlaz (cin, cout, iomanip)
           - Grananja (if, else if, switch)
           - Petlje (for, while, do-while)
           - Jednodimenzionalne nizove
           - Osnovne algoritme (minimum, maksimum, suma, pretraga).
           - NE KORISTI: Vektore, klase, pokazivače (osim ako učenik eksplicitno ne pita za napredno).
        3. DETEKCIJA GREŠAKA: Ako kod ima sintaksnu grešku, objasni je laički. Ako je logika pogrešna, daj primer inputa za koji kod pada.
        4. TON: Budi strog ali pravičan i ohrabrujući. Govori na srpskom jeziku.
        5. FORMATIRANJE: Koristi Markdown za kod.
        """
    })

# --- UI INTERFEJS ---

st.title("💻 Vežbaonica za Programiranje (C++)")
st.caption("Virtuelni asistent za učenike specijalizovanih IT odeljenja")

col_editor, col_chat = st.columns([1.2, 1])

with col_editor:
    st.subheader("Tvoj kod")
    # Default kod koji se pojavljuje
    default_code = """#include <iostream>
using namespace std;

int main() {
    // Ovde napiši svoj kod
    
    return 0;
}"""
    student_code = st.text_area("C++ Editor", height=450, value=default_code, key="editor")
    
    st.subheader("Pitanje za profesora")
    student_question = st.text_input("Šta želiš da pitaš?", placeholder="Npr: Zašto mi ne radi petlja?")
    
    btn_check = st.button("🚀 Pošalji na pregled", type="primary")

with col_chat:
    st.subheader("Razgovor sa profesorom")
    chat_container = st.container(height=550)

    # Prikaz istorije
    with chat_container:
        if len(st.session_state.messages) == 1:
            st.info("Zdravo! Ja sam tvoj virtuelni profesor. Zalepi svoj zadatak ili napiši kod, pa da vidimo kako ti ide.")
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-msg user-msg"><b>Učenik:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f'<div class="chat-msg bot-msg"><b>Profesor:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

# --- LOGIKA SLANJA ---
if btn_check:
    if not api_key:
        st.error("Nedostaje API ključ! Zamoli administratora da podesi 'Secrets'.")
    else:
        # Formiramo prompt koji šaljemo AI-u
        full_prompt = f"Ovo je moj C++ kod:\n```cpp\n{student_code}\n```\n\nMoje pitanje/komentar: {student_question}"
        
        # Dodajemo u istoriju (prikazujemo u chatu)
        st.session_state.messages.append({"role": "user", "content": full_prompt})
        
        client = OpenAI(api_key=api_key)
        
        with st.spinner("Profesor pregleda tvoj rad..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", # Preporuka za najbolju logiku
                    messages=st.session_state.messages,
                    temperature=0.5 # Malo manja kreativnost za preciznije objašnjenje
                )
                
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                st.rerun() # Osvežavamo stranicu da se vidi odgovor
                
            except Exception as e:
                st.error(f"Greška u komunikaciji: {e}")