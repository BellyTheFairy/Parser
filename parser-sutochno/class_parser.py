import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from random import randint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time() 
        result = func(*args, **kwargs)
        end_time = time.time()   
        
        execution_time = end_time - start_time
        log_message = f"Функция: {func.__name__} — Время выполнения: {execution_time:.2f} сек.\n"
        print(log_message.strip())

        # Запись в файл лога (требование для проверки на GitHub)
        with open("py_log.txt", "a", encoding="utf-8") as f:
            f.write(log_message)
            
        return result
    return wrapper


class SutochnoParser:
    def __init__(self):
        # 1. Открытие сайта Суточно.ру (раздел Камчатка / Петропавловск-Камчатский)
        self.base_url = 'https://pk.sutochno.ru/'
        self.links_list = []
        self.info_list = []
        self.csv_path = "kamchatka_rentals.csv"
        
        # Настройка Chrome для стабильной работы и снижения шанса блокировки
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def __del__(self):
        try:
            self.driver.quit()
            print('driver quit')
        except Exception:
            pass

    @log_execution_time
    def open_site(self):
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Закрытие баннера с куки (если появляется)
        try:
            cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Хорошо') or contains(text(), 'Принять')]")
            cookie_btn.click()
            time.sleep(1)
        except Exception:
            pass  # Баннера может не быть

    @log_execution_time
    def get_links_on_page(self):
        # Ищем все ссылки и фильтруем те, что ведут на конкретные объявления (имеют вид /1234567)
        elements = self.driver.find_elements(By.TAG_NAME, 'a')
        for element in elements:
            href = element.get_attribute('href')
            if href:
                # Регулярное выражение ищет ссылки вида pk.sutochno.ru/цифры или /цифры
                if re.search(r'pk\.sutochno\.ru/\d+$', href) or re.search(r'^/\d+$', href):
                    full_link = f"https://pk.sutochno.ru{href}" if href.startswith('/') else href
                    if full_link not in self.links_list:
                        self.links_list.append(full_link)
        print(f"Найдено уникальных ссылок на объявления: {len(self.links_list)}")

    @log_execution_time
    def go_to_the_next_page(self):
        try:
            # Кнопка "Смотреть все" или пагинация внизу страницы
            next_btn = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Смотреть все') or contains(text(), 'Далее')]")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(1)
            next_btn.click()
            time.sleep(randint(2, 4))
            return True
        except Exception:
            print("Следующая страница не найдена или достигнут конец списка.")
            return False

    @log_execution_time
    def collect_multiple_pages(self, max_pages=2):
        """Этичный сбор данных с нескольких страниц"""
        for page in range(max_pages):
            print(f"\n--- Сбор ссылок со страницы {page + 1} ---")
            self.get_links_on_page()
            if not self.go_to_the_next_page():
                break
            time.sleep(randint(3, 6)) # Этичная задержка между страницами

    @log_execution_time
    def get_info(self):
        # Ограничиваем количество для примера (уберите [:15], чтобы собрать все найденные ссылки)
        for link in self.links_list[:15]: 
            try:
                self.driver.get(link)
                time.sleep(randint(2, 5)) # 2. Этичный сбор данных: случайная задержка
                
                model_data = {}
                model_data['Ссылка'] = link
                
                # Название объекта
                try:
                    model_data['Название'] = self.driver.find_element(By.XPATH, "//h1").text.strip()
                except Exception:
                    model_data['Название'] = 'Не найдено'

                # Цена (ищем элемент с рублем и извлекаем число)
                try:
                    price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '₽')]")
                    price_found = False
                    for el in price_elements:
                        txt = el.text.strip()
                        if '₽' in txt and any(char.isdigit() for char in txt):
                            price_match = re.search(r'(\d[\d\s]*)\s*₽', txt)
                            if price_match:
                                model_data['Цена'] = price_match.group(1).replace(' ', '') + ' ₽'
                                price_found = True
                                break
                    if not price_found:
                        model_data['Цена'] = 'Не найдено'
                except Exception:
                    model_data['Цена'] = 'Не найдено'

                # Рейтинг и количество отзывов
                try:
                    review_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'отзыв')]").text
                    rating_match = re.search(r'(\d+[.,]\d+)', review_text)
                    model_data['Рейтинг'] = rating_match.group(1).replace(',', '.') if rating_match else 'Нет рейтинга'
                    
                    reviews_match = re.search(r'(\d+)\s*отзыв', review_text)
                    model_data['Отзывы'] = reviews_match.group(1) if reviews_match else '0'
                except Exception:
                    model_data['Рейтинг'] = 'Нет рейтинга'
                    model_data['Отзывы'] = '0'

                self.info_list.append(model_data)
                print(f"✓ Собраны данные: {model_data['Название'][:40]}...")
            except Exception as e:
                print(f"✗ Ошибка при обработке {link}: {e}")

    @log_execution_time
    def process_data(self):
        df = pd.DataFrame(self.info_list)
        
        # 4. Обработка: удаление дубликатов по ссылке
        initial_len = len(df)
        df = df.drop_duplicates(subset=['Ссылка'])
        print(f"Удалено дубликатов: {initial_len - len(df)}")
        
        # 4 & 5. Очистка от ошибочных данных и интерпретация (создание числовых столбцов)
        df['Цена_число'] = pd.to_numeric(df['Цена'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')
        df['Рейтинг_число'] = pd.to_numeric(df['Рейтинг'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)
        
        # Фильтрация ошибочных данных (цена не может быть <= 0 или NaN)
        df = df[df['Цена_число'] > 0]
        
        # 5. Интерпретация: удаление исходных "грязных" текстовых столбцов и переименование
        cols_to_drop = [col for col in ['Цена', 'Рейтинг'] if col in df.columns]
        df = df.drop(columns=cols_to_drop)
        
        df = df.rename(columns={
            'Название': 'Название_объекта',
            'Отзывы': 'Количество_отзывов',
            'Цена_число': 'Цена_за_сутки_руб',
            'Рейтинг_число': 'Рейтинг'
        })
        
        df = df.reset_index(drop=True)
        self.info_list = df.to_dict('records')
        print("Данные успешно обработаны: дубликаты удалены, цены очищены, столбцы интерпретированы.")
        return df

    @log_execution_time
    def save_and_visualize(self):
        df = pd.DataFrame(self.info_list)
        
        # 6. Представление данных в таблице (CSV)
        df.to_csv(self.csv_path, index=False, sep=';', encoding='utf-8-sig')
        print(f"Данные сохранены в {self.csv_path}")
        
        # 6. Представление данных в графическом виде (Гистограмма цен)
        try:
            plt.figure(figsize=(10, 6))
            plt.hist(df['Цена_за_сутки_руб'], bins=10, color='skyblue', edgecolor='black')
            plt.title('Распределение цен на посуточную аренду в Камчатке (Петропавловск-Камчатский)')
            plt.xlabel('Цена за сутки (руб)')
            plt.ylabel('Количество объявлений')
            plt.grid(axis='y', alpha=0.75)
            plt.savefig('price_distribution.png', dpi=300, bbox_inches='tight')
            print("График успешно сохранен как price_distribution.png")
        except Exception as e:
            print(f"Не удалось построить график: {e}")

    def run(self):
        # Очистка старого лога перед новым запуском
        if os.path.exists("py_log.txt"):
            os.remove("py_log.txt")
            
        self.open_site()
        self.collect_multiple_pages(max_pages=2) # Соберет ссылки с 2 страниц
        self.get_info()
        self.process_data()
        self.save_and_visualize()


if __name__ == "__main__":
    parser = SutochnoParser()
    parser.run()
    del parser