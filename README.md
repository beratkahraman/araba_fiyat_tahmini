# 🚗 Yapay Zeka Destekli 2. El Araba Fiyat Tahmini ve Fırsat Analizi

Bu proje, Türkiye 2. el otomobil piyasasını analiz ederek araçların adil piyasa değerini hesaplayan ve piyasa değerinin altında satılan "fırsat araçlarını" tespit eden uçtan uca (End-to-End) bir Veri Bilimi uygulamasıdır.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![CatBoost](https://img.shields.io/badge/ML-CatBoost-green)

## 🎯 Projenin Özellikleri

* **🕷️ Veri Toplama:** `Selenium` ve `BeautifulSoup` kullanılarak 45.000'den fazla gerçek araç ilanı toplanmıştır.
* **🧹 Veri Temizleme:** Eksik veriler, hatalı girişler ve aykırı değerler (Outliers) istatistiksel yöntemlerle temizlenmiştir.
* **🧠 Yapay Zeka Modeli:** Kategorik verilerle yüksek performans gösteren **CatBoost** algoritması kullanılmıştır. Model, **%79 R² (Başarı Skoru)** ve **~230.000 TL Ortalama Hata Payı (MAE)** ile çalışmaktadır.
* **📊 Arayüz (Web UI):** `Streamlit` ile geliştirilen kullanıcı dostu arayüz sayesinde:
    * Kullanıcılar araç özelliklerini girerek tahmini fiyatı öğrenebilir.
    * "Ağır Hasar" gibi durumlar manuel olarak fiyata yansıtılır.
    * **Fırsat Avcısı** modülü ile binlerce ilan arasından en karlı olanlar listelenir.

## 🛠️ Kullanılan Teknolojiler

* **Diller & Kütüphaneler:** Python, Pandas, NumPy, Scikit-Learn
* **Scraping:** Selenium (Undetected-Chromedriver), BeautifulSoup4
* **Model:** CatBoost Regressor (GridSearch ile optimize edildi)
* **Arayüz:** Streamlit
* **Görselleştirme:** Matplotlib, SHAP (Model açıklanabilirliği için denemeler yapıldı)

## 🚀 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için adımları izleyin:

1.  **Projeyi klonlayın:**
    ```bash
    git clone [https://github.com/beratkahraman/araba-fiyat-tahmini.git](https://github.com/beratkahraman/araba-fiyat-tahmini.git)
    cd araba-fiyat-tahmini
    ```

2.  **Gerekli kütüphaneleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Uygulamayı başlatın:**
    ```bash
    streamlit run app/streamlit_app.py
    ```

## 📂 Proje Yapısı

```text
araba_fiyat_tahmini/
├── data/                   # Veri setleri (Ham ve İşlenmiş)
├── src/                    # Veri toplama (Scraping) kodları
├── notebooks/              # Model eğitimi ve analiz (Jupyter Notebook)
├── models/                 # Eğitilmiş CatBoost modelleri (.pkl)
├── app/                    # Streamlit arayüz kodları
├── chromedriver.exe        # Selenium sürücüsü
└── requirements.txt        # Kütüphane listesi
