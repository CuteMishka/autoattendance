import os
import re
import time
import requests
from playwright.sync_api import sync_playwright

def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")

def check_and_click(page):
    try:
        pattern = re.compile(r"Отметиться|Белгілену", re.IGNORECASE)
        attendance_buttons = page.locator(".v-button-caption").get_by_text(pattern)
        
        count = attendance_buttons.count()
        if count > 0:
            for i in range(count):
                attendance_buttons.nth(i).click()
                msg = "✅ Успешно: Отметка на портале WSP поставлена!"
                print(msg)
                send_telegram(msg)
                time.sleep(2)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при поиске кнопки: {e}")
        return False

def run_attendance():
    LOGIN = os.environ.get('WSP_LOGIN')
    PASSWORD = os.environ.get('WSP_PASSWORD')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            start_time = time.strftime('%H:%M')
            print(f"--- Старт сессии: {start_time} ---")
            
            # Начальная авторизация
            page.goto("https://wsp.kbtu.kz/RegistrationOnline")
            page.wait_for_timeout(5000)

            # Переключение языка
            russian_flag = page.locator('img[src*="flags/ru.png"]')
            if russian_flag.is_visible():
                russian_flag.click()
                page.wait_for_timeout(3000)

            # Вход
            page.fill('input#gwt-uid-4', LOGIN)
            page.fill('input#gwt-uid-6', PASSWORD)
            page.click('div.v-button-primary')
            page.wait_for_timeout(10000)

            # Цикл мониторинга: 28 минут (28 попыток по 1 минуте)
            for attempt in range(28):
                print(f"Попытка {attempt + 1}/28 (Время: {time.strftime('%H:%M:%S')})")
                
                check_and_click(page)
                
                if attempt < 27:
                    time.sleep(60) # Ждем 1 минуту
                    page.reload()
                    page.wait_for_timeout(5000)
                    
                    # Если после перезагрузки выкинуло на страницу входа
                    if page.locator('input#gwt-uid-4').is_visible():
                        print("Сессия истекла, перезаходим...")
                        page.fill('input#gwt-uid-4', LOGIN)
                        page.fill('input#gwt-uid-6', PASSWORD)
                        page.click('div.v-button-primary')
                        page.wait_for_timeout(8000)

        except Exception as e:
            print(f"Критическая ошибка: {e}")
        finally:
            browser.close()
            print("--- Сессия завершена ---")

if __name__ == "__main__":
    run_attendance()
