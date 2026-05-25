import os
from PIL import Image, ImageDraw, ImageFont

def draw_rounded_rectangle(draw, x, y, w, h, radius, fill, outline, width=2):
    # Draw rounded rectangle with thick border
    draw.rounded_rectangle(
        [(x, y), (x + w, y + h)],
        radius=radius,
        fill=fill,
        outline=outline,
        width=width
    )

def draw_text_centered(draw, x, y, w, h, text, font, fill=(0, 0, 0), line_spacing=6):
    lines = text.split('\n')
    
    # Calculate total height of the text block
    line_heights = []
    line_widths = []
    for line in lines:
        if not line:
            line_heights.append(font.size)
            line_widths.append(0)
            continue
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        line_widths.append(line_w)
        line_heights.append(line_h)
    
    total_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    
    # Starting y coordinate to vertically center the text block
    curr_y = y + (h - total_height) / 2
    
    for i, line in enumerate(lines):
        if line:
            # Horizontally center the line
            curr_x = x + (w - line_widths[i]) / 2
            # Draw line
            # We adjust baseline slightly for better visual centering
            draw.text((curr_x, curr_y - 2), line, font=font, fill=fill)
        curr_y += line_heights[i] + line_spacing

def generate_wireframe(filename, width, height, elements):
    # Create white canvas
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Attempt to load Arial
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    if not os.path.exists(font_path):
        font_path = "arial.ttf"
    
    try:
        font = ImageFont.truetype(font_path, 13)
        font_large = ImageFont.truetype(font_path, 14)
    except IOError:
        font = ImageFont.load_default()
        font_large = font
        
    for el in elements:
        x, y, w, h, text = el
        # Use slightly larger font for header/title
        el_font = font_large if h <= 50 or "Шапка:" in text or "Форма" in text or "кабинет" in text or "Панель" in text else font
        draw_rounded_rectangle(
            draw, x, y, w, h, 
            radius=12, 
            fill=(248, 248, 248), 
            outline=(51, 51, 51), 
            width=2
        )
        draw_text_centered(draw, x, y, w, h, text, el_font)
        
    img.save(filename, "PNG")
    print(f"Generated {filename} successfully.")

def main():
    # 1. Main Page
    main_elements = [
        (25, 25, 750, 50, "Шапка: Логотип | О клинике | Услуги | Специалисты | Личный кабинет  [Войти]"),
        (25, 95, 750, 90, "Промо-баннер: Современная клиника для всей семьи\n[Кнопка: Записаться на приём]"),
        (25, 205, 236, 100, "Направление: Терапия\nПриемы терапевта,\nпервичная диагностика"),
        (282, 205, 236, 100, "Направление: Кардиология\nКонсультации, ЭКГ,\nУЗИ сердца"),
        (539, 205, 236, 100, "Направление: Анализы\nЗабор крови, ПЦР,\nэкспресс-тесты"),
        (25, 325, 750, 60, "Адрес: г. Москва, ул. Автозаводская, 16 | Телефон: +7 (495) 123-45-67"),
        (25, 405, 750, 50, "Подвал: © 2026 Частная клиника. Все права защищены.")
    ]
    generate_wireframe("wireframe_main.png", 800, 480, main_elements)
    
    # 2. Booking Page
    booking_elements = [
        (25, 25, 750, 50, "Шапка: Логотип | Пациент: Амплеенков Д.О. | Личный кабинет | [Выйти]"),
        (25, 95, 750, 50, "Форма онлайн-записи на приём"),
        (25, 165, 365, 90, "Шаг 1: Направление и врач\n[Выбрать специальность]\n[Выбрать врача]"),
        (410, 165, 365, 90, "Шаг 2: Выберите услугу\n[Выбрать услугу]\nДлительность: 30 мин., Цена: 1500 руб."),
        (25, 275, 750, 100, "Шаг 3: Выберите дату и свободное время\n[Интерактивный календарь]\n[Слоты: 09:00, 09:30, 10:00 (занят), 10:30, 11:00]"),
        (25, 395, 750, 90, "Подтверждение записи\nВыбран врач: Иванов И.И., услуга: Прием терапевта\nДата и время: 28.05.2026 в 09:30\n[Кнопка: Подтвердить запись]"),
        (25, 505, 750, 50, "Подвал: Служба поддержки клиники | © 2026")
    ]
    generate_wireframe("wireframe_booking.png", 800, 580, booking_elements)
    
    # 3. Doctor Cabinet
    doctor_elements = [
        (25, 25, 750, 50, "Шапка: Логотип | Врач: Петров П.П. (Терапевт) | [Выйти]"),
        (25, 95, 750, 50, "Личный кабинет врача — Расписание и ведение приёма"),
        (25, 165, 365, 250, "Мое расписание на сегодня\n\n09:00 - Амплеенков Д.О. (Терапия) [Принят]\n09:30 - Сидоров С.С. (Осмотр) [В процессе]\n10:30 - Козлов К.К. (Консультация) [Ожидание]\n11:00 - Свободный слот"),
        (410, 165, 365, 250, "Форма активного приёма: Сидоров С.С.\n\n[Текстовая область: Жалобы и анамнез]\n[Текстовое поле: Первичный диагноз]\n[Текстовая область: Назначения и рецепты]\n\n[Кнопка: Добавить документ]\n[Кнопка: Завершить приём]"),
        (25, 435, 750, 50, "Подвал: Система электронных медицинских карт частной клиники")
    ]
    generate_wireframe("wireframe_doctor.png", 800, 510, doctor_elements)
    
    # 4. Admin Panel
    admin_elements = [
        (25, 25, 750, 50, "Шапка: Панель управления | Администратор: Смирнова А.А. | [Выйти]"),
        (25, 95, 240, 330, "Боковое меню\n\n[Управление врачами]\n[Управление услугами]\n[Расписание клиники]\n[База пациентов]\n[Управление записями]"),
        (285, 95, 490, 330, "Раздел: Управление расписанием врачей\n\nФильтры: [Выбрать дату: 28.05.2026] | [Врач: Иванов И.И. (Терапевт)]\n\nТаблица слотов расписания:\n09:00 - Занят (Пациент: Амплеенков Д.О.) [Отменить запись]\n09:30 - Занят (Пациент: Сидоров С.С.) [Отменить запись]\n10:00 - Свободен [Изменить] [Удалить]\n10:30 - Свободен [Изменить] [Удалить]\n\n[Кнопка: Добавить новые слоты в расписание]"),
        (25, 445, 750, 50, "Подвал: Административный интерфейс управления ресурсами клиники. Сессия активна.")
    ]
    generate_wireframe("wireframe_admin.png", 800, 520, admin_elements)

    # 5. Authorization Page
    auth_elements = [
        (25, 25, 750, 50, "Шапка: Логотип | [На главную страницу клиники]"),
        (25, 95, 750, 50, "Страница авторизации и регистрации"),
        (25, 165, 365, 250, "Форма входа (Авторизация)\n\n[Поле ввода: Email]\n[Поле ввода: Пароль]\n\n[Кнопка: Войти в кабинет]"),
        (410, 165, 365, 250, "Форма регистрации пациента\n\n[Поле ввода: ФИО пациента]\n[Поле ввода: Дата рождения]\n[Поле ввода: Номер телефона]\n[Поле ввода: Email]\n[Поле ввода: Пароль]\n\n[Кнопка: Зарегистрироваться]"),
        (25, 435, 750, 50, "Подвал: Защита персональных данных пациентов согласно ФЗ-152 | © 2026")
    ]
    generate_wireframe("wireframe_auth.png", 800, 510, auth_elements)

if __name__ == "__main__":
    main()
