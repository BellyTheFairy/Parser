#доставь тайм слипы и проверь корректность ссылок

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pandas as pd
import time

from grafic import price_grafic 

url = 'https://pk.sutochno.ru/'

def logging(text):
    with open("function-log.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)

def open_site():
    start = time.time()
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") 
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)

    # Обработка куки
    try:
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Хорошо')]"))
        )
        button.click()
        time.sleep(1)
    except:
        pass

    all_time = time.time() - start
    logging(f"Вызываемая функция: open_site() - Время выполнения: {all_time:.2f} сек")
    return driver

def get_links(driver):
    start = time.time()
    links = []
    elements = driver.find_elements(By.TAG_NAME, 'a')

    for el in elements:
        href = el.get_attribute('href')
        if href and re.search(r'sutochno\.ru/\d+', href):
            clean_href = href.split('#')[0].split('?')[0]
            
            if clean_href not in links:
                links.append(clean_href)

    all_time = time.time() - start
    logging(f"Вызываемая функция: get_links() - Время выполнения: {all_time:.2f} сек. Найдено ссылок: {len(links)}")
    return links

def go_next_page(driver):
    start = time.time()

    try:
        next_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Далее')] | //button[contains(text(), 'Далее')] | //*[contains(@class, 'pagination-next')]")
        next_btn.click()
        time.sleep(3) 
        result = True
    except:
        result = False

    all_time = time.time() - start
    logging(f"Вызываемая функция: go_next_page() - Время выполнения: {all_time:.2f} сек")
    return result

def collect_links(driver, pages):
    start = time.time()
    all_links = []

    for i in range(pages):
        logging(f"Сбор ссылок на странице {i+1}...")
        links = get_links(driver)
        for link in links:
            if link not in all_links:
                all_links.append(link)

        if not go_next_page(driver):
            logging("Переход на следующую страницу не удался")
            break
        
        time.sleep(2)

    all_time = time.time() - start
    logging(f"Вызываемая функция: collect_links() - Время выполнения: {all_time:.2f} сек")
    return all_links

def get_info(driver, links):
    start = time.time()
    data = []

    for i, link in enumerate(links):
        logging(f"Обработка ссылки {i+1}/{len(links)}: {link}")
        driver.get(link)
        time.sleep(2) 

        item = {'Ссылка': link}
        
        try:
            item['Название'] = driver.find_element(By.TAG_NAME, "h1").text
        except:
            item['Название'] = 'Не найдено'

        try:
            # ИСПРАВЛЕНО: ищем цену более целенаправленно, чтобы не зацепить фильтры сбоку
            price_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '₽')]")
            price_text = "0"
            for el in price_elements:
                text = el.text
                # Ищем цену, рядом с которой есть указание "за сутки"
                if 'за сутки' in text.lower() or re.search(r'\d[\d\s]*\s*₽', text):
                    match = re.search(r'(\d[\d\s]*)\s*₽', text)
                    if match:
                        price_text = match.group(1).replace(' ', '')
                        break 

            item['Цена'] = price_text
        except:
            item['Цена'] = '0'

        try:
            review_text = driver.find_element(By.XPATH, "//*[contains(text(), 'отзыв')]").text
            match = re.search(r'(\d+[.,]\d+)', review_text)
            item['Рейтинг'] = match.group(1).replace(',', '.') if match else '0'
        except:
            item['Рейтинг'] = '0'

        data.append(item)

    all_time = time.time() - start
    logging(f"Вызываемая функция: get_info() - Время выполнения: {all_time:.2f} сек")
    return data

def process_data(data):
    start = time.time()
    df = pd.DataFrame(data)
    
    df['Цена'] = pd.to_numeric(df['Цена'], errors='coerce').fillna(0).astype(int)
    df['Рейтинг'] = pd.to_numeric(df['Рейтинг'], errors='coerce').fillna(0.0)

    csv_filename = "sutochno_data.csv"
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    logging(f"Данные сохранены в {csv_filename}")

    all_time = time.time() - start
    logging(f"Вызываемая функция: process_data() - Время выполнения: {all_time:.2f} сек")

def main():
    start = time.time()
    logging("Парсер запущен")
    
    driver = open_site()
    search_url = "https://pk.sutochno.ru/region"
    logging(f"Переход по адресу: {search_url}")
    driver.get(search_url)
    time.sleep(3)
    
    pages_to_parse = 4
    all_links = collect_links(driver, pages_to_parse)
    
    if not all_links:
        logging("Ссылки не найдены.")
        driver.quit()
        return

    data = get_info(driver, all_links)
    process_data(data)
    
    driver.quit()
    all_time = time.time() - start
    logging(f"Парсер завершил работу. Общее время: {all_time:.2f} сек")

if __name__ == "__main__":
    main()