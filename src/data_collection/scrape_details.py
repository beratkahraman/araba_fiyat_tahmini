import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
from tqdm import tqdm
import pandas as pd
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

INPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'ilan_linkleri.txt')
OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'ilanlar_ham.csv')



def create_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')

    print("\n[INFO] Yeni bir Chrome driver başlatılıyor...")
    try:
        return uc.Chrome(options=options, use_subprocess=True)
    except Exception as e:
        print(f"[KRİTİK HATA] Driver başlatılamadı: {e}")
        return None


def main():
    try:
        with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as f:
            all_links = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Hata: '{INPUT_FILE_PATH}' dosyası bulunamadı.")
        return

    processed_links = set()
    if os.path.exists(OUTPUT_FILE_PATH):
        try:
            df_existing = pd.read_csv(OUTPUT_FILE_PATH, on_bad_lines='skip', low_memory=False)
            processed_links = set(df_existing['Link'])
            print(
                f"[INFO] Mevcut CSV dosyasında {len(processed_links)} adet işlenmiş link bulundu. Kaldığı yerden devam edilecek.")
        except Exception as e:
            print(f"[UYARI] Mevcut dosya okunurken hata oluştu: {e}. Baştan başlanabilir.")

    links_to_scrape = [link for link in all_links if link not in processed_links]

    if not links_to_scrape:
        print("[INFO] Tüm linkler zaten işlenmiş. Program sonlandırılıyor.")
        return

    driver = create_driver()
    if not driver: return

    all_car_data = []
    save_interval = 100

    try:
        for i, ilan_linki in enumerate(tqdm(links_to_scrape, desc="İlan Detayları Çekiliyor")):
            try:
                driver.get(ilan_linki)
                time.sleep(random.uniform(2, 4))

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                ilan_data = {'Link': ilan_linki}

                def get_text_safely(element):
                    return element.text.strip() if element else None

                ilan_data['Başlık'] = get_text_safely(soup.find("div", class_="product-title"))
                ilan_data['Fiyat'] = get_text_safely(soup.find("span", class_="product-price-new"))

                for item in soup.find_all("div", class_="property-item"):
                    key_element = item.find("div", class_="property-key")
                    value_element = item.find("div", class_="property-value")
                    if key_element and value_element:
                        ilan_data[key_element.text.strip()] = value_element.text.strip()

                ilan_data['Tramer'] = get_text_safely(soup.select_one(".tramer-info .property-value"))

                hasar_bilgileri = {}
                damage_info_container = soup.find("div", class_="car-damage-info")
                if damage_info_container:
                    for item in damage_info_container.find_all("div", class_="car-damage-info-item"):
                        status_element = item.find("p")
                        if status_element:
                            status = status_element.text.strip()
                            parts_list = item.find_all("li")
                            parts = ", ".join([p.text.strip() for p in parts_list if p.text.strip() != "-"])
                            hasar_bilgileri[status] = parts if parts else "Yok"

                ilan_data['Boyalı Parçalar'] = hasar_bilgileri.get('Boyalı', 'Belirtilmemiş')
                ilan_data['Lokal Boyalı Parçalar'] = hasar_bilgileri.get('Lokal boyalı', 'Belirtilmemiş')
                ilan_data['Değişen Parçalar'] = hasar_bilgileri.get('Değişmiş', 'Belirtilmemiş')

                all_car_data.append(ilan_data)

                if (i + 1) % save_interval == 0:
                    df_batch = pd.DataFrame(all_car_data)
                    header = not os.path.exists(OUTPUT_FILE_PATH)
                    df_batch.to_csv(OUTPUT_FILE_PATH, mode='a', header=header, index=False, encoding='utf-8-sig')
                    all_car_data = []

            except Exception as e:
                error_str = str(e).lower()
                if "read timed out" in error_str or "invalid session id" in error_str:
                    print("[INFO] Önemli bir driver hatası tespit edildi. Driver yeniden başlatılıyor...")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = create_driver()
                    if not driver:
                        print("[KRİTİK HATA] Yeni driver başlatılamadı. Program sonlandırılıyor.")
                        break
                continue

    finally:
        if all_car_data:
            df_final = pd.DataFrame(all_car_data)
            header = not os.path.exists(OUTPUT_FILE_PATH)
            df_final.to_csv(OUTPUT_FILE_PATH, mode='a', header=header, index=False, encoding='utf-8-sig')
            print(f"\n[INFO] Kalan {len(all_car_data)} ilan dosyaya kaydedildi.")
        if driver:
            driver.quit()
        print("\n-------------------------------------------")
        print(f"İşlem tamamlandı veya durduruldu. Veriler '{OUTPUT_FILE_PATH}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()