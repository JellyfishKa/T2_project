"""
T2 AI Route Planner — Project Report PDF Generator
Генерирует полный отчёт-документ проекта (смета, роадмап, описание).
A4 формат, ~18 страниц.
Запуск: py generate_project_report.py
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

# ─── Страница A4 ──────────────────────────────────────────────────────────────
W = 210 * mm
H = 297 * mm
ML = 20 * mm   # left margin
MR = 20 * mm   # right margin
MT = 20 * mm
MB = 18 * mm
CW = W - ML - MR   # content width

# ─── Цвета ────────────────────────────────────────────────────────────────────
DARK    = HexColor('#0F172A')
BLUE    = HexColor('#1D4ED8')
LBLUE   = HexColor('#3B82F6')
GREEN   = HexColor('#16A34A')
RED     = HexColor('#DC2626')
ORANGE  = HexColor('#EA580C')
YELLOW  = HexColor('#D97706')
GRAY    = HexColor('#6B7280')
LGRAY   = HexColor('#E5E7EB')
VLGRAY  = HexColor('#F8FAFC')
WHITE   = HexColor('#FFFFFF')


# ─── Класс документа ─────────────────────────────────────────────────────────

class Doc:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=(W, H))
        self.c.setTitle('T2 AI Route Planner — Описание проекта')
        self.c.setAuthor('Команда T2')
        self.c.setSubject('Проектная документация')
        self.page = 0
        self.y = H - MT   # текущая позиция

    def new_page(self):
        self.c.showPage()
        self.page += 1
        self.y = H - MT
        self._draw_page_chrome()

    def _draw_page_chrome(self):
        """Верхняя полоса и номер страницы на каждой странице."""
        self.c.setFillColor(BLUE)
        self.c.rect(0, H - 8*mm, W, 8*mm, fill=1, stroke=0)
        self.c.setFillColor(WHITE)
        self.c.setFont('Helvetica-Bold', 7)
        self.c.drawString(ML, H - 5.5*mm, 'T2 AI Route Planner — Проектная документация')
        self.c.drawRightString(W - MR, H - 5.5*mm, f'Страница {self.page}')
        # Нижняя линия
        self.c.setStrokeColor(LGRAY)
        self.c.setLineWidth(0.5)
        self.c.line(ML, MB, W - MR, MB)

    def save(self):
        self.c.save()

    # ─── Примитивы ──────────────────────────────────────────────────────────

    def check_space(self, needed):
        """Переворачивает страницу, если не хватает места."""
        if self.y - needed < MB + 5*mm:
            self.new_page()

    def section_header(self, text, color=BLUE):
        self.check_space(16*mm)
        self.y -= 6*mm
        self.c.setFillColor(color)
        self.c.rect(ML, self.y - 1*mm, CW, 9*mm, fill=1, stroke=0)
        self.c.setFillColor(WHITE)
        self.c.setFont('Helvetica-Bold', 12)
        self.c.drawString(ML + 4*mm, self.y + 2*mm, text.upper())
        self.y -= 8*mm

    def subsection(self, text, color=DARK):
        self.check_space(10*mm)
        self.y -= 4*mm
        self.c.setFillColor(color)
        self.c.setFont('Helvetica-Bold', 11)
        self.c.drawString(ML, self.y, text)
        self.y -= 6*mm
        # Подчёркивание
        self.c.setStrokeColor(LGRAY)
        self.c.setLineWidth(0.5)
        self.c.line(ML, self.y + 1*mm, W - MR, self.y + 1*mm)
        self.y -= 2*mm

    def para(self, text, indent=0, size=10, color=DARK, bold=False):
        """Одиночная строка текста с переносом."""
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        self.c.setFont(font, size)
        x = ML + indent
        max_w = CW - indent
        # Перенос по словам
        words = text.split()
        line = ''
        for word in words:
            test = line + (' ' if line else '') + word
            if self.c.stringWidth(test, font, size) <= max_w:
                line = test
            else:
                if line:
                    self.check_space(size * 0.5 * mm + 2*mm)
                    self.c.setFillColor(color)
                    self.c.drawString(x, self.y, line)
                    self.y -= (size * 0.45 * mm + 1.5*mm)
                line = word
        if line:
            self.check_space(size * 0.5 * mm + 2*mm)
            self.c.setFillColor(color)
            self.c.drawString(x, self.y, line)
            self.y -= (size * 0.45 * mm + 1.5*mm)

    def bullet(self, text, indent=4*mm, marker='•', color=DARK, marker_color=BLUE):
        self.check_space(6*mm)
        self.c.setFillColor(marker_color)
        self.c.setFont('Helvetica-Bold', 10)
        self.c.drawString(ML + indent, self.y, marker)
        self.c.setFillColor(color)
        self.c.setFont('Helvetica', 10)
        # Перенос
        max_w = CW - indent - 5*mm
        words = text.split()
        line = ''
        x = ML + indent + 4*mm
        for word in words:
            test = line + (' ' if line else '') + word
            if self.c.stringWidth(test, 'Helvetica', 10) <= max_w:
                line = test
            else:
                if line:
                    self.c.drawString(x, self.y, line)
                    self.y -= 5*mm
                    x_continue = ML + indent + 4*mm
                    self.c.setFillColor(color)
                line = word
        if line:
            self.c.drawString(x, self.y, line)
            self.y -= 5*mm

    def spacer(self, h=3*mm):
        self.y -= h

    def hline(self, color=LGRAY):
        self.check_space(4*mm)
        self.c.setStrokeColor(color)
        self.c.setLineWidth(0.5)
        self.c.line(ML, self.y, W - MR, self.y)
        self.y -= 3*mm

    def kv_row(self, key, value, key_w=55*mm, bg=None):
        """Строка ключ–значение в таблице."""
        row_h = 7*mm
        self.check_space(row_h + 1*mm)
        if bg:
            self.c.setFillColor(bg)
            self.c.rect(ML, self.y - row_h + 2*mm, CW, row_h, fill=1, stroke=0)
        self.c.setFillColor(GRAY)
        self.c.setFont('Helvetica-Bold', 9)
        self.c.drawString(ML + 2*mm, self.y - 3*mm, key)
        self.c.setFillColor(DARK)
        self.c.setFont('Helvetica', 9)
        val_x = ML + key_w
        # Обрезаем если слишком длинно
        val_str = str(value)
        if self.c.stringWidth(val_str, 'Helvetica', 9) > CW - key_w - 4*mm:
            while self.c.stringWidth(val_str + '...', 'Helvetica', 9) > CW - key_w - 4*mm and val_str:
                val_str = val_str[:-1]
            val_str += '...'
        self.c.drawString(val_x, self.y - 3*mm, val_str)
        self.c.setStrokeColor(LGRAY)
        self.c.setLineWidth(0.3)
        self.c.line(ML, self.y - row_h + 2*mm, W - MR, self.y - row_h + 2*mm)
        self.y -= row_h

    def table_header(self, cols):
        """Заголовок таблицы."""
        widths = [c[1] for c in cols]
        row_h = 7*mm
        self.check_space(row_h + 1*mm)
        x = ML
        self.c.setFillColor(DARK)
        self.c.rect(ML, self.y - row_h + 2*mm, CW, row_h, fill=1, stroke=0)
        for label, w in cols:
            self.c.setFillColor(WHITE)
            self.c.setFont('Helvetica-Bold', 8.5)
            self.c.drawString(x + 1.5*mm, self.y - 3*mm, label)
            x += w
        self.y -= row_h

    def table_row(self, values, cols, bg=None, colors=None):
        """Строка таблицы."""
        row_h = 7*mm
        self.check_space(row_h + 1*mm)
        if bg:
            self.c.setFillColor(bg)
            self.c.rect(ML, self.y - row_h + 2*mm, CW, row_h, fill=1, stroke=0)
        x = ML
        for i, (val, w) in enumerate(zip(values, [c[1] for c in cols])):
            col = colors[i] if colors and i < len(colors) else DARK
            self.c.setFillColor(col)
            self.c.setFont('Helvetica', 8.5)
            val_str = str(val)
            if self.c.stringWidth(val_str, 'Helvetica', 8.5) > w - 2*mm:
                while self.c.stringWidth(val_str + '..', 'Helvetica', 8.5) > w - 2*mm and val_str:
                    val_str = val_str[:-1]
                val_str += '..'
            self.c.drawString(x + 1.5*mm, self.y - 3*mm, val_str)
            x += w
        self.c.setStrokeColor(LGRAY)
        self.c.setLineWidth(0.3)
        self.c.line(ML, self.y - row_h + 2*mm, W - MR, self.y - row_h + 2*mm)
        self.y -= row_h

    def colored_badge_inline(self, text, color, text_color=WHITE, size=8):
        """Рисует маленький цветной бейдж по текущей позиции."""
        w = self.c.stringWidth(text, 'Helvetica-Bold', size) + 4*mm
        h = 4*mm
        self.c.setFillColor(color)
        self.c.roundRect(ML, self.y - 1*mm, w, h, 1.5, fill=1, stroke=0)
        self.c.setFillColor(text_color)
        self.c.setFont('Helvetica-Bold', size)
        self.c.drawString(ML + 2*mm, self.y + 0.5*mm, text)
        self.y -= 6*mm

    def week_block(self, week_num, title, period, status_color, items):
        """Блок-карточка недели для роадмапа."""
        bh = 8*mm + len(items) * 5*mm + 4*mm
        self.check_space(bh + 2*mm)
        # Фон
        self.c.setFillColor(VLGRAY)
        self.c.roundRect(ML, self.y - bh, CW, bh, 3, fill=1, stroke=0)
        # Левая полоска
        self.c.setFillColor(status_color)
        self.c.roundRect(ML, self.y - bh, 5, bh, 3, fill=1, stroke=0)
        # Заголовок блока
        self.c.setFillColor(DARK)
        self.c.setFont('Helvetica-Bold', 11)
        self.c.drawString(ML + 4*mm, self.y - 6*mm, f'Неделя {week_num}: {title}')
        self.c.setFillColor(GRAY)
        self.c.setFont('Helvetica', 8.5)
        self.c.drawString(ML + 4*mm, self.y - 11*mm, period)
        # Статус
        self.c.setFillColor(status_color)
        status_text = '✓ Завершено'
        sw = self.c.stringWidth(status_text, 'Helvetica-Bold', 8) + 4*mm
        self.c.roundRect(W - MR - sw - 2, self.y - 9*mm, sw, 5*mm, 2, fill=1, stroke=0)
        self.c.setFillColor(WHITE)
        self.c.setFont('Helvetica-Bold', 8)
        self.c.drawString(W - MR - sw, self.y - 6.5*mm, status_text)
        # Пункты
        iy = self.y - 15*mm
        for item in items:
            self.c.setFillColor(status_color)
            self.c.circle(ML + 7*mm, iy + 1.5*mm, 1.2*mm, fill=1, stroke=0)
            self.c.setFillColor(DARK)
            self.c.setFont('Helvetica', 9)
            self.c.drawString(ML + 10*mm, iy, item)
            iy -= 5*mm
        self.y -= bh + 3*mm

    def info_box(self, title, lines, color=BLUE):
        """Блок с иконкой и текстом для важных фактов."""
        bh = 6*mm + len(lines) * 5*mm + 4*mm
        self.check_space(bh + 2*mm)
        self.c.setFillColor(HexColor('#EFF6FF'))
        self.c.roundRect(ML, self.y - bh, CW, bh, 3, fill=1, stroke=0)
        self.c.setFillColor(color)
        self.c.roundRect(ML, self.y - bh, 4, bh, 3, fill=1, stroke=0)
        self.c.setFillColor(color)
        self.c.setFont('Helvetica-Bold', 10)
        self.c.drawString(ML + 5*mm, self.y - 5*mm, title)
        for i, line in enumerate(lines):
            self.c.setFillColor(DARK)
            self.c.setFont('Helvetica', 9.5)
            self.c.drawString(ML + 5*mm, self.y - 11*mm - i * 5*mm, line)
        self.y -= bh + 3*mm


# ─── СОДЕРЖИМОЕ ──────────────────────────────────────────────────────────────

def build_report(path):
    doc = Doc(path)
    c = doc.c

    # ══════════════════════════════════════════════════════════════════════════
    # ОБЛОЖКА
    # ══════════════════════════════════════════════════════════════════════════
    doc.page = 1

    # Фон
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Декоративные полосы
    c.setFillColor(BLUE)
    c.rect(0, 0, 8*mm, H, fill=1, stroke=0)
    c.setFillColor(HexColor('#F59E0B'))
    c.rect(8*mm, 0, 3*mm, H, fill=1, stroke=0)

    # Верхний блок
    c.setFillColor(HexColor('#1E293B'))
    c.rect(0, H - 40*mm, W, 40*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 9)
    c.drawString(18*mm, H - 12*mm, 'КОНКУРС T2  ·  ВНЕДРЕНИЕ ИИ-ТЕХНОЛОГИЙ  ·  МОРДОВИЯ 2026')

    # Главный заголовок
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 34)
    c.drawString(18*mm, H - 70*mm, 'T2 AI Route Planner')
    c.setFillColor(HexColor('#F59E0B'))
    c.setFont('Helvetica-Bold', 17)
    c.drawString(18*mm, H - 83*mm, 'Проектная документация')

    # Разделитель
    c.setStrokeColor(HexColor('#374151'))
    c.setLineWidth(1.5)
    c.line(18*mm, H - 91*mm, W - 18*mm, H - 91*mm)

    # Описание проекта
    c.setFillColor(HexColor('#94A3B8'))
    c.setFont('Helvetica', 10.5)
    desc_lines = [
        'AI-платформа оптимизации маршрутов и управления',
        'расписанием посещений торговых точек Мордовии.',
        'Разработана за 4 недели командой из 4 человек.',
    ]
    for i, line in enumerate(desc_lines):
        c.drawString(18*mm, H - 100*mm - i*13, line)

    # Мета-информация (блок)
    meta = [
        ('Период разработки', '6 января — 27 февраля 2026 (4 недели)'),
        ('Команда',           '3 разработчика + TL/PM'),
        ('Методология',       'Agile Lite (Kanban), 2-дневные итерации'),
        ('Статус',            'Production-Ready'),
        ('Сервер',            'Ubuntu 24.04, Docker Compose, Tailscale'),
        ('Репозиторий',       'github.com/JellyfishKa/T2_project'),
    ]
    my = H - 135*mm
    for key, val in meta:
        c.setFillColor(HexColor('#374151'))
        c.rect(18*mm, my - 7*mm, CW - 6*mm, 7.5*mm, fill=1, stroke=0)
        c.setFillColor(HexColor('#94A3B8'))
        c.setFont('Helvetica-Bold', 8.5)
        c.drawString(22*mm, my - 4*mm, key)
        c.setFillColor(WHITE)
        c.setFont('Helvetica', 8.5)
        c.drawString(75*mm, my - 4*mm, val)
        my -= 9*mm

    # Команда
    c.setFillColor(HexColor('#374151'))
    c.rect(18*mm, 65*mm, CW - 6*mm, 7*mm, fill=1, stroke=0)
    c.setFillColor(HexColor('#94A3B8'))
    c.setFont('Helvetica-Bold', 9)
    c.drawString(22*mm, 68*mm, 'КОМАНДА:')
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 9)
    c.drawString(50*mm, 68*mm, 'Маклаков С. (TL/PM)  ·  Кижаев Р. (Backend)  ·  Наумкин В. (Frontend)  ·  Мукасеев Д. (ML)')

    # Нижняя строка
    c.setFillColor(HexColor('#1E293B'))
    c.rect(0, 0, W, 16*mm, fill=1, stroke=0)
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 8)
    c.drawCentredString(W/2, 6*mm, 'Конкурс: «Внедрение ИИ-технологий для повышения эффективности работы розничной сети Т2»')

    # Версия
    c.setFillColor(HexColor('#475569'))
    c.setFont('Helvetica', 8)
    c.drawRightString(W - 5*mm, 6*mm, 'v1.2.0  ·  Февраль 2026')

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 2: ОГЛАВЛЕНИЕ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('Содержание')
    doc.spacer(3*mm)

    toc = [
        ('1.', 'Задача и требования конкурса',       '3'),
        ('2.', 'Решение и архитектура системы',       '4'),
        ('3.', 'База данных',                         '5'),
        ('4.', 'Роадмап разработки',                  '6'),
        ('   4.1', 'Неделя 1 — Инфраструктура + LLM',  '6'),
        ('   4.2', 'Неделя 2 — MVP',                    '7'),
        ('   4.3', 'Неделя 3 — Production-Ready',       '7'),
        ('   4.4', 'Неделя 4 — Расписание + Excel',     '8'),
        ('5.', 'Ключевые функции',                    '9'),
        ('   5.1', 'ИИ-оптимизация маршрутов',          '9'),
        ('   5.2', 'Планировщик расписания A/B/C/D',    '10'),
        ('   5.3', 'Форс-мажоры',                       '11'),
        ('   5.4', 'Excel-экспорт и аналитика',         '12'),
        ('6.', 'Полный список API-эндпоинтов',        '13'),
        ('7.', 'Технологический стек',                '14'),
        ('8.', 'Тестирование и качество',             '15'),
        ('9.', 'Развёртывание',                       '16'),
        ('10.', 'Соответствие конкурсным требованиям','17'),
    ]

    for num, title, page in toc:
        doc.check_space(7*mm)
        is_main = not num.startswith('  ')
        c.setFillColor(DARK if is_main else GRAY)
        c.setFont('Helvetica-Bold' if is_main else 'Helvetica', 10 if is_main else 9.5)
        c.drawString(ML + (0 if is_main else 5*mm), doc.y, f'{num}  {title}')
        c.setFillColor(LGRAY)
        dots_x = ML + 4*mm
        dots_end = W - MR - 10*mm
        line_y = doc.y - 1.5*mm
        c.setDash(1, 3)
        c.setStrokeColor(LGRAY)
        c.setLineWidth(0.5)
        c.line(dots_x + c.stringWidth(f'{num}  {title}', 'Helvetica-Bold' if is_main else 'Helvetica', 10 if is_main else 9.5), line_y, dots_end, line_y)
        c.setDash()
        c.setFillColor(DARK if is_main else GRAY)
        c.setFont('Helvetica', 9)
        c.drawRightString(W - MR, doc.y, page)
        doc.y -= (7*mm if is_main else 6*mm)

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 3: ЗАДАЧА И ТРЕБОВАНИЯ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('1. Задача и требования конкурса')
    doc.spacer(2*mm)

    doc.subsection('1.1 Контекст задачи')
    doc.para('T2 поставила задачу разработать программу мониторинга и составления маршрутов торговой команды в реальном времени для сети из 250 торговых точек в Мордовии (г.о. Саранск + 22 района).')
    doc.spacer(2*mm)

    doc.subsection('1.2 Функциональные требования (из PDF конкурса)')

    doc.para('Блок 1: Формирование оптимизированных маршрутов', bold=True)
    reqs1 = [
        'Расчёт маршрутов с минимизацией километража',
        'Учёт рабочего времени торговых представителей (9:00–18:00, пн–пт)',
        'Сегментация ТТ по категориям A/B/C/D с учётом приоритетности посещения',
        'Гарантия 100% охвата базы ТТ, включая автоперенос пропущенных точек',
    ]
    for r in reqs1:
        doc.bullet(r)
    doc.spacer(2*mm)

    doc.para('Блок 2: Форс-мажоры', bold=True)
    reqs2 = [
        'Анализ факторов: болезнь сотрудника, погодные условия, неисправность транспорта',
        'Автоматизированное перераспределение ТТ на других сотрудников',
        'Равномерное распределение по ближайшим доступным дням',
    ]
    for r in reqs2:
        doc.bullet(r)
    doc.spacer(2*mm)

    doc.para('Блок 3: Аналитика и выгрузка данных', bold=True)
    reqs3 = [
        'Статистика по посещаемости торговых точек',
        'Отчёт о времени нахождения торгового представителя на каждой ТТ',
        'Детализация по времени и дате посещения каждой точки',
        'Учёт количества выходов торгового представителя на маршрут',
    ]
    for r in reqs3:
        doc.bullet(r)
    doc.spacer(3*mm)

    doc.subsection('1.3 Данные организатора')
    cols = [('Территория', 85*mm), ('ТТ', 25*mm), ('Категория', 30*mm), ('Частота', 30*mm)]
    doc.table_header(cols)
    districts = [
        ('г.о. Саранск', '30', 'A (20%)', '3 раза/мес'),
        ('Ардатовский, Атяшевский, Атюрьевский р-ны', '30', 'B (30%)', '2 раза/мес'),
        ('Дубёнский, Ельниковский, Зубово-Полянский р-ны', '30', 'C (20%)', '1 раз/мес'),
        ('Инсарский, Ичалковский, Кадошкинский р-ны', '30', 'D (30%)', '1 раз/квартал'),
        ('...ещё 12 районов (по 10 ТТ каждый)', '120', 'Смешанное', 'По категории'),
        ('ИТОГО', '250 ТТ', '4 категории', '4 сотрудника'),
    ]
    for i, row in enumerate(districts):
        bg = VLGRAY if i % 2 == 0 else None
        last = (i == len(districts) - 1)
        doc.table_row(row, cols, bg=HexColor('#E0F2FE') if last else bg,
                      colors=[DARK, BLUE if last else DARK, DARK, DARK])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 4: РЕШЕНИЕ И АРХИТЕКТУРА
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('2. Решение и архитектура системы')
    doc.spacer(2*mm)

    doc.subsection('2.1 Обзор решения')
    doc.para('Создана полноценная веб-платформа AI Route Planner, включающая: REST API бэкенд на FastAPI, Vue 3 SPA фронтенд, PostgreSQL БД, два локальных LLM (Qwen 0.5B + Llama 1B), алгоритм планировщика расписания, систему форс-мажоров, Excel-экспорт и аналитику. Всё запускается в Docker Compose одной командой.')
    doc.spacer(3*mm)

    doc.subsection('2.2 Высокоуровневая архитектура')

    # ASCII-схема архитектуры
    arch_lines = [
        ('┌──────────────────────────────────────────────────────────────┐', LGRAY),
        ('│                     БРАУЗЕР (Vue 3 SPA)                      │', BLUE),
        ('│  Home · Dashboard · Optimize · Analytics · Schedule · Reps  │', BLUE),
        ('└──────────────────────────┬───────────────────────────────────┘', LGRAY),
        ('                           │ HTTP (Nginx proxy)                 ', GRAY),
        ('┌──────────────────────────▼───────────────────────────────────┐', LGRAY),
        ('│              BACKEND FastAPI (Python 3.11)                    │', DARK),
        ('│  /optimize  /schedule  /reps  /force_majeure  /export  /reps │', DARK),
        ('└──────┬─────────────┬────────────────┬─────────────────────────┘', LGRAY),
        ('       │             │                │                           ', GRAY),
        ('  ┌────▼───┐   ┌────▼────┐   ┌───────▼──────┐                  ', LGRAY),
        ('  │PostgreSQL│  │  Redis  │   │  Qwen / Llama │                 ', DARK),
        ('  │  (БД)  │   │ (кеш)  │   │  (GGUF/local) │                 ', DARK),
        ('  └────────┘   └─────────┘   └───────────────┘                 ', LGRAY),
    ]
    c.setFont('Courier', 8)
    for line, color in arch_lines:
        doc.check_space(4.5*mm)
        c.setFillColor(color)
        c.drawString(ML + 2*mm, doc.y, line)
        doc.y -= 4.5*mm

    doc.spacer(3*mm)
    doc.subsection('2.3 Основные компоненты')
    components = [
        ('SchedulePlanner',        'Алгоритм построения месячного плана визитов (A×3, B×2, C×1, D×квартал)'),
        ('Optimizer (3 варианта)', 'Greedy nearest-neighbor · Priority-first (A→D) · Balanced (60% dist + 40% prio)'),
        ('ForceMajeureService',    'Round-robin перераспределение визитов при форс-мажоре'),
        ('LLM: Qwen 0.5B',        'Генерация pros/cons для вариантов маршрута (GGUF, ~400 MB)'),
        ('LLM: Llama 1B',         'Альтернативная модель по выбору пользователя (GGUF, ~808 MB)'),
        ('Excel Export (openpyxl)','4 листа: Расписание / Журнал визитов / Статистика ТТ / Активность ТП'),
        ('Insights API',           'Охват ТТ, план/факт, по категориям, по районам, активность сотрудников'),
    ]
    cols_c = [('Компонент', 65*mm), ('Описание', CW - 65*mm)]
    doc.table_header(cols_c)
    for i, (k, v) in enumerate(components):
        doc.table_row([k, v], cols_c, bg=VLGRAY if i % 2 == 0 else None,
                      colors=[BLUE, DARK])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 5: БАЗА ДАННЫХ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('3. Схема базы данных')
    doc.spacer(2*mm)

    doc.para('PostgreSQL, 8 таблиц. ORM: SQLAlchemy async. Автоматические миграции через Alembic + AUTO ALTER TABLE при старте контейнера.')
    doc.spacer(3*mm)

    tables = [
        ('locations', 'Торговые точки',
         'id (PK) · name · lat · lon · category (A/B/C/D) · city · district · address · time_window_start · time_window_end'),
        ('sales_reps', 'Торговые представители',
         'id (PK) · name · status (active/sick/vacation/unavailable) · created_at'),
        ('visit_schedule', 'Плановые визиты',
         'id (PK) · location_id (FK) · rep_id (FK) · planned_date · status (planned/completed/skipped/rescheduled/cancelled) · created_at'),
        ('visit_log', 'Фактические визиты',
         'id (PK) · schedule_id (FK) · location_id (FK) · rep_id (FK) · visited_date · time_in · time_out · notes · created_at'),
        ('force_majeure_events', 'Форс-мажоры',
         'id (PK) · type (illness/weather/vehicle_breakdown/other) · rep_id (FK) · event_date · description · affected_tt_ids (JSON) · redistributed_to (JSON) · created_at'),
        ('routes', 'История LLM-маршрутов',
         'id (PK) · name · locations_order (JSON) · total_distance · total_time · total_cost · model_used · created_at'),
        ('metrics', 'Метрики LLM-моделей',
         'id (PK) · route_id (FK) · model_name · response_time_ms · quality_score · cost · timestamp'),
        ('optimization_results', 'Сравнение оптимизаций',
         'id (PK) · original_route (JSON) · optimized_route (JSON) · improvement_percentage · model_used · created_at'),
    ]

    for tname, tdesc, tfields in tables:
        doc.check_space(22*mm)
        # Заголовок таблицы
        c.setFillColor(HexColor('#1E40AF'))
        c.roundRect(ML, doc.y - 6*mm, CW, 7*mm, 2, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9.5)
        c.drawString(ML + 3*mm, doc.y - 3.5*mm, tname)
        c.setFillColor(HexColor('#BAD0F8'))
        c.setFont('Helvetica', 8.5)
        c.drawString(ML + 55*mm, doc.y - 3.5*mm, f'— {tdesc}')
        doc.y -= 7*mm
        # Поля
        c.setFillColor(VLGRAY)
        c.roundRect(ML, doc.y - 10*mm, CW, 11*mm, 2, fill=1, stroke=0)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 8)
        # Переносим длинные поля
        max_w = CW - 4*mm
        fields_text = tfields
        if c.stringWidth(fields_text, 'Helvetica', 8) <= max_w:
            c.drawString(ML + 3*mm, doc.y - 3.5*mm, fields_text)
            c.drawString(ML + 3*mm, doc.y - 8*mm, '')
        else:
            # Две строки
            words = fields_text.split(' · ')
            line1, line2 = '', ''
            for word in words:
                test = line1 + (' · ' if line1 else '') + word
                if c.stringWidth(test, 'Helvetica', 8) <= max_w:
                    line1 = test
                else:
                    line2 = (line2 + ' · ' if line2 else '') + word
            c.drawString(ML + 3*mm, doc.y - 3.5*mm, line1)
            c.drawString(ML + 3*mm, doc.y - 8*mm, line2)
        doc.y -= 11*mm
        doc.spacer(1.5*mm)

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 6: РОАДМАП
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('4. Роадмап разработки')
    doc.spacer(2*mm)
    doc.para('Проект разработан за 4 недели (6 января — 27 февраля 2026) командой из 4 человек методологией Agile Lite (Kanban). Каждая неделя — отдельный спринт с конкретными целями и acceptance criteria.')
    doc.spacer(3*mm)

    doc.week_block(1, 'Инфраструктура + LLM-интеграция', '6–13 января 2026', GREEN, [
        'Инициализация репозитория, структура папок, CI/CD (GitHub Actions)',
        'FastAPI backend: базовые эндпоинты, SQLAlchemy, PostgreSQL',
        'Интеграция LLM: QwenClient + LlamaClient (GGUF через llama-cpp-python)',
        'Vue 3 фронтенд: layout, роутинг, mock API',
        'ML: бенчмарк моделей, quality evaluator',
        'Docker Compose: 4 сервиса (postgres, redis, backend, frontend, nginx)',
        'Результат: базовая оптимизация маршрутов работает (POST /optimize)',
    ])

    doc.week_block(2, 'MVP — полная оптимизация', '14–21 января 2026', BLUE, [
        'Единый /optimize endpoint с fallback (Qwen → Llama → Greedy)',
        'CRUD /locations с поддержкой CSV/JSON загрузки',
        'Dashboard: статистика, метрики LLM, история маршрутов',
        'Analytics: графики Chart.js (расстояние, стоимость, качество)',
        'ML: сравнение Qwen vs Llama, benchmark runner',
        'Frontend: OptimizeView, DashboardView — полностью рабочие',
        'Результат: MVP feature-complete, все страницы работают',
    ])

    doc.week_block(3, 'Production-Ready', '22–31 января 2026', ORANGE, [
        'Удалена T-Pro модель (16+ GB RAM, нестабильна)',
        'Финальная цепочка: Qwen → Greedy (Llama — по выбору, не одновременно)',
        'Docker multi-stage builds оптимизированы',
        'CI/CD: GitHub Actions, тесты, линтинг, coverage',
        'Nginx: SPA routing, API reverse proxy',
        'Результат: стабильная production-ready система',
    ])

    doc.week_block(4, 'Расписание + Excel + Аналитика', '24–27 февраля 2026', HexColor('#7C3AED'), [
        'БД: 4 новые таблицы (SalesRep, VisitSchedule, VisitLog, ForceMajeureEvent)',
        'SchedulePlanner: алгоритм A/B/C/D, MAX 14 ТТ/день, auto-reschedule skipped',
        'ForceMajeureService: round-robin перераспределение, 4 типа инцидентов',
        'LLM варианты: /optimize/variants (3 алгоритма + pros/cons от LLM)',
        'Excel export: 4 листа (Расписание, Журнал, Статистика, Активность ТП)',
        'Analytics: реальный /insights API + UI с охватом ТТ по категориям',
        'ScheduleView + RepsView: новые страницы, Day modal, спиннер, кнопки',
        'Результат: все конкурсные требования выполнены',
    ])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 7–9: КЛЮЧЕВЫЕ ФУНКЦИИ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('5. Ключевые функции')
    doc.spacer(2*mm)

    doc.subsection('5.1 ИИ-оптимизация маршрутов')
    doc.para('Система предлагает три детерминированных алгоритма, LLM используется для генерации pros/cons (оценки) каждого варианта — это задача, с которой малые модели справляются надёжно.')
    doc.spacer(2*mm)

    algos = [
        ('Вариант 1', 'Greedy (минимум расстояния)',
         'Nearest-neighbor с матрицей расстояний Haversine. Начинает с точки высшего приоритета. Минимизирует суммарный километраж.'),
        ('Вариант 2', 'Priority-first (A→B→C→D)',
         'Сначала все точки A (greedy внутри группы), затем B, C, D. Каждая группа начинается с ближайшей к последней посещённой точке.'),
        ('Вариант 3', 'Balanced (60% dist + 40% prio)',
         'Взвешенный score = 0.6×distance + 0.4×priority_penalty (A=0км, B=3км, C=8км, D=15км). Компромисс между расстоянием и важностью.'),
    ]

    cols_a = [('', 25*mm), ('Алгоритм', 50*mm), ('Описание', CW - 75*mm)]
    doc.table_header(cols_a)
    variant_colors = [BLUE, GREEN, HexColor('#7C3AED')]
    for i, (num, name, desc) in enumerate(algos):
        bg = VLGRAY if i % 2 == 0 else None
        doc.table_row([num, name, desc], cols_a, bg=bg, colors=[variant_colors[i], DARK, GRAY])

    doc.spacer(3*mm)
    doc.para('После вычисления метрик (расстояние, время, стоимость, quality_score) — вызывается LLM для оценки:', color=GRAY)
    doc.spacer(1*mm)
    doc.bullet('LLM получает метрики 3 вариантов + краткое описание', marker_color=BLUE)
    doc.bullet('Генерирует 2 pros и 2 cons для каждого варианта на русском языке', marker_color=BLUE)
    doc.bullet('Graceful fallback: если LLM не ответила — варианты показываются без текста', marker_color=BLUE)
    doc.bullet('Timeout: 90 секунд на LLM-оценку, frontend показывает прогресс-бар', marker_color=BLUE)

    doc.spacer(3*mm)
    doc.subsection('5.2 Планировщик расписания (SchedulePlanner)')
    doc.para('Алгоритм автоматически генерирует месячный план посещений для всей команды.')
    doc.spacer(2*mm)

    plan_steps = [
        ('Шаг 1', 'Определяет рабочие дни месяца (пн–пт, без выходных)'),
        ('Шаг 2', 'Для каждой ТТ по категории вычисляет плановые даты: A→нед.1,2,3; B→нед.1,3; C→середина; D→квартал'),
        ('Шаг 3', 'Собирает пул задач (location_id, planned_date, category), сортирует по (дата, приоритет)'),
        ('Шаг 4', 'Round-robin распределение по сотрудникам с балансировкой загрузки'),
        ('Шаг 5', 'Ограничение: MAX 14 ТТ/день на сотрудника (14 = floor(510мин / 35мин/ТТ))'),
        ('Шаг 6', 'Если ТТ помечена как skipped — автоматически создаётся новая запись на ближайший свободный день'),
        ('Шаг 7', 'Batch insert в visit_schedule, логирование coverage_pct'),
    ]

    for step, desc in plan_steps:
        doc.check_space(7*mm)
        c.setFillColor(GREEN)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(ML, doc.y, step + ':')
        c.setFillColor(DARK)
        c.setFont('Helvetica', 9)
        c.drawString(ML + 15*mm, doc.y, desc)
        doc.y -= 6*mm

    doc.new_page()
    doc._draw_page_chrome()

    doc.subsection('5.3 Форс-мажоры (ForceMajeureService)')
    doc.spacer(2*mm)

    doc.para('Поддерживаются 4 типа форс-мажоров. При регистрации инцидента система автоматически:')
    fm_types = [
        ('illness',           'Болезнь',              'Дополнительно меняет rep.status → sick'),
        ('weather',           'Погодные условия',      'Только перераспределение ТТ'),
        ('vehicle_breakdown', 'Неисправность транспорта','Только перераспределение ТТ'),
        ('other',             'Другое',                'Произвольное описание'),
    ]

    cols_fm = [('Тип',  40*mm), ('Название', 55*mm), ('Поведение системы', CW - 95*mm)]
    doc.table_header(cols_fm)
    for i, (typ, name, behavior) in enumerate(fm_types):
        doc.table_row([typ, name, behavior], cols_fm,
                      bg=VLGRAY if i % 2 == 0 else None,
                      colors=[BLUE, DARK, GRAY])

    doc.spacer(3*mm)
    doc.para('Алгоритм перераспределения:', bold=True)
    doc.spacer(1*mm)
    fm_steps = [
        'Находит все planned визиты сотрудника на дату инцидента',
        'Получает список активных сотрудников (status=active, id ≠ пострадавший)',
        'Делит ТТ равномерно методом round-robin',
        'Для каждого сотрудника ищет ближайший рабочий день с capacity < 14 ТТ',
        'Создаёт новые visit_schedule (status=rescheduled), отменяет старые (cancelled)',
        'Записывает ForceMajeureEvent с redistributed_to JSON-полем',
    ]
    for s in fm_steps:
        doc.bullet(s)

    doc.spacer(3*mm)
    doc.subsection('5.4 Excel-интеграция')
    doc.para('Полный цикл: экспорт заполненных данных → внешнее заполнение → импорт обратно.')
    doc.spacer(2*mm)

    excel_sheets = [
        ('Лист 1', 'Расписание',      'Все плановые визиты с датами, сотрудниками, категориями ТТ, статусами'),
        ('Лист 2', 'Журнал визитов',  'Выполненные визиты с time_in, time_out, длительностью в минутах'),
        ('Лист 3', 'Статистика ТТ',   'Каждая ТТ: запланировано/выполнено/пропущено, % выполнения (цвет)'),
        ('Лист 4', 'Активность ТП',   'Каждый сотрудник: выходов на маршрут, ТТ посещено, % выполнения'),
    ]

    cols_ex = [('', 20*mm), ('Лист', 40*mm), ('Содержимое', CW - 60*mm)]
    doc.table_header(cols_ex)
    sheet_colors = [BLUE, GREEN, YELLOW, RED]
    for i, (num, name, content) in enumerate(excel_sheets):
        doc.table_row([num, name, content], cols_ex,
                      bg=VLGRAY if i % 2 == 0 else None,
                      colors=[sheet_colors[i], DARK, GRAY])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 10: API ЭНДПОИНТЫ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('6. Полный список API-эндпоинтов (33 эндпоинта)')
    doc.spacer(2*mm)

    endpoint_groups = [
        ('Система', [
            ('GET',  '/health',                      'Health check (DB + LLM статусы)'),
            ('GET',  '/api/v1/health',               'Health check для фронтенда'),
        ]),
        ('Оптимизация маршрутов', [
            ('POST', '/api/v1/optimize',             'Greedy-оптимизация (< 100 мс)'),
            ('POST', '/api/v1/qwen/optimize',        'Прямой вызов Qwen'),
            ('POST', '/api/v1/llama/optimize',       'Прямой вызов Llama'),
            ('POST', '/api/v1/optimize/variants',    '3 варианта + LLM pros/cons (timeout 180 сек)'),
            ('POST', '/api/v1/optimize/confirm',     'Сохранение выбранного варианта'),
        ]),
        ('Торговые точки', [
            ('GET',  '/api/v1/locations/',           'Список ТТ с пагинацией'),
            ('POST', '/api/v1/locations/',           'Создание ТТ'),
            ('GET',  '/api/v1/locations/{id}',       'Детали ТТ'),
            ('PUT',  '/api/v1/locations/{id}',       'Обновление ТТ'),
            ('DELETE','/api/v1/locations/{id}',      'Удаление ТТ'),
            ('POST', '/api/v1/locations/upload',     'Загрузка из XLSX/CSV/JSON'),
        ]),
        ('Торговые представители', [
            ('GET',  '/api/v1/reps',                 'Список ТП'),
            ('POST', '/api/v1/reps',                 'Создание ТП'),
            ('PATCH','/api/v1/reps/{id}',            'Обновление (статус, имя)'),
            ('DELETE','/api/v1/reps/{id}',           'Удаление ТП'),
        ]),
        ('Расписание', [
            ('POST', '/api/v1/schedule/generate',    'Генерация месячного плана'),
            ('GET',  '/api/v1/schedule/',            'Полный план на месяц'),
            ('GET',  '/api/v1/schedule/daily',       'Маршруты всех ТП на конкретный день'),
            ('GET',  '/api/v1/schedule/{rep_id}',    'План конкретного ТП'),
            ('PATCH','/api/v1/schedule/{id}',        'Обновление статуса визита (skipped → автоперенос)'),
        ]),
        ('Форс-мажоры и визиты', [
            ('POST', '/api/v1/force_majeure',        'Форс-мажор + перераспределение ТТ'),
            ('GET',  '/api/v1/force_majeure',        'История форс-мажоров'),
            ('POST', '/api/v1/visits',               'Фиксация визита (time_in/time_out)'),
            ('GET',  '/api/v1/visits/',              'История визитов с фильтрами'),
            ('GET',  '/api/v1/visits/stats',         'Статистика посещаемости за месяц'),
        ]),
        ('Аналитика и экспорт', [
            ('GET',  '/api/v1/metrics',              'Метрики LLM-моделей'),
            ('GET',  '/api/v1/insights',             'Охват ТТ, активность ТП, по районам'),
            ('GET',  '/api/v1/routes/',              'История маршрутов (пагинация)'),
            ('GET',  '/api/v1/routes/{id}',          'Детали маршрута с метриками'),
            ('GET',  '/api/v1/export/schedule',      'Excel-отчёт 4 листа (?month=YYYY-MM)'),
            ('GET',  '/api/v1/benchmark/compare',    'Сравнение LLM-моделей'),
        ]),
    ]

    method_colors = {'GET': GREEN, 'POST': BLUE, 'PATCH': ORANGE, 'PUT': HexColor('#7C3AED'), 'DELETE': RED}

    for group, endpoints in endpoint_groups:
        doc.check_space(10*mm + len(endpoints) * 7*mm)
        # Заголовок группы
        doc.c.setFillColor(HexColor('#F1F5F9'))
        doc.c.rect(ML, doc.y - 6*mm, CW, 6.5*mm, fill=1, stroke=0)
        doc.c.setFillColor(DARK)
        doc.c.setFont('Helvetica-Bold', 9)
        doc.c.drawString(ML + 2*mm, doc.y - 3.5*mm, group)
        doc.y -= 7*mm

        for method, epath, desc in endpoints:
            doc.check_space(7*mm)
            mcol = method_colors.get(method, GRAY)
            # Метод-бейдж
            bw = 15*mm
            doc.c.setFillColor(mcol)
            doc.c.roundRect(ML + 2*mm, doc.y - 4.5*mm, bw, 5*mm, 1.5, fill=1, stroke=0)
            doc.c.setFillColor(WHITE)
            doc.c.setFont('Helvetica-Bold', 7.5)
            doc.c.drawCentredString(ML + 2*mm + bw/2, doc.y - 2.5*mm, method)
            # Path
            doc.c.setFillColor(DARK)
            doc.c.setFont('Courier', 8.5)
            doc.c.drawString(ML + 19*mm, doc.y - 2.5*mm, epath)
            # Описание
            doc.c.setFillColor(GRAY)
            doc.c.setFont('Helvetica', 8.5)
            doc.c.drawString(ML + 90*mm, doc.y - 2.5*mm, desc)
            doc.c.setStrokeColor(LGRAY)
            doc.c.setLineWidth(0.3)
            doc.c.line(ML, doc.y - 5*mm, W - MR, doc.y - 5*mm)
            doc.y -= 6.5*mm

        doc.spacer(2*mm)

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 11: ТЕХНОЛОГИИ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('7. Технологический стек')
    doc.spacer(2*mm)

    tech_sections = [
        ('Backend', BLUE, [
            ('Язык',          'Python 3.11+'),
            ('Фреймворк',     'FastAPI (async, Pydantic v2)'),
            ('ORM',           'SQLAlchemy 2.0 (async) + Alembic'),
            ('База данных',   'PostgreSQL 15 + asyncpg driver'),
            ('Кеш',          'Redis 7'),
            ('LLM Runtime',   'llama-cpp-python 0.3.16 (GGUF)'),
            ('Модель 1',      'Qwen2-0.5B-Instruct Q4_K_M (~400 MB, ~0.6 GB RAM)'),
            ('Модель 2',      'Llama-3.2-1B-Instruct Q4_K_M (~808 MB, ~1.2 GB RAM)'),
            ('Excel',         'openpyxl 3.1.5 (чтение + запись)'),
            ('Тестирование',  'pytest + pytest-asyncio (61 тест, 64% coverage)'),
        ]),
        ('Frontend', GREEN, [
            ('Фреймворк',     'Vue 3 + Vite 5 + TypeScript'),
            ('Стилизация',    'TailwindCSS 3'),
            ('Графики',       'Chart.js 4 + vue-chartjs'),
            ('HTTP',         'Axios (с retry + timeout)'),
            ('Тестирование',  'Vitest + Vue Test Utils (182 теста, ~70% coverage)'),
            ('Страницы',      'Home · Dashboard · Optimize · Analytics · Schedule · Reps'),
        ]),
        ('DevOps & Infrastructure', DARK, [
            ('Контейнеры',    'Docker + Docker Compose (4 сервиса)'),
            ('Реверс-прокси', 'Nginx (SPA routing + API proxy)'),
            ('CI/CD',        'GitHub Actions (lint + test + coverage)'),
            ('Сервер',        'Ubuntu 24.04, ~55 GB disk, Tailscale VPN'),
            ('Адрес',         'http://100.120.184.98 (фронт) · :8000 (API) · :8000/docs (Swagger)'),
        ]),
    ]

    for section, color, items in tech_sections:
        doc.subsection(section, color)
        cols_t = [('Параметр', 50*mm), ('Значение', CW - 50*mm)]
        doc.table_header(cols_t)
        for i, (k, v) in enumerate(items):
            doc.table_row([k, v], cols_t, bg=VLGRAY if i % 2 == 0 else None,
                          colors=[color, DARK])
        doc.spacer(3*mm)

    doc.subsection('Требования к серверу')
    srv_reqs = [
        ('RAM', 'Минимум 4 GB · Рекомендуется 8 GB (LLM занимает ~1.2 GB)'),
        ('Диск', 'Минимум 8 GB · Рекомендуется 15 GB (модели + образы)'),
        ('CPU', 'Минимум 2 ядра · Рекомендуется 4 ядра (inference быстрее)'),
        ('ОС', 'Ubuntu 22.04+ · Рекомендуется Ubuntu 24.04 LTS'),
    ]
    cols_s = [('Ресурс', 30*mm), ('Требования', CW - 30*mm)]
    doc.table_header(cols_s)
    for i, (k, v) in enumerate(srv_reqs):
        doc.table_row([k, v], cols_s, bg=VLGRAY if i % 2 == 0 else None)

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 12: ТЕСТИРОВАНИЕ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('8. Тестирование и качество')
    doc.spacer(2*mm)

    doc.subsection('8.1 Тестовое покрытие')
    cov_data = [
        ('Backend (pytest)',   '61',   '64%',  'pytest tests/ -v --cov=src'),
        ('Frontend (vitest)',  '182',  '~70%', 'npx vitest run --coverage'),
        ('ML/Benchmarks',      '15',   '~80%', 'python ml/benchmarks/llm_benchmark.py --mock'),
        ('TypeScript',         '0 ошибок', '100%', 'npx tsc --noEmit'),
        ('ИТОГО',              '258+', '~68%', 'GitHub Actions (CI)'),
    ]
    cols_cov = [('Компонент', 50*mm), ('Тестов', 25*mm), ('Coverage', 30*mm), ('Команда', CW - 105*mm)]
    doc.table_header(cols_cov)
    for i, row in enumerate(cov_data):
        is_last = (i == len(cov_data) - 1)
        doc.table_row(row, cols_cov,
                      bg=HexColor('#F0FDF4') if is_last else (VLGRAY if i % 2 == 0 else None),
                      colors=[DARK, BLUE, GREEN, GRAY])

    doc.spacer(3*mm)
    doc.subsection('8.2 Ключевые тест-кейсы')
    test_cases = [
        'POST /optimize — возвращает упорядоченный список location_ids за < 1 сек',
        'POST /optimize/variants — возвращает ровно 3 варианта с метриками',
        'POST /schedule/generate — все ТТ получают нужное кол-во визитов по категории',
        'PATCH /schedule/{id} status=skipped — автоматически создаётся rescheduled запись',
        'POST /force_majeure — все affected_tt_ids перераспределяются, ни одна не теряется',
        'GET /export/schedule — Excel файл содержит 4 листа, размер > 5 KB',
        'GET /insights — coverage_pct корректно считается от реальных ТТ в БД',
        'TypeScript: npx tsc --noEmit — 0 ошибок компиляции',
    ]
    for tc in test_cases:
        doc.bullet(tc, marker_color=GREEN)

    doc.spacer(3*mm)
    doc.subsection('8.3 Производительность')
    perf_data = [
        ('POST /optimize',          '< 100 мс',  'Greedy nearest-neighbor, чистый Python'),
        ('POST /optimize/variants',  '30–90 сек', 'Включает LLM inference для pros/cons'),
        ('POST /schedule/generate',  '< 500 мс',  '250 ТТ, 4 сотрудника, 1 месяц'),
        ('GET /export/schedule',     '< 2 сек',   'openpyxl генерация 4 листов'),
        ('POST /force_majeure',      '< 200 мс',  'БД-операции, без LLM'),
        ('LLM: первый запрос',       '5–15 сек',  'Загрузка GGUF модели в RAM'),
        ('LLM: последующие запросы', '3–8 сек',   'Модель уже в памяти (lazy load)'),
    ]
    cols_p = [('Эндпоинт / Операция', 65*mm), ('Время', 30*mm), ('Комментарий', CW - 95*mm)]
    doc.table_header(cols_p)
    for i, row in enumerate(perf_data):
        doc.table_row(row, cols_p,
                      bg=VLGRAY if i % 2 == 0 else None,
                      colors=[DARK, BLUE, GRAY])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 13: РАЗВЁРТЫВАНИЕ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('9. Развёртывание')
    doc.spacer(2*mm)

    doc.subsection('9.1 Быстрый старт (Docker Compose)')
    steps_deploy = [
        ('git clone https://github.com/JellyfishKa/T2_project.git && cd T2_project', DARK),
        ('cp backend/.env.example backend/.env  # заполнить DATABASE_PASSWORD', DARK),
        ('# Скачать LLM модели (~1.2 GB):', GRAY),
        ('python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download(\'Qwen/Qwen2-0.5B-Instruct-GGUF\', \'qwen2-0_5b-instruct-q4_k_m.gguf\', local_dir=\'backend/src/models/\')"', DARK),
        ('docker compose build  # 5–15 минут первый раз', DARK),
        ('docker compose up -d', DARK),
        ('curl http://localhost:8000/health  # {"status": "healthy"}', GREEN),
        ('# Загрузить данные:', GRAY),
        ('curl -X POST http://localhost:8000/api/v1/locations/upload -F "file=@mordovia_250.xlsx"', DARK),
        ('curl -X POST http://localhost:8000/api/v1/reps -H "Content-Type: application/json" -d \'{"name": "Иванов И.И."}\'', DARK),
        ('curl -X POST "http://localhost:8000/api/v1/schedule/generate" -H "Content-Type: application/json" -d \'{"month": "2026-02"}\'', DARK),
    ]
    c.setFont('Courier', 7.5)
    for code, color in steps_deploy:
        doc.check_space(5*mm)
        c.setFillColor(HexColor('#1E293B'))
        c.rect(ML, doc.y - 4*mm, CW, 4.5*mm, fill=1, stroke=0)
        c.setFillColor(color if color != DARK else HexColor('#E2E8F0'))
        c.drawString(ML + 2*mm, doc.y - 0.5*mm, code[:110])
        doc.y -= 5*mm

    doc.spacer(3*mm)
    doc.subsection('9.2 Переменные окружения (.env)')
    env_vars = [
        ('DATABASE_USER',     'postgres',                   'Пользователь PostgreSQL'),
        ('DATABASE_PASSWORD', 'СЕКРЕТНЫЙ_ПАРОЛЬ',           'Обязательно изменить!'),
        ('DATABASE_HOST',     'postgres',                   'Имя Docker сервиса (не localhost)'),
        ('DATABASE_NAME',     't2',                         'Имя базы данных'),
        ('QWEN_MODEL_ID',     'qwen2-0_5b-instruct-q4_k_m.gguf', 'Имя файла модели'),
        ('LLAMA_MODEL_ID',    'Llama-3.2-1B-Instruct-Q4_K_M.gguf', 'Имя файла модели'),
        ('CORS_ORIGINS',      'http://100.120.184.98,...',  'Разрешённые origins через запятую'),
    ]
    cols_env = [('Переменная', 55*mm), ('Пример', 60*mm), ('Описание', CW - 115*mm)]
    doc.table_header(cols_env)
    for i, row in enumerate(env_vars):
        doc.table_row(row, cols_env,
                      bg=VLGRAY if i % 2 == 0 else None,
                      colors=[BLUE, HexColor('#7C3AED'), GRAY])

    doc.spacer(3*mm)
    doc.subsection('9.3 Адреса сервисов')
    urls = [
        ('Фронтенд',       'http://100.120.184.98',           'Основной интерфейс (Nginx)'),
        ('Backend API',    'http://100.120.184.98:8000',       'REST API'),
        ('Swagger UI',     'http://100.120.184.98:8000/docs',  'Интерактивная документация'),
        ('PostgreSQL',     '100.120.184.98:5432',              'БД (DBeaver, pgAdmin)'),
    ]
    cols_u = [('Сервис', 35*mm), ('URL', 70*mm), ('Описание', CW - 105*mm)]
    doc.table_header(cols_u)
    for i, row in enumerate(urls):
        doc.table_row(row, cols_u, bg=VLGRAY if i % 2 == 0 else None, colors=[DARK, BLUE, GRAY])

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦА 14: СООТВЕТСТВИЕ ТРЕБОВАНИЯМ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('10. Соответствие конкурсным требованиям')
    doc.spacer(2*mm)

    doc.para('Итоговая таблица соответствия каждому пункту конкурсного задания T2.')
    doc.spacer(3*mm)

    requirements_full = [
        # Блок 1
        ('1.1', 'Расчёт маршрутов с минимизацией километража',
         '✓ Выполнено',
         'Алгоритм Greedy (Haversine + nearest-neighbor). /optimize + /optimize/variants. 15–20% экономия.',
         GREEN),
        ('1.2', 'Учёт рабочего времени торговых представителей',
         '✓ Выполнено',
         'SchedulePlanner: 09:00–18:00, пн–пт, MAX 14 ТТ/день (= 510 мин / 35 мин/ТТ).',
         GREEN),
        ('1.3', 'Сегментация ТТ по категориям A/B/C/D',
         '✓ Выполнено',
         'A=3x/мес, B=2x, C=1x, D=квартал. Алгоритм Priority-first. Цветовая кодировка в UI.',
         GREEN),
        ('1.4', '100% охват базы ТТ + механизм пропущенных точек',
         '✓ Выполнено',
         'coverage_pct в /insights. Если status=skipped → автоматически создаётся rescheduled визит.',
         GREEN),
        # Блок 2
        ('2.1', 'Анализ факторов форс-мажора (болезнь, погода, транспорт)',
         '✓ Выполнено',
         '4 типа: illness, weather, vehicle_breakdown, other. Хранятся в force_majeure_events.',
         GREEN),
        ('2.2', 'Автоматическое перераспределение ТТ',
         '✓ Выполнено',
         'Round-robin по активным ТП, поиск ближайшего дня с capacity < 14. Status → rescheduled.',
         GREEN),
        ('2.3', 'Равномерное распределение на ближайшие доступные дни',
         '✓ Выполнено',
         '_chunked_round_robin() + _find_available_day() до 30 дней вперёд.',
         GREEN),
        # Блок 3
        ('3.1', 'Статистика по посещаемости ТТ',
         '✓ Выполнено',
         '/visits/stats + /insights: план/факт, по категориям, по районам, coverage_pct.',
         GREEN),
        ('3.2', 'Отчёт о времени нахождения ТП на каждой ТТ',
         '✓ Выполнено',
         'time_in/time_out в VisitLog. Excel «Журнал визитов» с длительностью в минутах.',
         GREEN),
        ('3.3', 'Детализация по времени и дате посещения',
         '✓ Выполнено',
         'VisitLog: visited_date + time_in + time_out. API /visits + Excel лист 2.',
         GREEN),
        ('3.4', 'Количество выходов торгового представителя на маршрут',
         '✓ Выполнено',
         'outings_count в /insights (уникальные дни с визитами). Excel «Активность ТП».',
         GREEN),
        ('3.5', 'Выгрузка аналитической информации',
         '✓ Выполнено',
         'GET /export/schedule?month=YYYY-MM → Excel 4 листа. Одна кнопка в UI.',
         GREEN),
    ]

    cols_req = [('#', 10*mm), ('Требование', 68*mm), ('Статус', 22*mm), ('Реализация', CW - 100*mm)]
    doc.table_header(cols_req)

    current_block = None
    for num, req, status, impl, color in requirements_full:
        block = num.split('.')[0]
        if block != current_block:
            current_block = block
            block_titles = {'1': 'Блок 1: Оптимизация маршрутов', '2': 'Блок 2: Форс-мажоры', '3': 'Блок 3: Аналитика и выгрузка'}
            doc.check_space(7*mm)
            c.setFillColor(HexColor('#DBEAFE'))
            c.rect(ML, doc.y - 5.5*mm, CW, 6*mm, fill=1, stroke=0)
            c.setFillColor(BLUE)
            c.setFont('Helvetica-Bold', 9)
            c.drawString(ML + 2*mm, doc.y - 3*mm, block_titles.get(block, ''))
            doc.y -= 6.5*mm

        doc.check_space(9*mm)
        # Фон строки
        c.setFillColor(VLGRAY)
        c.rect(ML, doc.y - 7.5*mm, CW, 8*mm, fill=1, stroke=0)
        # Номер
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 8)
        c.drawString(ML + 1*mm, doc.y - 4*mm, num)
        # Требование
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(ML + 11*mm, doc.y - 2.5*mm, req[:55])
        # Статус
        c.setFillColor(color)
        c.roundRect(ML + 79*mm, doc.y - 5.5*mm, 21*mm, 5*mm, 2, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(ML + 89*mm, doc.y - 3*mm, status)
        # Реализация
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 7.5)
        impl_short = impl[:95] + '..' if len(impl) > 95 else impl
        c.drawString(ML + 101*mm, doc.y - 2.5*mm, impl_short)
        c.setStrokeColor(LGRAY)
        c.setLineWidth(0.3)
        c.line(ML, doc.y - 7.5*mm, W - MR, doc.y - 7.5*mm)
        doc.y -= 8.5*mm

    doc.spacer(3*mm)
    doc.info_box('Итог: все 12 конкурсных требований выполнены', [
        'Платформа реализует полный цикл: загрузка данных → планирование → трекинг → аналитика → экспорт',
        'Локальный ИИ: данные клиентов не покидают сервер компании',
        '33 API эндпоинта · 8 таблиц БД · 6 страниц UI · 258+ тестов',
    ], GREEN)

    doc.new_page()

    # ══════════════════════════════════════════════════════════════════════════
    # ПОСЛЕДНЯЯ СТРАНИЦА: КОНТАКТЫ И ССЫЛКИ
    # ══════════════════════════════════════════════════════════════════════════
    doc._draw_page_chrome()

    doc.section_header('Команда и контакты')
    doc.spacer(3*mm)

    team = [
        ('Сергей Маклаков', 'TL / PM',            'Архитектура, CI/CD, документация, координация', '@maklakov_tkdrm'),
        ('Роман Кижаев',    'Backend Engineer',    'FastAPI, SQLAlchemy, LLM-интеграция, Excel, алгоритмы', '[TBD]'),
        ('Владислав Наумкин','Frontend Engineer',  'Vue 3, TypeScript, UI/UX, прогресс-бар, 3 варианта', '[TBD]'),
        ('Дмитрий Мукасеев','ML / Analytics',      'SchedulePlanner, ForceMajeure, Insights, датасет 250 ТТ', '[TBD]'),
    ]

    cols_team = [('Имя', 48*mm), ('Роль', 45*mm), ('Зона ответственности', 65*mm), ('Контакт', CW - 158*mm)]
    doc.table_header(cols_team)
    for i, row in enumerate(team):
        doc.table_row(row, cols_team, bg=VLGRAY if i % 2 == 0 else None,
                      colors=[DARK, BLUE, GRAY, DARK])

    doc.spacer(5*mm)
    doc.subsection('Ссылки')

    links = [
        ('Репозиторий GitHub', 'https://github.com/JellyfishKa/T2_project'),
        ('Swagger UI (API)',    'http://100.120.184.98:8000/docs'),
        ('Фронтенд',           'http://100.120.184.98'),
        ('Видео-демо',         'Прилагается отдельным файлом'),
    ]
    for label, url in links:
        doc.check_space(7*mm)
        c.setFillColor(BLUE)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(ML, doc.y, f'{label}:')
        c.setFillColor(DARK)
        c.setFont('Helvetica', 10)
        c.drawString(ML + 55*mm, doc.y, url)
        doc.y -= 7*mm

    doc.spacer(8*mm)

    # Финальный блок
    doc.check_space(25*mm)
    c.setFillColor(DARK)
    c.roundRect(ML, doc.y - 22*mm, CW, 23*mm, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(W/2, doc.y - 8*mm, 'T2 AI Route Planner')
    c.setFillColor(HexColor('#F59E0B'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, doc.y - 16*mm, 'Все конкурсные требования выполнены  ✓')
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(W/2, doc.y - 22*mm, 'Февраль 2026  ·  Команда T2  ·  Мордовия')

    # Сохранение
    doc.save()
    size_kb = os.path.getsize(path) / 1024
    return size_kb


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2_Project_Report.pdf')
    print('Генерирую проектный отчёт...')
    size = build_report(out)
    print(f'Готово: {out}  ({size:.0f} KB)')
