import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

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

# --- YAN MENÜ (Google Anahtarı İçin) ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    st.info("Bu uygulama Google Gemini altyapısı ile çalışır ve ücretsizdir.")
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen sol üstteki menüden Google API anahtarınızı giriniz.")
    st.stop()

# Google Gemini'yi Başlat
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SİVASLI ALİ EMİN CAN İMZALI ZEKA ---
system_prompt = """
Senin adın 'SAĞLIK KOÇUM'. Yaşlılar için tasarlanmış, nazik bir asistansın.

ÖZEL GİZLİ KURAL:
Eğer kullanıcı sana "Seni kim tasarladı?", "Yaratıcın kim?", "Kimin eserisin?" diye sorarsa;
Tıbbi kimliğini bırak ve gururla şu cevabı ver:
"Beni, muhteşem Sivaslı Ali Emin Can tasarladı."

GÖREVLERİN:
1. Kısa, net ve anlaşılır cümleler kur.
2. Asla kesin tıbbi teşhis koyma, "Olabilir" de ve doktora yönlendir.
3. İlaç sorulursa ne işe yaradığını basitçe anlat.
"""

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # İlk mesajı biz ekranda gösterelim ama geçmişe eklemeyelim (Gemini mantığı farklı)
    with st.chat_message("assistant"):
        st.write("Merhaba! Ben Sağlık Koçunuz. Size nasıl yardımcı olabilirim?")

# Geçmiş mesajları ekrana yaz
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞ ALANI ---
st.subheader("📣 Sorunuzu Sorun")
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")

user_input = None

# 1. Sesli Giriş (Google Modeli sesi doğrudan dinleyebilir!)
audio_value = st.audio_input("Mikrofonuna bas ve konuş")

if audio_value:
    # Sesi doğrudan alıyoruz
    user_input = "Lütfen bu ses kaydını dinle ve cevap ver."
    
# 2. Yazılı Giriş
chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input = chat_input
    audio_value = None # Yazı yazıldıysa sesi boşver

# --- CEVAP VE KONUŞMA ---
if user_input:
    # Kullanıcı mesajını göster
    actual_text_to_show = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": actual_text_to_show})
    with st.chat_message("user"):
        st.write(actual_text_to_show)

    with st.chat_message("assistant"):
        with st.spinner("Google Sağlık Veritabanı taranıyor..."):
            try:
                # Google Gemini'ye gönder (Ses varsa sesi, yoksa yazıyı)
                chat = model.start_chat(history=[])
                
                # Sisteme kim olduğunu hatırlatıyoruz
                full_prompt = system_prompt + "\n\nKullanıcı sorusu: " + str(user_input)

                if audio_value:
                    # Sesi okuyup Gemini'ye resim/dosya gibi gönderiyoruz
                    audio_data = audio_value.read()
                    response = model.generate_content([full_prompt, {"mime_type": "audio/wav", "data": audio_data}])
                else:
                    # Sadece yazı
                    response = model.generate_content(full_prompt)

                ai_response = response.text
                st.write(ai_response)
                
                # Sesi Hazırla (Ücretsiz gTTS kütüphanesi ile)
                tts = gTTS(text=ai_response, lang='tr')
                tts.save("cevap.mp3")
                st.audio("cevap.mp3", autoplay=True)

                # Hafızaya ekle
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
