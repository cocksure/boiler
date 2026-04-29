"""
Твёрдотопливный котёл (ОВТ, КВГ) — горизонтальный с загрузочной дверцей,
колосниковой решёткой, зольником.
"""

import math
import svgwrite
from drawing_engine.base import BaseDrawing
from backend.models import SolidFuelBoilerParams


class SolidFuelBoilerDrawing(BaseDrawing):

    ELLIPSE_RATIO = 0.2
    NOZZLE_H = 60

    def __init__(self, params: SolidFuelBoilerParams, scale: float = 0.1):
        super().__init__(scale)
        self.p = params
        self.head_depth = params.outer_diameter * self.ELLIPSE_RATIO

    # ─── ВИД СБОКУ (продольный разрез) ───────────────────────────

    def draw_side_view(self, dwg, ox, oy):
        g = dwg.g(id="view_side")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        L = self.s(p.total_length)
        hd = self.s(self.head_depth)
        wt = self.s(p.wall_thickness)
        Ri = R - wt
        sh = self.s(p.support_height)
        nh = self.s(self.NOZZLE_H)

        # Топка
        Fw = self.s(p.furnace_width) / 2
        Fh = self.s(p.furnace_height)
        Fl = self.s(p.furnace_length)

        # Колосник
        grate_z = self.s(p.grate_position_z)
        grate_l = self.s(p.grate_length)

        # Зольник
        ash_h = self.s(p.ash_pit_height)

        bx = ox + hd + self.s(30) + 5  # Место для дверцы слева
        cy = oy + R + nh + 20

        # ── Цилиндрическая часть ──
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))

        # Днища
        self.ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, self.S_MAIN)

        # Внутренние стенки
        g.add(dwg.line((bx, cy - Ri), (bx + L, cy - Ri), **self.S_THIN))
        g.add(dwg.line((bx, cy + Ri), (bx + L, cy + Ri), **self.S_THIN))

        # Осевая
        g.add(dwg.line((bx - hd - 15, cy), (bx + L + hd + 15, cy), **self.S_CENTER))

        # ── Топка (внутри корпуса, нижняя часть) ──
        ft = self.s(p.front_head_thickness)
        furnace_left = bx + ft
        furnace_right = furnace_left + Fl
        furnace_top = cy + R - Fh - self.s(20)
        furnace_bot = cy + R - self.s(20)

        g.add(dwg.rect(insert=(furnace_left, furnace_top),
                        size=(Fl, Fh), **self.S_MAIN))

        # ── Колосниковая решётка ──
        grate_y = furnace_bot - grate_z + Fh
        g.add(dwg.line((furnace_left + 5, grate_y), (furnace_left + grate_l, grate_y),
                        **self.S_THICK))
        # Штрихи колосника
        for i in range(int(grate_l / 3)):
            gx = furnace_left + 5 + i * 3
            g.add(dwg.line((gx, grate_y - 1.5), (gx, grate_y + 1.5), **self.S_THIN))

        # ── Зольник (под колосником) ──
        ash_top = grate_y
        ash_bot = grate_y + ash_h
        g.add(dwg.rect(insert=(furnace_left, ash_top),
                        size=(Fl, ash_h), **self.S_THIN))
        g.add(dwg.text("Зольник", insert=(furnace_left + Fl / 2, ash_top + ash_h / 2 + 1.5),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # ── Загрузочная дверца (спереди — слева) ──
        dw = self.s(p.door_width)
        dh = self.s(p.door_height)
        dz = self.s(p.door_position_z)
        door_y = cy + R - dz - dh
        door_x = bx - hd
        # Дверца как прямоугольник с петлями
        g.add(dwg.rect(insert=(door_x - self.s(15), door_y),
                        size=(self.s(15), dh), **self.S_MAIN))
        self.hatch_rect(dwg, g, door_x - self.s(15), door_y, self.s(15), dh)
        # Ручка
        g.add(dwg.circle(center=(door_x - self.s(7), door_y + dh * 0.3), r=1.5, **self.S_MAIN))
        g.add(dwg.text("Загрузочная\nдверца", insert=(door_x - self.s(20), door_y + dh / 2),
                        text_anchor="end", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # ── Дверца зольника (ниже) ──
        adw = self.s(p.ash_door_width)
        adh = self.s(p.ash_door_height)
        ash_door_y = grate_y + 2
        g.add(dwg.rect(insert=(door_x - self.s(12), ash_door_y),
                        size=(self.s(12), adh), **self.S_MAIN))
        g.add(dwg.text("Зольная\nдверца", insert=(door_x - self.s(17), ash_door_y + adh / 2),
                        text_anchor="end", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # ── Дымогарные трубы (над топкой — пунктир) ──
        tube_zone_top = cy - Ri + self.s(20)
        tube_zone_bot = furnace_top - self.s(10)
        if tube_zone_bot > tube_zone_top:
            n_vis = min(p.smoke_tube_rows, 4)
            for i in range(n_vis):
                ty = tube_zone_top + (tube_zone_bot - tube_zone_top) * i / max(n_vis - 1, 1)
                g.add(dwg.line((furnace_left, ty), (furnace_right, ty), **self.S_HIDDEN))

        # ── Патрубки ──
        inlet_cx = bx + self.s(p.inlet_position_x)
        outlet_cx = bx + self.s(p.outlet_position_x)
        self.nozzle_side(dwg, g, inlet_cx, cy - R,
                         p.inlet_diameter / 2, self.NOZZLE_H,
                         direction="up", label="G1 Вход")
        self.nozzle_side(dwg, g, outlet_cx, cy - R,
                         p.outlet_diameter / 2, self.NOZZLE_H,
                         direction="up", label="G2 Выход")
        self.nozzle_side(dwg, g, bx + L + hd, cy,
                         p.flue_diameter / 2, self.NOZZLE_H,
                         direction="right", label="Дымоход")

        # ── Опоры ──
        spacing = L / (p.support_count + 1)
        for i in range(p.support_count):
            scx = bx + spacing * (i + 1)
            self.saddle_support(dwg, g, scx, cy + R, p.support_width, p.support_height)

        # ── Размеры ──
        self.dim_h(dwg, g, bx, bx + L,
                   cy - R - nh - 5, p.total_length, above=True)
        self.dim_v(dwg, g, cy - R, cy + R,
                   bx - hd - self.s(25), p.outer_diameter, left=True)
        self.dim_h(dwg, g, furnace_left, furnace_right,
                   cy + R + 8, p.furnace_length, above=False)

        self.view_label(dwg, g, bx + L / 2, cy + R + sh + 25, "Вид сбоку (разрез)")
        dwg.add(g)

        total_w = L + 2 * hd + self.MARGIN + nh + 60
        total_h = R * 2 + sh + nh + 70
        return total_w, total_h

    # ─── ВИД СПЕРЕДИ ─────────────────────────────────────────────

    def draw_front_view(self, dwg, ox, oy):
        g = dwg.g(id="view_front")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = R - self.s(p.wall_thickness)
        sh = self.s(p.support_height)
        nh = self.s(self.NOZZLE_H)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + nh + 20

        # Корпус
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))

        # Осевые
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Загрузочная дверца (прямоугольник на передней стенке)
        dw = self.s(p.door_width) / 2
        dh = self.s(p.door_height)
        dz = self.s(p.door_position_z)
        door_top = cy + R - dz - dh
        g.add(dwg.rect(insert=(cx - dw, door_top), size=(dw * 2, dh), **self.S_THICK))
        g.add(dwg.text("Загрузочная дверца", insert=(cx, door_top + dh / 2 + 1.5),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))
        # Ручка
        g.add(dwg.circle(center=(cx, door_top + dh * 0.3), r=2, **self.S_MAIN))

        # Дверца зольника (ниже)
        adw = self.s(p.ash_door_width) / 2
        adh = self.s(p.ash_door_height)
        grate_y = cy + R - self.s(p.grate_position_z)
        g.add(dwg.rect(insert=(cx - adw, grate_y + 2), size=(adw * 2, adh), **self.S_MAIN))
        g.add(dwg.text("Зольник", insert=(cx, grate_y + 2 + adh / 2 + 1),
                        text_anchor="middle", font_size="3mm",
                        font_family=self.FONT, fill="black"))

        # Дымогарные трубы
        self.smoke_tubes_cross(dwg, g, cx, cy - R * 0.2, Ri * 0.7,
                               self.s(p.furnace_width / 2) * 0.3,
                               p.smoke_tube_diameter, p.smoke_tube_count,
                               p.smoke_tube_rows)

        # Опора
        sw = self.s(p.support_width) * 1.5
        bot_y = cy + R + self.s(p.support_height)
        g.add(dwg.rect(insert=(cx - sw/2, cy + R), size=(sw, bot_y - cy - R), **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - sw/2, cy + R, sw, bot_y - cy - R)
        g.add(dwg.line((cx - sw/2 - 5, bot_y), (cx + sw/2 + 5, bot_y), **self.S_MAIN))

        # Размеры
        self.dim_diameter(dwg, g, cx, cy, R, p.outer_diameter, 45)

        self.view_label(dwg, g, cx, bot_y + 15, "Вид спереди (А)")
        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sh + nh + 60

    # ─── ВИД СВЕРХУ ──────────────────────────────────────────────

    def draw_top_view(self, dwg, ox, oy):
        g = dwg.g(id="view_top")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        L = self.s(p.total_length)
        hd = self.s(self.head_depth)

        bx = ox + hd + 5
        cy = oy + R + self.DIM_OFFSET

        # Корпус
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))
        self.ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, self.S_MAIN)

        # Осевая
        g.add(dwg.line((bx - hd - 10, cy), (bx + L + hd + 10, cy), **self.S_CENTER))

        # Патрубки
        ir = self.s(p.inlet_diameter / 2)
        inlet_cx = bx + self.s(p.inlet_position_x)
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=ir * 1.4, **self.S_MAIN))
        g.add(dwg.circle(center=(inlet_cx, cy - R * 0.3), r=ir, **self.S_MAIN))

        orr = self.s(p.outlet_diameter / 2)
        outlet_cx = bx + self.s(p.outlet_position_x)
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=orr * 1.4, **self.S_MAIN))
        g.add(dwg.circle(center=(outlet_cx, cy + R * 0.3), r=orr, **self.S_MAIN))

        # Дымоход
        fr = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(bx + L + hd, cy), r=fr, **self.S_MAIN))

        # Размеры
        self.dim_h(dwg, g, bx, bx + L, cy - R - 3, p.total_length, above=True)
        self.dim_v(dwg, g, cy - R, cy + R, bx - hd - 3, p.outer_diameter, left=True)

        self.view_label(dwg, g, bx + L / 2, cy + R + self.DIM_OFFSET + 10, "Вид сверху (В)")
        dwg.add(g)
        return L + 2 * hd + 30, R * 2 + self.DIM_OFFSET * 2 + 30

    # ─── Полный чертёж ───────────────────────────────────────────

    def generate(self, views=None) -> str:
        if views is None:
            views = ["side", "front", "top"]

        R = self.s(self.p.outer_diameter / 2)
        L = self.s(self.p.total_length)
        hd = self.s(self.head_depth)
        sh = self.s(self.p.support_height)

        side_w = L + 2 * hd + 100
        side_h = R * 2 + sh + 120
        front_w = R * 2 + 80

        page_w = max(594, side_w + front_w + 60)
        page_h = max(480, side_h + R * 2 + 160)

        dwg = svgwrite.Drawing(size=(f"{page_w}mm", f"{page_h}mm"),
                               viewBox=f"0 0 {page_w} {page_h}")

        p = self.p
        self.draw_frame(dwg, page_w, page_h,
                        name=p.name,
                        boiler_type="Твёрдотопливный (ОВТ/КВГ)",
                        dimensions=f"\u2300{p.outer_diameter:.0f} \u00d7 {p.total_length:.0f} мм")

        ml, mt = 25, 50
        sw, s_h = 0, 0
        if "side" in views:
            sw, s_h = self.draw_side_view(dwg, ox=ml, oy=mt)
        if "front" in views:
            self.draw_front_view(dwg, ox=ml + sw + 15, oy=mt)
        if "top" in views:
            self.draw_top_view(dwg, ox=ml, oy=mt + s_h + 10)

        return dwg.tostring()