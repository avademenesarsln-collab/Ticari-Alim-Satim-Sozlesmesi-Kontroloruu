import streamlit as st
import google.generativeai as genai

# Sayfa Ayarları
st.set_page_config(page_title="Ticari Sözleşme Asistanı", page_icon="⚖️", layout="wide")

st.title("⚖️ Ticari Mal Alım Satım Sözleşmesi Asistanı")
st.write("Sözleşme taslağınızı aşağıya yapıştırın. Yapay zeka; süreler, yetki, faiz ve edimler açısından hukuki riskleri analiz edip ilgili mevzuatı önünüze getirsin.")

# Şifre Çekme ve Model Ayarlama (Günlük limiti geniş olan 3.5 sürümü)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
except Exception as e:
    st.error("API Anahtarı bulunamadı. Lütfen Streamlit Secrets ayarlarınızı kontrol edin.")

# Kullanıcıdan sözleşme metnini alacağımız geniş metin kutusu
sozlesme_metni = st.text_area("İncelenecek Sözleşme Metnini Buraya Yapıştırın:", height=300)

if st.button("Sözleşmeyi Hukuken Analiz Et"):
    if sozlesme_metni:
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
            {sozlesme_metni}
            """

            try:
                # Yaratıcılık sıfıra yakın (0.1), kanuna mutlak sadakat.
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=4096,
                    )
                )
                
                st.success("Hukuki Analiz Tamamlandı!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Yapay Zeka API Hatası: {e}")
                
    else:
        st.warning("Lütfen analiz edilecek sözleşme metnini kutuya yapıştırın.")
