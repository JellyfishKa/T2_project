"""
T2 AI Route Planner — Presentation PDF Generator
Генерирует 11-слайдовую презентацию для конкурса T2.
Запуск: py generate_presentation.py
"""

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# ─── Размер слайда (16:9, landscape) ─────────────────────────────────────────
W = 297 * mm
H = 167 * mm

# ─── Цвета T2 ────────────────────────────────────────────────────────────────
DARK    = HexColor('#0F172A')   # почти чёрный
BLUE    = HexColor('#1D4ED8')   # T2 синий
LBLUE   = HexColor('#3B82F6')   # светло-синий
YELLOW  = HexColor('#F59E0B')   # T2 жёлтый
GREEN   = HexColor('#10B981')   # зелёный
RED     = HexColor('#EF4444')   # красный
ORANGE  = HexColor('#F97316')   # оранжевый
GRAY    = HexColor('#6B7280')   # серый
LGRAY   = HexColor('#E5E7EB')   # светло-серый
VLIGHT  = HexColor('#F1F5F9')   # почти белый
WHITE   = HexColor('#FFFFFF')
CARD_BG = HexColor('#F8FAFC')


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def slide_bg(c, dark=False):
    """Заливка фона слайда."""
    c.setFillColor(DARK if dark else WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def accent_bar(c, color=BLUE, height=8*mm):
    """Горизонтальная полоса вверху слайда."""
    c.setFillColor(color)
    c.rect(0, H - height, W, height, fill=1, stroke=0)


def slide_number(c, num, total=11):
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawRightString(W - 8*mm, 5*mm, f'{num} / {total}')


def title_text(c, text, y, size=32, color=DARK, align='left', x=None, width=None):
    c.setFillColor(color)
    c.setFont('Helvetica-Bold', size)
    if align == 'center':
        cx = x if x else W / 2
        c.drawCentredString(cx, y, text)
    else:
        cx = x if x else 18*mm
        c.drawString(cx, y, text)


def body_text(c, text, x, y, size=13, color=DARK, bold=False):
    c.setFillColor(color)
    font = 'Helvetica-Bold' if bold else 'Helvetica'
    c.setFont(font, size)
    c.drawString(x, y, text)


def wrap_text(c, text, x, y, max_width, size=12, color=DARK, leading=16):
    """Простой перенос текста по словам."""
    c.setFillColor(color)
    c.setFont('Helvetica', size)
    words = text.split()
    line = ''
    cur_y = y
    for word in words:
        test = line + (' ' if line else '') + word
        if c.stringWidth(test, 'Helvetica', size) <= max_width:
            line = test
        else:
            if line:
                c.drawString(x, cur_y, line)
                cur_y -= leading
            line = word
    if line:
        c.drawString(x, cur_y, line)
    return cur_y


def card(c, x, y, w, h, bg=CARD_BG, border=LGRAY, radius=4):
    """Карточка с фоном и border."""
    c.setFillColor(bg)
    c.setStrokeColor(border)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def colored_badge(c, x, y, w, h, color, text, text_color=WHITE, size=11):
    """Цветной бейдж с текстом."""
    c.setFillColor(color)
    c.roundRect(x, y, w, h, 3, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont('Helvetica-Bold', size)
    c.drawCentredString(x + w/2, y + h/2 - 4, text)


def divider(c, y, color=LGRAY, x_start=18*mm, x_end=None):
    if x_end is None:
        x_end = W - 18*mm
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.line(x_start, y, x_end, y)


def progress_bar(c, x, y, w, h, pct, bg=LGRAY, fg=BLUE):
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
    if pct > 0:
        c.setFillColor(fg)
        c.roundRect(x, y, w * pct, h, 2, fill=1, stroke=0)


def icon_circle(c, x, y, r, color, text, text_size=14):
    c.setFillColor(color)
    c.circle(x, y, r, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', text_size)
    c.drawCentredString(x, y - text_size * 0.35, text)


def section_label(c, text, x=18*mm, y=None):
    """Маленький label-бейдж раздела над заголовком."""
    tw = c.stringWidth(text, 'Helvetica-Bold', 8) + 8
    c.setFillColor(BLUE)
    c.roundRect(x, y, tw, 12, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(x + 4, y + 3, text)


# ─── СЛАЙД 1: Титульный ──────────────────────────────────────────────────────

def slide_01(c):
    # Тёмный фон
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Декоративный прямоугольник слева
    c.setFillColor(BLUE)
    c.rect(0, 0, 6*mm, H, fill=1, stroke=0)

    # Жёлтая полоска
    c.setFillColor(YELLOW)
    c.rect(6*mm, 0, 2*mm, H, fill=1, stroke=0)

    # Большой заголовок
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 48)
    c.drawString(22*mm, H/2 + 22*mm, 'T2 · AI Route Planner')

    # Подзаголовок
    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(22*mm, H/2 + 6*mm, 'Внедрение ИИ-технологий для повышения')
    c.drawString(22*mm, H/2 - 4*mm, 'эффективности работы розничной сети Т2')

    # Разделитель
    c.setStrokeColor(HexColor('#374151'))
    c.setLineWidth(1)
    c.line(22*mm, H/2 - 12*mm, W - 22*mm, H/2 - 12*mm)

    # Нижний блок: команда
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 11)
    team = 'Маклаков С.  ·  Кижаев Р.  ·  Наумкин В.  ·  Мукасеев Д.'
    c.drawString(22*mm, H/2 - 24*mm, team)

    c.setFillColor(HexColor('#374151'))
    c.setFont('Helvetica', 10)
    c.drawString(22*mm, H/2 - 34*mm, 'Февраль 2026  ·  Конкурс T2  ·  Команда 4 разработчика')

    # Декоративный круг справа
    c.setFillColor(HexColor('#1E293B'))
    c.circle(W - 35*mm, H/2, 38*mm, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.circle(W - 35*mm, H/2, 28*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(W - 35*mm, H/2 + 8*mm, 'AI')
    c.setFont('Helvetica', 11)
    c.drawCentredString(W - 35*mm, H/2 - 6*mm, 'Route')
    c.drawCentredString(W - 35*mm, H/2 - 16*mm, 'Planner')


# ─── СЛАЙД 2: Проблема ────────────────────────────────────────────────────────

def slide_02(c):
    slide_bg(c)
    accent_bar(c, RED)

    section_label(c, 'ПРОБЛЕМА', 18*mm, H - 20*mm)
    title_text(c, 'Как сейчас строятся маршруты?', H - 32*mm, 26, DARK)

    # 3 карточки проблем
    problems = [
        ('✗', RED,    'Всё вручную',
         'Руководитель составляет маршруты\nв Excel каждую неделю — 2–3 часа'),
        ('✗', ORANGE, 'Нет приоритетов',
         'Флагманские точки А посещаются\nтак же редко, как точки D'),
        ('✗', HexColor('#8B5CF6'), 'Форс-мажор = хаос',
         'Заболел ТП — 10+ точек выпали.\nНикто не знает, что делать'),
    ]

    cx = [18*mm, 107*mm, 196*mm]
    cw = 82*mm
    ch = 68*mm
    cy = H - 115*mm

    for i, (icon, color, title, desc) in enumerate(problems):
        card(c, cx[i], cy, cw, ch, bg=CARD_BG, border=color)
        # Верхняя полоса
        c.setFillColor(color)
        c.roundRect(cx[i], cy + ch - 6, cw, 6, 2, fill=1, stroke=0)
        # Иконка-кружок
        icon_circle(c, cx[i] + 14*mm, cy + ch - 22, 8*mm, color, icon, 18)
        # Заголовок
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(cx[i] + 4*mm, cy + ch - 36, title)
        # Описание
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 10.5)
        lines = desc.split('\n')
        for j, line in enumerate(lines):
            c.drawString(cx[i] + 4*mm, cy + ch - 50 - j*14, line)

    # Нижняя строка-акцент
    c.setFillColor(DARK)
    c.rect(18*mm, 10*mm, W - 36*mm, 16*mm, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(W/2, 15.5*mm,
        '250 торговых точек  ·  4 сотрудника  ·  каждый месяц — одни и те же проблемы')

    slide_number(c, 2)


# ─── СЛАЙД 3: Решение ─────────────────────────────────────────────────────────

def slide_03(c):
    slide_bg(c)
    accent_bar(c, BLUE)

    section_label(c, 'РЕШЕНИЕ', 18*mm, H - 20*mm)
    title_text(c, 'Что мы разработали', H - 32*mm, 26, DARK)

    # Центральная схема-стрелка
    arrow_y = H - 68*mm
    steps = [
        (BLUE,   '1',  'База 250 ТТ',      'XLSX / CSV загрузка'),
        (LBLUE,  '2',  'ИИ-оптимизация',   'Qwen или Llama'),
        (GREEN,  '3',  'Расписание',        'Месяц за секунды'),
        (YELLOW, '4',  'Аналитика',         'Excel одной кнопкой'),
    ]
    box_w = 58*mm
    box_h = 30*mm
    gap = 10*mm
    start_x = 18*mm

    for i, (color, num, title, sub) in enumerate(steps):
        bx = start_x + i * (box_w + gap)
        # Карточка
        c.setFillColor(color)
        c.roundRect(bx, arrow_y - box_h/2, box_w, box_h, 5, fill=1, stroke=0)
        # Номер
        c.setFillColor(WHITE)
        c.setFillColorRGB(1, 1, 1, 0.3)
        c.circle(bx + 8*mm, arrow_y + box_h/2 - 8*mm, 7*mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(bx + 8*mm, arrow_y + box_h/2 - 11*mm, num)
        # Текст
        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(bx + box_w/2, arrow_y + 2*mm, title)
        c.setFont('Helvetica', 9)
        c.drawCentredString(bx + box_w/2, arrow_y - 9*mm, sub)

        # Стрелка между блоками
        if i < 3:
            ax = bx + box_w + 1*mm
            c.setFillColor(LGRAY)
            c.setFont('Helvetica-Bold', 20)
            c.drawString(ax, arrow_y - 5*mm, '→')

    # 4 блока фич внизу
    feats = [
        (BLUE,   '🗺',  '3 варианта маршрута',  'Greedy · Priority · Balanced'),
        (GREEN,  '📅',  'Расписание A/B/C/D',   'MAX 14 ТТ/день на ТП'),
        (RED,    '⚡',  'Форс-мажоры',          'Авторераспределение ТТ'),
        (YELLOW, '📊',  'Аналитика + Excel',     '4 листа отчётности'),
    ]
    fy = H - 120*mm
    fw = 63*mm
    fh = 26*mm
    fx = 18*mm

    for i, (col, ico, title, sub) in enumerate(feats):
        bx = fx + i * (fw + 4*mm)
        card(c, bx, fy - fh, fw, fh, bg=CARD_BG)
        # Полоска слева
        c.setFillColor(col)
        c.roundRect(bx, fy - fh, 3*mm, fh, 2, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(bx + 6*mm, fy - 11*mm, title)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 9.5)
        c.drawString(bx + 6*mm, fy - 21*mm, sub)

    slide_number(c, 3)


# ─── СЛАЙД 4: Оптимизация маршрутов ─────────────────────────────────────────

def slide_04(c):
    slide_bg(c)
    accent_bar(c, BLUE)

    section_label(c, 'ОПТИМИЗАЦИЯ', 18*mm, H - 20*mm)
    title_text(c, 'Три варианта маршрута с ИИ-оценкой', H - 32*mm, 24, DARK)

    # Левая колонка: прогресс-бар
    lx = 18*mm
    lw = 88*mm

    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(lx, H - 50*mm, 'Процесс оптимизации:')

    steps_p = [
        ('Подготовка данных',  0.15, GREEN,  '< 1 сек'),
        ('Расчёт 3 вариантов', 0.30, BLUE,   '< 1 сек'),
        ('ИИ-анализ (Qwen)',   0.85, YELLOW, '30–90 сек'),
        ('Результат готов',    1.00, GREEN,  '✓'),
    ]
    py = H - 65*mm
    for label, pct, col, timing in steps_p:
        c.setFillColor(DARK)
        c.setFont('Helvetica', 9.5)
        c.drawString(lx, py, label)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 8.5)
        c.drawRightString(lx + lw, py, timing)
        progress_bar(c, lx, py - 10, lw, 6, pct, LGRAY, col)
        py -= 24

    # Разделитель по центру
    c.setStrokeColor(LGRAY)
    c.setLineWidth(1)
    c.line(113*mm, H - 45*mm, 113*mm, 28*mm)

    # Правая колонка: 3 варианта
    rx = 118*mm
    rw = 160*mm
    variants = [
        (BLUE,   '1', 'Минимум расстояния',
         '+ Дешевле по топливу и времени',
         '– Игнорирует приоритеты A/B',
         '12.5 км · 2.3 ч · 87 ₽'),
        (GREEN,  '2', 'По приоритету A→B→C→D',
         '+ Флагманы посещаются первыми',
         '– Маршрут чуть длиннее',
         '15.2 км · 2.8 ч · 106 ₽'),
        (YELLOW, '3', 'Оптимальный баланс',
         '+ Компромисс: расстояние + важность',
         '+ Рекомендован ИИ-моделью',
         '13.1 км · 2.5 ч · 92 ₽'),
    ]

    vy = H - 50*mm
    vh = 32*mm
    vw = rw - 4*mm
    for i, (col, num, title, pro, con, metrics) in enumerate(variants):
        cy_v = vy - i * (vh + 4*mm)
        card(c, rx, cy_v - vh, vw, vh, bg=CARD_BG)
        # Номер-бейдж
        c.setFillColor(col)
        c.roundRect(rx, cy_v - vh, 10*mm, vh, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 15)
        c.drawCentredString(rx + 5*mm, cy_v - vh/2 - 5*mm, num)
        # Заголовок
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(rx + 13*mm, cy_v - 8*mm, title)
        # Метрики
        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(rx + 13*mm, cy_v - 17*mm, metrics)
        # Плюс/минус
        c.setFillColor(GREEN)
        c.setFont('Helvetica', 9)
        c.drawString(rx + 13*mm, cy_v - 25*mm, pro)
        c.setFillColor(RED)
        c.drawString(rx + 13*mm, cy_v - 33*mm, con)

    slide_number(c, 4)


# ─── СЛАЙД 5: Расписание A/B/C/D ─────────────────────────────────────────────

def slide_05(c):
    slide_bg(c)
    accent_bar(c, GREEN)

    section_label(c, 'РАСПИСАНИЕ', 18*mm, H - 20*mm)
    title_text(c, 'Умное планирование по категориям ТТ', H - 32*mm, 24, DARK)

    # Левая часть: категории
    cats = [
        (RED,    'A', 'Флагманы',    '3 визита / месяц', '09:00–12:00'),
        (ORANGE, 'B', 'Ключевые',    '2 визита / месяц', '09:00–15:00'),
        (YELLOW, 'C', 'Стандартные', '1 визит  / месяц', '09:00–18:00'),
        (GRAY,   'D', 'Редкие',      '1 визит  / квартал','09:00–18:00'),
    ]
    lx = 18*mm
    cy_cat = H - 50*mm
    row_h = 22*mm

    for col, letter, name, freq, window in cats:
        # Бейдж категории
        colored_badge(c, lx, cy_cat - 14*mm, 10*mm, 14*mm, col, letter, WHITE, 13)
        # Название
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(lx + 13*mm, cy_cat - 6*mm, name)
        # Частота
        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(lx + 13*mm, cy_cat - 17*mm, freq)
        # Окно
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 9)
        c.drawString(lx + 75*mm, cy_cat - 17*mm, window)
        divider(c, cy_cat - 22*mm, LGRAY, lx, lx + 100*mm)
        cy_cat -= row_h

    # Блок-число
    c.setFillColor(DARK)
    c.roundRect(lx, 14*mm, 100*mm, 18*mm, 4, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(lx + 4*mm, 20*mm, 'MAX 14 ТТ в день на одного сотрудника')

    # Правая часть: mock UI расписания
    rx = 126*mm
    rw = 154*mm

    c.setFillColor(DARK)
    c.roundRect(rx, 12*mm, rw, H - 46*mm, 6, fill=1, stroke=0)

    # Шапка
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(rx + 4*mm, H - 40*mm, 'Расписание маршрутов  ·  Февраль 2026')
    c.setFillColor(GREEN)
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(rx + rw - 4*mm, H - 40*mm, 'Охват: 87%')

    divider(c, H - 44*mm, HexColor('#374151'), rx + 4*mm, rx + rw - 4*mm)

    rows = [
        ('Иванов И.И.',   '03.02', ['A','B','C','C','C'],   'завтра'),
        ('Петрова М.С.',  '03.02', ['A','B','B','C','D'],   'завтра'),
        ('Сидоров А.В.',  '04.02', ['A','C','C','C','C'],   'сб-нт'),
        ('Козлов Д.Н.',   '05.02', ['B','B','C','C','C'],   'ср'),
    ]
    cat_colors_ui = {'A': RED, 'B': ORANGE, 'C': YELLOW, 'D': GRAY}
    ry = H - 54*mm
    for rep, date, cats_row, day in rows:
        c.setFillColor(WHITE)
        c.setFont('Helvetica', 9)
        c.drawString(rx + 4*mm, ry, rep)
        c.setFillColor(GRAY)
        c.drawString(rx + 50*mm, ry, date)
        bx2 = rx + 72*mm
        for cat in cats_row:
            col2 = cat_colors_ui.get(cat, GRAY)
            c.setFillColor(col2)
            c.roundRect(bx2, ry - 2, 9*mm, 11, 2, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 8)
            c.drawCentredString(bx2 + 4.5*mm, ry + 1, cat)
            bx2 += 11*mm
        ry -= 18

    # Кнопка
    c.setFillColor(BLUE)
    c.roundRect(rx + 4*mm, 20*mm, rw - 8*mm, 15*mm, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(rx + rw/2, 25*mm, '⟳  Оптимизировать маршрут (ИИ)')

    slide_number(c, 5)


# ─── СЛАЙД 6: Форс-мажоры ─────────────────────────────────────────────────────

def slide_06(c):
    slide_bg(c)
    accent_bar(c, RED)

    section_label(c, 'ФОРС-МАЖОРЫ', 18*mm, H - 20*mm)
    title_text(c, 'Система сама перестраивается', H - 32*mm, 26, DARK)

    # 4 типа форс-мажора
    fmtypes = [
        (RED,    'Болезнь',      'сотрудника'),
        (BLUE,   'Погодные',     'условия'),
        (ORANGE, 'Неисправность','транспорта'),
        (GRAY,   'Другое',       ''),
    ]
    fx = 18*mm
    fw = 58*mm
    fh = 26*mm
    for i, (col, t1, t2) in enumerate(fmtypes):
        bx = fx + i * (fw + 2*mm)
        card(c, bx, H - 68*mm, fw, fh, bg=CARD_BG)
        c.setFillColor(col)
        c.circle(bx + 8*mm, H - 55*mm, 5*mm, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(bx + 15*mm, H - 53*mm, t1)
        c.setFont('Helvetica', 9)
        c.drawString(bx + 15*mm, H - 63*mm, t2)

    # Схема перераспределения
    sx = 18*mm
    sy = H - 88*mm
    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(sx, sy, 'Пример: Иванов заболел 5 февраля')

    # Блок-диаграмма
    steps_fm = [
        (RED,   'Иванов\nзаболел',          '11 плановых\nТТ освободились'),
        (BLUE,  'Система\nищет слоты',       '3 активных ТП\nс запасом'),
        (GREEN, 'Round-robin\nраспределение','Петрова +4\nСидоров +4\nКозлов +3'),
        (GREEN, 'Результат',                 'Все 11 ТТ\nперераспределены'),
    ]
    bx3 = sx
    bw3 = 62*mm
    bh3 = 36*mm
    by3 = H - 120*mm

    for i, (col, title, desc) in enumerate(steps_fm):
        card(c, bx3, by3 - bh3, bw3, bh3, bg=CARD_BG)
        c.setFillColor(col)
        c.roundRect(bx3, by3 - bh3, 3, bh3, 1, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 10)
        for j, ln in enumerate(title.split('\n')):
            c.drawString(bx3 + 6*mm, by3 - 10*mm - j*13, ln)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 9)
        for j, ln in enumerate(desc.split('\n')):
            c.drawString(bx3 + 6*mm, by3 - 24*mm - j*11, ln)
        if i < 3:
            c.setFillColor(GRAY)
            c.setFont('Helvetica-Bold', 18)
            c.drawString(bx3 + bw3 + 1*mm, by3 - bh3/2 - 6*mm, '→')
        bx3 += bw3 + 5*mm

    # Нижняя строка
    c.setFillColor(GREEN)
    c.roundRect(18*mm, 10*mm, W - 36*mm, 16*mm, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(W/2, 15*mm, '✓  Ни одна торговая точка не выпадает из охвата')

    slide_number(c, 6)


# ─── СЛАЙД 7: Аналитика и Excel ───────────────────────────────────────────────

def slide_07(c):
    slide_bg(c)
    accent_bar(c, GREEN)

    section_label(c, 'АНАЛИТИКА', 18*mm, H - 20*mm)
    title_text(c, 'Полная отчётность одной кнопкой', H - 32*mm, 26, DARK)

    # 4 листа Excel
    sheets = [
        (BLUE,   '1', 'Расписание',        'Все плановые визиты\nс категориями A/B/C/D'),
        (GREEN,  '2', 'Журнал визитов',    'Время прихода/ухода\nдлительность на ТТ'),
        (YELLOW, '3', 'Статистика ТТ',     '% выполнения\nпо каждой точке'),
        (RED,    '4', 'Активность ТП',     'Выходов на маршрут\nТТ посещено'),
    ]
    sw = 60*mm
    sh = 44*mm
    sx = 18*mm
    sy = H - 48*mm

    for i, (col, num, title, desc) in enumerate(sheets):
        bx = sx + i * (sw + 4*mm)
        card(c, bx, sy - sh, sw, sh, bg=CARD_BG)
        # Excel иконка
        c.setFillColor(col)
        c.roundRect(bx + 3*mm, sy - 14*mm, 12*mm, 10*mm, 2, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(bx + 9*mm, sy - 10*mm, 'XLS')
        # Номер листа
        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(bx + 17*mm, sy - 8*mm, f'Лист {num}')
        # Название
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(bx + 3*mm, sy - 22*mm, title)
        # Описание
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 9)
        for j, ln in enumerate(desc.split('\n')):
            c.drawString(bx + 3*mm, sy - 33*mm - j*11, ln)

    # Метрики-числа
    metrics = [
        (BLUE,  '87%',  'Охват ТТ'),
        (GREEN, '14',   'ТТ/день'),
        (YELLOW,'3.2ч', 'Среднее\nна маршрут'),
        (RED,   '95%',  'Точки A\nвыполнены'),
    ]
    mx = 18*mm
    mw = 60*mm
    mh = 30*mm
    my = H - 118*mm

    for i, (col, val, label) in enumerate(metrics):
        bx = mx + i * (mw + 4*mm)
        c.setFillColor(HexColor('#F0FDF4') if col == GREEN
                       else HexColor('#EFF6FF') if col == BLUE
                       else HexColor('#FFFBEB') if col == YELLOW
                       else HexColor('#FEF2F2'))
        c.roundRect(bx, my - mh, mw, mh, 4, fill=1, stroke=0)
        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 22)
        c.drawCentredString(bx + mw/2, my - 16*mm, val)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 8.5)
        for j, ln in enumerate(label.split('\n')):
            c.drawCentredString(bx + mw/2, my - 23*mm - j*10, ln)

    # Кнопка Excel
    c.setFillColor(HexColor('#16A34A'))
    c.roundRect(18*mm, 10*mm, 100*mm, 16*mm, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(68*mm, 15.5*mm, '↓  Скачать Excel-отчёт')

    c.setFillColor(DARK)
    c.setFont('Helvetica', 9.5)
    c.drawString(125*mm, 15.5*mm, 'Доступно в разделах: Расписание и Аналитика')

    slide_number(c, 7)


# ─── СЛАЙД 8: Технологии ──────────────────────────────────────────────────────

def slide_08(c):
    slide_bg(c)
    accent_bar(c, DARK, 6*mm)

    section_label(c, 'ТЕХНОЛОГИИ', 18*mm, H - 20*mm)
    title_text(c, 'Технологический стек', H - 32*mm, 26, DARK)

    cols = [
        ('Backend', BLUE, [
            'Python 3.11 + FastAPI (async)',
            'PostgreSQL + SQLAlchemy ORM',
            'Qwen 2 · 0.5B (GGUF)',
            'Llama 3.2 · 1B (GGUF)',
            'llama-cpp-python · openpyxl',
            '33 API эндпоинта',
        ]),
        ('Frontend', GREEN, [
            'Vue 3 + TypeScript',
            'TailwindCSS + Chart.js',
            '6 страниц интерфейса',
            'Прогресс-бар LLM-ожидания',
            '3 варианта маршрута с UI',
            'Excel-экспорт из браузера',
        ]),
        ('DevOps & AI', YELLOW, [
            'Docker Compose (4 сервиса)',
            'Nginx — SPA + API прокси',
            'GitHub Actions CI/CD',
            'PostgreSQL + Redis',
            'Локальный запуск LLM',
            'Данные не покидают сервер',
        ]),
    ]

    cw = 84*mm
    ch = 90*mm
    cx_start = 18*mm
    gap = 5*mm

    for i, (title, col, items) in enumerate(cols):
        bx = cx_start + i * (cw + gap)
        # Шапка колонки
        c.setFillColor(col)
        c.roundRect(bx, H - 38*mm - ch, cw, ch, 5, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(bx + cw/2, H - 53*mm, title)
        # Разделитель
        c.setStrokeColor(HexColor('#FFFFFF40'))
        c.setLineWidth(0.5)
        c.line(bx + 4*mm, H - 57*mm, bx + cw - 4*mm, H - 57*mm)
        # Элементы
        c.setFillColor(WHITE)
        c.setFont('Helvetica', 10)
        for j, item in enumerate(items):
            c.drawString(bx + 5*mm, H - 65*mm - j*13, '· ' + item)

    # Нижний акцент
    c.setFillColor(DARK)
    c.roundRect(18*mm, 10*mm, W - 36*mm, 18*mm, 4, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, 16.5*mm,
        '🔒  Всё работает локально — данные клиентов не покидают сервер компании')

    slide_number(c, 8)


# ─── СЛАЙД 9: Бизнес-результат ────────────────────────────────────────────────

def slide_09(c):
    slide_bg(c)
    accent_bar(c, GREEN)

    section_label(c, 'РЕЗУЛЬТАТ', 18*mm, H - 20*mm)
    title_text(c, 'Что это даёт T2', H - 32*mm, 28, DARK)

    results = [
        (BLUE,   '15–20%',   'экономия\nкилометража',    'Оптимизация маршрутов\nснижает пробег'),
        (GREEN,  'Секунды',  'вместо\n3 часов вручную',  'Расписание на месяц\nгенерируется мгновенно'),
        (RED,    '100%',     'охват ТТ\nпри форс-мажоре','Ни одна точка\nне выпадает'),
        (YELLOW, '4 листа',  'Excel-отчёт\nодной кнопкой','Аналитика всегда\nготова к отчёту'),
        (LBLUE,  '33',       'API\nэндпоинта',           'Production-ready\nдля внедрения'),
    ]

    rw = 50*mm
    rh = 60*mm
    gap = 3*mm
    rx_start = 18*mm
    ry = H - 48*mm

    for i, (col, val, label, desc) in enumerate(results):
        bx = rx_start + i * (rw + gap)
        # Карточка
        c.setFillColor(col)
        c.roundRect(bx, ry - rh, rw, rh, 6, fill=1, stroke=0)
        # Большое число
        c.setFillColor(WHITE)
        fs = 26 if len(val) <= 4 else 20
        c.setFont('Helvetica-Bold', fs)
        c.drawCentredString(bx + rw/2, ry - 20*mm, val)
        # Подпись под числом
        c.setFillColor(HexColor('#FFFFFFCC'))
        c.setFont('Helvetica-Bold', 9)
        for j, ln in enumerate(label.split('\n')):
            c.drawCentredString(bx + rw/2, ry - 31*mm - j*11, ln)
        # Описание
        c.setFillColor(WHITE)
        c.setFont('Helvetica', 8.5)
        for j, ln in enumerate(desc.split('\n')):
            c.drawCentredString(bx + rw/2, ry - 48*mm - j*11, ln)

    # Нижняя строка
    c.setFillColor(DARK)
    c.rect(18*mm, 10*mm, W - 36*mm, 18*mm, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(W/2, 15.5*mm,
        'Реализует ВСЕ требования конкурсного задания T2  ✓')

    slide_number(c, 9)


# ─── СЛАЙД 10: Команда ────────────────────────────────────────────────────────

def slide_10(c):
    slide_bg(c)
    accent_bar(c, BLUE)

    section_label(c, 'КОМАНДА', 18*mm, H - 20*mm)
    title_text(c, 'Кто это сделал', H - 32*mm, 28, DARK)

    members = [
        (BLUE,  'С.М.',  'Сергей Маклаков',   'TL · PM',          ['Архитектура системы', 'CI/CD + GitHub Actions', 'Документация', 'Координация']),
        (GREEN, 'Р.К.',  'Роман Кижаев',       'Backend Engineer', ['FastAPI + SQLAlchemy', 'LLM-интеграция', 'Алгоритмы маршрутов', 'Excel-экспорт']),
        (YELLOW,'В.Н.',  'Владислав Наумкин',  'Frontend Engineer',['Vue 3 + TypeScript', 'Прогресс-бар LLM', '3 варианта UI', 'Аналитика-дашборд']),
        (RED,   'Д.М.',  'Дмитрий Мукасеев',   'ML · Analytics',   ['SchedulePlanner A/B/C/D', 'ForceMajeureService', 'Insights API', 'Датасет 250 ТТ']),
    ]

    cw = 62*mm
    ch = 72*mm
    cx_s = 18*mm
    cy_s = H - 45*mm

    for i, (col, initials, name, role, tasks) in enumerate(members):
        bx = cx_s + i * (cw + 4*mm)
        card(c, bx, cy_s - ch, cw, ch)
        # Аватар
        c.setFillColor(col)
        c.circle(bx + cw/2, cy_s - 12*mm, 9*mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(bx + cw/2, cy_s - 15.5*mm, initials)
        # Имя
        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 10)
        # Разбиваем имя
        parts = name.split()
        c.drawCentredString(bx + cw/2, cy_s - 26*mm, parts[0])
        c.drawCentredString(bx + cw/2, cy_s - 36*mm, ' '.join(parts[1:]))
        # Роль
        colored_badge(c, bx + 5*mm, cy_s - 44*mm, cw - 10*mm, 10*mm, col, role, WHITE, 8)
        # Задачи
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 8.5)
        for j, task in enumerate(tasks):
            c.drawString(bx + 4*mm, cy_s - 56*mm - j*10, '· ' + task)

    # Нижняя строка
    c.setFillColor(LGRAY)
    c.roundRect(18*mm, 10*mm, W - 36*mm, 14*mm, 4, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.setFont('Helvetica', 10)
    c.drawCentredString(W/2, 14*mm,
        '4 недели  ·  Agile  ·  Production-Ready  ·  Все конкурсные требования выполнены')

    slide_number(c, 10)


# ─── СЛАЙД 11: Финал ──────────────────────────────────────────────────────────

def slide_11(c):
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(BLUE)
    c.rect(0, 0, 6*mm, H, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.rect(6*mm, 0, 2*mm, H, fill=1, stroke=0)

    # Центральный текст
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(W/2, H/2 + 28*mm, 'T2 · AI Route Planner')

    c.setFillColor(YELLOW)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(W/2, H/2 + 14*mm, 'Все требования конкурса — выполнены  ✓')

    c.setStrokeColor(HexColor('#374151'))
    c.setLineWidth(1)
    c.line(50*mm, H/2 + 7*mm, W - 50*mm, H/2 + 7*mm)

    # Ссылки
    links = [
        ('GitHub', 'github.com/JellyfishKa/T2_project'),
        ('Swagger UI', '100.120.184.98:8000/docs'),
        ('Видео-демо', 'смотрите приложенный ролик'),
    ]
    ly = H/2 - 4*mm
    for label, link in links:
        c.setFillColor(BLUE)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(W/2 - 60*mm, ly, label + ':')
        c.setFillColor(HexColor('#94A3B8'))
        c.setFont('Helvetica', 11)
        c.drawString(W/2 - 30*mm, ly, link)
        ly -= 16

    # Большое «Спасибо»
    c.setFillColor(HexColor('#1E293B'))
    c.circle(W - 40*mm, H/2 + 5*mm, 30*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(W - 40*mm, H/2 + 10*mm, 'Спасибо!')
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 10)
    c.drawCentredString(W - 40*mm, H/2 - 4*mm, 'Ответим')
    c.drawCentredString(W - 40*mm, H/2 - 14*mm, 'на вопросы')

    # Нижняя строка
    c.setFillColor(HexColor('#1E293B'))
    c.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(W/2, 4*mm,
        '@maklakov_tkdrm  ·  Команда T2  ·  Февраль 2026')


# ─── ГЕНЕРАЦИЯ PDF ────────────────────────────────────────────────────────────

def generate():
    out_path = os.path.join(os.path.dirname(__file__), 'T2_AI_Route_Planner_Presentation.pdf')

    c = canvas.Canvas(out_path, pagesize=(W, H))
    c.setTitle('T2 AI Route Planner — Презентация')
    c.setAuthor('Команда T2')
    c.setSubject('Внедрение ИИ-технологий для повышения эффективности работы розничной сети Т2')

    slides = [
        (slide_01, 'Титульный'),
        (slide_02, 'Проблема'),
        (slide_03, 'Решение'),
        (slide_04, 'ИИ-оптимизация'),
        (slide_05, 'Расписание A/B/C/D'),
        (slide_06, 'Форс-мажоры'),
        (slide_07, 'Аналитика и Excel'),
        (slide_08, 'Технологии'),
        (slide_09, 'Результат'),
        (slide_10, 'Команда'),
        (slide_11, 'Финал'),
    ]

    for fn, name in slides:
        fn(c)
        print(f'  ✓  Слайд: {name}')
        c.showPage()

    c.save()
    size_kb = os.path.getsize(out_path) / 1024
    print(f'\nГотово! → {out_path}  ({size_kb:.0f} KB, {len(slides)} слайдов)')
    return out_path


if __name__ == '__main__':
    print('Генерирую презентацию T2...')
    generate()
