import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import math
from multiprocessing import Process

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

DATA_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'ilanlar_ham.csv')

# --- AYARLAR ---
CALISAN_SAYISI = 5
# ----------------

def get_price_worker(worker_id, subset_indices, all_data_file):
    """Her bir çalışanın (tarayıcının) yapacağı iş."""

    wait_time = worker_id * 5
    print(f"[Worker-{worker_id}] Hazırlanıyor... {wait_time} saniye bekleyip başlayacak.")
    time.sleep(wait_time)

    print(f"[Worker-{worker_id}] İş başı yapıyor! {len(subset_indices)} ilan tarayacak.")

    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Worker/{worker_id}')

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
    except Exception as e:
        print(f"[Worker-{worker_id}] Driver başlatılamadı! Hata: {e}")
        return

    try:
        df = pd.read_csv(all_data_file, on_bad_lines='skip', low_memory=False)
    except:
        if driver: driver.quit()
        return

    results = []
    save_interval = 50
    temp_file = f"temp_result_{worker_id}.csv"

    count = 0
    for idx in subset_indices:
        if idx >= len(df):
            continue

        link = df.at[idx, 'Link']
        found_price = None

        try:
            driver.set_page_load_timeout(20)
            driver.get(link)
            time.sleep(random.uniform(0.5, 1.5))

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            selectors = [
                ("div", "desktop-information-price"),
                ("div", "product-price"),
                ("span", "product-price-new"),
                ("span", "price"),
                ("div", "price-container")
            ]
            for tag, cls in selectors:
                elm = soup.find(tag, class_=cls)
                if elm:
                    txt = elm.text.strip()
                    if "TL" in txt or any(c.isdigit() for c in txt):
                        found_price = txt
                        break

            if not found_price:
                found_price = "Bulunamadı"

        except Exception:
            try:
                driver.quit()
                time.sleep(3)
                driver = uc.Chrome(options=options, use_subprocess=True)
            except:
                pass
            found_price = "Hata"

        results.append({'Index': idx, 'Fiyat': found_price})
        count += 1

        if count % save_interval == 0:
            pd.DataFrame(results).to_csv(temp_file, index=False)
            print(f"[Worker-{worker_id}] {count}/{len(subset_indices)} tamamlandı.")

    pd.DataFrame(results).to_csv(temp_file, index=False)
    if driver: driver.quit()
    print(f"[Worker-{worker_id}] GÖREV TAMAMLANDI. Dosya kaydedildi: {temp_file}")


def main():
    print(f"--- OTOMATİK TURBO MOD BAŞLATILIYOR ({CALISAN_SAYISI} ÇEKİRDEK) ---")

    try:
        df = pd.read_csv(DATA_FILE_PATH, on_bad_lines='skip', low_memory=False)
    except Exception as e:
        print(f"Dosya okunamadı: {e}")
        return

    eksik_indexler = df[df['Fiyat'].isna() | (df['Fiyat'] == '')].index.tolist()

    toplam_is = len(eksik_indexler)
    print(f"Toplam Satır: {len(df)}")
    print(f"Tamir Edilecek: {toplam_is}")

    if toplam_is == 0:
        print("Yapılacak iş yok! Tüm fiyatlar dolu.")
        return

    chunk_size = math.ceil(toplam_is / CALISAN_SAYISI)
    chunks = [eksik_indexler[i:i + chunk_size] for i in range(0, toplam_is, chunk_size)]

    processes = []

    for i in range(len(chunks)):
        p = Process(target=get_price_worker, args=(i, chunks[i], DATA_FILE_PATH))
        processes.append(p)
        p.start()

    print("\nTüm çalışanlar sahaya gönderildi. Pencerelerin sırayla açılmasını bekle...\n")
    for p in processes:
        p.join()

    print("\n--- TÜM İŞLEMLER BİTTİ. VERİLER BİRLEŞTİRİLİYOR ---")

    guncellenen_sayisi = 0
    for i in range(len(chunks)):
        temp_file = f"temp_result_{i}.csv"
        if os.path.exists(temp_file):
            try:
                df_temp = pd.read_csv(temp_file)
                for _, row in df_temp.iterrows():
                    orj_idx = int(row['Index'])
                    yeni_fiyat = row['Fiyat']
                    if pd.notna(yeni_fiyat) and yeni_fiyat != "Hata":
                        df.at[orj_idx, 'Fiyat'] = yeni_fiyat

                guncellenen_sayisi += len(df_temp)
                os.remove(temp_file)
            except Exception as e:
                print(f"Hata: {temp_file} birleştirilemedi. {e}")

    df.to_csv(DATA_FILE_PATH, index=False, encoding='utf-8-sig')
    print(f"Tebrikler! Toplam {guncellenen_sayisi} ilan güncellendi ve '{DATA_FILE_PATH}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()