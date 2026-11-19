from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import pandas as pd
import matplotlib.pyplot as plt
from random import randint
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
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)

    #обработка куки
    try:
        button = driver.find_element(By.XPATH, "//button[contains(text(), 'Хорошо')]")
        button.click()
        time.sleep(2)
    except:
        pass

    all_time = time.time() - start
    logging(f"Вызываемая функция: open_site() - Время выполнения:{all_time:.2f} сек")
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
                links.append(href)

    all_time = time.time() - start
    logging(f"Вызываемая функция: get_links() - Время выполнения:{all_time:.2f} сек")
    return links

def go_next_page(driver):

    start = time.time()

    try:
        next = driver.find_element(By.XPATH, "//a[contains(text(), 'Далее')]")
        next.click()
        time.sleep(2)
        result = True
    except:
        result = False

    all_time = time.time() - start
    logging(f"Вызываемая функция: go_next_page() - Время выполнения:{all_time:.2f} сек")
    return result

#сбор ссылок 
def collect_links(driver, pages):

    start = time.time()
    all_links = []

    for i in range(pages):
        links = get_links(driver)
        for link in links:
            if link not in all_links:
                all_links.append(link)

        if not go_next_page(driver):
            break

        time.sleep(3)

    all_time = time.time() - start
    logging(f"Вызываемая функция: collect_links() - Время выполнения:{all_time:.2f} сек")
    return all_links

def get_info(driver, links):

    start = time.time()
    data = []

    for link in links:
        driver.get(link)
        time.sleep(randint(2, 4))

        item = {'Ссылка': link}
        item['Название'] = driver.find_element(By.XPATH, "//h1").text

        price_text = driver.find_element(By.XPATH, "//*[contains(text(), '₽')]").text
        match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
        item['Цена'] = match.group(1).replace(' ', '') if match else '0'

        try:
            review_text = driver.find_element(By.XPATH, "//*[contains(text(), 'отзыв')]").text
            match = re.search(r'(\d+[.,]\d+)', review_text)
            item['Рейтинг'] = match.group(1).replace(',', '.') if match else '0'
        except:
            item['Рейтинг'] = '0'

        data.append(item)

    all_time = time.time() - start
    logging(f"Вызываемая функция: get_info() - Время выполнения:{all_time:.2f} сек")
    return data

def process_data(data):

    start = time.time()
    df = pd.DataFrame(data)
    size = len(df)

    df['Цена'] = pd.to_numeric(df['Цена'], errors='coerce').fillna(0).astype(int)
    df['Рейтинг'] = pd.to_numeric(df['Рейтинг'], errors='coerce').fillna(0.0)

    csv_filename = "sutochno_data.csv"
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    logging(f"Данные сохранены в {csv_filename}")

    
    plot_filename = "price_grafic.png"
    success = price_grafic(df, filename=plot_filename)
    
    if success:
        logging(f"График успешно сохранен в {plot_filename}")
    else:
        logging("Не удалось построить график")

    all_time = time.time() - start
    logging(f"Вызываемая функция: process_data() - Время выполнения:{all_time:.2f} сек")

def main():

    start = time.time()
    logging("Парсер запущен")
    
    driver = open_site()
    
    search_url = "https://sutochno.ru/search?address=Камчатка"
    driver.get(search_url)
    time.sleep(3)
    
    pages_to_parse = 4
    all_links = collect_links(driver, pages_to_parse)
    
    if not all_links:
        logging("Ссылки не найдены.")
        driver.quit()
        return

    all_time = time.time() - start
    logging(f"Вызываемая функция: main() - Время выполнения:{all_time:.2f} сек")

if __name__ == "__main__":
    main()