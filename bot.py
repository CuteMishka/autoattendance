import os
import re
import time
import requests
from playwright.sync_api import sync_playwright

def send_telegram(message):
    """Отправляет уведомление в Telegram."""
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
    """Ищет кнопку отметки и нажимает её."""
    try:
        # Регулярное выражение для поиска на русском и казахском
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
            # Отправляем сообщение один раз за запуск воркфлоу
            start_time = time.strftime('%H:%M')
            send_telegram(f"🚀 Запуск сессии мониторинга ({start_time}). Проверяю каждые 2 минуты...")

            print(f"--- Старт сессии: {start_time} ---")
            page.goto("https://wsp.kbtu.kz/RegistrationOnline")
            page.wait_for_timeout(5000)

            # ШАГ 1: Переключение на русский язык через флаг
            russian_flag = page.locator('img[src*="flags/ru.png"]')
            if russian_flag.is_visible():
                russian_flag.click()
                print("Язык переключен на русский.")
                page.wait_for_timeout(3000)

            # ШАГ 2: Авторизация
            page.fill('input#gwt-uid-4', LOGIN)
            page.fill('input#gwt-uid-6', PASSWORD)
            page.click('div.v-button-primary')
            page.wait_for_timeout(10000)

            # ШАГ 3: Цикл мониторинга (9 попыток)
            for attempt in range(9):
                print(f"Попытка {attempt + 1}/9...")
                
                # Если нашли кнопку — отметимся (функция сама отправит ТГ-сообщение об успехе)
                check_and_click(page)
                
                if attempt < 8:
                    time.sleep(120) # Пауза 2 минуты
                    page.reload()
                    page.wait_for_timeout(10000)

        except Exception as e:
            print(f"Ошибка: {e}")
            # Опционально: send_telegram(f"❌ Сбой бота: {e}")
        finally:
            browser.close()
            print("--- Сессия завершена ---")

if __name__ == "__main__":
    run_attendance()