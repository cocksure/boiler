"""
Экспорт чертежей в DXF (для AutoCAD).
Базовый экспорт — работает для горизонтальных котлов,
для остальных создаёт упрощённый чертёж.
"""

import io
import math
import ezdxf
from ezdxf import units
from backend.models import BaseBoilerParams


class DXFExporter:
    """Экспорт чертежа в формат DXF"""

    def __init__(self, params: BaseBoilerParams):
        self.p = params

    def generate(self) -> bytes:
        """Генерирует DXF файл"""
        doc = ezdxf.new("R2010")
        doc.units = units.MM
        msp = doc.modelspace()

        p = self.p

        # Для горизонтальных котлов — полный чертёж
        if hasattr(p, 'total_length') and hasattr(p, 'outer_diameter'):
            self._draw_horizontal(msp, p)
        elif hasattr(p, 'total_height') and hasattr(p, 'outer_diameter'):
            self._draw_vertical(msp, p)

        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue().encode("utf-8")

    def _draw_horizontal(self, msp, p):
        """DXF для горизонтальных котлов"""
        r = p.outer_diameter / 2
        L = p.total_length

        # Вид сбоку — корпус
        msp.add_lwpolyline([
            (0, -r), (L, -r), (L, r), (0, r)
        ], close=True)

        # Осевая
        msp.add_line((-50, 0), (L + 50, 0),
                     dxfattribs={"linetype": "CENTER", "color": 1})

        # Жаровая труба (если есть)
        if hasattr(p, 'furnace_diameter') and hasattr(p, 'furnace_length'):
            rf = p.furnace_diameter / 2
            ft = getattr(p, 'front_head_thickness', 12)
            fl = p.furnace_length
            msp.add_lwpolyline([
                (ft, -rf), (ft + fl, -rf), (ft + fl, rf), (ft, rf)
            ], close=True)

        # Опоры
        spacing = L / (p.support_count + 1)
        for i in range(p.support_count):
            sx = spacing * (i + 1) - p.support_width / 2
            msp.add_lwpolyline([
                (sx, r), (sx + p.support_width, r),
                (sx + p.support_width, r + p.support_height),
                (sx, r + p.support_height)
            ], close=True)

        # Размер длины
        dim = msp.add_linear_dim(
            base=(0, -r - 100), p1=(0, -r), p2=(L, -r), dimstyle="EZDXF")
        dim.render()

        # Вид спереди (справа)
        cx = L + 500
        msp.add_circle((cx, 0), r)
        if hasattr(p, 'furnace_diameter'):
            msp.add_circle((cx, 0), p.furnace_diameter / 2)
        msp.add_line((cx - r - 30, 0), (cx + r + 30, 0),
                     dxfattribs={"linetype": "CENTER", "color": 1})
        msp.add_line((cx, -r - 30), (cx, r + 30),
                     dxfattribs={"linetype": "CENTER", "color": 1})

        # Дымогарные трубы
        if hasattr(p, 'smoke_tube_diameter') and hasattr(p, 'smoke_tube_count'):
            ri = r - getattr(p, 'wall_thickness', 8)
            rf = getattr(p, 'furnace_diameter', r * 0.6) / 2
            rs = p.smoke_tube_diameter / 2
            zone_in = rf + rs + 10
            zone_out = ri - rs - 5
            rows = getattr(p, 'smoke_tube_rows', 3)
            if zone_out > zone_in and rows > 0:
                placed = 0
                for row in range(rows):
                    if placed >= p.smoke_tube_count: break
                    r_row = zone_in + (zone_out - zone_in) * row / max(rows - 1, 1)
                    n = min(int(2 * math.pi * r_row / (rs * 2 + 5)),
                            p.smoke_tube_count - placed)
                    for j in range(n):
                        if placed >= p.smoke_tube_count: break
                        angle = 2 * math.pi * j / n
                        msp.add_circle(
                            (cx + r_row * math.cos(angle), r_row * math.sin(angle)),
                            rs, dxfattribs={"color": 8})
                        placed += 1

        # Вид сверху (снизу)
        oy = -(r + 500)
        msp.add_lwpolyline([
            (0, oy - r), (L, oy - r), (L, oy + r), (0, oy + r)
        ], close=True)
        msp.add_line((-50, oy), (L + 50, oy),
                     dxfattribs={"linetype": "CENTER", "color": 1})

        # Патрубки
        if hasattr(p, 'inlet_position_x'):
            msp.add_circle((p.inlet_position_x, oy), p.inlet_diameter / 2)
        if hasattr(p, 'outlet_position_x'):
            msp.add_circle((p.outlet_position_x, oy), p.outlet_diameter / 2)
        # Дымоход
        flue_d = getattr(p, 'flue_diameter', 250)
        msp.add_circle((L, oy), flue_d / 2)

    def _draw_vertical(self, msp, p):
        """DXF для вертикальных котлов"""
        r = p.outer_diameter / 2
        H = p.total_height

        # Вид спереди — корпус
        msp.add_lwpolyline([
            (-r, 0), (r, 0), (r, H), (-r, H)
        ], close=True)

        # Осевая
        msp.add_line((0, -50), (0, H + 50),
                     dxfattribs={"linetype": "CENTER", "color": 1})

        # Топка
        if hasattr(p, 'furnace_diameter') and hasattr(p, 'furnace_height'):
            rf = p.furnace_diameter / 2
            msp.add_lwpolyline([
                (-rf, 0), (rf, 0), (rf, p.furnace_height), (-rf, p.furnace_height)
            ], close=True)

        # Вид сверху (справа)
        cx = r + 500
        msp.add_circle((cx, H / 2), r)
        msp.add_line((cx - r - 20, H / 2), (cx + r + 20, H / 2),
                     dxfattribs={"linetype": "CENTER", "color": 1})

        # Размер высоты
        dim = msp.add_linear_dim(
            base=(-r - 100, 0), p1=(-r, 0), p2=(-r, H),
            angle=90, dimstyle="EZDXF")
        dim.render()