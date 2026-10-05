import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import io
import os

# Sayfa Ayarları
st.set_page_config(page_title="Ticari Sözleşme Asistanı", page_icon="⚖️", layout="wide")

st.title("⚖️ Ticari Mal Alım Satım Sözleşmesi Asistanı")
st.write("Sözleşme taslağınızı yükleyin. Yapay zeka, sisteme gömülü güncel kanunlara (TTK, TBK, TMK, HMK) göre riskleri analiz etsin.")

# Şifre Çekme ve Model Ayarlama
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
except Exception as e:
    st.error("API Anahtarı bulunamadı. Lütfen Streamlit Secrets ayarlarınızı kontrol edin.")

# 1. MEVZUAT VERİTABANINI YÜKLEME (ÖNBELLEKLİ)
@st.cache_data(show_spinner=False)
def mevzuat_veritabanini_hazirla():
    mevzuat_metni = ""
    kanunlar = ["tbk.pdf", "ttk.pdf", "tmk.pdf", "hmk.pdf"]
    yuklenenler = []
    
    for kanun in kanunlar:
        if os.path.exists(kanun):
            try:
                okuyucu = PyPDF2.PdfReader(kanun)
                for sayfa in okuyucu.pages:
                    if sayfa.extract_text():
                        mevzuat_metni += sayfa.extract_text() + "\n"
                yuklenenler.append(kanun.upper().replace(".PDF", ""))
            except Exception:
                pass
    return mevzuat_metni, yuklenenler

with st.spinner("Arka planda hukuk kütüphanesi (Mevzuat) hafızaya alınıyor..."):
    sistem_mevzuati, yuklenen_kanunlar = mevzuat_veritabanini_hazirla()

if yuklenen_kanunlar:
    st.success(f"📚 Sisteme Entegre Edilen Mevzuat: {', '.join(yuklenen_kanunlar)}")
else:
    st.warning("⚠️ Sistemde yüklü kanun dosyası (tbk.pdf, ttk.pdf vs.) bulunamadı. Yapay zeka kendi dahili hafızasını kullanacak. Kanunları GitHub'a yüklerseniz sistem otomatik entegre edecektir.")

# Hafıza (Session State) Ayarı
if "analiz_raporu" not in st.session_state:
    st.session_state.analiz_raporu = None

# 2. DOSYA YÜKLEME ALANI
yuklenen_dosya = st.file_uploader("Sözleşme Dosyasını Yükleyin (PDF veya DOCX)", type=["pdf", "docx"])
sozlesme_metni = ""

if yuklenen_dosya is not None:
    if yuklenen_dosya.name.endswith('.pdf'):
        try:
            pdf_okuyucu = PyPDF2.PdfReader(yuklenen_dosya)
            for sayfa in pdf_okuyucu.pages:
                if sayfa.extract_text():
                    sozlesme_metni += sayfa.extract_text() + "\n"
        except Exception as e:
            st.error(f"PDF okuma hatası: {e}")
            
    elif yuklenen_dosya.name.endswith('.docx'):
        try:
            doc = docx.Document(yuklenen_dosya)
            for paragraf in doc.paragraphs:
                sozlesme_metni += paragraf.text + "\n"
        except Exception as e:
            st.error(f"Word okuma hatası: {e}")

guncel_metin = st.text_area("Sözleşme Metni:", value=sozlesme_metni, height=300)

# 3. ANALİZ BUTONU
if st.button("Sözleşmeyi Hukuken Analiz Et"):
    if guncel_metin.strip():
        with st.spinner("Güncel mevzuat taranıyor ve riskler hesaplanıyor..."):
            
            prompt = f"""
            Sen Türkiye'de görev yapan uzman bir Ticaret Hukuku Avukatı ve İç Denetim/Risk Yönetimi uzmanısın.
            
            GÖREV: Aşağıdaki sözleşmeyi incele. Kendi varsayımlarını değil, SADECE DİKKATE ALMAN İÇİN SANA VERİLEN AŞAĞIDAKİ GÜNCEL MEVZUAT METNİNİ baz alarak hukuki risk analizi yap.
            (Eğer güncel mevzuat metni boşsa kendi Türk Hukuku bilgini kullan).
            
            SİSTEME YÜKLENEN GÜNCEL MEVZUAT:
            {sistem_mevzuati[:150000]} # Optimizasyon için karakter sınırı
            
            LÜTFEN ÇIKTIYI SADECE AŞAĞIDAKİ GİBİ BİR MARKDOWN TABLOSU FORMATINDA VER.
            
            | İnceleme Konusu | Sözleşmedeki Mevcut Durum | Hukuki Risk Seviyesi | İlgili Mevzuat | Revizyon Önerisi ve Çözüm |
            | :--- | :--- | :--- | :--- | :--- |
            
            Tablonun altına, sözleşmenin genel risk durumunu özetleyen en fazla 3 cümlelik kısa bir "Yönetici Özeti" ekle.

            İNCELENECEK SÖZLEŞME TASLAĞI:
            {guncel_metin}
            """

            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=8192,
                    )
                )
                st.session_state.analiz_raporu = response.text
                
            except Exception as e:
                st.error(f"Yapay Zeka API Hatası: {e}")
                
    else:
        st.warning("Lütfen analiz edilecek bir dosya yükleyin veya kutuya sözleşme metnini girin.")

# 4. SONUÇ EKRANI VE İNDİRME BUTONU
if st.session_state.analiz_raporu:
    st.success("Hukuki Analiz Tamamlandı!")
    st.markdown(st.session_state.analiz_raporu)
    
    doc = docx.Document()
    doc.add_heading('Sözleşme Hukuki Risk Denetim Raporu', 0)
    doc.add_paragraph("Bu rapor, sisteme entegre güncel mevzuat veritabanı kullanılarak oluşturulmuştur.\n")
    doc.add_paragraph(st.session_state.analiz_raporu)
    
    bio = io.BytesIO()
    doc.save(bio)
    
    st.download_button(
        label="📄 Raporu Word (.docx) Olarak İndir",
        data=bio.getvalue(),
        file_name="sozlesme_risk_raporu.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
