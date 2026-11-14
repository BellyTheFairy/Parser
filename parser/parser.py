from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

def parsing():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') #чтобы браузер работал в фоновом режиме 
    options.add_argument('--disable-blink-features=AutomationControlled') #скрыбаем что мы бот
    options.add_argument('user-agent=Win64; AppleWebKit/537.36 Chrome/114.0.0.0')

    browser = webdriver.Chrome(options=options)
    
    browser.implicitly_wait(5)

    try:
        url = "http://catalog.onliner.by/"
        browser.get(url)

        wait = WebDriverWait(browser, 10)
        books = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.product_pod")))
        
        data = []

        # Сбор данных
        for phone in phones:
            # Название
            title = phone.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("title")
            
            price = phone.find_element(By.CSS_SELECTOR, ".price_color").text
            
            link = phone.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")

            data.append({
                "title": title,
                "price": price,
                "link": link
            })

        # 5. Сохранение в JSON
        with open("phones_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Кол-во ссылок {len(data)}. Данные сохранены в phones_data.json")

    except TimeoutException:
        print("Ошибка: Не удалось дождаться загрузки элементов на странице.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    parsing()