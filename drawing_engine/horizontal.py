"""
Горизонтальный жаротрубный котёл (КВа-Гн/Лжн) — 3-ходовой.
Виды: сбоку, спереди, сзади, сверху.
"""

import math
import svgwrite
from drawing_engine.base import BaseDrawing
from backend.models import HorizontalFireTubeParams


class HorizontalFireTubeDrawing(BaseDrawing):

    ELLIPSE_RATIO = 0.25
    NOZZLE_H_RATIO = 0.08

    def __init__(self, params: HorizontalFireTubeParams, scale: float = 0.1):
        super().__init__(scale)
        self.p = params
        self.head_depth = params.outer_diameter * self.ELLIPSE_RATIO
        self.nozzle_h = max(params.outer_diameter * self.NOZZLE_H_RATIO, 60)

    # ─── ВИД СБОКУ ──────────────────────────────────────────────

    def draw_side_view(self, dwg, ox, oy):
        g = dwg.g(id="view_side")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        L = self.s(p.total_length)
        Rf = self.s(p.furnace_diameter / 2)
        Lf = self.s(p.furnace_length)
        hd = self.s(self.head_depth)
        wt = self.s(p.wall_thickness)
        nh = self.s(self.nozzle_h)
        sh = self.s(p.support_height)

        bx = ox + hd + 5
        cy = oy + R + nh + 15

        # Цилиндрическая часть
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))

        # Эллиптические днища
        self.ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx, cy, hd - wt, Ri, 90, 270, self.S_THIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd - wt, Ri, -90, 90, self.S_THIN)

        # Внутренние стенки
        g.add(dwg.line((bx, cy - Ri), (bx + L, cy - Ri), **self.S_THIN))
        g.add(dwg.line((bx, cy + Ri), (bx + L, cy + Ri), **self.S_THIN))

        # Жаровая труба (1-й ход)
        ft = self.s(p.front_head_thickness)
        fstart = bx + ft
        g.add(dwg.line((fstart, cy - Rf), (fstart + Lf, cy - Rf), **self.S_MAIN))
        g.add(dwg.line((fstart, cy + Rf), (fstart + Lf, cy + Rf), **self.S_MAIN))
        g.add(dwg.line((fstart, cy - Rf), (fstart, cy + Rf), **self.S_MAIN))
        g.add(dwg.line((fstart + Lf, cy - Rf), (fstart + Lf, cy + Rf), **self.S_MAIN))

        # Поворотная камера (задняя)
        pc_x = fstart + Lf
        pc_w = self.s(80)
        g.add(dwg.rect(insert=(pc_x, cy - Ri), size=(pc_w, Ri * 2), **self.S_HIDDEN))

        # Дымогарные трубы (2-й ход — пунктир, обратно)
        zone_top = cy - (Rf + Ri) / 2
        zone_bot = cy + (Rf + Ri) / 2
        tube_start = pc_x + pc_w
        tube_end = bx + ft
        # Верхний и нижний пучок
        g.add(dwg.line((tube_end, zone_top), (tube_start, zone_top), **self.S_HIDDEN))
        g.add(dwg.line((tube_end, zone_bot), (tube_start, zone_bot), **self.S_HIDDEN))
        # Средняя зона
        mid1 = cy - (Rf * 0.3 + Ri) / 2
        mid2 = cy + (Rf * 0.3 + Ri) / 2
        g.add(dwg.line((tube_end, mid1), (tube_start, mid1), **self.S_HIDDEN))
        g.add(dwg.line((tube_end, mid2), (tube_start, mid2), **self.S_HIDDEN))

        # Обозначение ходов газов стрелками
        arrow_y = cy + Rf * 0.7
        # 1-й ход →
        self._gas_flow_arrow(dwg, g, fstart + Lf * 0.3, arrow_y, "right", "1")
        # 2-й ход ←
        self._gas_flow_arrow(dwg, g, fstart + Lf * 0.6, zone_bot + 3, "left", "2")

        # Осевая линия
        g.add(dwg.line((bx - hd - 10, cy), (bx + L + hd + 10, cy), **self.S_CENTER))

        # Патрубки
        inlet_cx = bx + self.s(p.inlet_position_x)
        outlet_cx = bx + self.s(p.outlet_position_x)
        self.nozzle_side(dwg, g, inlet_cx, cy - R,
                         p.inlet_diameter / 2, self.nozzle_h,
                         direction="up", label="G1 Вход")
        self.nozzle_side(dwg, g, outlet_cx, cy - R,
                         p.outlet_diameter / 2, self.nozzle_h,
                         direction="up", label="G2 Выход")
        self.nozzle_side(dwg, g, bx + L + hd, cy,
                         p.flue_diameter / 2, self.nozzle_h,
                         direction="right", label="Дымоход")

        # Опоры
        spacing = L / (p.support_count + 1)
        for i in range(p.support_count):
            scx = bx + spacing * (i + 1)
            self.saddle_support(dwg, g, scx, cy + R, p.support_width, p.support_height)

        # Размерные линии
        self.dim_h(dwg, g, bx - hd, bx + L + hd,
                   cy - R - nh - 5, p.total_length + 2 * self.head_depth, above=True)
        self.dim_h(dwg, g, bx, bx + L,
                   cy - R - nh - 20, p.total_length, above=True)
        self.dim_v(dwg, g, cy - R, cy + R,
                   bx - hd - 5, p.outer_diameter, left=True)
        self.dim_h(dwg, g, fstart, fstart + Lf,
                   cy + R + 8, p.furnace_length, above=False)
        self.dim_v(dwg, g, cy - Rf, cy + Rf,
                   bx + L + hd + nh + 10, p.furnace_diameter, left=False)

        self.view_label(dwg, g, bx + L / 2, cy + R + sh + 25, "Вид сбоку")
        dwg.add(g)

        total_w = L + 2 * hd + self.MARGIN + nh + 40
        total_h = R * 2 + sh + nh + self.MARGIN + 50
        return total_w, total_h

    # ─── ВИД СПЕРЕДИ ─────────────────────────────────────────────

    def draw_front_view(self, dwg, ox, oy):
        g = dwg.g(id="view_front")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        Rf = self.s(p.furnace_diameter / 2)
        sh = self.s(p.support_height)
        nh = self.s(self.nozzle_h)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + nh + 15

        # Корпус
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))
        # Жаровая труба (горелка)
        g.add(dwg.circle(center=(cx, cy), r=Rf, **self.S_MAIN))
        # Горелка в центре
        g.add(dwg.circle(center=(cx, cy), r=Rf * 0.4, **self.S_THIN))
        g.add(dwg.text("Горелка", insert=(cx, cy + 2), text_anchor="middle",
                        font_size="3mm", font_family=self.FONT, fill="black"))

        # Осевые
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымогарные трубы (в пространстве между жаровой и корпусом)
        self.smoke_tubes_cross(dwg, g, cx, cy, Ri, Rf,
                               p.smoke_tube_diameter, p.smoke_tube_count,
                               p.smoke_tube_rows)

        # Патрубки сверху
        self.nozzle_side(dwg, g, cx - self.s(p.outer_diameter * 0.15), cy - R,
                         p.inlet_diameter / 2, self.nozzle_h,
                         direction="up", label="G1")
        self.nozzle_side(dwg, g, cx + self.s(p.outer_diameter * 0.15), cy - R,
                         p.outlet_diameter / 2, self.nozzle_h,
                         direction="up", label="G2")

        # Опора
        sw = self.s(p.support_width) * 1.5
        top_y = cy + R
        bot_y = top_y + self.s(p.support_height)
        g.add(dwg.rect(insert=(cx - sw/2, top_y), size=(sw, bot_y - top_y), **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - sw/2, top_y, sw, bot_y - top_y)
        g.add(dwg.line((cx - sw/2 - 5, bot_y), (cx + sw/2 + 5, bot_y), **self.S_MAIN))

        # Размеры
        self.dim_diameter(dwg, g, cx, cy, R, p.outer_diameter, 45)
        self.dim_diameter(dwg, g, cx, cy, Rf, p.furnace_diameter, 135)

        self.view_label(dwg, g, cx, bot_y + 15, "Вид спереди (А)")
        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sh + nh + 50

    # ─── ВИД СЗАДИ ───────────────────────────────────────────────

    def draw_rear_view(self, dwg, ox, oy):
        g = dwg.g(id="view_rear")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        Rf = self.s(p.furnace_diameter / 2)
        sh = self.s(p.support_height)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + 15

        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))

        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымоход
        flue_r = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(cx, cy), r=flue_r, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=flue_r * 0.8, **self.S_THIN))
        g.add(dwg.text("Дымоход", insert=(cx, cy - flue_r - 2),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # Дымогарные трубы пунктиром
        self.smoke_tubes_cross(dwg, g, cx, cy, Ri, Rf,
                               p.smoke_tube_diameter, p.smoke_tube_count,
                               p.smoke_tube_rows, style=self.S_HIDDEN)

        # Опора
        sw = self.s(p.support_width) * 1.5
        top_y = cy + R
        bot_y = top_y + self.s(p.support_height)
        g.add(dwg.rect(insert=(cx - sw/2, top_y), size=(sw, bot_y - top_y), **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - sw/2, top_y, sw, bot_y - top_y)
        g.add(dwg.line((cx - sw/2 - 5, bot_y), (cx + sw/2 + 5, bot_y), **self.S_MAIN))

        self.dim_diameter(dwg, g, cx, cy, flue_r, p.flue_diameter, 30)
        self.view_label(dwg, g, cx, bot_y + 15, "Вид сзади (Б)")
        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sh + 50

    # ─── ВИД СВЕРХУ ──────────────────────────────────────────────

    def draw_top_view(self, dwg, ox, oy):
        g = dwg.g(id="view_top")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        L = self.s(p.total_length)
        hd = self.s(self.head_depth)
        Rf = self.s(p.furnace_diameter / 2)

        bx = ox + hd + 5
        cy = oy + R + self.DIM_OFFSET

        # Корпус
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))

        # Днища
        self.ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, self.S_MAIN)

        # Осевая
        g.add(dwg.line((bx - hd - 10, cy), (bx + L + hd + 10, cy), **self.S_CENTER))

        # Жаровая труба пунктиром
        ft = self.s(p.front_head_thickness)
        g.add(dwg.line((bx + ft, cy - Rf), (bx + ft + self.s(p.furnace_length), cy - Rf),
                        **self.S_HIDDEN))
        g.add(dwg.line((bx + ft, cy + Rf), (bx + ft + self.s(p.furnace_length), cy + Rf),
                        **self.S_HIDDEN))

        # Патрубки (круги сверху)
        inlet_cx = bx + self.s(p.inlet_position_x)
        outlet_cx = bx + self.s(p.outlet_position_x)
        ir = self.s(p.inlet_diameter / 2)
        orr = self.s(p.outlet_diameter / 2)
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=ir * 1.4, **self.S_MAIN))
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=ir, **self.S_MAIN))
        g.add(dwg.text("G1", insert=(inlet_cx, cy - R * 0.3 - ir * 1.4 - 2),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=orr * 1.4, **self.S_MAIN))
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=orr, **self.S_MAIN))
        g.add(dwg.text("G2", insert=(outlet_cx, cy + R * 0.3 + orr * 1.4 + 4),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # Дымоход
        fr = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(bx + L + hd, cy), r=fr, **self.S_MAIN))
        g.add(dwg.circle(center=(bx + L + hd, cy), r=fr * 0.8, **self.S_THIN))

        # Размеры
        self.dim_h(dwg, g, bx, bx + L, cy - R - 3, p.total_length, above=True)
        self.dim_v(dwg, g, cy - R, cy + R, bx - hd - 3, p.outer_diameter, left=True)

        self.view_label(dwg, g, bx + L / 2, cy + R + self.DIM_OFFSET + 10, "Вид сверху (В)")
        dwg.add(g)
        return L + 2 * hd + self.MARGIN + 20, R * 2 + self.DIM_OFFSET * 2 + 30

    # ─── Вспомогательные ─────────────────────────────────────────

    def _gas_flow_arrow(self, dwg, g, x, y, direction, label):
        """Стрелка направления газов"""
        length = 15
        a = 2
        if direction == "right":
            g.add(dwg.line((x, y), (x + length, y), stroke="red",
                           stroke_width="0.3", fill="none"))
            g.add(dwg.polygon([(x+length, y), (x+length-a, y-a), (x+length-a, y+a)],
                              fill="red"))
        else:
            g.add(dwg.line((x, y), (x - length, y), stroke="red",
                           stroke_width="0.3", fill="none"))
            g.add(dwg.polygon([(x-length, y), (x-length+a, y-a), (x-length+a, y+a)],
                              fill="red"))
        g.add(dwg.text(label, insert=(x + (5 if direction == "right" else -5), y - 2),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="red"))

    # ─── Полный чертёж ───────────────────────────────────────────

    def generate(self, views=None) -> str:
        if views is None:
            views = ["side", "front", "rear", "top"]

        R = self.s(self.p.outer_diameter / 2)
        L = self.s(self.p.total_length)
        hd = self.s(self.head_depth)
        nh = self.s(self.nozzle_h)
        sh = self.s(self.p.support_height)

        side_w = L + 2 * hd + self.MARGIN + nh + 50
        circle_w = (R + self.DIM_OFFSET) * 2 + 30
        side_h = R * 2 + sh + nh + self.MARGIN + 50
        top_h = R * 2 + self.DIM_OFFSET * 2 + 40

        page_w = max(594, side_w + circle_w * 2 + 60)
        page_h = max(480, 50 + side_h + 10 + top_h + 90)

        dwg = svgwrite.Drawing(size=(f"{page_w}mm", f"{page_h}mm"),
                               viewBox=f"0 0 {page_w} {page_h}")

        p = self.p
        self.draw_frame(dwg, page_w, page_h,
                        name=p.name,
                        boiler_type="КВа-Гн (жаротрубный)",
                        dimensions=f"\u2300{p.outer_diameter:.0f} \u00d7 {p.total_length:.0f} мм")

        ml, mt = 25, 50
        sw, s_h = 0, 0
        if "side" in views:
            sw, s_h = self.draw_side_view(dwg, ox=ml, oy=mt)
        fw = 0
        if "front" in views:
            fw, _ = self.draw_front_view(dwg, ox=ml + sw + 10, oy=mt)
        if "rear" in views:
            self.draw_rear_view(dwg, ox=ml + sw + 10 + fw + 10, oy=mt)
        if "top" in views:
            self.draw_top_view(dwg, ox=ml, oy=mt + s_h + 10)

        return dwg.tostring()