import os
import re
import time
from playwright.sync_api import sync_playwright

def check_and_click(page):
    """
    Функция ищет кнопку отметки на странице и нажимает её.
    """
    try:
        # Регулярное выражение для поиска текста "Отметиться" или "Белгілену" (регистр игнорируется)
        attendance_pattern = re.compile(r"Отметиться|Белгілену", re.IGNORECASE)
        
        # Находим все элементы с текстом кнопки
        attendance_buttons = page.locator(".v-button-caption").get_by_text(attendance_pattern)
        count = attendance_buttons.count()
        
        if count > 0:
            print(f"[{time.strftime('%H:%M:%S')}] Найдено активных занятий: {count}. Нажимаю...")
            for i in range(count):
                # Нажимаем на кнопку
                attendance_buttons.nth(i).click()
                print(f"Успешно: Кнопка №{i+1} нажата.")
            return True
        return False
    except Exception as e:
        print(f"Ошибка при поиске кнопки: {e}")
        return False

def run_attendance():
    # Данные для входа из переменных окружения (GitHub Secrets)
    LOGIN = os.environ.get('WSP_LOGIN')
    PASSWORD = os.environ.get('WSP_PASSWORD')

    if not LOGIN or not PASSWORD:
        print("Ошибка: Логин или пароль не найдены в переменных окружения.")
        return

    with sync_playwright() as p:
        # Запуск в фоновом режиме (headless)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"--- Начало сессии: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            # Переход на портал
            page.goto("https://wsp.kbtu.kz/RegistrationOnline")
            page.wait_for_timeout(5000) # Ждем прогрузку Vaadin скриптов

            # ШАГ 1: Переключение на русский язык через флаг
            print("Попытка переключения на русский язык...")
            russian_flag = page.locator('img[src*="flags/ru.png"]')
            if russian_flag.is_visible():
                russian_flag.click()
                print("Клик по флагу выполнен.")
                page.wait_for_timeout(3000) # Ждем обновления интерфейса
            else:
                print("Флаг не найден или уже выбран русский язык.")

            # ШАГ 2: Авторизация
            print(f"Авторизация под пользователем: {LOGIN}")
            page.fill('input#gwt-uid-4', LOGIN)
            page.fill('input#gwt-uid-6', PASSWORD)
            
            # Нажимаем на основную кнопку входа
            page.click('div.v-button-primary')
            
            # Длительное ожидание загрузки личного кабинета (портал бывает медленным)
            page.wait_for_timeout(10000)

            # ШАГ 3: Цикл мониторинга (каждые 2 минуты в течение 18 минут)
            # Это позволяет «дежурить» на странице в рамках одного запуска GitHub Action
            for attempt in range(9):
                print(f"[{time.strftime('%H:%M:%S')}] Проверка №{attempt + 1}...")
                
                # Проверяем наличие кнопки
                if check_and_click(page):
                    print("Действие выполнено.")
                else:
                    print("Кнопок для отметки пока нет.")

                # Если это не последняя попытка — ждем и обновляем страницу
                if attempt < 8:
                    time.sleep(120) # Пауза 2 минуты
                    print("Обновление страницы...")
                    page.reload()
                    page.wait_for_timeout(10000) # Ждем прогрузку после релоада

        except Exception as e:
            print(f"Критическая ошибка в работе бота: {e}")
        
        finally:
            browser.close()
            print(f"--- Сессия завершена: {time.strftime('%H:%M:%S')} ---")

if __name__ == "__main__":
    run_attendance()