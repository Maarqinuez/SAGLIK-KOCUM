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
st.markdown("<h3 style='text-align: center; color: #455A64;'>Kişisel Dijital Sağlık Asistanınız</h3>", unsafe_allow_html=True)
st.write("---")

# --- YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    st.success("**Ali Emin Can tarafından yapılmıştır.**")
    st.divider()
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen sol üstteki menüden Google API anahtarınızı giriniz.")
    st.stop()

# Google Gemini'yi Başlat
genai.configure(api_key=api_key)

# Model Seçimi (Garanti Çalışan)
selected_model_name = 'gemini-1.5-flash' # Öncelik Flash
try:
    # Eğer Flash yoksa Pro'ya geçecek basit kontrol
    test_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    selected_model_name = 'gemini-pro'

model = genai.GenerativeModel(selected_model_name)

# --- KALİTELİ SES FONKSİYONU (MICROSOFT EDGE TTS) ---
async def speak_text(text):
    # 'tr-TR-NesrinNeural' sesi ChatGPT kalitesinde, akıcı bir Türk kadın sesidir.
    communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
    await communicate.save("cevap.mp3")

# --- ZEKA AYARLARI ---
system_prompt = """
Senin adın 'SAĞLIK KOÇUM'. Yaşlılar için tasarlanmış, nazik bir asistansın.

ÖZEL GİZLİ KURAL:
Eğer kullanıcı sana "Seni kim tasarladı?", "Yaratıcın kim?" derse;
Tıbbi kimliğini bırak ve gururla: "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.

GÖREVLERİN:
1. Kısa, net ve anlaşılır cümleler kur samimi ve içtende ol bir arkadaşmış gibi aynı.
2. Tıbbi teşhisleri çok belirleyici ve nokta atışı olsun, "Olabilir,Belki,Galiba" deme Acilse doktora yönlendir.
3. İlaç sorulursa ne işe yaradığını anlat yan etkilerini.
4. Senden kilo vermek isteyenlere çok samimi ve yardımcı ol diyet listesini uzman bir diyetisyen gibi hazırla.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.chat_message("assistant"):
        st.write("Merhaba! Ben Sağlık Koçunuz. Size nasıl yardımcı olabilirim?")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞ ALANI ---
st.subheader("📣 Sorunuzu Sorun")
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")

user_input = None
audio_value = st.audio_input("Mikrofonuna bas ve konuş")

if audio_value:
    user_input = "Lütfen bu ses kaydını dinle ve cevap ver."
    
chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input = chat_input
    audio_value = None 

# --- CEVAP VE KONUŞMA ---
if user_input:
    # Ekrana yaz
    actual_text_to_show = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": actual_text_to_show})
    with st.chat_message("user"):
        st.write(actual_text_to_show)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum..."):
            try:
                chat = model.start_chat(history=[])
                full_prompt = system_prompt + "\n\nKullanıcı sorusu: " + str(user_input)

                # Cevabı Al
                response = model.generate_content(full_prompt)
                ai_response = response.text
                st.write(ai_response)
                
                # --- SESİ OLUŞTUR (YENİ SİSTEM) ---
                # Async fonksiyonu Streamlit içinde güvenle çalıştırma:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(speak_text(ai_response))
                
                # Sesi Çal
                st.audio("cevap.mp3", autoplay=True)
                # ----------------------------------

                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
