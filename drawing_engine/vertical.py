"""
Вертикальный котёл (КВс, КОГн, КВ-Т).
Виды: спереди, сбоку, сверху.
"""

import math
import svgwrite
from drawing_engine.base import BaseDrawing
from backend.models import VerticalBoilerParams


class VerticalBoilerDrawing(BaseDrawing):

    NOZZLE_H = 60

    def __init__(self, params: VerticalBoilerParams, scale: float = 0.1):
        super().__init__(scale)
        self.p = params

    # ─── ВИД СПЕРЕДИ (главный вид) ───────────────────────────────

    def draw_front_view(self, dwg, ox, oy):
        """Вид спереди — вертикальный разрез"""
        g = dwg.g(id="view_front")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)
        H = self.s(p.total_height)
        Rf = self.s(p.furnace_diameter / 2)
        Fh = self.s(p.furnace_height)
        sh = self.s(p.support_height)
        jg = self.s(p.jacket_gap)
        nh = self.s(self.NOZZLE_H)

        cx = ox + R + self.DIM_OFFSET + 10
        base_y = oy + H + sh + 20  # Нижняя точка (пол)
        top_y = base_y - sh - H    # Верх корпуса

        # ── Корпус (вертикальный цилиндр — прямоугольник) ──
        # Наружный
        g.add(dwg.line((cx - R, top_y), (cx - R, base_y - sh), **self.S_MAIN))
        g.add(dwg.line((cx + R, top_y), (cx + R, base_y - sh), **self.S_MAIN))

        # Верхняя крышка (эллипс)
        self.ellipse_arc(dwg, g, cx, top_y, R, self.s(p.outer_diameter * 0.15),
                         180, 360, self.S_MAIN)

        # Днище (плоское или эллипс)
        g.add(dwg.line((cx - R, base_y - sh), (cx + R, base_y - sh), **self.S_MAIN))

        # ── Внутренний контур (водяная рубашка) ──
        inner_left = cx - Ri
        inner_right = cx + Ri
        g.add(dwg.line((inner_left, top_y + self.s(10)), (inner_left, base_y - sh - self.s(10)),
                        **self.S_THIN))
        g.add(dwg.line((inner_right, top_y + self.s(10)), (inner_right, base_y - sh - self.s(10)),
                        **self.S_THIN))

        # ── Топка (нижняя часть) ──
        furnace_top = base_y - sh - Fh
        furnace_bot = base_y - sh
        g.add(dwg.rect(insert=(cx - Rf, furnace_top),
                        size=(Rf * 2, Fh), **self.S_MAIN))

        # Колосник внутри топки (если твёрдое топливо)
        if p.has_door:
            grate_y = furnace_bot - self.s(50)
            g.add(dwg.line((cx - Rf + 3, grate_y), (cx + Rf - 3, grate_y), **self.S_MAIN))
            # Решётка (штрихи)
            for i in range(int(Rf * 2 / 4)):
                gx = cx - Rf + 3 + i * 4
                g.add(dwg.line((gx, grate_y - 1), (gx, grate_y + 1), **self.S_THIN))

        # ── Жаровые трубы (вертикальные — пунктир) ──
        tube_zone_top = furnace_top - self.s(50)
        tube_zone_bot = furnace_top
        r_smoke = self.s(p.smoke_tube_diameter / 2)
        n_visible = min(p.smoke_tube_count, 8)
        spacing = (Ri * 2 - r_smoke * 4) / max(n_visible - 1, 1)
        for i in range(n_visible):
            tx = inner_left + r_smoke * 2 + i * spacing
            g.add(dwg.line((tx, tube_zone_top), (tx, tube_zone_bot), **self.S_HIDDEN))

        # ── Дверца загрузки (если есть) ──
        if p.has_door:
            dw = self.s(p.door_width) / 2
            dh = self.s(p.door_height)
            dz = base_y - sh - self.s(p.door_position_z) - dh
            g.add(dwg.rect(insert=(cx - R - 2, dz), size=(4, dh), **self.S_THICK))
            g.add(dwg.text("Дверца", insert=(cx - R - 8, dz + dh / 2),
                           text_anchor="end", font_size="3mm",
                           font_family=self.FONT, fill="black",
                           transform=f"rotate(-90,{cx - R - 8},{dz + dh / 2})"))

        # ── Осевая линия ──
        g.add(dwg.line((cx, top_y - 10), (cx, base_y + 5), **self.S_CENTER))

        # ── Патрубки ──
        inlet_y = base_y - sh - self.s(p.inlet_position_z)
        outlet_y = base_y - sh - self.s(p.outlet_position_z)
        # Вход — слева
        self.nozzle_side(dwg, g, cx - R, inlet_y,
                         p.inlet_diameter / 2, self.NOZZLE_H,
                         direction="left", label="G1 Вход")
        # Выход — справа
        self.nozzle_side(dwg, g, cx + R, outlet_y,
                         p.outlet_diameter / 2, self.NOZZLE_H,
                         direction="right", label="G2 Выход")
        # Дымоход — сверху
        if p.flue_position == "top":
            flue_y = top_y - self.s(p.outer_diameter * 0.15)
            self.nozzle_side(dwg, g, cx, flue_y,
                             p.flue_diameter / 2, self.NOZZLE_H,
                             direction="up", label="Дымоход")
        else:
            self.nozzle_side(dwg, g, cx + R, top_y + self.s(50),
                             p.flue_diameter / 2, self.NOZZLE_H,
                             direction="right", label="Дымоход")

        # ── Опоры (ножки) ──
        leg_w = self.s(p.support_width) / 2
        g.add(dwg.rect(insert=(cx - R + 5, base_y - sh),
                        size=(leg_w, sh), **self.S_MAIN))
        g.add(dwg.rect(insert=(cx + R - 5 - leg_w, base_y - sh),
                        size=(leg_w, sh), **self.S_MAIN))
        g.add(dwg.line((cx - R - 5, base_y), (cx + R + 5, base_y), **self.S_MAIN))

        # ── Размерные линии ──
        self.dim_v(dwg, g, top_y, base_y - sh, cx - R - 5,
                   p.total_height, left=True)
        self.dim_h(dwg, g, cx - R, cx + R, top_y - 10,
                   p.outer_diameter, above=True)
        # Высота топки
        self.dim_v(dwg, g, furnace_top, furnace_bot,
                   cx + R + nh + 10, p.furnace_height, left=False)

        self.view_label(dwg, g, cx, base_y + 15, "Вид спереди")
        dwg.add(g)
        return R * 2 + self.DIM_OFFSET * 2 + nh * 2 + 30, H + sh + 50

    # ─── ВИД СБОКУ ──────────────────────────────────────────────

    def draw_side_view(self, dwg, ox, oy):
        """Вид сбоку (поворот на 90°)"""
        g = dwg.g(id="view_side")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        H = self.s(p.total_height)
        sh = self.s(p.support_height)
        Rf = self.s(p.furnace_diameter / 2)
        Fh = self.s(p.furnace_height)

        cx = ox + R + 10
        base_y = oy + H + sh + 20
        top_y = base_y - sh - H

        # Корпус
        g.add(dwg.line((cx - R, top_y), (cx - R, base_y - sh), **self.S_MAIN))
        g.add(dwg.line((cx + R, top_y), (cx + R, base_y - sh), **self.S_MAIN))
        self.ellipse_arc(dwg, g, cx, top_y, R, self.s(p.outer_diameter * 0.15),
                         180, 360, self.S_MAIN)
        g.add(dwg.line((cx - R, base_y - sh), (cx + R, base_y - sh), **self.S_MAIN))

        # Топка пунктиром
        furnace_top = base_y - sh - Fh
        g.add(dwg.rect(insert=(cx - Rf, furnace_top),
                        size=(Rf * 2, Fh), **self.S_HIDDEN))

        # Осевая
        g.add(dwg.line((cx, top_y - 10), (cx, base_y + 5), **self.S_CENTER))

        # Дверца (вид сбоку — видна выступающая)
        if p.has_door:
            dh = self.s(p.door_height)
            dz = base_y - sh - self.s(p.door_position_z) - dh
            door_depth = self.s(30)
            g.add(dwg.rect(insert=(cx - R - door_depth, dz),
                           size=(door_depth, dh), **self.S_MAIN))
            # Ручка
            g.add(dwg.circle(center=(cx - R - door_depth / 2, dz + dh / 2),
                             r=2, **self.S_THIN))

        # Опоры
        leg_w = self.s(p.support_width) / 2
        g.add(dwg.rect(insert=(cx - R + 5, base_y - sh), size=(leg_w, sh), **self.S_MAIN))
        g.add(dwg.rect(insert=(cx + R - 5 - leg_w, base_y - sh), size=(leg_w, sh), **self.S_MAIN))
        g.add(dwg.line((cx - R - 5, base_y), (cx + R + 5, base_y), **self.S_MAIN))

        self.view_label(dwg, g, cx, base_y + 15, "Вид сбоку")
        dwg.add(g)
        return R * 2 + 30, H + sh + 50

    # ─── ВИД СВЕРХУ ──────────────────────────────────────────────

    def draw_top_view(self, dwg, ox, oy):
        """Вид сверху — круг с патрубками"""
        g = dwg.g(id="view_top")
        p = self.p
        R = self.s(p.outer_diameter / 2)
        Ri = self.s(p.inner_diameter / 2)

        cx = ox + R + self.DIM_OFFSET + 10
        cy = oy + R + self.DIM_OFFSET + 10

        # Корпус
        g.add(dwg.circle(center=(cx, cy), r=R, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=Ri, **self.S_THIN))

        # Осевые
        ext = 8
        g.add(dwg.line((cx - R - ext, cy), (cx + R + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - R - ext), (cx, cy + R + ext), **self.S_CENTER))

        # Дымоход сверху
        fr = self.s(p.flue_diameter / 2)
        g.add(dwg.circle(center=(cx, cy), r=fr, **self.S_MAIN))
        g.add(dwg.circle(center=(cx, cy), r=fr * 0.8, **self.S_THIN))

        # Жаровые трубы (кружки)
        Rf = self.s(p.furnace_diameter / 2)
        r_smoke = self.s(p.smoke_tube_diameter / 2)
        tube_zone_r = (Ri + Rf) / 2
        n_tubes = min(p.smoke_tube_count, 20)
        for i in range(n_tubes):
            angle = 2 * math.pi * i / n_tubes
            tx = cx + tube_zone_r * math.cos(angle)
            ty = cy + tube_zone_r * math.sin(angle)
            g.add(dwg.circle(center=(tx, ty), r=r_smoke, **self.S_THIN))

        # Размеры
        self.dim_diameter(dwg, g, cx, cy, R, p.outer_diameter, 45)

        self.view_label(dwg, g, cx, cy + R + self.DIM_OFFSET + 10, "Вид сверху")
        dwg.add(g)
        return (R + self.DIM_OFFSET) * 2 + 20, (R + self.DIM_OFFSET) * 2 + 30

    # ─── Полный чертёж ───────────────────────────────────────────

    def generate(self, views=None) -> str:
        if views is None:
            views = ["front", "side", "top"]

        R = self.s(self.p.outer_diameter / 2)
        H = self.s(self.p.total_height)
        sh = self.s(self.p.support_height)
        nh = self.s(self.NOZZLE_H)

        front_w = R * 2 + self.DIM_OFFSET * 2 + nh * 2 + 40
        front_h = H + sh + 60
        side_w = R * 2 + 40
        top_w = (R + self.DIM_OFFSET) * 2 + 30

        page_w = max(594, front_w + side_w + top_w + 80)
        page_h = max(480, front_h + top_w + 100)

        dwg = svgwrite.Drawing(size=(f"{page_w}mm", f"{page_h}mm"),
                               viewBox=f"0 0 {page_w} {page_h}")

        p = self.p
        self.draw_frame(dwg, page_w, page_h,
                        name=p.name,
                        boiler_type="Вертикальный (КВс/КОГн)",
                        dimensions=f"\u2300{p.outer_diameter:.0f} \u00d7 H{p.total_height:.0f} мм")

        ml, mt = 25, 50
        fw, fh = 0, 0
        if "front" in views:
            fw, fh = self.draw_front_view(dwg, ox=ml, oy=mt)
        if "side" in views:
            self.draw_side_view(dwg, ox=ml + fw + 15, oy=mt)
        if "top" in views:
            self.draw_top_view(dwg, ox=ml, oy=mt + fh + 10)

        return dwg.tostring()