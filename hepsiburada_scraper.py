from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

class HepsiburadaLaptopScraper:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.start_url = 'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98'
        self.product_links = []

    def scrape(self):
        self.driver.get(self.start_url)
        time.sleep(3)  # Sayfanın yüklenmesi için bekle

        for page in range(1, 6):  # Sayfa 1'den 5'e kadar gez
            if page > 1:
                next_page_url = f"{self.start_url}?sayfa={page}"
                self.driver.get(next_page_url)
                time.sleep(3)  # Sayfanın yüklenmesi için bekle

            product_list_items = self.driver.find_elements(By.CSS_SELECTOR, 'li[data-test-id="product-card"]')
            for item in product_list_items:
                link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                if link and link not in self.product_links:
                    self.product_links.append(link)

        self.driver.quit()
        self.save_to_json()

    def save_to_json(self):
        with open('laptops.json', 'w', encoding='utf-8') as f:
            json.dump(self.product_links, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scraper = HepsiburadaLaptopScraper()
    scraper.scrape()
