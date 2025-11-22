import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
from tqdm import tqdm
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

INPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'marka_linkleri.txt')
OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'ilan_linkleri.txt')
DRIVER_PATH = os.path.join(PROJECT_ROOT, 'chromedriver.exe')

def get_last_page_for_brand(driver, brand_url):
    try:
        driver.get(brand_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        pagination_ul = soup.find('ul', class_='pagination')
        if not pagination_ul: return 1

        last_page_link = pagination_ul.find('a', title='Son Sayfa')
        if not last_page_link:
            all_li = pagination_ul.find_all('li')
            if len(all_li) > 2:
                return int(all_li[-2].text.strip())
            return 1

        href = last_page_link.get('href')
        return int(href.split('page=')[-1])

    except Exception as e:
        print(f"\nSayfa sayısı alınırken hata: {e}")
        return 1


def create_driver():
    options = uc.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')

    print("\n[INFO] Undetected Chrome driver başlatılıyor...")
    try:
        # driver_executable_path ile exe'nin yerini tam olarak gösteriyoruz
        return uc.Chrome(options=options, driver_executable_path=DRIVER_PATH, use_subprocess=True)
    except Exception as e:
        print(f"[HATA] Driver başlatılamadı: {e}")
        return None


def main():
    try:
        # Dinamik input yolunu kullanıyoruz
        with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as f:
            brand_urls = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Hata: '{INPUT_FILE_PATH}' dosyası bulunamadı.")
        return

    driver = create_driver()
    if not driver:
        return

    total_links_found = 0

    # Dinamik output yolunu kullanıyoruz
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f_ilanlar:
        for brand_url in tqdm(brand_urls, desc="Tüm Markalar"):
            last_page = get_last_page_for_brand(driver, brand_url)
            print(f"\n-> {brand_url.split('/')[-1].upper()} markası için {last_page} sayfa taranacak...")

            for page_num in tqdm(range(1, last_page + 1), desc=f"{brand_url.split('/')[-1]}"):
                url = f"{brand_url}?page={page_num}"

                try:
                    driver.get(url)
                    time.sleep(random.uniform(2, 4))

                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                    ilan_listesi = soup.find_all("tr", class_="listing-list-item", id=True)
                    if not ilan_listesi: continue

                    for ilan_satiri in ilan_listesi:
                        link_elementi = ilan_satiri.find("td", class_="listing-modelname").find('a')
                        if link_elementi:
                            ilan_linki = "https://www.arabam.com" + link_elementi.get('href')
                            f_ilanlar.write(ilan_linki + '\n')
                            total_links_found += 1

                except Exception as e:
                    print(f"\n  !! Sayfa {url} işlenirken bir hata oluştu: {e}")
                    continue

    driver.quit()

    print("\n-------------------------------------------")
    print(f"Toplam {total_links_found} adet ilan linki '{OUTPUT_FILE_PATH}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()