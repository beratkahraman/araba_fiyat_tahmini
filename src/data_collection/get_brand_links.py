from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'marka_linkleri.txt')
DRIVER_PATH = os.path.join(PROJECT_ROOT, 'chromedriver.exe')

CATEGORY_URLS = [
    "https://www.arabam.com/ikinci-el/otomobil",
    "https://www.arabam.com/ikinci-el/arazi-suv-pick-up"
]


def get_brand_links():
    """Selenium kullanarak dinamik olarak yüklenen marka linklerini toplar."""

    # ChromeDriver'ın yolunu dinamik olarak veriyoruz
    service = Service(executable_path=DRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36')

    driver = webdriver.Chrome(service=service, options=options)

    brand_links = set()

    for category_url in CATEGORY_URLS:
        print(f"'{category_url}' kategorisindeki markalar çekiliyor...")
        try:
            driver.get(category_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "category-list-wrapper"))
            )

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            category_wrapper = soup.find('div', class_='category-list-wrapper')

            if category_wrapper:
                link_elements = category_wrapper.find_all('a', class_='list-item')
                for link_element in link_elements:
                    href = link_element.get('href')
                    if href and href.startswith('/'):
                        full_link = "https://www.arabam.com" + href
                        brand_links.add(full_link)
            else:
                print(f"Uyarı: '{category_url}' için marka listesi kutusu bulunamadı.")

        except Exception as e:
            print(f"Hata: {category_url} çekilirken bir sorun oluştu. {e}")

    driver.quit()

    print(f"\nToplam {len(brand_links)} adet benzersiz marka linki bulundu.")

    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        for link in sorted(list(brand_links)):
            f.write(link + '\n')

    print(f"'{OUTPUT_FILE_PATH}' dosyası başarıyla oluşturuldu.")


if __name__ == "__main__":
    get_brand_links()