import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx

# Sayfa Ayarları
st.set_page_config(page_title="Ticari Sözleşme Asistanı", page_icon="⚖️", layout="wide")

st.title("⚖️ Ticari Mal Alım Satım Sözleşmesi Asistanı")
st.write("Sözleşme taslağınızı PDF veya Word olarak yükleyin, yapay zeka hukuki riskleri analiz etsin.")

# Şifre Çekme ve Model Ayarlama
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
except Exception as e:
    st.error("API Anahtarı bulunamadı. Lütfen Streamlit Secrets ayarlarınızı kontrol edin.")

# 1. DOSYA YÜKLEME ALANI
yuklenen_dosya = st.file_uploader("Sözleşme Dosyasını Yükleyin (PDF veya DOCX formatında)", type=["pdf", "docx"])

sozlesme_metni = ""

# 2. DOSYA OKUMA İŞLEMİ
if yuklenen_dosya is not None:
    if yuklenen_dosya.name.endswith('.pdf'):
        try:
            pdf_okuyucu = PyPDF2.PdfReader(yuklenen_dosya)
            for sayfa in pdf_okuyucu.pages:
                if sayfa.extract_text():
                    sozlesme_metni += sayfa.extract_text() + "\n"
            st.success("✅ PDF başarıyla okundu! Metni aşağıda inceleyebilir veya düzenleyebilirsiniz.")
        except Exception as e:
            st.error(f"PDF okuma hatası: {e}")
            
    elif yuklenen_dosya.name.endswith('.docx'):
        try:
            doc = docx.Document(yuklenen_dosya)
            for paragraf in doc.paragraphs:
                sozlesme_metni += paragraf.text + "\n"
            st.success("✅ Word dosyası başarıyla okundu! Metni aşağıda inceleyebilir veya düzenleyebilirsiniz.")
        except Exception as e:
            st.error(f"Word okuma hatası: {e}")

# 3. METİN KUTUSU (Hem fallback hem de okunan metni göstermek için)
# 'value' parametresine sozlesme_metni'ni veriyoruz ki dosya yüklendiğinde kutu otomatik dolsun.
guncel_metin = st.text_area("Sözleşme Metni (İsterseniz düzenleyebilir veya doğrudan buraya yapıştırabilirsiniz):", value=sozlesme_metni, height=300)

if st.button("Sözleşmeyi Hukuken Analiz Et"):
    if guncel_metin.strip():
        with st.spinner("Sözleşme maddeleri taranıyor, hukuki riskler ve mevzuat eşleştiriliyor..."):
            
            prompt = f"""
            Sen Türkiye'de görev yapan, İstanbul Barosuna kayıtlı uzman bir Ticaret Hukuku Avukatı ve İç Denetim/Risk Yönetimi uzmanısın.
            Aşağıdaki ticari mal alım satım sözleşmesi metnini incele. Sadece genel geçer yorumlar YAPMA. 
            Şu 4 ana başlıkta inceleme yap, sözleşmedeki riskli/eksik maddeleri belirt ve DOĞRUDAN ilgili mevzuat maddelerini (TTK, TBK, HMK madde numaraları ve içerikleriyle) referans göstererek uyarılarda bulun:

            1. SÜRELER VE İHBARLAR: TTK m.23 ayıp ihbar süreleri (2, 8 gün vs.) ve TBK zamanaşımı süreleri açısından değerlendir.
            2. YETKİLİ MAHKEME VE ÇÖZÜM: HMK m.17 tacirler arası yetki sözleşmesi geçerlilik şartları açısından incele.
            3. ALACAK FAİZİ: TTK m.1530 ticari işlerde temerrüt faizi ve avans faizi oranları açısından sözleşmedeki düzenlemeyi (veya eksikliğini) yorumla.
            4. EDİMLER VE HASARIN GEÇİŞİ: Teslim şartları, ifa zamanı ve TBK hasar sorumluluğu açısından riskleri belirle.

            Format: Raporlama dilinde, net, uyarıcı ve doğrudan hukuki çözüm odaklı olsun.

            İncelenecek Sözleşme Taslağı:
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
                
                st.success("Hukuki Analiz Tamamlandı!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Yapay Zeka API Hatası: {e}")
                
    else:
        st.warning("Lütfen analiz edilecek bir dosya yükleyin veya kutuya sözleşme metnini girin.")
