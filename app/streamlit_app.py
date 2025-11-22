import streamlit as st
import pandas as pd
import joblib
import os
import numpy as np
import datetime

st.set_page_config(
    page_title="Araba Fiyat Analizi",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

CURRENT_FILE_PATH = os.path.abspath(__file__)
APP_DIR = os.path.dirname(CURRENT_FILE_PATH)
PROJECT_ROOT = os.path.dirname(APP_DIR)

MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'catboost_model.pkl')
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'ilanlar_final.csv')
CURRENT_YEAR = datetime.date.today().year


@st.cache_resource
def load_models():
    m_main = joblib.load(os.path.join(PROJECT_ROOT, 'models', "catboost_main.pkl"))
    m_low = joblib.load(os.path.join(PROJECT_ROOT, 'models', "catboost_low.pkl"))
    m_high = joblib.load(os.path.join(PROJECT_ROOT, 'models', "catboost_high.pkl"))
    return m_main, m_low, m_high


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False)
    cat_cols = ['Marka', 'Seri', 'Model', 'Vites Tipi', 'Yakıt Tipi', 'Kasa Tipi', 'Renk', 'Kimden', 'Çekiş']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df = df[df[col] != 'nan']
    return df


try:
    model_main, model_low, model_high = load_models()
    df = load_data()
except Exception as e:
    st.error(f"Yükleme Hatası: {e}")
    st.stop()


with st.sidebar:
    st.title("📊 Veri Seti Durumu")

    try:
        file_time = os.path.getmtime(DATA_PATH)
        last_update = datetime.datetime.fromtimestamp(file_time).strftime("%d.%m.%Y")
    except:
        last_update = "Bilinmiyor"

    st.metric(label="Eğitimde Kullanılan Veri", value=f"{len(df):,}")
    st.metric(label="Son Güncelleme", value=last_update)

    st.divider()

    st.info(f"""
    **Proje Künyesi:**
    * **Model:** CatBoost Regressor
    * **Taranan İlan Sayısı:** 45.000+
    * **Temizlenmiş Veri:** {len(df):,} adet

    **Açıklama:**
    45.000'den fazla ham veri toplanmış, aykırı değerler (outliers) ve hatalı girişler temizlenerek **{len(df):,}** adet yüksek kaliteli veri ile model eğitilmiştir.
    
    **Geliştirici:**
    Bu proje eğitim ve portfolyo amaçlı hazırlanmıştır.
    """)

    st.caption(f"vFinal | © {CURRENT_YEAR}")


def prepare_input(df_input, model):
    df_proc = df_input.copy()

    if 'Boyalı Parçalar' in df_proc.columns and df_proc['Boyalı Parçalar'].dtype == 'object':
        def count_parts(text):
            if pd.isna(text) or str(text) in ['Yok', 'Belirtilmemiş', 'Orijinal', 'Tamamı orjinal', 'Hatasız',
                                              'nan']: return 0
            return len(str(text).split(','))

        def check_part(text, part):
            if pd.isna(text): return 0
            return 1 if part.lower() in str(text).lower() else 0

        df_proc['Boyali_Sayisi'] = df_proc['Boyalı Parçalar'].apply(count_parts) + df_proc[
            'Lokal Boyalı Parçalar'].apply(count_parts)
        df_proc['Degisen_Sayisi'] = df_proc['Değişen Parçalar'].apply(count_parts)

        df_proc['Kaput_Degisen'] = df_proc['Değişen Parçalar'].apply(lambda x: check_part(x, 'kaput'))
        df_proc['Tavan_Boyali'] = df_proc['Boyalı Parçalar'].apply(lambda x: check_part(x, 'tavan'))

    if 'Yıl' in df_proc.columns:
        df_proc['Yas'] = CURRENT_YEAR - df_proc['Yıl']
        df_proc['Yas'] = df_proc['Yas'].replace(0, 1)

    if 'Kilometre' in df_proc.columns and 'Yas' in df_proc.columns:
        df_proc['Yillik_KM'] = df_proc['Kilometre'] / df_proc['Yas']

    if 'Boyali_Sayisi' in df_proc.columns and 'Degisen_Sayisi' in df_proc.columns:
        df_proc['Hasar_Skoru'] = (df_proc['Boyali_Sayisi'] * 1) + (df_proc['Degisen_Sayisi'] * 2)

    for col in ['Motor Hacmi', 'Motor Gücü', 'Yakıt Deposu', 'Ort. Yakıt Tüketimi']:
        if col in df_proc.columns and df_proc[col].dtype == 'object':
            df_proc[col] = pd.to_numeric(
                df_proc[col].astype(str).str.replace(' cc', '').str.replace(' hp', '').str.replace(' lt',
                                                                                                   '').str.replace('.',
                                                                                                                   '').str.replace(
                    ',', '.'), errors='coerce').fillna(0).astype(int)

    if 'Tramer' in df_proc.columns and df_proc['Tramer'].dtype == 'object':
        df_proc['Tramer'] = pd.to_numeric(df_proc['Tramer'].astype(str).str.replace(' TL', '').str.replace('.', ''),
                                          errors='coerce').fillna(0).astype(int)

    model_cols = model.feature_names_
    for col in model_cols:
        if col not in df_proc.columns:
            if col in ['Marka', 'Seri', 'Model', 'Renk', 'Kimden', 'Vites Tipi', 'Yakıt Tipi', 'Kasa Tipi', 'Çekiş']:
                df_proc[col] = "Bilinmiyor"
            else:
                df_proc[col] = 0

    return df_proc[model_cols]


st.title("🚗 Yapay Zeka Araba Değerleme")

tab1, tab2 = st.tabs(["💰 Fiyat Hesapla", "🕵️‍♂️ Fırsat Bul"])

with tab1:
    c1, c2 = st.columns([1, 1.2], gap="large")

    with c1:
        st.subheader("Araç Özellikleri")
        markalar = sorted(df['Marka'].unique())
        s_marka = st.selectbox("Marka", markalar)

        seriler = sorted(df[df['Marka'] == s_marka]['Seri'].unique())
        s_seri = st.selectbox("Seri", seriler)

        modeller = sorted(df[(df['Marka'] == s_marka) & (df['Seri'] == s_seri)]['Model'].unique())
        s_model = st.selectbox("Model", modeller)

        col_y, col_k = st.columns(2)
        yil = col_y.number_input("Yıl", 1990, CURRENT_YEAR, 2020)
        km = col_k.number_input("Kilometre", min_value=0, max_value=1000000, value=50000, step=5000)

        col_v, col_ykt = st.columns(2)
        vites = col_v.selectbox("Vites Tipi", sorted(df['Vites Tipi'].unique()))
        yakit = col_ykt.selectbox("Yakıt Tipi", sorted(df['Yakıt Tipi'].unique()))

    with c2:
        st.subheader("Ekspertiz Durumu")

        chk1, chk2 = st.columns(2)
        kaput_degisen = chk1.checkbox("Kaput Değişen")
        kaput_boyali = chk2.checkbox("Kaput Boyalı")

        chk3, chk4 = st.columns(2)
        tavan_boyali = chk3.checkbox("Tavan Boyalı")

        agir_hasar = chk4.checkbox("⚠️ Ağır Hasar / Pert Kaydı")

        st.markdown("---")

        diger_boyali = st.slider("Diğer Boyalı Parça Sayısı", 0, 10, 0)
        diger_degisen = st.slider("Diğer Değişen Parça Sayısı", 0, 10, 0)

        tramer = st.number_input("Tramer Kaydı (TL)", 0, 5000000, 0, step=1000)

        st.divider()
        hesapla = st.button("Fiyatı Hesapla 🔮", use_container_width=True, type="primary")

    if hesapla:
        ref = df[df['Model'] == s_model].iloc[0] if not df[df['Model'] == s_model].empty else df.iloc[0]

        toplam_boyali = diger_boyali + (1 if kaput_boyali else 0) + (1 if tavan_boyali else 0)
        toplam_degisen = diger_degisen + (1 if kaput_degisen else 0)

        input_data = pd.DataFrame({
            'Marka': [s_marka], 'Seri': [s_seri], 'Model': [s_model],
            'Yıl': [yil], 'Kilometre': [km], 'Vites Tipi': [vites], 'Yakıt Tipi': [yakit],
            'Kasa Tipi': [ref['Kasa Tipi']], 'Motor Hacmi': [ref['Motor Hacmi']],
            'Motor Gücü': [ref['Motor Gücü']], 'Çekiş': [ref['Çekiş']],
            'Renk': [ref['Renk']], 'Kimden': ['Sahibinden'],
            'Boyali_Sayisi': [toplam_boyali],
            'Degisen_Sayisi': [toplam_degisen],
            'Tramer': [tramer],
            'Kaput_Degisen': [1 if kaput_degisen else 0],
            'Tavan_Boyali': [1 if tavan_boyali else 0]
        })

        processed_input = prepare_input(input_data, model_main)

        try:
            pred_main = np.expm1(model_main.predict(processed_input)[0])
            pred_low = np.expm1(model_low.predict(processed_input)[0])
            pred_high = np.expm1(model_high.predict(processed_input)[0])

            if agir_hasar:
                factor = 0.70  # %30 indirim
                pred_main *= factor
                pred_low *= factor
                pred_high *= factor
                st.warning("⚠️ Araç 'Ağır Hasarlı' olduğu için piyasa değerinden **%30** düşülmüştür.")

            st.markdown(f"<h2 style='text-align: center; color: #2ecc71;'>{int(pred_main):,} TL</h2>",
                        unsafe_allow_html=True)
            st.info(f"📊 Piyasa Aralığı: **{int(pred_low):,} TL** - **{int(pred_high):,} TL**")

        except Exception as e:
            st.error(f"Hata: {e}")

with tab2:
    with st.expander("Filtreler", expanded=True):
        col1, col2 = st.columns(2)
        f_butce = col1.number_input("Max Bütçe", value=1500000, step=50000)
        f_yil = col2.slider("Yıl Aralığı", 2000, CURRENT_YEAR, (2015, CURRENT_YEAR))
        f_marka = st.selectbox("Marka Filtresi", ["Tümü"] + sorted(df['Marka'].unique()))

    if st.button("Fırsatları Tara"):
        with st.spinner("Piyasa taranıyor..."):
            f_df = df.copy()
            if f_marka != "Tümü": f_df = f_df[f_df['Marka'] == f_marka]
            f_df = f_df[(f_df['Fiyat'] <= f_butce) & (f_df['Yıl'] >= f_yil[0]) & (f_df['Yıl'] <= f_yil[1])]

            if len(f_df) > 0:
                processed_data = prepare_input(f_df, model_main)

                log_preds = model_main.predict(processed_data)
                f_df['AI_Tahmin'] = np.expm1(log_preds)

                f_df['Kazanç'] = f_df['AI_Tahmin'] - f_df['Fiyat']
                firsatlar = f_df[f_df['Kazanç'] > 20000].sort_values('Kazanç', ascending=False).head(50)

                if not firsatlar.empty:
                    st.success(f"{len(firsatlar)} adet fırsat bulundu!")
                    st.dataframe(
                        firsatlar[
                            ['Marka', 'Model', 'Yıl', 'Kilometre', 'Tramer', 'Fiyat', 'AI_Tahmin', 'Kazanç', 'Link']],
                        column_config={
                            "Link": st.column_config.LinkColumn("İlan", display_text="Git"),
                            "Fiyat": st.column_config.NumberColumn("Fiyat", format="%d TL"),
                            "AI_Tahmin": st.column_config.NumberColumn("Gerçek Değer", format="%d TL"),
                            "Kazanç": st.column_config.ProgressColumn("Potansiyel Kar", format="%d TL", min_value=0,
                                                                      max_value=int(firsatlar['Kazanç'].max()))
                        }, hide_index=True
                    )
                else:
                    st.info("Fırsat bulunamadı.")
            else:
                st.warning("İlan bulunamadı.")