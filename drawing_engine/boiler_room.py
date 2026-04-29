"""
Проект котельной (МТУ) — Модульная Тепловая Установка.
Генерирует:
 - План вид сверху (компоновка оборудования)
 - Разрез 1-1 (вид сбоку)
 - Экспликация оборудования (таблица)
 - Монтажная схема (трубопроводная обвязка)
Поддержка нескольких типов котлов в одном помещении.
"""

import math
import svgwrite
from drawing_engine.base import BaseDrawing
from backend.models import BoilerRoomParams


class BoilerRoomDrawing(BaseDrawing):

    # Шрифты — крупные, читаемые
    F_TITLE = "18px"
    F_SUBTITLE = "14px"
    F_LABEL = "13px"
    F_DIM = "12px"
    F_SMALL = "11px"
    F_TBL_HDR = "13px"
    F_TBL = "12px"
    F_TBL_SM = "11px"

    def __init__(self, params: BoilerRoomParams, scale: float = 0.15):
        super().__init__(scale)
        self.p = params
        self._build_boiler_groups()
        self._build_equipment_list()

    def _build_boiler_groups(self):
        """Собирает группы котлов"""
        p = self.p
        self.boiler_groups = []
        self.boiler_groups.append({
            "series": p.boiler_series, "power": p.boiler_power,
            "count": p.boiler_count, "length": p.boiler_length,
            "width": p.boiler_width, "height": p.boiler_height,
        })
        if p.boiler2_enabled and p.boiler2_count > 0:
            self.boiler_groups.append({
                "series": p.boiler2_series, "power": p.boiler2_power,
                "count": p.boiler2_count, "length": p.boiler2_length,
                "width": p.boiler2_width, "height": p.boiler2_height,
            })
        self.total_boiler_count = sum(bg["count"] for bg in self.boiler_groups)

    def _build_equipment_list(self):
        p = self.p
        self.equipment = []
        n = 1
        for bg in self.boiler_groups:
            self.equipment.append({
                "pos": n,
                "name": f"Котёл водонагревательный мощностью {bg['power']:.0f} кВт",
                "name2": f"с газовой горелкой {bg['series']}",
                "unit": "шт.", "qty": bg["count"], "note": ""
            })
            n += 1
        self.equipment.append({"pos": n, "name": f"Мембранный расширительный бак {p.expansion_tank_volume:.0f} л",
                                "name2": "", "unit": "шт.", "qty": p.expansion_tank_count, "note": ""})
        n += 1
        self.equipment.append({"pos": n, "name": "Насос зимний (циркуляционный)", "name2": "",
                                "unit": "шт.", "qty": p.pump_winter_count,
                                "note": "1 раб. 1 рез." if p.pump_winter_count >= 2 else ""})
        n += 1
        self.equipment.append({"pos": n, "name": "Насос ГВС циркуляционный", "name2": "",
                                "unit": "шт.", "qty": p.pump_gvs_count,
                                "note": "1 раб. 1 рез." if p.pump_gvs_count >= 2 else ""})
        n += 1
        self.equipment.append({"pos": n, "name": "Насос подпиточный", "name2": "",
                                "unit": "шт.", "qty": p.pump_makeup_count, "note": "1 рабочий"})
        n += 1
        if p.has_heat_exchanger:
            self.equipment.append({"pos": n, "name": f"Теплообменник {p.heat_exchanger_power:.0f} кВт",
                                    "name2": "", "unit": "шт.", "qty": self.total_boiler_count, "note": ""})
            n += 1
        self.equipment.append({"pos": n, "name": f"Грязевик Ду{p.mud_filter_dn}",
                                "name2": "", "unit": "шт.", "qty": 1, "note": ""})
        n += 1
        self.equipment.append({"pos": n, "name": f"Водомер Ду{p.water_meter_dn}",
                                "name2": "", "unit": "шт.", "qty": 1, "note": ""})
        n += 1
        self.equipment.append({"pos": n, "name": f"Труба дымовая Ø{p.chimney_diameter:.0f} H={p.chimney_height/1000:.0f}м",
                                "name2": "", "unit": "шт.", "qty": p.chimney_count, "note": ""})
        n += 1
        self.equipment.append({"pos": n, "name": "Шкаф АВ и ЭО", "name2": "",
                                "unit": "комп.", "qty": 1, "note": ""})
        n += 1
        if p.louver_count > 0:
            self.equipment.append({"pos": n, "name": f"Жалюзийная решётка {p.louver_width:.0f}x{p.louver_height:.0f}(h)",
                                    "name2": "", "unit": "шт.", "qty": p.louver_count, "note": ""})

    # ═══════════════════════════════════════════════════════════
    #  ГЕНЕРАЦИЯ
    # ═══════════════════════════════════════════════════════════

    def generate(self) -> str:
        p = self.p
        s = self.s

        oy_top = 120  # отступ сверху для заголовков и маркеров разреза

        plan_w = s(p.room_length) + 200
        plan_h = s(p.room_width) + oy_top + 80

        section_w = s(p.room_width) + 200
        section_h = s(p.roof_height) + oy_top + 80

        expl_w = 660
        row_h = 40
        expl_h = (len(self.equipment) + 2) * row_h + oy_top + 20

        schema_w = 980
        schema_h = 640

        top_h = max(plan_h, expl_h) + 30
        bot_h = max(section_h, schema_h) + 30

        page_w = max(plan_w + expl_w + 100, section_w + schema_w + 100)
        page_h = top_h + bot_h + 180  # 180 — место под штамп

        dwg = svgwrite.Drawing(size=(f"{page_w}px", f"{page_h}px"),
                               viewBox=f"0 0 {page_w} {page_h}")

        self._draw_frame_px(dwg, page_w, page_h)

        self.draw_plan_view(dwg, 80, oy_top)
        self.draw_equipment_table(dwg, plan_w + 60, oy_top, row_h=row_h)
        self.draw_section_view(dwg, 80, top_h + 60)
        self.draw_piping_schema(dwg, section_w + 80, top_h + 60)

        return dwg.tostring()

    # ═══════════════════════════════════════════════════════════
    #  ПЛАН ВИД СВЕРХУ
    # ═══════════════════════════════════════════════════════════

    def draw_plan_view(self, dwg, ox, oy):
        g = dwg.g(id="plan_view")
        p = self.p
        s = self.s

        rw = s(p.room_length)
        rh = s(p.room_width)
        wall = s(200)

        g.add(dwg.text("Компоновка оборудования", insert=(ox + rw / 2, oy - 22),
                        text_anchor="middle", font_size=self.F_TITLE,
                        font_family=self.FONT, fill="black", font_weight="bold"))
        g.add(dwg.text("План вид сверху", insert=(ox + rw / 2, oy - 8),
                        text_anchor="middle", font_size=self.F_SUBTITLE,
                        font_family=self.FONT, fill="black"))

        # Стены
        g.add(dwg.rect(insert=(ox, oy), size=(rw, rh), **self.S_THICK))
        g.add(dwg.rect(insert=(ox + wall, oy + wall),
                        size=(rw - wall * 2, rh - wall * 2), **self.S_MAIN))
        self._hatch_walls(dwg, g, ox, oy, rw, rh, wall)

        # Дверь
        door_w = s(1200)
        dx = ox + rw - wall
        dy = oy + rh / 2 - door_w / 2
        g.add(dwg.rect(insert=(dx, dy), size=(wall, door_w), fill="white", stroke="none"))
        g.add(dwg.line((dx, dy), (dx + wall, dy), **self.S_MAIN))
        g.add(dwg.line((dx, dy + door_w), (dx + wall, dy + door_w), **self.S_MAIN))

        # ── Котлы: каждая группа — своя колонка (по горизонтали) ──
        avail_h = rh - wall * 2
        boiler_gap_v = s(600)   # вертикальный зазор внутри группы
        boiler_gap_h = s(700)   # зазор между группами
        ch_offset = s(380)      # смещение дымохода от правого края котла
        cr = s(p.chimney_diameter / 2)

        # Параметры каждой группы
        col_info = []
        for gi, bg in enumerate(self.boiler_groups):
            bw_b = s(bg["length"])
            bh_b = s(bg["width"])
            n = bg["count"]
            gap_v = boiler_gap_v
            total_h_col = n * bh_b + max(n - 1, 0) * gap_v
            # Если не влезает — сжимаем зазор
            if total_h_col > avail_h * 0.95:
                gap_v = max(s(150), (avail_h * 0.9 - n * bh_b) / max(n - 1, 1))
                total_h_col = n * bh_b + max(n - 1, 0) * gap_v
            col_info.append({
                "bw": bw_b, "bh": bh_b, "n": n,
                "gap_v": gap_v, "total_h": total_h_col, "pos": gi + 1,
            })

        boiler_x = ox + wall + s(300)  # старт первой колонки
        col_x = boiler_x
        chimney_label_done = False
        en_ch = self._find_eq_num("Труба дымовая")
        max_bw = max(c["bw"] for c in col_info) if col_info else s(1800)
        rightmost_x = boiler_x  # для насосной группы

        for ci, c in enumerate(col_info):
            start_y = oy + wall + (avail_h - c["total_h"]) / 2
            cur_y = start_y

            for j in range(c["n"]):
                bcx = col_x + c["bw"] / 2
                bcy = cur_y + c["bh"] / 2

                # Котёл (круговой символ)
                self._draw_boiler_plan(dwg, g, col_x, cur_y, c["bw"], c["bh"], c["pos"])

                # Фундамент пунктиром
                fw = s(p.boiler_foundation_length)
                fh_f = s(p.boiler_foundation_width)
                g.add(dwg.rect(insert=(bcx - fw/2, bcy - fh_f/2),
                               size=(fw, fh_f), **self.S_HIDDEN))

                # Дымоход (правее котла)
                ch_x = col_x + c["bw"] + ch_offset
                ch_y = bcy
                g.add(dwg.circle(center=(ch_x, ch_y), r=cr, **self.S_MAIN))
                g.add(dwg.line((ch_x - cr - 4, ch_y), (ch_x + cr + 4, ch_y), **self.S_CENTER))
                g.add(dwg.line((ch_x, ch_y - cr - 4), (ch_x, ch_y + cr + 4), **self.S_CENTER))
                if not chimney_label_done:
                    g.add(dwg.text(f"Ø{p.chimney_diameter:.0f}",
                                   insert=(ch_x, ch_y - cr - 7),
                                   text_anchor="middle", font_size=self.F_DIM,
                                   font_family=self.FONT, fill="black"))
                    if en_ch:
                        self._pos_label(dwg, g, ch_x + cr + 20, ch_y, en_ch)
                    chimney_label_done = True

                rightmost_x = max(rightmost_x, ch_x + cr)
                cur_y += c["bh"] + c["gap_v"]

            # Подпись фундамента (один раз, первая группа)
            if ci == 0:
                fy_lbl = oy + wall + avail_h + 14
                g.add(dwg.text("Фундамент под котёл",
                               insert=(col_x + c["bw"] / 2, fy_lbl),
                               text_anchor="middle", font_size=self.F_SMALL,
                               font_family=self.FONT, fill="black"))
                g.add(dwg.text(
                    f"{p.boiler_foundation_length:.0f}×{p.boiler_foundation_width:.0f}×{p.boiler_foundation_height:.0f}(h)",
                    insert=(col_x + c["bw"] / 2, fy_lbl + 14),
                    text_anchor="middle", font_size=self.F_SMALL,
                    font_family=self.FONT, fill="black"))

            col_x += c["bw"] + boiler_gap_h

        # Шкаф АВ и ЭО (правый верхний угол)
        cw = s(600)
        ch = s(400)
        cx_s = ox + rw - wall - cw - s(200)
        cy_s = oy + wall + s(100)
        g.add(dwg.rect(insert=(cx_s, cy_s), size=(cw, ch), **self.S_MAIN))
        g.add(dwg.text("Шкаф АВ и ЭО", insert=(cx_s + cw / 2, cy_s + ch / 2 + 3),
                        text_anchor="middle", font_size=self.F_SMALL,
                        font_family=self.FONT, fill="black"))
        en = self._find_eq_num("Шкаф")
        if en:
            self._pos_label(dwg, g, cx_s + cw + 15, cy_s + ch / 2, en)

        # Насосная группа (правее всех котлов и дымоходов)
        pump_x = rightmost_x + s(400)
        pump_y = oy + wall + s(300)
        self._draw_pump_group(dwg, g, pump_x, pump_y)

        # Газ
        gas_x = ox + s(1500)
        g.add(dwg.line((gas_x, oy - 12), (gas_x, oy + wall + 5), **self.S_MAIN))
        g.add(dwg.text("Газ", insert=(gas_x + 10, oy - 4),
                        font_size=self.F_LABEL, font_family=self.FONT, fill="black",
                        font_style="italic"))

        # Выходы T1-T4 сверху
        for i, lbl in enumerate(["T1", "B1", "T2", "T4", "T3"]):
            px = ox + rw - s(500) + i * s(250)
            g.add(dwg.line((px, oy), (px, oy - 22), **self.S_MAIN))
            g.add(dwg.polygon([(px, oy - 22), (px - 3, oy - 14), (px + 3, oy - 14)], fill="black"))
            g.add(dwg.text(lbl, insert=(px, oy - 27), text_anchor="middle",
                           font_size=self.F_DIM, font_family=self.FONT, fill="black"))

        # Жалюзийные решётки
        if p.louver_count > 0:
            lw = s(p.louver_width)
            for i in range(p.louver_count):
                ly = oy + rh * 0.3 + i * (lw + s(300))
                lx = ox + rw - wall / 2
                g.add(dwg.rect(insert=(lx - 4, ly), size=(8, lw),
                               fill="none", stroke="black", stroke_width="0.5"))
                en = self._find_eq_num("Жалюзийная")
                if en:
                    self._pos_label(dwg, g, lx + 20, ly + lw / 2, en)

        # Размеры
        self.dim_h(dwg, g, ox, ox + rw, oy + rh + 18, p.room_length, above=False)
        self.dim_v(dwg, g, oy, oy + rh, ox - 18, p.room_width, left=True)

        # Линия разреза А-Б
        cut_x = boiler_x + col_info[0]["bw"] / 2 if col_info else boiler_x + max_bw / 2
        for label, yy in [("А", oy - 35), ("Б", oy + rh + 35)]:
            g.add(dwg.circle(center=(cut_x, yy), r=8,
                             stroke="black", stroke_width="0.5", fill="white"))
            g.add(dwg.text(label, insert=(cut_x, yy + 3), text_anchor="middle",
                           font_size=self.F_LABEL, font_family=self.FONT,
                           fill="black", font_weight="bold"))
        g.add(dwg.line((cut_x, oy - 27), (cut_x, oy - 18), stroke="black", stroke_width="0.7"))
        g.add(dwg.line((cut_x, oy - 18), (cut_x, oy + rh + 18), **self.S_CENTER))
        g.add(dwg.line((cut_x, oy + rh + 18), (cut_x, oy + rh + 27), stroke="black", stroke_width="0.7"))

        dwg.add(g)

    def _draw_boiler_plan(self, dwg, g, x, y, w, h, pos_num):
        """Котёл вид сверху — круг (вертикальный цилиндр по ГОСТ)"""
        cx = x + w / 2
        cy = y + h / 2
        r = min(w, h) / 2 * 0.88

        # Внешний корпус (окружность)
        g.add(dwg.circle(center=(cx, cy), r=r, stroke="black", stroke_width="1.0", fill="none"))
        # Внутренний контур (жаровая часть)
        g.add(dwg.circle(center=(cx, cy), r=r * 0.55, stroke="black", stroke_width="0.4", fill="none"))

        # Осевые линии (через центр с выносом за круг)
        ext = 18
        g.add(dwg.line((cx - r - ext, cy), (cx + r + ext, cy), **self.S_CENTER))
        g.add(dwg.line((cx, cy - r - ext), (cx, cy + r + ext), **self.S_CENTER))

        # Опоры — 4 лапы (крест в кружке по ГОСТ)
        fr = 6
        for angle_deg in [45, 135, 225, 315]:
            rad = math.radians(angle_deg)
            fx = cx + r * 0.72 * math.cos(rad)
            fy = cy + r * 0.72 * math.sin(rad)
            g.add(dwg.circle(center=(fx, fy), r=fr, stroke="black", stroke_width="0.4", fill="white"))
            g.add(dwg.line((fx - fr * 0.7, fy), (fx + fr * 0.7, fy), **self.S_THIN))
            g.add(dwg.line((fx, fy - fr * 0.7), (fx, fy + fr * 0.7), **self.S_THIN))

        self._pos_label(dwg, g, cx + r + 32, cy, pos_num)

    def _draw_pump_group(self, dwg, g, x, y):
        p = self.p
        s = self.s
        pw, ph, gap = s(220), s(180), s(200)
        row = 0
        for label, count in [("Зимн.", p.pump_winter_count), ("ГВС", p.pump_gvs_count),
                              ("Подп.", p.pump_makeup_count)]:
            for i in range(count):
                cx = x + (i % 3) * (pw + gap) + pw / 2
                cy = y + row * (ph + gap) + ph / 2
                r = pw * 0.38
                g.add(dwg.circle(center=(cx, cy), r=r, stroke="black", stroke_width="0.4", fill="none"))
                tr = r * 0.5
                g.add(dwg.polygon([(cx - tr * 0.5, cy - tr), (cx + tr, cy), (cx - tr * 0.5, cy + tr)],
                                   fill="none", stroke="black", stroke_width="0.3"))
            row += 1
        # РБ
        tr = s(200)
        tx = x + (pw + gap) * 2 + pw
        g.add(dwg.circle(center=(tx, y + tr), r=tr, **self.S_MAIN))
        g.add(dwg.text("РБ", insert=(tx, y + tr + 3), text_anchor="middle",
                        font_size=self.F_LABEL, font_family=self.FONT, fill="black"))
        en = self._find_eq_num("расширительный")
        if en:
            self._pos_label(dwg, g, tx + tr + 15, y + tr, en)

    def _hatch_walls(self, dwg, g, ox, oy, rw, rh, wall):
        self.hatch_rect(dwg, g, ox, oy, rw, wall)
        self.hatch_rect(dwg, g, ox, oy + rh - wall, rw, wall)
        self.hatch_rect(dwg, g, ox, oy + wall, wall, rh - wall * 2)
        self.hatch_rect(dwg, g, ox + rw - wall, oy + wall, wall, rh - wall * 2)

    def _draw_frame_px(self, dwg, w, h):
        """Рамка и штамп ГОСТ 2.104 для px-координатной системы"""
        g = dwg.g(id="frame")
        # Внешняя рамка
        g.add(dwg.rect(insert=(0, 0), size=(w, h),
                        stroke="black", stroke_width="0.5", fill="white"))
        # Внутренняя рамка (поле чертежа)
        g.add(dwg.rect(insert=(20, 5), size=(w - 25, h - 10),
                        stroke="black", stroke_width="1.5", fill="none"))

        # ── Левая вертикальная полоса штампа (ГОСТ 2.104) ────────
        lx = 20   # левый край (совпадает с внутренней рамкой)
        lw = 55   # ширина полосы
        lh = 170  # высота области подписей
        ly = h - 5 - lh  # верхний край области подписей

        # Вертикальная линия, отделяющая полосу от поля чертежа
        g.add(dwg.line((lx + lw, 5), (lx + lw, h - 5),
                        stroke="black", stroke_width="0.8"))

        rows = ["Разраб.", "Провер.", "Нач.отд.", "Н.контр.", "Утв."]
        rh_s = lh // len(rows)
        col1 = 22  # ширина колонки «имя»
        col2 = 18  # ширина колонки «подпись»
        for i, label in enumerate(rows):
            ry = ly + i * rh_s
            ry2 = ry + rh_s
            g.add(dwg.line((lx, ry2), (lx + lw, ry2),
                           stroke="black", stroke_width="0.5"))
            g.add(dwg.line((lx + col1, ry), (lx + col1, ry2),
                           stroke="black", stroke_width="0.3"))
            g.add(dwg.line((lx + col1 + col2, ry), (lx + col1 + col2, ry2),
                           stroke="black", stroke_width="0.3"))
            mid_y = ry + rh_s / 2
            cx_lbl = lx + col1 / 2
            g.add(dwg.text(label, insert=(cx_lbl, mid_y + 4),
                           text_anchor="middle", font_size="10px",
                           font_family=self.FONT, fill="black",
                           transform=f"rotate(-90,{cx_lbl},{mid_y})"))

        # ── Основная надпись (штамп) внизу справа ────────────────
        sw, sh = 500, 170
        sx = w - 5 - sw
        sy = h - 5 - sh

        g.add(dwg.rect(insert=(sx, sy), size=(sw, sh),
                        stroke="black", stroke_width="1.5", fill="white"))

        # Горизонтальные линии
        for dy in [42, 84, 115, 142]:
            g.add(dwg.line((sx, sy + dy), (sx + sw, sy + dy),
                           stroke="black", stroke_width="0.7"))
        # Вертикальные разделители
        g.add(dwg.line((sx + 160, sy), (sx + 160, sy + sh),
                        stroke="black", stroke_width="0.7"))
        g.add(dwg.line((sx + 295, sy), (sx + 295, sy + 42),
                        stroke="black", stroke_width="0.5"))

        # Подписи в левой части штампа
        sig_rows = ["Разработал", "Проверил", "Нач. отдела", "Н. контроль", "Утвердил"]
        for i, lbl in enumerate(sig_rows):
            ry = sy + i * (sh // len(sig_rows))
            g.add(dwg.text(lbl, insert=(sx + 6, ry + 16),
                           font_size="11px", font_family=self.FONT, fill="black"))

        # Основные тексты в правой части
        p = self.p
        tc = sx + 330
        g.add(dwg.text(p.name, insert=(tc, sy + 30),
                        text_anchor="middle", font_size="22px",
                        font_family=self.FONT, fill="black", font_weight="bold"))
        g.add(dwg.text("Компоновка оборудования. ЭП",
                        insert=(tc, sy + 65),
                        text_anchor="middle", font_size="13px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text(f"МТУ-{p.power_kw:.0f}",
                        insert=(tc, sy + 100),
                        text_anchor="middle", font_size="16px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text(f"Масштаб 1:{int(1/self.scale)}", insert=(sx + 220, sy + 25),
                        text_anchor="middle", font_size="11px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text("Формат А1", insert=(sx + 220, sy + 55),
                        text_anchor="middle", font_size="11px",
                        font_family=self.FONT, fill="black"))
        g.add(dwg.text("Лист 1", insert=(sx + 220, sy + 80),
                        text_anchor="middle", font_size="11px",
                        font_family=self.FONT, fill="black"))

        dwg.add(g)

    def _pos_label(self, dwg, g, x, y, num):
        g.add(dwg.circle(center=(x, y), r=14, stroke="black", stroke_width="0.8", fill="white"))
        g.add(dwg.text(str(num), insert=(x, y + 5), text_anchor="middle",
                        font_size="13px", font_family=self.FONT, fill="black"))

    def _find_eq_num(self, keyword):
        for eq in self.equipment:
            if keyword.lower() in eq["name"].lower():
                return eq["pos"]
        return None

    # ═══════════════════════════════════════════════════════════
    #  РАЗРЕЗ 1-1
    # ═══════════════════════════════════════════════════════════

    def draw_section_view(self, dwg, ox, oy):
        """Разрез 1-1 — как в референсах IMG_0081"""
        g = dwg.g(id="section_view")
        p = self.p
        s = self.s

        rw = s(p.room_width)
        h_wall = s(p.room_height)
        h_roof = s(p.roof_height)
        wall = s(200)
        eaves_y = oy + h_roof - h_wall  # карниз
        floor_y = oy + h_roof           # уровень пола
        roof_y = oy                     # конёк крыши
        mid_x = ox + rw / 2

        # ── Заголовок ──
        g.add(dwg.text("Компоновка оборудования", insert=(mid_x, oy - 25),
                        text_anchor="middle", font_size=self.F_TITLE,
                        font_family=self.FONT, fill="black", font_weight="bold"))
        g.add(dwg.text("Разрез 1-1", insert=(mid_x, oy - 8),
                        text_anchor="middle", font_size=self.F_SUBTITLE,
                        font_family=self.FONT, fill="black"))

        # ── Пол + грунт ──
        g.add(dwg.line((ox - 40, floor_y), (ox + rw + 40, floor_y), **self.S_THICK))
        self.hatch_rect(dwg, g, ox - 30, floor_y, rw + 60, 14)

        # ── Стены (двойные линии с штриховкой) ──
        g.add(dwg.line((ox, floor_y), (ox, eaves_y), **self.S_THICK))
        g.add(dwg.line((ox + rw, floor_y), (ox + rw, eaves_y), **self.S_THICK))
        g.add(dwg.line((ox + wall, floor_y), (ox + wall, eaves_y), **self.S_MAIN))
        g.add(dwg.line((ox + rw - wall, floor_y), (ox + rw - wall, eaves_y), **self.S_MAIN))
        self.hatch_rect(dwg, g, ox, eaves_y, wall, h_wall)
        self.hatch_rect(dwg, g, ox + rw - wall, eaves_y, wall, h_wall)

        # ── Крыша (двускатная) ──
        overhang = 20
        g.add(dwg.polyline(
            [(ox - overhang, eaves_y), (mid_x, roof_y), (ox + rw + overhang, eaves_y)],
            **self.S_THICK))
        # Карнизная линия
        g.add(dwg.line((ox - overhang, eaves_y), (ox + rw + overhang, eaves_y), **self.S_MAIN))

        # ── Котлы в разрезе (несколько, рядом) ──
        bg = self.boiler_groups[0]
        bw_single = s(bg["width"])
        bh_boiler = s(bg["height"])
        fund_h = s(p.boiler_foundation_height)
        fund_w = s(p.boiler_foundation_width)

        n_boilers = min(bg["count"], 3)  # не более 3 в разрезе
        spacing = (rw - wall * 2) / (n_boilers + 1)
        boiler_tops = []

        for i in range(n_boilers):
            bcx = ox + wall + spacing * (i + 1)
            by_top = floor_y - fund_h - bh_boiler
            bx = bcx - bw_single / 2
            boiler_tops.append((bcx, by_top, bw_single, bh_boiler))

            # Фундамент
            fx = bcx - fund_w / 2
            g.add(dwg.rect(insert=(fx, floor_y - fund_h),
                           size=(fund_w, fund_h), **self.S_MAIN))
            self.hatch_rect(dwg, g, fx, floor_y - fund_h, fund_w, fund_h)

            # Котёл (прямоугольник с осевой)
            g.add(dwg.rect(insert=(bx, by_top), size=(bw_single, bh_boiler),
                           stroke="black", stroke_width="0.8", fill="none"))
            g.add(dwg.line((bcx, by_top - 8), (bcx, floor_y + 5), **self.S_CENTER))
            if i == 0:
                self._pos_label(dwg, g, bx - 22, by_top + bh_boiler / 2, 1)

        # ── Дымоходы (через крышу, с зонтом) ──
        cr = s(p.chimney_diameter / 2)
        ch_above = s(600)  # возвышение над коньком
        chimney_idx = self._find_eq_num("Труба дымовая")

        drawn_chimneys = 0
        for i, (bcx, by_top, bw_s, bh_b) in enumerate(boiler_tops):
            if drawn_chimneys >= p.chimney_count:
                break
            ch_bottom = by_top  # выходит из верха котла
            ch_top_y = roof_y - ch_above

            # Линии дымохода (сквозь крышу)
            g.add(dwg.line((bcx - cr, ch_bottom), (bcx - cr, ch_top_y), **self.S_MAIN))
            g.add(dwg.line((bcx + cr, ch_bottom), (bcx + cr, ch_top_y), **self.S_MAIN))

            # Зонт (шапка дымохода)
            zw = cr * 2.2
            zh = cr * 0.8
            g.add(dwg.polyline(
                [(bcx - zw, ch_top_y + zh), (bcx, ch_top_y), (bcx + zw, ch_top_y + zh)],
                **self.S_MAIN))
            g.add(dwg.line((bcx - cr, ch_top_y + zh), (bcx + cr, ch_top_y + zh), **self.S_MAIN))

            # Подпись диаметра
            if i == 0:
                g.add(dwg.text(f"Ø{p.chimney_diameter:.0f}",
                               insert=(bcx + cr + 8, (ch_bottom + ch_top_y) / 2),
                               font_size=self.F_DIM, font_family=self.FONT, fill="black"))
                if chimney_idx:
                    self._pos_label(dwg, g, bcx + cr + 40,
                                    (ch_bottom + ch_top_y) / 2, chimney_idx)
            drawn_chimneys += 1

        # ── Отметки уровней (стиль ГОСТ) ──
        def _level_mark(yy, txt, side="right"):
            arrow_x = ox + rw + 30 if side == "right" else ox - 30
            dir_x = 1 if side == "right" else -1
            g.add(dwg.line((ox + rw if side == "right" else ox, yy),
                           (arrow_x, yy), **self.S_DIM))
            g.add(dwg.polygon(
                [(arrow_x, yy), (arrow_x - dir_x * 8, yy - 3), (arrow_x - dir_x * 8, yy + 3)],
                fill="black"))
            g.add(dwg.text(txt, insert=(arrow_x + dir_x * 5, yy - 4),
                           text_anchor="start" if side == "right" else "end",
                           font_size=self.F_DIM, font_family=self.FONT, fill="black"))

        _level_mark(floor_y, "0.000", "left")
        _level_mark(eaves_y, f"+{p.room_height/1000:.3f}", "right")
        _level_mark(roof_y, f"+{p.roof_height/1000:.3f}", "right")

        # ── Размеры ──
        self.dim_h(dwg, g, ox + wall, ox + rw - wall,
                   floor_y + 25, p.room_width - 400, above=False)
        self.dim_h(dwg, g, ox, ox + rw,
                   floor_y + 48, p.room_width, above=False)

        # Маркеры А и Б разреза
        for lbl, xx in [("А", ox - 30), ("Б", ox + rw + 30)]:
            g.add(dwg.circle(center=(xx, floor_y + 30), r=12,
                             stroke="black", stroke_width="0.7", fill="white"))
            g.add(dwg.text(lbl, insert=(xx, floor_y + 35), text_anchor="middle",
                           font_size=self.F_LABEL, font_family=self.FONT,
                           fill="black", font_weight="bold"))

        dwg.add(g)

    # ═══════════════════════════════════════════════════════════
    #  ЭКСПЛИКАЦИЯ
    # ═══════════════════════════════════════════════════════════

    def draw_equipment_table(self, dwg, ox, oy, row_h=40):
        g = dwg.g(id="equipment_table")

        col_w = [50, 360, 60, 55, 135]
        total_w = sum(col_w)

        g.add(dwg.text("Экспликация оборудования",
                        insert=(ox + total_w / 2, oy - 10),
                        text_anchor="middle", font_size=self.F_TITLE,
                        font_family=self.FONT, fill="black", font_weight="bold"))

        hdr_y = oy + 8
        headers = ["Поз.", "Наименование", "Ед.\nизм.", "Кол-\nво", "Примечание"]
        cx = ox
        for hdr, w in zip(headers, col_w):
            g.add(dwg.rect(insert=(cx, hdr_y), size=(w, row_h),
                           stroke="black", stroke_width="0.8", fill="#e8e8e8"))
            parts = hdr.split("\n")
            if len(parts) == 1:
                g.add(dwg.text(parts[0], insert=(cx + w / 2, hdr_y + row_h / 2 + 5),
                               text_anchor="middle", font_size=self.F_TBL_HDR,
                               font_family=self.FONT, fill="black", font_weight="bold"))
            else:
                g.add(dwg.text(parts[0], insert=(cx + w / 2, hdr_y + row_h / 2 - 3),
                               text_anchor="middle", font_size=self.F_TBL_HDR,
                               font_family=self.FONT, fill="black", font_weight="bold"))
                g.add(dwg.text(parts[1], insert=(cx + w / 2, hdr_y + row_h / 2 + 12),
                               text_anchor="middle", font_size=self.F_TBL_HDR,
                               font_family=self.FONT, fill="black", font_weight="bold"))
            cx += w

        for idx, eq in enumerate(self.equipment):
            ry = hdr_y + row_h + idx * row_h
            cx = ox
            fill = "#f9f9f9" if idx % 2 == 0 else "white"
            vals = [str(eq["pos"]), eq["name"], eq["unit"], str(eq["qty"]), eq.get("note", "")]
            aligns = ["middle", "start", "middle", "middle", "middle"]

            for ci, (val, w) in enumerate(zip(vals, col_w)):
                g.add(dwg.rect(insert=(cx, ry), size=(w, row_h),
                               stroke="black", stroke_width="0.5", fill=fill))
                tx = cx + 6 if aligns[ci] == "start" else cx + w / 2
                g.add(dwg.text(val, insert=(tx, ry + row_h / 2 + 5),
                               text_anchor=aligns[ci], font_size=self.F_TBL,
                               font_family=self.FONT, fill="black"))
                if ci == 1 and eq.get("name2"):
                    g.add(dwg.text(eq["name2"], insert=(tx, ry + row_h - 6),
                                   text_anchor="start", font_size=self.F_TBL_SM,
                                   font_family=self.FONT, fill="black"))
                cx += w

        dwg.add(g)

    # ═══════════════════════════════════════════════════════════
    #  МОНТАЖНАЯ СХЕМА
    # ═══════════════════════════════════════════════════════════

    def draw_piping_schema(self, dwg, ox, oy):
        """Монтажная схема — трубопроводная обвязка (ГОСТ-стиль)"""
        g = dwg.g(id="piping_schema")
        p = self.p
        F = self.FONT

        # ── Локальные функции-символы ─────────────────────────
        def pipe(x1, y1, x2, y2):
            g.add(dwg.line((x1,y1),(x2,y2), stroke="black", stroke_width="1.5", fill="none"))

        def pipe_t(x1, y1, x2, y2):
            g.add(dwg.line((x1,y1),(x2,y2), stroke="black", stroke_width="0.6", fill="none"))

        def valve_h(x, y, sz=9):
            """Задвижка горизонтальная"""
            g.add(dwg.polygon([(x-sz,y-sz*.55),(x,y),(x-sz,y+sz*.55)], fill="black"))
            g.add(dwg.polygon([(x+sz,y-sz*.55),(x,y),(x+sz,y+sz*.55)], fill="black"))

        def valve_v(x, y, sz=9):
            """Задвижка вертикальная"""
            g.add(dwg.polygon([(x-sz*.55,y-sz),(x,y),(x+sz*.55,y-sz)], fill="black"))
            g.add(dwg.polygon([(x-sz*.55,y+sz),(x,y),(x+sz*.55,y+sz)], fill="black"))

        def check_h(x, y, sz=8):
            """Обратный клапан (горизонт.)"""
            g.add(dwg.line((x,y-sz),(x,y+sz), stroke="black", stroke_width="0.8"))
            g.add(dwg.polygon([(x-sz*.9,y-sz*.5),(x,y),(x-sz*.9,y+sz*.5)], fill="black"))

        def pump(x, y, r=13):
            """Насос"""
            g.add(dwg.circle(center=(x,y), r=r, stroke="black", stroke_width="0.8", fill="white"))
            tr = r*.55
            g.add(dwg.polygon([(x-tr*.5,y-tr),(x+tr,y),(x-tr*.5,y+tr)], fill="black"))

        def mano(x, y, r=8):
            """Манометр"""
            g.add(dwg.circle(center=(x,y), r=r, stroke="black", stroke_width="0.6", fill="white"))
            g.add(dwg.text("P", insert=(x,y+3.5), text_anchor="middle",
                            font_size="11px", font_family=F, fill="black"))

        def dot(x, y):
            g.add(dwg.circle(center=(x,y), r=4.5, fill="black"))

        def fa(x, y, d="right"):
            """Стрелка направления потока"""
            sz = 6
            pts = {"right":[(x,y),(x-sz*1.5,y-sz*.5),(x-sz*1.5,y+sz*.5)],
                   "left": [(x,y),(x+sz*1.5,y-sz*.5),(x+sz*1.5,y+sz*.5)],
                   "down": [(x,y),(x-sz*.5,y-sz*1.5),(x+sz*.5,y-sz*1.5)],
                   "up":   [(x,y),(x-sz*.5,y+sz*1.5),(x+sz*.5,y+sz*1.5)]}
            g.add(dwg.polygon(pts[d], fill="black"))

        def lbl(x, y, txt, above=True):
            g.add(dwg.text(txt, insert=(x, y+(-9 if above else 15)),
                            text_anchor="middle", font_size=self.F_DIM, font_family=F, fill="black"))

        def lbl_v(x, y, txt, left=True):
            g.add(dwg.text(txt, insert=(x+(-6 if left else 6), y),
                            text_anchor="end" if left else "start",
                            font_size=self.F_DIM, font_family=F, fill="black"))

        def out_lbl(x, y, txt, d="right", clr="black"):
            if d == "right":
                g.add(dwg.polygon([(x,y),(x-10,y-5),(x-10,y+5)], fill=clr))
                g.add(dwg.text(txt, insert=(x+7,y+5), font_size=self.F_LABEL,
                                font_family=F, fill=clr, font_weight="bold"))
            else:
                g.add(dwg.polygon([(x,y),(x+10,y-5),(x+10,y+5)], fill=clr))
                g.add(dwg.text(txt, insert=(x-7,y+5), text_anchor="end",
                                font_size=self.F_LABEL, font_family=F, fill=clr, font_weight="bold"))

        def he_box(x, y, w, h, pos=None):
            """Теплообменник (прямоугольник + диагонали)"""
            g.add(dwg.rect(insert=(x,y), size=(w,h), stroke="black", stroke_width="1.0", fill="white"))
            g.add(dwg.line((x,y),(x+w,y+h), stroke="black", stroke_width="0.5"))
            g.add(dwg.line((x,y+h),(x+w,y), stroke="black", stroke_width="0.5"))
            g.add(dwg.text("ТО", insert=(x+w/2,y+h/2+4), text_anchor="middle",
                            font_size=self.F_LABEL, font_family=F, fill="black"))
            if pos:
                self._pos_label(dwg, g, x+w+20, y+h/2, pos)

        def du(x, y, n):
            g.add(dwg.text(f"Ду{n}", insert=(x,y), text_anchor="middle",
                            font_size=self.F_DIM, font_family=F, fill="black"))

        # ── ЗАГОЛОВОК ────────────────────────────────────────
        g.add(dwg.text("Монтажная схема", insert=(ox+440, oy-14),
                        text_anchor="middle", font_size=self.F_TITLE,
                        font_family=F, fill="black", font_weight="bold"))

        # ── КООРДИНАТНАЯ СЕТКА ───────────────────────────────
        # Y-уровни
        y_rb  = oy + 40   # РБ
        y1    = oy + 90   # Подача T1
        y2    = oy + 145  # Обратка T2
        y_bt  = oy + 82   # Верх котла
        y_bb  = oy + 258  # Низ котла
        y_bc  = oy + 170  # Центр котла
        y_p   = oy + 310  # Насосы отопления
        y_hec = oy + 385  # Центр ТО
        y_t3  = oy + 445  # T3 ГВС подача
        y_t4  = oy + 495  # T4 ГВС обратка
        y_mup = oy + 560  # B1 подпитка

        # X-позиции
        x_lft  = ox + 50
        x_vm   = ox + 110   # водомер
        x_lc   = ox + 190   # левый вертикальный ствол
        x_gr   = ox + 250   # грязевик
        x_pmp  = ox + 320   # начало насосов отопления
        x_b1l  = ox + 430   # котёл 1 левый
        x_b1r  = ox + 570   # котёл 1 правый
        x_b1c  = ox + 500   # котёл 1 центр
        x_b2l  = ox + 600   # котёл 2 левый
        x_b2r  = ox + 740   # котёл 2 правый
        x_b2c  = ox + 670   # котёл 2 центр
        x_rb   = ox + 840   # РБ
        x_out  = ox + 910   # выводы

        bw = x_b1r - x_b1l    # ширина котла 140
        bh = y_bb - y_bt      # высота котла 176

        # ── РБ — РАСШИРИТЕЛЬНЫЙ БАК ──────────────────────────
        rb_r = 24
        g.add(dwg.circle(center=(x_rb, y_rb), r=rb_r,
                          stroke="black", stroke_width="1.2", fill="white"))
        g.add(dwg.text("РБ", insert=(x_rb, y_rb+5), text_anchor="middle",
                        font_size=self.F_SMALL, font_family=F, fill="black", font_weight="bold"))
        pipe(x_rb, y_rb+rb_r, x_rb, y1)
        dot(x_rb, y1)
        # Предохранительный клапан
        sv_x = x_rb + 55
        pipe(sv_x, y1, sv_x, y_rb - 5)
        g.add(dwg.polygon([(sv_x,y_rb-5),(sv_x-7,y_rb+9),(sv_x+7,y_rb+9)], fill="black"))
        g.add(dwg.text("Ду15", insert=(sv_x+9, y_rb), text_anchor="start",
                        font_size=self.F_DIM, font_family=F, fill="black"))
        en_rb = self._find_eq_num("расширительный")
        if en_rb:
            self._pos_label(dwg, g, x_rb, y_rb - rb_r - 18, en_rb)

        # ── ГЛАВНЫЕ КОЛЛЕКТОРЫ: ПОДАЧА T1 и ОБРАТКА T2 ──────
        pipe(x_lc, y1, x_out, y1)
        pipe(x_lc, y2, x_out, y2)
        lbl((x_b1c+x_rb)/2, y1, f"Ø{p.pipe_main_dn}", above=True)
        lbl((x_b1c+x_rb)/2, y2, f"Ø{p.pipe_main_dn}", above=False)
        fa(x_out-40, y1, "right")
        fa(x_lc+40, y2, "left")
        out_lbl(x_out, y1, "T1", "right", "red")
        out_lbl(x_out, y2, "T2", "right", "blue")

        # ── КОТЁЛ 1 ──────────────────────────────────────────
        bg0 = self.boiler_groups[0]
        g.add(dwg.rect(insert=(x_b1l,y_bt), size=(bw,bh),
                        stroke="black", stroke_width="1.2", fill="white"))
        g.add(dwg.text(bg0["series"], insert=(x_b1c, y_bc-10),
                        text_anchor="middle", font_size=self.F_SMALL, font_family=F, fill="black"))
        g.add(dwg.text(f"{bg0['power']:.0f}кВт", insert=(x_b1c, y_bc+10),
                        text_anchor="middle", font_size=self.F_SMALL, font_family=F, fill="black"))
        self._pos_label(dwg, g, x_b1l-22, y_bc, 1)
        # Ветки котла 1
        b1s, b1r = x_b1c-18, x_b1c+18
        pipe(b1s, y_bt, b1s, y1); pipe(b1r, y_bt, b1r, y2)
        valve_v(b1s, y_bt+30); valve_v(b1r, y_bt+30)
        pipe_t(x_b1c, y_bt, x_b1c, y_bt-16); mano(x_b1c, y_bt-24)
        lbl_v(b1s, (y_bt+y1)//2, f"Ø{p.pipe_branch_dn}", left=True)
        dot(b1s, y1); dot(b1r, y2)

        # ── КОТЁЛ 2 ──────────────────────────────────────────
        bg1 = self.boiler_groups[1] if len(self.boiler_groups)>1 else self.boiler_groups[0]
        pos2 = 2 if len(self.boiler_groups)>1 else 1
        g.add(dwg.rect(insert=(x_b2l,y_bt), size=(bw,bh),
                        stroke="black", stroke_width="1.2", fill="white"))
        g.add(dwg.text(bg1["series"], insert=(x_b2c, y_bc-10),
                        text_anchor="middle", font_size=self.F_SMALL, font_family=F, fill="black"))
        g.add(dwg.text(f"{bg1['power']:.0f}кВт", insert=(x_b2c, y_bc+10),
                        text_anchor="middle", font_size=self.F_SMALL, font_family=F, fill="black"))
        self._pos_label(dwg, g, x_b2l-22, y_bc, pos2)
        b2s, b2r = x_b2c-18, x_b2c+18
        pipe(b2s, y_bt, b2s, y1); pipe(b2r, y_bt, b2r, y2)
        valve_v(b2s, y_bt+30); valve_v(b2r, y_bt+30)
        pipe_t(x_b2c, y_bt, x_b2c, y_bt-16); mano(x_b2c, y_bt-24)
        lbl_v(b2s, (y_bt+y1)//2, f"Ø{p.pipe_branch_dn}", left=True)
        dot(b2s, y1); dot(b2r, y2)

        # ── НАСОСЫ ОТОПЛЕНИЯ (на обратке) ───────────────────
        # Горизонтальный участок обратки к насосам
        pipe(x_lc, y2, x_b1l, y2)
        # Вертикальный ствол слева
        pipe(x_lc, y1, x_lc, y_mup)
        dot(x_lc, y2)

        # Грязевик
        g.add(dwg.rect(insert=(x_gr-14,y2-18), size=(28,36),
                       stroke="black", stroke_width="0.8", fill="white"))
        g.add(dwg.line((x_gr-14,y2-18),(x_gr+14,y2+18), stroke="black", stroke_width="0.5"))
        g.add(dwg.line((x_gr-14,y2+18),(x_gr+14,y2-18), stroke="black", stroke_width="0.5"))
        en_gr = self._find_eq_num("Грязевик")
        if en_gr:
            self._pos_label(dwg, g, x_gr+30, y2, en_gr)

        # Насосы
        pump_gap = 55
        for i in range(p.pump_winter_count):
            px = x_pmp + i*pump_gap
            pump(px, y_p)
            mano(px, y_p-30); pipe_t(px, y_p-13, px, y_p-22)
            du(px, y_p+30, p.mud_filter_dn)

        # Горизонтальный участок насосов
        pipe_r = x_pmp + p.pump_winter_count*pump_gap + 25
        pipe(x_lc, y_p, pipe_r, y_p)
        pipe(x_lc, y2, x_lc, y_p); dot(x_lc, y_p)
        pipe(pipe_r, y_p, pipe_r, y2); dot(pipe_r, y2)
        lbl(x_lc+60, y_p, f"Ø{p.pipe_main_dn}", above=True)
        fa(x_lc+80, y_p, "right")
        check_h(pipe_r-30, y_p)

        # ── ГВС (ТЕПЛООБМЕННИК) ───────────────────────────────
        if p.has_heat_exchanger:
            he_w, he_h = 75, 65
            he_x = x_lc - he_w - 40
            he_y = y_hec - he_h//2
            he_box(he_x, he_y, he_w, he_h, self._find_eq_num("Теплообменник"))

            # Первичный контур (из вертикального ствола к ТО)
            pipe(x_lc, y_hec-16, he_x, y_hec-16)
            pipe(x_lc, y_hec+16, he_x, y_hec+16)
            valve_h(x_lc-30, y_hec-16); valve_h(x_lc-30, y_hec+16)
            fa(x_lc-55, y_hec-16, "left"); fa(x_lc-55, y_hec+16, "right")
            dot(x_lc, y_hec-16); dot(x_lc, y_hec+16)
            lbl((he_x+x_lc)//2, y_hec-16, f"Ø{p.pipe_branch_dn}", above=True)

            # ГВС насосы (левее ТО, вторичный контур)
            gvs_pump_xs = [he_x-50-i*52 for i in range(p.pump_gvs_count)]
            for gpx in gvs_pump_xs:
                pump(gpx, y_t3, r=12)
                mano(gpx, y_t3-30); pipe_t(gpx, y_t3-12, gpx, y_t3-22)
            left_gvs = min(gvs_pump_xs)-35 if gvs_pump_xs else he_x-85

            # ГВС контур (замкнутый контур)
            pipe(left_gvs, y_t3, x_out, y_t3)
            pipe(left_gvs, y_t4, x_out, y_t4)
            pipe(left_gvs, y_t3, left_gvs, y_t4)
            lbl((he_x+x_out)//2, y_t3, f"Ø{p.pipe_gvs_dn}", above=True)
            lbl((he_x+x_out)//2, y_t4, f"Ø{p.pipe_gvs_dn}", above=False)
            fa(x_out-40, y_t3, "right"); fa(x_out-40, y_t4, "left")
            out_lbl(x_out, y_t3, "T3", "right", "red")
            out_lbl(x_out, y_t4, "T4", "right", "blue")

        # ── ПОДПИТКА (B1) ────────────────────────────────────
        pipe(x_lft, y_mup, x_out, y_mup)
        lbl(ox+350, y_mup, f"Ø{p.pipe_gvs_dn}", above=True)
        fa(x_lft+40, y_mup, "right")
        out_lbl(x_lft, y_mup, "B1", "left", "green")

        # Насос подпитки
        mup_x = x_lc + 80
        pump(mup_x, y_mup, r=12)
        valve_h(mup_x-52, y_mup); valve_h(mup_x+52, y_mup)
        check_h(mup_x+75, y_mup)

        # Водомер
        wm_r = 13
        g.add(dwg.circle(center=(x_vm,y_mup), r=wm_r,
                          stroke="black", stroke_width="0.8", fill="white"))
        g.add(dwg.line((x_vm-8,y_mup-10),(x_vm+8,y_mup+10), stroke="black", stroke_width="0.6"))
        du(x_vm, y_mup+28, p.water_meter_dn)
        en_wm = self._find_eq_num("Водомер")
        if en_wm:
            self._pos_label(dwg, g, x_vm, y_mup-28, en_wm)

        pipe(x_lc, y_mup, x_lc, y_p+14)
        dot(x_lc, y_mup)

        dwg.add(g)

    def _draw_valve(self, dwg, g, x, y, size=5):
        g.add(dwg.polygon([(x - size, y - size / 2), (x, y), (x - size, y + size / 2)],
                           fill="none", stroke="black", stroke_width="0.4"))
        g.add(dwg.polygon([(x + size, y - size / 2), (x, y), (x + size, y + size / 2)],
                           fill="none", stroke="black", stroke_width="0.4"))

    def _draw_pump_symbol(self, dwg, g, x, y, r=9):
        g.add(dwg.circle(center=(x, y), r=r, stroke="black", stroke_width="0.5", fill="white"))
        tr = r * 0.55
        g.add(dwg.polygon([(x - tr * 0.5, y - tr), (x + tr, y), (x - tr * 0.5, y + tr)], fill="black"))