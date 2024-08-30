import streamlit as st
import sqlite3
import time
import os
import google.generativeai as genai

# Ortam değişkeninden API anahtarını ayarlayın
os.environ['GEMINI_API_KEY'] = 'AIzaSyA1-uLTtQ4YRhZpDfrC82LMp0S23nT_K34'  # <-- Kendi API anahtarınızı buraya ekleyin
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Modeli başlat
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Tek seferlik veritabanı bağlantısı
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Veritabanına bağlan ve tabloyu oluştur
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (question TEXT PRIMARY KEY, response TEXT)''')
    conn.commit()

# Veritabanına soru-cevap çifti ekle
def insert_into_db(question, response):
    c.execute("INSERT OR IGNORE INTO chat_history (question, response) VALUES (?, ?)", (question, response))
    conn.commit()

# Veritabanından cevabı getir
def get_response_from_db(question):
    c.execute("SELECT response FROM chat_history WHERE question = ?", (question,))
    result = c.fetchone()
    return result[0] if result else None

# Veritabanını başlat
init_db()

st.title("💬 AVD Consultancy & Bogazici University")

# Avd için özel prompt
avd_prompt = """
Bir KPI hesaplama asistanısın. Sana sorulan şirket için kpi değeri hesaplayıp matplotlib kütüphanesinden grafik oluşturma metodu kullanarak çalıştırıp chat ekranında göstermelisin. AVD Danışmanlık ve Boğaziçi Üniversitesi bünyesinde satj yapan 6 öğrencinin bitirme projesisin.
"""

# Oturum durumunu kontrol et
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Size nasıl yardımcı olabilirim?"}]

# Önceki mesajları göster
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="🧑‍💻").write(msg["content"])
    else:
        st.chat_message(msg["role"], avatar="🤖").write(msg["content"])

# Yanıt oluşturma fonksiyonu
def generate_response(prompt):
    try:
        # Metin üretme
        response = model.generate_content([
            avd_prompt,
            f"input: {prompt}",
            "output: | |"
        ])
        return response.text  # Yanıtın sadece metin kısmını döndür
    except Exception as e:
        return f'API Hatası: {e}'

# Yanıtı yavaş yavaş yazdırma fonksiyonu
def type_text(response_text, delay=0.05):
    placeholder = st.empty()
    for i in range(len(response_text) + 1):
        placeholder.write(response_text[:i])
        time.sleep(delay)

# Kullanıcıdan girdi alma ve işleme
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🧑‍💻").write(prompt)
    
    # "..." ile bekletme etkisi
    placeholder = st.chat_message("assistant", avatar="🕷")
    time.sleep(0.5)  # Bekleme süresi
    
    # Veritabanından cevabı almayı dene
    response = get_response_from_db(prompt)
    
    # Eğer veritabanında cevap yoksa, modeli kullan
    if response is None:
        response = generate_response(prompt)
        insert_into_db(prompt, response)  # Cevabı veritabanına kaydet
    
    # "..." yerine yanıtı yavaş yavaş yazdırma
    placeholder.empty()
    type_text(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
