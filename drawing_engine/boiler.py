"""
Параметрический генератор чертежей котлов.
Генерирует виды: спереди, сзади, слева (сбоку), справа, сверху
с эллиптическими днищами, размерными линиями, штриховкой.
"""

import math
import svgwrite
from backend.models import HorizontalFireTubeParams


class BoilerDrawing:
    """Генератор SVG чертежей котла — реалистичные проекции"""

    MARGIN = 30
    DIM_OFFSET = 20
    ARROW_SIZE = 2.5
    NOZZLE_HEIGHT_RATIO = 0.08  # Высота патрубка = 8% от диаметра
    ELLIPSE_RATIO = 0.25  # Глубина эллиптического днища = 25% от диаметра

    # Стили линий (ГОСТ 2.303)
    S_MAIN = {"stroke": "black", "stroke-width": "0.5", "fill": "none"}
    S_THIN = {"stroke": "black", "stroke-width": "0.25", "fill": "none"}
    S_CENTER = {"stroke": "black", "stroke-width": "0.18", "fill": "none",
                "stroke-dasharray": "10,3,2,3"}
    S_HIDDEN = {"stroke": "black", "stroke-width": "0.25", "fill": "none",
                "stroke-dasharray": "4,2"}
    S_DIM = {"stroke": "black", "stroke-width": "0.18", "fill": "none"}
    S_HATCH = {"stroke": "black", "stroke-width": "0.1", "fill": "none"}

    FONT = "ISOCPEUR, Arial, sans-serif"

    def __init__(self, params: HorizontalFireTubeParams, scale: float = 0.1):
        self.p = params
        self.scale = scale
        # Глубина эллиптического днища (реальные мм)
        self.head_depth = params.outer_diameter * self.ELLIPSE_RATIO
        # Высота патрубка (реальные мм)
        self.nozzle_h = max(params.outer_diameter * self.NOZZLE_HEIGHT_RATIO, 60)

    def s(self, v: float) -> float:
        """Реальные мм -> мм на чертеже"""
        return v * self.scale

    # ═══════════════════════════════════════════════════════════════
    #  ПРИМИТИВЫ: эллипсы, патрубки, размерные линии
    # ═══════════════════════════════════════════════════════════════

    def _ellipse_arc(self, cx, cy, rx, ry, start_deg, end_deg, n=60):
        """Точки эллиптической дуги"""
        pts = []
        for i in range(n + 1):
            a = math.radians(start_deg + (end_deg - start_deg) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        return pts

    def _draw_ellipse_arc(self, dwg, g, cx, cy, rx, ry, start_deg=0, end_deg=360, style=None):
        """Рисует эллиптическую дугу через polyline"""
        if style is None:
            style = self.S_MAIN
        pts = self._ellipse_arc(cx, cy, rx, ry, start_deg, end_deg)
        g.add(dwg.polyline(pts, **style))

    def _draw_nozzle_side(self, dwg, g, cx, cy_base, radius, height, direction="up",
                          label="", flange=True):
        """Патрубок вид сбоку (прямоугольник + фланец)"""
        r = self.s(radius)
        h = self.s(height)
        flange_w = r * 1.4
        flange_h = self.s(6)

        if direction == "up":
            y_top = cy_base - h
            # Стенки патрубка
            g.add(dwg.line((cx - r, cy_base), (cx - r, y_top), **self.S_MAIN))
            g.add(dwg.line((cx + r, cy_base), (cx + r, y_top), **self.S_MAIN))
            # Фланец
            if flange:
                g.add(dwg.rect(insert=(cx - flange_w, y_top - flange_h),
                               size=(flange_w * 2, flange_h), **self.S_MAIN))
            else:
                g.add(dwg.line((cx - r, y_top), (cx + r, y_top), **self.S_MAIN))
            # Осевая
            g.add(dwg.line((cx, cy_base + 3), (cx, y_top - flange_h - 5), **self.S_CENTER))
            # Подпись
            if label:
                g.add(dwg.text(label, insert=(cx, y_top - flange_h - 3),
                               text_anchor="middle", font_size="2.8px",
                               font_family=self.FONT, fill="black"))
        elif direction == "down":
            y_bot = cy_base + h
            g.add(dwg.line((cx - r, cy_base), (cx - r, y_bot), **self.S_MAIN))
            g.add(dwg.line((cx + r, cy_base), (cx + r, y_bot), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(cx - flange_w, y_bot),
                               size=(flange_w * 2, flange_h), **self.S_MAIN))
            else:
                g.add(dwg.line((cx - r, y_bot), (cx + r, y_bot), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base - 3), (cx, y_bot + flange_h + 5), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(cx, y_bot + flange_h + 7),
                               text_anchor="middle", font_size="2.8px",
                               font_family=self.FONT, fill="black"))
        elif direction == "right":
            x_end = cx + h
            g.add(dwg.line((cx, cy_base - r), (x_end, cy_base - r), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base + r), (x_end, cy_base + r), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(x_end, cy_base - flange_w),
                               size=(flange_h, flange_w * 2), **self.S_MAIN))
            else:
                g.add(dwg.line((x_end, cy_base - r), (x_end, cy_base + r), **self.S_MAIN))
            g.add(dwg.line((cx - 3, cy_base), (x_end + flange_h + 5, cy_base), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(x_end + flange_h + 3, cy_base - 3),
                               text_anchor="start", font_size="2.8px",
                               font_family=self.FONT, fill="black"))
        elif direction == "left":
            x_end = cx - h
            g.add(dwg.line((cx, cy_base - r), (x_end, cy_base - r), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base + r), (x_end, cy_base + r), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(x_end - flange_h, cy_base - flange_w),
                               size=(flange_h, flange_w * 2), **self.S_MAIN))
            else:
                g.add(dwg.line((x_end, cy_base - r), (x_end, cy_base + r), **self.S_MAIN))
            g.add(dwg.line((cx + 3, cy_base), (x_end - flange_h - 5, cy_base), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(x_end - flange_h - 3, cy_base - 3),
                               text_anchor="end", font_size="2.8px",
                               font_family=self.FONT, fill="black"))

    def _draw_nozzle_circle(self, dwg, g, cx, cy, outer_r, inner_r=None, label=""):
        """Патрубок вид с торца (два концентрических круга)"""
        r_out = self.s(outer_r)
        r_in = self.s(inner_r if inner_r else outer_r * 0.7)
        g.add(dwg.circle(center=(cx, cy), r=r_out, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=r_in, **self.S_THIN))
        if label:
            g.add(dwg.text(label, insert=(cx, cy - r_out - 2),
                           text_anchor="middle", font_size="2.5px",
                           font_family=self.FONT, fill="black"))

    # ═══════════════════════════════════════════════════════════════
    #  РАЗМЕРНЫЕ ЛИНИИ
    # ═══════════════════════════════════════════════════════════════

    def _dim_h(self, dwg, g, x1, x2, y, value, above=True):
        """Горизонтальная размерная линия"""
        off = -self.DIM_OFFSET if above else self.DIM_OFFSET
        yd = y + off
        a = self.ARROW_SIZE
        # Выносные
        g.add(dwg.line((x1, y), (x1, yd + (2 if above else -2)), **self.S_DIM))
        g.add(dwg.line((x2, y), (x2, yd + (2 if above else -2)), **self.S_DIM))
        # Линия
        g.add(dwg.line((x1, yd), (x2, yd), **self.S_DIM))
        # Стрелки
        g.add(dwg.polygon([(x1, yd), (x1 + a, yd - a/2), (x1 + a, yd + a/2)], fill="black"))
        g.add(dwg.polygon([(x2, yd), (x2 - a, yd - a/2), (x2 - a, yd + a/2)], fill="black"))
        # Текст
        ty = yd - 1.5 if above else yd + 4.5
        g.add(dwg.text(f"{value:.0f}", insert=((x1+x2)/2, ty),
                        text_anchor="middle", font_size="3.2px",
                        font_family=self.FONT, fill="black"))

    def _dim_v(self, dwg, g, y1, y2, x, value, left=True):
        """Вертикальная размерная линия"""
        off = -self.DIM_OFFSET if left else self.DIM_OFFSET
        xd = x + off
        a = self.ARROW_SIZE
        g.add(dwg.line((x, y1), (xd + (2 if left else -2), y1), **self.S_DIM))
        g.add(dwg.line((x, y2), (xd + (2 if left else -2), y2), **self.S_DIM))
        g.add(dwg.line((xd, y1), (xd, y2), **self.S_DIM))
        g.add(dwg.polygon([(xd, y1), (xd - a/2, y1 + a), (xd + a/2, y1 + a)], fill="black"))
        g.add(dwg.polygon([(xd, y2), (xd - a/2, y2 - a), (xd + a/2, y2 - a)], fill="black"))
        tx = xd - 2.5 if left else xd + 4.5
        mid = (y1 + y2) / 2
        g.add(dwg.text(f"{value:.0f}", insert=(tx, mid),
                        text_anchor="middle", font_size="3.2px",
                        font_family=self.FONT, fill="black",
                        transform=f"rotate(-90,{tx},{mid})"))

    def _dim_diameter(self, dwg, g, cx, cy, radius, value, angle_deg=45):
        """Размер диаметра через центр"""
        a = math.radians(angle_deg)
        x1 = cx - radius * math.cos(a)
        y1 = cy - radius * math.sin(a)
        x2 = cx + radius * math.cos(a)
        y2 = cy + radius * math.sin(a)
        g.add(dwg.line((x1, y1), (x2, y2), **self.S_DIM))
        ar = self.ARROW_SIZE
        g.add(dwg.circle(center=(x1, y1), r=0.5, fill="black"))
        g.add(dwg.circle(center=(x2, y2), r=0.5, fill="black"))
        mx, my = (x1+x2)/2, (y1+y2)/2
        g.add(dwg.text(f"\u2300{value:.0f}", insert=(mx + 3, my - 2),
                        text_anchor="start", font_size="3.2px",
                        font_family=self.FONT, fill="black"))

    # ═══════════════════════════════════════════════════════════════
    #  ШТРИХОВКА
    # ═══════════════════════════════════════════════════════════════

    def _hatch_rect(self, dwg, g, x, y, w, h, spacing=1.8):
        """Штриховка прямоугольной области"""
        step = spacing * math.sqrt(2)
        total = w + h
        for i in range(int(total / step) + 2):
            sx = x + i * step
            sy = y + h
            ex = sx + h
            ey = y
            clipped = self._clip(sx, sy, ex, ey, x, y, x + w, y + h)
            if clipped:
                g.add(dwg.line(clipped[0], clipped[1], **self.S_HATCH))

    def _clip(self, x1, y1, x2, y2, cx1, cy1, cx2, cy2):
        """Cohen-Sutherland clipping"""
        def code(x, y):
            c = 0
            if x < cx1: c |= 1
            if x > cx2: c |= 2
            if y < cy1: c |= 4
            if y > cy2: c |= 8
            return c
        c1, c2 = code(x1, y1), code(x2, y2)
        for _ in range(20):
            if not (c1 | c2): return (x1, y1), (x2, y2)
            if c1 & c2: return None
            c = c1 or c2
            dx, dy = x2 - x1, y2 - y1
            if c & 8:
                x = x1 + dx * (cy2 - y1) / dy if dy else x1; y = cy2
            elif c & 4:
                x = x1 + dx * (cy1 - y1) / dy if dy else x1; y = cy1
            elif c & 2:
                y = y1 + dy * (cx2 - x1) / dx if dx else y1; x = cx2
            else:
                y = y1 + dy * (cx1 - x1) / dx if dx else y1; x = cx1
            if c == c1: x1, y1, c1 = x, y, code(x, y)
            else: x2, y2, c2 = x, y, code(x, y)
        return None

    # ═══════════════════════════════════════════════════════════════
    #  ВИД СЛЕВА (ГЛАВНЫЙ ВИД — продольная проекция)
    # ═══════════════════════════════════════════════════════════════

    def draw_side_view(self, dwg, ox, oy):
        """Главный вид — вид слева (продольная проекция)"""
        g = dwg.g(id="view_side")
        p = self.p

        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        L = self.s(p.total_length)
        Rf = self.s(p.furnace_diameter / 2)
        Lf = self.s(p.furnace_length)
        hd = self.s(self.head_depth)  # Глубина эллиптического днища
        wt = self.s(p.wall_thickness)
        nh = self.s(self.nozzle_h)
        sh = self.s(p.support_height)

        # Центр оси котла
        cx_start = ox + hd + 5  # Начало цилиндрической части
        cy = oy + R + nh + 15

        # ── Цилиндрическая часть корпуса ──
        # Верхняя и нижняя линии
        g.add(dwg.line((cx_start, cy - R), (cx_start + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((cx_start, cy + R), (cx_start + L, cy + R), **self.S_MAIN))

        # ── Эллиптические днища ──
        # Переднее (левое) днище
        self._draw_ellipse_arc(dwg, g, cx_start, cy, hd, R, 90, 270, style=self.S_MAIN)
        # Внутренний контур переднего днища
        hd_i = hd - wt
        self._draw_ellipse_arc(dwg, g, cx_start, cy, hd_i, Ri, 90, 270, style=self.S_THIN)

        # Заднее (правое) днище
        self._draw_ellipse_arc(dwg, g, cx_start + L, cy, hd, R, -90, 90, style=self.S_MAIN)
        self._draw_ellipse_arc(dwg, g, cx_start + L, cy, hd_i, Ri, -90, 90, style=self.S_THIN)

        # ── Внутренние стенки (видимые линии верх и низ) ──
        g.add(dwg.line((cx_start, cy - Ri), (cx_start + L, cy - Ri), **self.S_THIN))
        g.add(dwg.line((cx_start, cy + Ri), (cx_start + L, cy + Ri), **self.S_THIN))

        # ── Жаровая труба ──
        ft = self.s(p.front_head_thickness)
        fstart = cx_start + ft
        g.add(dwg.line((fstart, cy - Rf), (fstart + Lf, cy - Rf), **self.S_MAIN))
        g.add(dwg.line((fstart, cy + Rf), (fstart + Lf, cy + Rf), **self.S_MAIN))
        # Торцы жаровой трубы
        g.add(dwg.line((fstart, cy - Rf), (fstart, cy + Rf), **self.S_MAIN))
        g.add(dwg.line((fstart + Lf, cy - Rf), (fstart + Lf, cy + Rf), **self.S_MAIN))

        # ── Дымогарные трубы (скрытые линии — пучок в верхней и нижней зоне) ──
        zone_top = cy - (Rf + Ri) / 2
        zone_bot = cy + (Rf + Ri) / 2
        # Верхний и нижний ряд пунктиром
        g.add(dwg.line((fstart, zone_top), (fstart + Lf, zone_top), **self.S_HIDDEN))
        g.add(dwg.line((fstart, zone_bot), (fstart + Lf, zone_bot), **self.S_HIDDEN))

        # ── Осевая линия ──
        g.add(dwg.line((cx_start - hd - 10, cy),
                        (cx_start + L + hd + 10, cy), **self.S_CENTER))

        # ── Патрубки ──
        inlet_cx = cx_start + self.s(p.inlet_position_x)
        outlet_cx = cx_start + self.s(p.outlet_position_x)
        flue_cx = cx_start + L + hd  # Дымоход на заднем днище

        # Входной (сверху)
        self._draw_nozzle_side(dwg, g, inlet_cx, cy - R,
                               p.inlet_diameter / 2, self.nozzle_h,
                               direction="up", label="Вход G1")
        # Выходной (сверху)
        self._draw_nozzle_side(dwg, g, outlet_cx, cy - R,
                               p.outlet_diameter / 2, self.nozzle_h,
                               direction="up", label="Выход G2")
        # Дымоход (справа)
        self._draw_nozzle_side(dwg, g, cx_start + L + hd, cy,
                               p.flue_diameter / 2, self.nozzle_h,
                               direction="right", label="Дымоход")

        # ── Опоры (седловые) ──
        sw = self.s(p.support_width)
        spacing = L / (p.support_count + 1)
        for i in range(p.support_count):
            sx = cx_start + spacing * (i + 1) - sw / 2
            # Седловая опора — трапеция
            top_w = sw
            bot_w = sw * 1.5
            top_y = cy + R
            bot_y = cy + R + sh
            # Трапеция
            pts = [
                (sx, top_y),
                (sx + top_w, top_y),
                (sx + top_w + (bot_w - top_w) / 2, bot_y),
                (sx - (bot_w - top_w) / 2, bot_y),
                (sx, top_y)
            ]
            g.add(dwg.polyline(pts, **self.S_MAIN))
            # Штриховка опоры
            bx = sx - (bot_w - top_w) / 2
            self._hatch_rect(dwg, g, bx, top_y, bot_w, sh)
            # Линия пола
            g.add(dwg.line((bx - 5, bot_y), (bx + bot_w + 5, bot_y), **self.S_MAIN))

        # ── Размерные линии ──
        # Общая длина (с днищами)
        total_w = L + 2 * hd
        self._dim_h(dwg, g, cx_start - hd, cx_start + L + hd,
                    cy - R - nh - 5, p.total_length + 2 * self.head_depth, above=True)
        # Длина цилиндрической части
        self._dim_h(dwg, g, cx_start, cx_start + L,
                    cy - R - nh - 20, p.total_length, above=True)
        # Диаметр корпуса
        self._dim_v(dwg, g, cy - R, cy + R,
                    cx_start - hd - 5, p.outer_diameter, left=True)
        # Длина топки
        self._dim_h(dwg, g, fstart, fstart + Lf,
                    cy + R + 8, p.furnace_length, above=False)
        # Диаметр топки
        self._dim_v(dwg, g, cy - Rf, cy + Rf,
                    cx_start + L + hd + nh + 10, p.furnace_diameter, left=False)

        # ── Название вида ──
        self._view_label(dwg, g, cx_start + L / 2, cy + R + sh + 20, "Вид сбоку")

        dwg.add(g)
        return total_w + self.MARGIN * 2 + 30, R * 2 + sh + nh + self.MARGIN * 2 + 40

    # ═══════════════════════════════════════════════════════════════
    #  ВИД СПЕРЕДИ (поперечное сечение)
    # ═══════════════════════════════════════════════════════════════

    def draw_front_view(self, dwg, ox, oy):
        """Вид спереди — поперечное сечение"""
        g = dwg.g(id="view_front")
        p = self.p

        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        Rf = self.s(p.furnace_diameter / 2)
        sh = self.s(p.support_height)
        nh = self.s(self.nozzle_h)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + nh + 15

        # Наружный контур
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        # Внутренний контур
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))
        # Жаровая труба (центрально или смещённо)
        g.add(dwg.circle(center=(cx, cy), r=Rf, **self.S_MAIN))

        # Осевые линии
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымогарные трубы
        self._draw_smoke_tubes(dwg, g, cx, cy, Ri, Rf)

        # Патрубки (круги с торца)
        # Входной — сверху слева
        inlet_cy = cy - R
        self._draw_nozzle_side(dwg, g, cx - self.s(p.outer_diameter * 0.15), cy - R,
                               p.inlet_diameter / 2, self.nozzle_h,
                               direction="up", label="G1")
        # Выходной — сверху справа
        self._draw_nozzle_side(dwg, g, cx + self.s(p.outer_diameter * 0.15), cy - R,
                               p.outlet_diameter / 2, self.nozzle_h,
                               direction="up", label="G2")

        # Опора (вид спереди — U-образная седловая)
        sw = self.s(p.support_width) * 1.5  # Видимая ширина
        top_y = cy + R
        bot_y = cy + R + sh
        # Прямоугольник опоры
        g.add(dwg.rect(insert=(cx - sw / 2, top_y), size=(sw, sh), **self.S_MAIN))
        self._hatch_rect(dwg, g, cx - sw / 2, top_y, sw, sh)
        # Линия пола
        g.add(dwg.line((cx - sw / 2 - 5, bot_y), (cx + sw / 2 + 5, bot_y), **self.S_MAIN))

        # Размеры
        self._dim_diameter(dwg, g, cx, cy, R, p.outer_diameter, angle_deg=45)
        self._dim_diameter(dwg, g, cx, cy, Rf, p.furnace_diameter, angle_deg=135)

        # Название
        self._view_label(dwg, g, cx, bot_y + 15, "Вид спереди (А)")

        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sh + nh + 50

    # ═══════════════════════════════════════════════════════════════
    #  ВИД СЗАДИ
    # ═══════════════════════════════════════════════════════════════

    def draw_rear_view(self, dwg, ox, oy):
        """Вид сзади — задняя стенка"""
        g = dwg.g(id="view_rear")
        p = self.p

        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        sh = self.s(p.support_height)
        nh = self.s(self.nozzle_h)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + 15

        # Наружный и внутренний контуры
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))

        # Осевые
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымоход (центральное отверстие)
        flue_r = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(cx, cy), r=flue_r, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=flue_r * 0.8, **self.S_THIN))
        g.add(dwg.text("Дымоход", insert=(cx, cy - flue_r - 2),
                        text_anchor="middle", font_size="2.5px",
                        font_family=self.FONT, fill="black"))

        # Дымогарные трубы (скрытые — пунктир)
        Rf = self.s(p.furnace_diameter / 2)
        self._draw_smoke_tubes(dwg, g, cx, cy, Ri, Rf, style=self.S_HIDDEN)

        # Опора
        sw = self.s(p.support_width) * 1.5
        top_y = cy + R
        bot_y = cy + R + sh
        g.add(dwg.rect(insert=(cx - sw / 2, top_y), size=(sw, sh), **self.S_MAIN))
        self._hatch_rect(dwg, g, cx - sw / 2, top_y, sw, sh)
        g.add(dwg.line((cx - sw / 2 - 5, bot_y), (cx + sw / 2 + 5, bot_y), **self.S_MAIN))

        # Размеры
        self._dim_diameter(dwg, g, cx, cy, flue_r, p.flue_diameter, angle_deg=30)

        # Название
        self._view_label(dwg, g, cx, bot_y + 15, "Вид сзади (Б)")

        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sh + 50

    # ═══════════════════════════════════════════════════════════════
    #  ВИД СВЕРХУ
    # ═══════════════════════════════════════════════════════════════

    def draw_top_view(self, dwg, ox, oy):
        """Вид сверху"""
        g = dwg.g(id="view_top")
        p = self.p

        R = self.s(p.outer_diameter / 2)
        L = self.s(p.total_length)
        hd = self.s(self.head_depth)
        nh = self.s(self.nozzle_h)

        # Начало цилиндрической части
        bx = ox + hd + 5
        cy = oy + R + self.DIM_OFFSET

        # Корпус (прямоугольник — вид сверху)
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))

        # Эллиптические днища (вид сверху — полуокружности)
        self._draw_ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, style=self.S_MAIN)
        self._draw_ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, style=self.S_MAIN)

        # Осевая
        g.add(dwg.line((bx - hd - 10, cy), (bx + L + hd + 10, cy), **self.S_CENTER))

        # Жаровая труба (скрытая — пунктир)
        Rf = self.s(p.furnace_diameter / 2)
        ft = self.s(p.front_head_thickness)
        g.add(dwg.line((bx + ft, cy - Rf), (bx + ft + self.s(p.furnace_length), cy - Rf),
                        **self.S_HIDDEN))
        g.add(dwg.line((bx + ft, cy + Rf), (bx + ft + self.s(p.furnace_length), cy + Rf),
                        **self.S_HIDDEN))

        # Патрубки (вид сверху — круги / прямоугольники)
        inlet_cx = bx + self.s(p.inlet_position_x)
        outlet_cx = bx + self.s(p.outlet_position_x)
        inlet_r = self.s(p.inlet_diameter / 2)
        outlet_r = self.s(p.outlet_diameter / 2)
        flange_r_in = inlet_r * 1.4
        flange_r_out = outlet_r * 1.4

        # Входной патрубок (круг + фланец)
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=flange_r_in, **self.S_MAIN))
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=inlet_r, **self.S_MAIN))
        g.add(dwg.text("G1", insert=(inlet_cx, cy - R * 0.3 - flange_r_in - 2),
                        text_anchor="middle", font_size="2.5px",
                        font_family=self.FONT, fill="black"))

        # Выходной патрубок
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=flange_r_out, **self.S_MAIN))
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=outlet_r, **self.S_MAIN))
        g.add(dwg.text("G2", insert=(outlet_cx, cy + R * 0.3 + flange_r_out + 4),
                        text_anchor="middle", font_size="2.5px",
                        font_family=self.FONT, fill="black"))

        # Дымоход (справа)
        flue_r = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(bx + L + hd, cy), r=flue_r, **self.S_MAIN))
        g.add(dwg.circle(center=(bx + L + hd, cy), r=flue_r * 0.8, **self.S_THIN))

        # Размерные линии
        self._dim_h(dwg, g, bx, bx + L, cy - R - 3, p.total_length, above=True)
        self._dim_v(dwg, g, cy - R, cy + R, bx - hd - 3, p.outer_diameter, left=True)

        # Название
        self._view_label(dwg, g, bx + L / 2, cy + R + self.DIM_OFFSET + 10, "Вид сверху (В)")

        dwg.add(g)
        return L + 2 * hd + self.MARGIN + 20, R * 2 + self.DIM_OFFSET * 2 + 30

    # ═══════════════════════════════════════════════════════════════
    #  ВСПОМОГАТЕЛЬНЫЕ
    # ═══════════════════════════════════════════════════════════════

    def _draw_smoke_tubes(self, dwg, g, cx, cy, r_inner, r_furnace, style=None):
        """Дымогарные трубы в поперечном сечении"""
        if style is None:
            style = self.S_THIN
        p = self.p
        r_smoke = self.s(p.smoke_tube_diameter / 2)
        zone_in = r_furnace + r_smoke + self.s(8)
        zone_out = r_inner - r_smoke - self.s(4)

        if p.smoke_tube_rows <= 0 or zone_out <= zone_in:
            return

        placed = 0
        for row in range(p.smoke_tube_rows):
            if placed >= p.smoke_tube_count:
                break
            r_row = zone_in + (zone_out - zone_in) * row / max(p.smoke_tube_rows - 1, 1)
            n_in_row = min(
                int(2 * math.pi * r_row / (r_smoke * 2 + self.s(4))),
                p.smoke_tube_count - placed
            )
            for j in range(n_in_row):
                if placed >= p.smoke_tube_count:
                    break
                angle = 2 * math.pi * j / n_in_row
                tx = cx + r_row * math.cos(angle)
                ty = cy + r_row * math.sin(angle)
                g.add(dwg.circle(center=(tx, ty), r=r_smoke, **style))
                placed += 1

    def _view_label(self, dwg, g, x, y, text):
        """Подпись вида"""
        g.add(dwg.text(text, insert=(x, y),
                        text_anchor="middle", font_size="4.5px",
                        font_family=self.FONT, fill="black", font_weight="bold"))
        # Подчёркивание
        tw = len(text) * 2.5
        g.add(dwg.line((x - tw, y + 1.5), (x + tw, y + 1.5),
                        stroke="black", stroke_width="0.3"))

    # ═══════════════════════════════════════════════════════════════
    #  РАМКА ЧЕРТЕЖА (ГОСТ 2.104)
    # ═══════════════════════════════════════════════════════════════

    def draw_frame(self, dwg, w, h):
        """Рамка и штамп"""
        g = dwg.g(id="frame")
        p = self.p

        # Внешняя рамка
        g.add(dwg.rect(insert=(0, 0), size=(w, h),
                        stroke="black", stroke_width="0.3", fill="white"))
        # Внутренняя рамка
        g.add(dwg.rect(insert=(20, 5), size=(w - 25, h - 10),
                        stroke="black", stroke_width="0.7", fill="none"))

        # Штамп (основная надпись)
        sw, sh = 185, 55
        sx = w - 5 - sw
        sy = h - 5 - sh
        g.add(dwg.rect(insert=(sx, sy), size=(sw, sh),
                        stroke="black", stroke_width="0.7", fill="white"))

        # Линии штампа
        rows = [15, 30, 40]
        for dy in rows:
            g.add(dwg.line((sx, sy + dy), (sx + sw, sy + dy),
                           stroke="black", stroke_width="0.35"))
        g.add(dwg.line((sx + 65, sy), (sx + 65, sy + sh),
                        stroke="black", stroke_width="0.35"))
        g.add(dwg.line((sx + 120, sy), (sx + 120, sy + 15),
                        stroke="black", stroke_width="0.35"))

        # Тексты
        tc = sx + 125
        g.add(dwg.text(p.name, insert=(tc + 30, sy + 12), text_anchor="middle",
                        font_size="7px", font_family=self.FONT,
                        fill="black", font_weight="bold"))
        g.add(dwg.text(f"Тип: {p.boiler_type.value}", insert=(tc + 30, sy + 25),
                        text_anchor="middle", font_size="3.5px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text(f"\u2300{p.outer_diameter:.0f} \u00d7 {p.total_length:.0f} мм",
                        insert=(tc + 30, sy + 37), text_anchor="middle",
                        font_size="3.5px", font_family=self.FONT, fill="black"))
        scale_val = int(1 / self.scale)
        g.add(dwg.text(f"Масштаб 1:{scale_val}", insert=(tc + 30, sy + 48),
                        text_anchor="middle", font_size="3px",
                        font_family=self.FONT, fill="black"))

        labels = ["Разработал", "Проверил", "Утвердил"]
        for i, lbl in enumerate(labels):
            g.add(dwg.text(lbl, insert=(sx + 4, sy + 12 + i * 15),
                           font_size="2.5px", font_family=self.FONT, fill="black"))

        dwg.add(g)

    # ═══════════════════════════════════════════════════════════════
    #  ГЕНЕРАЦИЯ ПОЛНОГО ЧЕРТЕЖА
    # ═══════════════════════════════════════════════════════════════

    def generate_full_drawing(self, views=None) -> str:
        """Генерирует полный чертёж, возвращает SVG"""
        if views is None:
            views = ["side", "front", "rear", "top"]

        R = self.s(self.p.outer_diameter / 2)
        L = self.s(self.p.total_length)
        hd = self.s(self.head_depth)
        nh = self.s(self.nozzle_h)
        sh = self.s(self.p.support_height)

        # Ширина бокового вида
        side_w = L + 2 * hd + self.MARGIN * 2 + 30 + nh + 30
        # Ширина одного круглого вида (спереди/сзади)
        circle_view_w = (R + self.DIM_OFFSET) * 2 + 30
        # Высота бокового вида
        side_h = R * 2 + sh + nh + self.MARGIN * 2 + 40
        # Высота вида сверху
        top_h = R * 2 + self.DIM_OFFSET * 2 + 40

        # Расчёт размера листа чтобы всё поместилось
        # Ряд 1: боковой + спереди + сзади
        row1_w = side_w + circle_view_w * 2 + 20
        # Ряд 2: вид сверху
        row2_w = side_w
        page_w = max(594, row1_w + 40)
        page_h = max(420, side_h + top_h + 80)

        dwg = svgwrite.Drawing(
            size=(f"{page_w}mm", f"{page_h}mm"),
            viewBox=f"0 0 {page_w} {page_h}"
        )

        self.draw_frame(dwg, page_w, page_h)

        margin_left = 25
        margin_top = 10

        # Главный вид (сбоку) — верхний левый
        sw, s_h = 0, 0
        if "side" in views:
            sw, s_h = self.draw_side_view(dwg, ox=margin_left, oy=margin_top)

        # Вид спереди — справа от главного вида
        front_w = 0
        if "front" in views:
            fx = margin_left + sw + 10
            fw, fh = self.draw_front_view(dwg, ox=fx, oy=margin_top)
            front_w = fw

        # Вид сзади — справа от вида спереди
        if "rear" in views:
            fx2 = margin_left + sw + 10 + front_w + 10
            self.draw_rear_view(dwg, ox=fx2, oy=margin_top)

        # Вид сверху — под главным видом
        if "top" in views:
            self.draw_top_view(dwg, ox=margin_left, oy=margin_top + s_h + 5)

        return dwg.tostring()