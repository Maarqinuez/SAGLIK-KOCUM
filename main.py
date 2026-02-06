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
    st.warning("👉 Lütfen önce sol menüden API anahtarını gir.")
    st.stop()

# --- GEMINI AYARLARI ---
genai.configure(api_key=api_key)

# --- MODEL SEÇİM MEKANİZMASI (ZIRHLI SİSTEM) ---
active_model = None
audio_active = False # Ses duyabilir mi?

try:
    # Önce Flash'ı dene (En iyisi bu)
    active_model = genai.GenerativeModel('gemini-1.5-flash')
    # Test atışı yapalım, gerçekten çalışıyor mu?
    active_model.generate_content("test")
    audio_active = True # Flash çalıştıysa sesi aç
except:
    # Flash patlarsa buraya düşer, ASLA ÇÖKMEZ
    try:
        # B Planı: Eski Gemini Pro'yu devreye al
        active_model = genai.GenerativeModel('gemini-pro')
        audio_active = False # Eski model sesi duyamaz
        st.info("ℹ️ Sunucu yoğunluğu nedeniyle 'Yazılı Mod' (Gemini Pro) devreye girdi.")
    except Exception as e:
        st.error(f"Kritik Hata: Hiçbir model çalıştırılamadı. API anahtarını kontrol et. Hata: {e}")
        st.stop()

# --- SES MOTORU (Nesrin Hanım) ---
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
        st.write("Selam! Ben Sağlık Koçun. Neyin var anlat bakalım?")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞLER ---
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")
user_input_text = None
user_audio_bytes = None

audio_value = st.audio_input("Mikrofonuna bas ve konuş")

# Ses işleme
if audio_value:
    if audio_active:
        user_audio_bytes = audio_value.read()
        user_input_text = "Sesli Mesaj"
    else:
        st.warning("⚠️ Şu an yedek moddasın. Sesini duyamıyorum, lütfen yazarak sor.")

chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input_text = chat_input
    user_audio_bytes = None

# --- CEVAP ---
if user_input_text:
    # Kullanıcı mesajını göster
    disp_text = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": disp_text})
    with st.chat_message("user"):
        st.write(disp_text)

    with st.chat_message("assistant"):
        with st.spinner("Analiz ediyorum..."):
            try:
                # --- ALİ EMİN CAN KURALLARI ---
                system_instruction = """
                Senin adın 'SAĞLIK KOÇUM'. 
                ÖZEL KURAL: "Seni kim tasarladı?" derlerse "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.

                TARZIN:
                1. Çok samimi, içten, kanka gibi konuş.
                2. Kısa ve net ol.

                GÖREVLERİN:
                1. TEŞHİS: Belirtilere bak ve en olası sebebi net söyle. "Galiba" deme.
                2. İLAÇ: Ne işe yaradığını ve yan etkisini söyle.
                3. DİYET: Kilo vermek isteyene samimi davran, diyetisyen gibi liste yap.
                """
                
                full_prompt = system_instruction
                if chat_input: full_prompt += "\n\nSoru: " + chat_input
                else: full_prompt += "\n\nBu ses kaydını dinle ve cevapla."

                # Cevabı al
                if user_audio_bytes and audio_active:
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
                # Eğer yine 429 hatası (Limit) verirse kullanıcıya net söyle
                if "429" in str(e):
                    st.error("Çok hızlı soru sordun, Google biraz bekle diyor. 10 saniye sonra tekrar dene.")
                else:
                    st.error(f"Bir hata oluştu: {e}")
