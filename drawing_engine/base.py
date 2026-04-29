"""
Базовый класс генератора чертежей — общие элементы для всех типов котлов.
Рамка (ГОСТ 2.104), размерные линии, штриховка, патрубки, опоры.
"""

import math
import svgwrite


class BaseDrawing:
    """Общие методы для всех типов чертежей"""

    MARGIN = 30
    DIM_OFFSET = 20
    ARROW_SIZE = 2.5

    # Стили линий (ГОСТ 2.303)
    S_MAIN = {"stroke": "black", "stroke-width": "0.5", "fill": "none"}
    S_THIN = {"stroke": "black", "stroke-width": "0.25", "fill": "none"}
    S_CENTER = {"stroke": "black", "stroke-width": "0.18", "fill": "none",
                "stroke-dasharray": "10,3,2,3"}
    S_HIDDEN = {"stroke": "black", "stroke-width": "0.25", "fill": "none",
                "stroke-dasharray": "4,2"}
    S_DIM = {"stroke": "black", "stroke-width": "0.18", "fill": "none"}
    S_HATCH = {"stroke": "black", "stroke-width": "0.1", "fill": "none"}
    S_THICK = {"stroke": "black", "stroke-width": "0.7", "fill": "none"}

    FONT = "ISOCPEUR, Arial, sans-serif"

    def __init__(self, scale: float = 0.1):
        self.scale = scale

    def s(self, v: float) -> float:
        """Реальные мм -> мм на чертеже"""
        return v * self.scale

    # ─── Эллиптические дуги ──────────────────────────────────────

    def ellipse_arc(self, dwg, g, cx, cy, rx, ry, start=0, end=360, style=None, n=60):
        """Рисует эллиптическую дугу"""
        if style is None:
            style = self.S_MAIN
        pts = []
        for i in range(n + 1):
            a = math.radians(start + (end - start) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        g.add(dwg.polyline(pts, **style))

    # ─── Патрубки ────────────────────────────────────────────────

    def nozzle_side(self, dwg, g, cx, cy_base, radius, height, direction="up",
                    label="", flange=True):
        """Патрубок: вид сбоку (прямоугольник + фланец)"""
        r = self.s(radius)
        h = self.s(height)
        fl_w = r * 1.4
        fl_h = self.s(6)

        if direction == "up":
            yt = cy_base - h
            g.add(dwg.line((cx - r, cy_base), (cx - r, yt), **self.S_MAIN))
            g.add(dwg.line((cx + r, cy_base), (cx + r, yt), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(cx - fl_w, yt - fl_h),
                               size=(fl_w * 2, fl_h), **self.S_MAIN))
            else:
                g.add(dwg.line((cx - r, yt), (cx + r, yt), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base + 3), (cx, yt - fl_h - 5), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(cx, yt - fl_h - 3),
                               text_anchor="middle", font_size="2.8px",
                               font_family=self.FONT, fill="black"))

        elif direction == "down":
            yb = cy_base + h
            g.add(dwg.line((cx - r, cy_base), (cx - r, yb), **self.S_MAIN))
            g.add(dwg.line((cx + r, cy_base), (cx + r, yb), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(cx - fl_w, yb),
                               size=(fl_w * 2, fl_h), **self.S_MAIN))
            else:
                g.add(dwg.line((cx - r, yb), (cx + r, yb), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base - 3), (cx, yb + fl_h + 5), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(cx, yb + fl_h + 7),
                               text_anchor="middle", font_size="2.8px",
                               font_family=self.FONT, fill="black"))

        elif direction == "right":
            xe = cx + h
            g.add(dwg.line((cx, cy_base - r), (xe, cy_base - r), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base + r), (xe, cy_base + r), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(xe, cy_base - fl_w),
                               size=(fl_h, fl_w * 2), **self.S_MAIN))
            else:
                g.add(dwg.line((xe, cy_base - r), (xe, cy_base + r), **self.S_MAIN))
            g.add(dwg.line((cx - 3, cy_base), (xe + fl_h + 5, cy_base), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(xe + fl_h + 3, cy_base - 3),
                               text_anchor="start", font_size="2.8px",
                               font_family=self.FONT, fill="black"))

        elif direction == "left":
            xe = cx - h
            g.add(dwg.line((cx, cy_base - r), (xe, cy_base - r), **self.S_MAIN))
            g.add(dwg.line((cx, cy_base + r), (xe, cy_base + r), **self.S_MAIN))
            if flange:
                g.add(dwg.rect(insert=(xe - fl_h, cy_base - fl_w),
                               size=(fl_h, fl_w * 2), **self.S_MAIN))
            else:
                g.add(dwg.line((xe, cy_base - r), (xe, cy_base + r), **self.S_MAIN))
            g.add(dwg.line((cx + 3, cy_base), (xe - fl_h - 5, cy_base), **self.S_CENTER))
            if label:
                g.add(dwg.text(label, insert=(xe - fl_h - 3, cy_base - 3),
                               text_anchor="end", font_size="2.8px",
                               font_family=self.FONT, fill="black"))

    def nozzle_circle(self, dwg, g, cx, cy, radius, label=""):
        """Патрубок: вид с торца (два круга)"""
        r = self.s(radius)
        g.add(dwg.circle(center=(cx, cy), r=r, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=r * 0.7, **self.S_THIN))
        if label:
            g.add(dwg.text(label, insert=(cx, cy - r - 2),
                           text_anchor="middle", font_size="2.5px",
                           font_family=self.FONT, fill="black"))

    # ─── Размерные линии ─────────────────────────────────────────

    def dim_h(self, dwg, g, x1, x2, y, value, above=True):
        """Горизонтальная размерная линия"""
        off = -self.DIM_OFFSET if above else self.DIM_OFFSET
        yd = y + off
        a = self.ARROW_SIZE
        g.add(dwg.line((x1, y), (x1, yd + (2 if above else -2)), **self.S_DIM))
        g.add(dwg.line((x2, y), (x2, yd + (2 if above else -2)), **self.S_DIM))
        g.add(dwg.line((x1, yd), (x2, yd), **self.S_DIM))
        g.add(dwg.polygon([(x1, yd), (x1+a, yd-a/2), (x1+a, yd+a/2)], fill="black"))
        g.add(dwg.polygon([(x2, yd), (x2-a, yd-a/2), (x2-a, yd+a/2)], fill="black"))
        ty = yd - 1.5 if above else yd + 4.5
        g.add(dwg.text(f"{value:.0f}", insert=((x1+x2)/2, ty),
                        text_anchor="middle", font_size="3.2px",
                        font_family=self.FONT, fill="black"))

    def dim_v(self, dwg, g, y1, y2, x, value, left=True):
        """Вертикальная размерная линия"""
        off = -self.DIM_OFFSET if left else self.DIM_OFFSET
        xd = x + off
        a = self.ARROW_SIZE
        g.add(dwg.line((x, y1), (xd + (2 if left else -2), y1), **self.S_DIM))
        g.add(dwg.line((x, y2), (xd + (2 if left else -2), y2), **self.S_DIM))
        g.add(dwg.line((xd, y1), (xd, y2), **self.S_DIM))
        g.add(dwg.polygon([(xd, y1), (xd-a/2, y1+a), (xd+a/2, y1+a)], fill="black"))
        g.add(dwg.polygon([(xd, y2), (xd-a/2, y2-a), (xd+a/2, y2-a)], fill="black"))
        tx = xd - 2.5 if left else xd + 4.5
        mid = (y1 + y2) / 2
        g.add(dwg.text(f"{value:.0f}", insert=(tx, mid),
                        text_anchor="middle", font_size="3.2px",
                        font_family=self.FONT, fill="black",
                        transform=f"rotate(-90,{tx},{mid})"))

    def dim_diameter(self, dwg, g, cx, cy, radius, value, angle_deg=45):
        """Размер диаметра"""
        a = math.radians(angle_deg)
        x1 = cx - radius * math.cos(a)
        y1 = cy - radius * math.sin(a)
        x2 = cx + radius * math.cos(a)
        y2 = cy + radius * math.sin(a)
        g.add(dwg.line((x1, y1), (x2, y2), **self.S_DIM))
        g.add(dwg.circle(center=(x1, y1), r=0.5, fill="black"))
        g.add(dwg.circle(center=(x2, y2), r=0.5, fill="black"))
        mx, my = (x1+x2)/2, (y1+y2)/2
        g.add(dwg.text(f"\u2300{value:.0f}", insert=(mx+3, my-2),
                        text_anchor="start", font_size="3.2px",
                        font_family=self.FONT, fill="black"))

    # ─── Штриховка ───────────────────────────────────────────────

    def hatch_rect(self, dwg, g, x, y, w, h, spacing=1.8):
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

    # ─── Дымогарные трубы ────────────────────────────────────────

    def smoke_tubes_cross(self, dwg, g, cx, cy, r_inner, r_furnace,
                          tube_d, count, rows, style=None):
        """Дымогарные трубы в поперечном сечении"""
        if style is None:
            style = self.S_THIN
        r_smoke = self.s(tube_d / 2)
        zone_in = r_furnace + r_smoke + self.s(8)
        zone_out = r_inner - r_smoke - self.s(4)
        if rows <= 0 or zone_out <= zone_in:
            return
        placed = 0
        for row in range(rows):
            if placed >= count:
                break
            r_row = zone_in + (zone_out - zone_in) * row / max(rows - 1, 1)
            n = min(int(2 * math.pi * r_row / (r_smoke * 2 + self.s(4))),
                    count - placed)
            for j in range(n):
                if placed >= count:
                    break
                angle = 2 * math.pi * j / n
                tx = cx + r_row * math.cos(angle)
                ty = cy + r_row * math.sin(angle)
                g.add(dwg.circle(center=(tx, ty), r=r_smoke, **style))
                placed += 1

    # ─── Седловая опора ──────────────────────────────────────────

    def saddle_support(self, dwg, g, cx, top_y, width, height):
        """Седловая опора (трапеция + штриховка)"""
        w = self.s(width)
        h = self.s(height)
        bw = w * 1.5
        by = top_y + h
        pts = [
            (cx - w/2, top_y), (cx + w/2, top_y),
            (cx + bw/2, by), (cx - bw/2, by), (cx - w/2, top_y)
        ]
        g.add(dwg.polyline(pts, **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - bw/2, top_y, bw, h)
        g.add(dwg.line((cx - bw/2 - 5, by), (cx + bw/2 + 5, by), **self.S_MAIN))

    # ─── Прямоугольная опора (для вертикальных) ──────────────────

    def rect_support(self, dwg, g, cx, top_y, width, height):
        """Прямоугольная опора"""
        w = self.s(width)
        h = self.s(height)
        g.add(dwg.rect(insert=(cx - w/2, top_y), size=(w, h), **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - w/2, top_y, w, h)
        g.add(dwg.line((cx - w/2 - 5, top_y + h), (cx + w/2 + 5, top_y + h), **self.S_MAIN))

    # ─── Подпись вида ────────────────────────────────────────────

    def view_label(self, dwg, g, x, y, text):
        g.add(dwg.text(text, insert=(x, y), text_anchor="middle",
                        font_size="4.5px", font_family=self.FONT,
                        fill="black", font_weight="bold"))
        tw = len(text) * 2.5
        g.add(dwg.line((x - tw, y + 1.5), (x + tw, y + 1.5),
                        stroke="black", stroke_width="0.3"))

    # ─── Рамка чертежа (ГОСТ 2.104) ─────────────────────────────

    def draw_frame(self, dwg, w, h, name="Котёл", boiler_type="", dimensions=""):
        g = dwg.g(id="frame")
        g.add(dwg.rect(insert=(0, 0), size=(w, h),
                        stroke="black", stroke_width="0.3", fill="white"))
        g.add(dwg.rect(insert=(20, 5), size=(w - 25, h - 10),
                        stroke="black", stroke_width="0.7", fill="none"))

        sw, sh = 185, 55
        sx = w - 5 - sw
        sy = h - 5 - sh
        g.add(dwg.rect(insert=(sx, sy), size=(sw, sh),
                        stroke="black", stroke_width="0.7", fill="white"))
        for dy in [15, 30, 40]:
            g.add(dwg.line((sx, sy+dy), (sx+sw, sy+dy),
                           stroke="black", stroke_width="0.35"))
        g.add(dwg.line((sx+65, sy), (sx+65, sy+sh),
                        stroke="black", stroke_width="0.35"))
        g.add(dwg.line((sx+120, sy), (sx+120, sy+15),
                        stroke="black", stroke_width="0.35"))

        tc = sx + 125
        g.add(dwg.text(name, insert=(tc+30, sy+12), text_anchor="middle",
                        font_size="7px", font_family=self.FONT,
                        fill="black", font_weight="bold"))
        g.add(dwg.text(f"Тип: {boiler_type}", insert=(tc+30, sy+25),
                        text_anchor="middle", font_size="3.5px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text(dimensions, insert=(tc+30, sy+37),
                        text_anchor="middle", font_size="3.5px",
                        font_family=self.FONT, fill="black"))
        sv = int(1 / self.scale)
        g.add(dwg.text(f"Масштаб 1:{sv}", insert=(tc+30, sy+48),
                        text_anchor="middle", font_size="3px",
                        font_family=self.FONT, fill="black"))
        for i, lbl in enumerate(["Разработал", "Проверил", "Утвердил"]):
            g.add(dwg.text(lbl, insert=(sx+4, sy+12+i*15),
                           font_size="2.5px", font_family=self.FONT, fill="black"))
        dwg.add(g)