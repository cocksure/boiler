"""
Паровой котёл — горизонтальный жаротрубный с паросборником.
"""

import math
import svgwrite
from drawing_engine.base import BaseDrawing
from backend.models import SteamBoilerParams


class SteamBoilerDrawing(BaseDrawing):

    ELLIPSE_RATIO = 0.25
    NOZZLE_H = 70

    def __init__(self, params: SteamBoilerParams, scale: float = 0.1):
        super().__init__(scale)
        self.p = params
        self.head_depth = params.outer_diameter * self.ELLIPSE_RATIO

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
        nh = self.s(self.NOZZLE_H)
        sh = self.s(p.support_height)
        sd_r = self.s(p.steam_drum_diameter / 2)
        sd_l = self.s(p.steam_drum_length)
        sd_off = self.s(p.steam_drum_offset_y)

        bx = ox + hd + 5
        cy = oy + R + sd_r * 2 + sd_off + nh + 25

        # ── Основной корпус ──
        g.add(dwg.line((bx, cy - R), (bx + L, cy - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy + R), (bx + L, cy + R), **self.S_MAIN))

        # Днища
        self.ellipse_arc(dwg, g, bx, cy, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy, hd, R, -90, 90, self.S_MAIN)

        # Внутренние стенки
        g.add(dwg.line((bx, cy - Ri), (bx + L, cy - Ri), **self.S_THIN))
        g.add(dwg.line((bx, cy + Ri), (bx + L, cy + Ri), **self.S_THIN))

        # Жаровая труба
        ft = self.s(p.front_head_thickness)
        fstart = bx + ft
        g.add(dwg.rect(insert=(fstart, cy - Rf), size=(Lf, Rf * 2), **self.S_MAIN))

        # Дымогарные трубы (пунктир)
        zone_top = cy - (Rf + Ri) / 2
        zone_bot = cy + (Rf + Ri) / 2
        g.add(dwg.line((fstart, zone_top), (fstart + Lf, zone_top), **self.S_HIDDEN))
        g.add(dwg.line((fstart, zone_bot), (fstart + Lf, zone_bot), **self.S_HIDDEN))

        # Осевая
        g.add(dwg.line((bx - hd - 10, cy), (bx + L + hd + 10, cy), **self.S_CENTER))

        # ── Паросборник (верхний барабан) ──
        sd_cy = cy - R - sd_off - sd_r
        sd_bx = bx + (L - sd_l) / 2  # Центрирован по длине

        # Цилиндрическая часть
        g.add(dwg.line((sd_bx, sd_cy - sd_r), (sd_bx + sd_l, sd_cy - sd_r), **self.S_MAIN))
        g.add(dwg.line((sd_bx, sd_cy + sd_r), (sd_bx + sd_l, sd_cy + sd_r), **self.S_MAIN))
        # Днища паросборника
        sd_hd = sd_r * 0.3
        self.ellipse_arc(dwg, g, sd_bx, sd_cy, sd_hd, sd_r, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, sd_bx + sd_l, sd_cy, sd_hd, sd_r, -90, 90, self.S_MAIN)

        # Осевая паросборника
        g.add(dwg.line((sd_bx - sd_hd - 5, sd_cy),
                        (sd_bx + sd_l + sd_hd + 5, sd_cy), **self.S_CENTER))

        # Соединительные трубы между корпусом и паросборником
        pipe_spacing = sd_l / 4
        for i in range(3):
            px = sd_bx + pipe_spacing * (i + 1)
            g.add(dwg.line((px, cy - R), (px, sd_cy + sd_r), **self.S_THIN))

        # ── Предохранительные клапаны (на паросборнике) ──
        sv_r = self.s(p.safety_valve_diameter / 2)
        for i in range(p.safety_valve_count):
            svx = sd_bx + sd_l * (0.3 + 0.4 * i)
            self.nozzle_side(dwg, g, svx, sd_cy - sd_r,
                             p.safety_valve_diameter / 2, 40,
                             direction="up", label=f"ПК{i+1}")

        # ── Уровнемер ──
        lg_x = sd_bx + self.s(p.level_gauge_position_x)
        lg_h = sd_r * 1.5
        g.add(dwg.rect(insert=(lg_x - 1, sd_cy - lg_h / 2),
                        size=(2, lg_h), **self.S_MAIN))
        g.add(dwg.line((lg_x - 1, sd_cy - lg_h / 2), (lg_x - 1, sd_cy + lg_h / 2),
                        stroke="blue", stroke_width="0.3"))
        g.add(dwg.text("Ур.", insert=(lg_x + 4, sd_cy),
                        font_size="3mm", font_family=self.FONT, fill="black"))

        # ── Патрубки основного корпуса ──
        inlet_cx = bx + self.s(p.inlet_position_x)
        self.nozzle_side(dwg, g, inlet_cx, cy + R,
                         p.inlet_diameter / 2, self.NOZZLE_H,
                         direction="down", label="G1 Питание")
        # Выход пара — на паросборнике
        outlet_cx = sd_bx + sd_l * 0.7
        self.nozzle_side(dwg, g, outlet_cx, sd_cy - sd_r,
                         p.outlet_diameter / 2, self.NOZZLE_H,
                         direction="up", label="G2 Пар")
        # Дымоход
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
                   sd_cy - sd_r - nh - 15, p.total_length, above=True)
        self.dim_v(dwg, g, cy - R, cy + R,
                   bx - hd - 5, p.outer_diameter, left=True)
        self.dim_v(dwg, g, sd_cy - sd_r, sd_cy + sd_r,
                   sd_bx - sd_hd - 5, p.steam_drum_diameter, left=True)

        self.view_label(dwg, g, bx + L / 2, cy + R + sh + 25, "Вид сбоку")
        dwg.add(g)

        total_w = L + 2 * hd + self.MARGIN + nh + 50
        total_h = R * 2 + sd_r * 2 + sd_off + sh + nh * 2 + 80
        return total_w, total_h

    # ─── ВИД СПЕРЕДИ ─────────────────────────────────────────────

    def draw_front_view(self, dwg, ox, oy):
        g = dwg.g(id="view_front")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        Rf = self.s(p.furnace_diameter / 2)
        sh = self.s(p.support_height)
        sd_r = self.s(p.steam_drum_diameter / 2)
        sd_off = self.s(p.steam_drum_offset_y)

        cx = ox + R + self.DIM_OFFSET + 5
        cy = oy + R + sd_r * 2 + sd_off + 25

        # Основной корпус
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))
        g.add(dwg.circle(center=(cx, cy), r=Rf, **self.S_MAIN))

        # Осевые
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымогарные трубы
        self.smoke_tubes_cross(dwg, g, cx, cy, Ri, Rf,
                               p.smoke_tube_diameter, p.smoke_tube_count,
                               p.smoke_tube_rows)

        # Паросборник (круг сверху)
        sd_cy = cy - R - sd_off - sd_r
        g.add(dwg.circle(center=(cx, sd_cy), r=sd_r, **self.S_MAIN))
        g.add(dwg.line((cx - 5, sd_cy), (cx + 5, sd_cy), **self.S_CENTER))
        g.add(dwg.line((cx, sd_cy - 5), (cx, sd_cy + 5), **self.S_CENTER))

        # Соединительные трубы
        g.add(dwg.line((cx - R * 0.3, cy - R), (cx - R * 0.3, sd_cy + sd_r), **self.S_THIN))
        g.add(dwg.line((cx + R * 0.3, cy - R), (cx + R * 0.3, sd_cy + sd_r), **self.S_THIN))

        # Горелка
        g.add(dwg.circle(center=(cx, cy), r=Rf * 0.4, **self.S_THIN))
        g.add(dwg.text("Горелка", insert=(cx, cy + 2), text_anchor="middle",
                        font_size="2.5px", font_family=self.FONT, fill="black"))

        # Опора
        sw = self.s(p.support_width) * 1.5
        top_y = cy + R
        bot_y = top_y + self.s(p.support_height)
        g.add(dwg.rect(insert=(cx - sw/2, top_y), size=(sw, bot_y - top_y), **self.S_MAIN))
        self.hatch_rect(dwg, g, cx - sw/2, top_y, sw, bot_y - top_y)
        g.add(dwg.line((cx - sw/2 - 5, bot_y), (cx + sw/2 + 5, bot_y), **self.S_MAIN))

        # Размеры
        self.dim_diameter(dwg, g, cx, cy, R, p.outer_diameter, 45)
        self.dim_diameter(dwg, g, cx, sd_cy, sd_r, p.steam_drum_diameter, 30)

        self.view_label(dwg, g, cx, bot_y + 15, "Вид спереди (А)")
        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, R * 2 + sd_r * 2 + sd_off + sh + 70

    # ─── ВИД СВЕРХУ ──────────────────────────────────────────────

    def draw_top_view(self, dwg, ox, oy):
        g = dwg.g(id="view_top")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        L = self.s(p.total_length)
        hd = self.s(self.head_depth)
        sd_r = self.s(p.steam_drum_diameter / 2)
        sd_l = self.s(p.steam_drum_length)

        bx = ox + hd + 5
        cy_main = oy + R + sd_r + self.DIM_OFFSET + 10
        cy_sd = cy_main - R - self.s(p.steam_drum_offset_y) / 2

        # Основной корпус
        g.add(dwg.line((bx, cy_main - R), (bx + L, cy_main - R), **self.S_MAIN))
        g.add(dwg.line((bx, cy_main + R), (bx + L, cy_main + R), **self.S_MAIN))
        self.ellipse_arc(dwg, g, bx, cy_main, hd, R, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, bx + L, cy_main, hd, R, -90, 90, self.S_MAIN)

        # Паросборник (прямоугольник сверху)
        sd_bx = bx + (L - sd_l) / 2
        g.add(dwg.line((sd_bx, cy_sd - sd_r), (sd_bx + sd_l, cy_sd - sd_r), **self.S_MAIN))
        g.add(dwg.line((sd_bx, cy_sd + sd_r), (sd_bx + sd_l, cy_sd + sd_r), **self.S_MAIN))
        sd_hd = sd_r * 0.3
        self.ellipse_arc(dwg, g, sd_bx, cy_sd, sd_hd, sd_r, 90, 270, self.S_MAIN)
        self.ellipse_arc(dwg, g, sd_bx + sd_l, cy_sd, sd_hd, sd_r, -90, 90, self.S_MAIN)

        # Осевые
        g.add(dwg.line((bx - hd - 5, cy_main), (bx + L + hd + 5, cy_main), **self.S_CENTER))

        # Дымоход
        fr = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(bx + L + hd, cy_main), r=fr, **self.S_MAIN))

        # Размеры
        self.dim_h(dwg, g, bx, bx + L, cy_sd - sd_r - 5, p.total_length, above=True)

        self.view_label(dwg, g, bx + L / 2, cy_main + R + self.DIM_OFFSET + 10,
                        "Вид сверху (В)")
        dwg.add(g)
        return L + 2 * hd + 30, R * 2 + sd_r * 2 + self.DIM_OFFSET * 2 + 40

    # ─── Полный чертёж ───────────────────────────────────────────

    def generate(self, views=None) -> str:
        if views is None:
            views = ["side", "front", "top"]

        R = self.s(self.p.outer_diameter / 2)
        L = self.s(self.p.total_length)
        sd_r = self.s(self.p.steam_drum_diameter / 2)

        side_w = L + self.s(self.head_depth) * 2 + 100
        side_h = R * 2 + sd_r * 2 + self.s(self.p.support_height) + 150
        front_w = R * 2 + 80

        page_w = max(594, side_w + front_w + 80)
        page_h = max(480, side_h + R * 2 + 190)

        dwg = svgwrite.Drawing(size=(f"{page_w}mm", f"{page_h}mm"),
                               viewBox=f"0 0 {page_w} {page_h}")

        p = self.p
        self.draw_frame(dwg, page_w, page_h,
                        name=p.name,
                        boiler_type=f"Паровой ({p.steam_capacity} т/ч, {p.pressure_mpa} МПа)",
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