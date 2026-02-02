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
        # Поиск кнопки по тексту на двух языках
        pattern = re.compile(r"Отметиться|Белгілену", re.IGNORECASE)
        attendance_buttons = page.locator(".v-button-caption").get_by_text(pattern)
        
        count = attendance_buttons.count()
        if count > 0:
            for i in range(count):
                # Нажимаем только если кнопка видна и доступна
                if attendance_buttons.nth(i).is_visible():
                    attendance_buttons.nth(i).click()
                    msg = f"✅ Успешно: Отметка поставлена в {time.strftime('%H:%M:%S')}"
                    print(msg)
                    send_telegram(msg)
                    time.sleep(5) # Пауза после клика
            return True
        return False
    except Exception as e:
        print(f"Ошибка при поиске кнопки: {e}")
        return False

def login_to_wsp(page, login, password):
    """Функция для (пере)авторизации на портале."""
    try:
        page.goto("https://wsp.kbtu.kz/RegistrationOnline")
        page.wait_for_timeout(5000)

        # Выбор русского языка
        russian_flag = page.locator('img[src*="flags/ru.png"]')
        if russian_flag.is_visible():
            russian_flag.click()
            page.wait_for_timeout(3000)

        # Заполнение данных
        page.fill('input#gwt-uid-4', login)
        page.fill('input#gwt-uid-6', password)
        page.click('div.v-button-primary')
        page.wait_for_timeout(10000)
        return True
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return False

def run_attendance():
    LOGIN = os.environ.get('WSP_LOGIN')
    PASSWORD = os.environ.get('WSP_PASSWORD')

    with sync_playwright() as p:
        # Запуск браузера с увеличенным таймаутом
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        try:
            print(f"--- Старт сессии мониторинга: {time.strftime('%H:%M:%S')} ---")
            login_to_wsp(page, LOGIN, PASSWORD)

            # Цикл на 55 минут (110 итераций по 30 секунд)
            for attempt in range(110):
                # Если нас выкинуло на страницу логина — заходим снова
                if page.locator('input#gwt-uid-4').is_visible():
                    print("Сессия потеряна, перелогин...")
                    login_to_wsp(page, LOGIN, PASSWORD)

                check_and_click(page)
                
                # Обновляем страницу каждые 30 секунд для проверки кнопки
                time.sleep(30)
                try:
                    page.reload()
                    page.wait_for_timeout(5000)
                except:
                    page.goto("https://wsp.kbtu.kz/RegistrationOnline")

        except Exception as e:
            send_telegram(f"⚠️ Бот столкнулся с ошибкой: {e}")
        finally:
            browser.close()
            print(f"--- Завершение сессии: {time.strftime('%H:%M:%S')} ---")

if __name__ == "__main__":
    run_attendance()
