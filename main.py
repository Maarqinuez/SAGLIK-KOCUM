import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK KOÇUM",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; color: #00796B;'>🩺 SAĞLIK KOÇUM</h1>", unsafe_allow_html=True)
st.write("---")

# --- YAN MENÜ ---
with st.sidebar:
    st.success("**Ali Emin Can tarafından yapılmıştır.**")
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen API anahtarını gir.")
    st.stop()

# --- GEMINI AYARLARI (AKILLI SEÇİM) ---
genai.configure(api_key=api_key)

# Önce en yeni modeli (Flash) deniyoruz, olmazsa eskiye (Pro) düşüyoruz.
active_model = None
can_hear_audio = False 

try:
    # 1. Deneme: Flash Modeli (Kulağı var, duyar)
    active_model = genai.GenerativeModel('gemini-1.5-flash')
    # Test edelim
    active_model.generate_content("test") 
    can_hear_audio = True
except:
    # 2. Deneme: Hata verirse Eski Pro Modeline geç
    active_model = genai.GenerativeModel('gemini-pro')
    can_hear_audio = False
    st.error("⚠️ Sistem eski sürümde çalışıyor (Sadece yazı yazabilirsin).")

# --- SES FONKSİYONU ---
async def speak_text(text):
    if not text: return
    try:
        communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
        await communicate.save("cevap.mp3")
    except:
        pass 

# --- ARAYÜZ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.chat_message("assistant"):
        st.write("Selam! Ben Sağlık Koçun. Neyin var anlat bakalım, hemen çözelim.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞLER ---
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")
user_input_text = None
user_audio_bytes = None

audio_value = st.audio_input("Mikrofonuna bas ve konuş")
if audio_value:
    if can_hear_audio:
        user_audio_bytes = audio_value.read()
        user_input_text = "Sesli Mesaj"
    else:
        st.warning("❌ Şu anki model sesi duyamıyor, lütfen yazarak sor.")

chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input_text = chat_input
    user_audio_bytes = None

# --- CEVAP ---
if user_input_text and (chat_input or (audio_value and can_hear_audio)):
    # Mesajı göster
    disp = chat_input if chat_input else "🎤 (Sesli Mesaj)"
    st.session_state.messages.append({"role": "user", "content": disp})
    with st.chat_message("user"):
        st.write(disp)

    with st.chat_message("assistant"):
        with st.spinner("İnceliyorum..."):
            try:
                # --- İŞTE SENİN İSTEDİĞİN ÖZEL GÖREVLER ---
                system_instruction = """
                Senin adın 'SAĞLIK KOÇUM'. 
                ÖZEL KURAL: "Seni kim tasarladı?" derlerse gururla "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.

                KİMLİK VE TON:
                1. Çok samimi, içten ve cana yakın bir arkadaş gibi konuş. Resmiyet yok.
                2. Kısa, net ve anlaşılır cümleler kur.

                GÖREVLERİN:
                1. TEŞHİS: Kullanıcı şikayetini söylediğinde, analizlerin çok net ve nokta atışı olsun. "Belki, galiba" gibi kaçamak laflar etme. Kendinden emin konuş. (Ama durum çok acil ve hayatiyse hemen doktora git de).
                2. İLAÇLAR: İlaç sorulursa ne işe yaradığını ve yan etkilerini net bir şekilde anlat.
                3. DİYET: Kilo vermek isteyenlere çok samimi davran, motive et. Onlara uzman bir diyetisyen gibi profesyonel ama uygulanabilir diyet listeleri hazırla.
                """
                
                full_prompt = system_instruction
                if chat_input: full_prompt += "\n\nSoru: " + chat_input
                else: full_prompt += "\n\nBu ses kaydını dinle ve cevapla."

                if user_audio_bytes and can_hear_audio:
                    response = active_model.generate_content([full_prompt, {"mime_type": "audio/wav", "data": user_audio_bytes}])
                else:
                    response = active_model.generate_content(full_prompt)
                
                ai_response = response.text
                st.write(ai_response)
                
                # Seslendir
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(speak_text(ai_response))
                st.audio("cevap.mp3", autoplay=True)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error(f"Beklenmedik bir hata: {e}")
