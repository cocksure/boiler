from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class BoilerType(str, Enum):
    """Тип котла — серии Chirchik Flame"""
    HORIZONTAL_FIRE_TUBE = "horizontal_fire_tube"  # КВа-Гн/Лжн — горизонтальный жаротрубный
    VERTICAL = "vertical"                           # КВс, КОГн, КВ-Т — вертикальный
    STEAM = "steam"                                 # Паровой
    SOLID_FUEL = "solid_fuel"                       # ОВТ, КВГ — твёрдотопливный
    BOILER_ROOM = "boiler_room"                     # МТУ — проект котельной


class FuelType(str, Enum):
    GAS = "gas"
    SOLID = "solid"
    LIQUID = "liquid"
    COMBINED = "combined"


# ═══════════════════════════════════════════════════════════════
#  БАЗОВЫЕ ПАРАМЕТРЫ (общие для всех типов)
# ═══════════════════════════════════════════════════════════════

class BaseBoilerParams(BaseModel):
    name: str = Field(default="Котёл", description="Название котла")
    boiler_type: BoilerType = Field(default=BoilerType.HORIZONTAL_FIRE_TUBE)
    fuel_type: FuelType = Field(default=FuelType.GAS)
    power_kw: float = Field(default=1000, gt=0, description="Тепловая мощность, кВт")

    # Патрубки
    inlet_diameter: float = Field(default=80, gt=0, description="Диаметр подачи воды, мм")
    outlet_diameter: float = Field(default=80, gt=0, description="Диаметр выхода воды, мм")
    flue_diameter: float = Field(default=250, gt=0, description="Диаметр дымохода, мм")

    # Опоры
    support_count: int = Field(default=2, ge=2, description="Количество опор")
    support_height: float = Field(default=300, gt=0, description="Высота опор, мм")
    support_width: float = Field(default=200, gt=0, description="Ширина опор, мм")


# ═══════════════════════════════════════════════════════════════
#  ГОРИЗОНТАЛЬНЫЙ ЖАРОТРУБНЫЙ (КВа-Гн)
# ═══════════════════════════════════════════════════════════════

class HorizontalFireTubeParams(BaseBoilerParams):
    """КВа-Гн/Лжн — 3-ходовой горизонтальный жаротрубный"""
    boiler_type: BoilerType = BoilerType.HORIZONTAL_FIRE_TUBE

    # Корпус
    outer_diameter: float = Field(default=1000, gt=0, description="Наружный диаметр, мм")
    wall_thickness: float = Field(default=8, gt=0, description="Толщина стенки, мм")
    total_length: float = Field(default=3000, gt=0, description="Длина цилиндра, мм")

    # Жаровая труба (1-й ход)
    furnace_diameter: float = Field(default=600, gt=0, description="Диаметр жаровой трубы, мм")
    furnace_length: float = Field(default=2000, gt=0, description="Длина жаровой трубы, мм")

    # Дымогарные трубы (2-й и 3-й ход)
    smoke_tube_diameter: float = Field(default=51, gt=0, description="Диаметр дымогарных труб, мм")
    smoke_tube_count: int = Field(default=40, gt=0, description="Количество дымогарных труб")
    smoke_tube_rows: int = Field(default=4, ge=1, description="Количество рядов")

    # Днища
    front_head_thickness: float = Field(default=12, gt=0, description="Толщина переднего днища, мм")
    rear_head_thickness: float = Field(default=12, gt=0, description="Толщина заднего днища, мм")

    # Положение патрубков
    inlet_position_x: float = Field(default=500, description="Позиция входа по длине, мм")
    outlet_position_x: float = Field(default=2500, description="Позиция выхода по длине, мм")

    @property
    def inner_diameter(self) -> float:
        return self.outer_diameter - 2 * self.wall_thickness


# ═══════════════════════════════════════════════════════════════
#  ВЕРТИКАЛЬНЫЙ (КВс, КОГн, КВ-Т)
# ═══════════════════════════════════════════════════════════════

class VerticalBoilerParams(BaseBoilerParams):
    """КВс / КОГн / КВ-Т — вертикальный котёл"""
    boiler_type: BoilerType = BoilerType.VERTICAL

    # Корпус
    outer_diameter: float = Field(default=700, gt=0, description="Наружный диаметр, мм")
    wall_thickness: float = Field(default=6, gt=0, description="Толщина стенки, мм")
    total_height: float = Field(default=1500, gt=0, description="Общая высота корпуса, мм")

    # Топка (нижняя часть)
    furnace_diameter: float = Field(default=500, gt=0, description="Диаметр топки, мм")
    furnace_height: float = Field(default=500, gt=0, description="Высота топки, мм")

    # Жаровые трубы (вертикальные)
    smoke_tube_diameter: float = Field(default=51, gt=0, description="Диаметр жаровых труб, мм")
    smoke_tube_count: int = Field(default=20, gt=0, description="Количество труб")

    # Теплообменная рубашка
    jacket_gap: float = Field(default=50, gt=0, description="Зазор водяной рубашки, мм")

    # Дверца (для КВ-Т — загрузочная)
    has_door: bool = Field(default=False, description="Загрузочная дверца (для твёрдого топлива)")
    door_width: float = Field(default=300, description="Ширина дверцы, мм")
    door_height: float = Field(default=250, description="Высота дверцы, мм")
    door_position_z: float = Field(default=200, description="Высота дверцы от основания, мм")

    # Патрубки: позиции
    inlet_position_z: float = Field(default=400, description="Высота входа воды от основания, мм")
    outlet_position_z: float = Field(default=1200, description="Высота выхода воды от основания, мм")
    flue_position: str = Field(default="top", description="Положение дымохода: top/back")

    @property
    def inner_diameter(self) -> float:
        return self.outer_diameter - 2 * self.wall_thickness


# ═══════════════════════════════════════════════════════════════
#  ПАРОВОЙ КОТЁЛ
# ═══════════════════════════════════════════════════════════════

class SteamBoilerParams(BaseBoilerParams):
    """Паровой котёл — горизонтальный с паросборником"""
    boiler_type: BoilerType = BoilerType.STEAM
    steam_capacity: float = Field(default=1.0, gt=0, description="Паропроизводительность, т/ч")
    pressure_mpa: float = Field(default=0.8, gt=0, description="Рабочее давление, МПа")

    # Корпус
    outer_diameter: float = Field(default=1200, gt=0, description="Наружный диаметр, мм")
    wall_thickness: float = Field(default=10, gt=0, description="Толщина стенки, мм")
    total_length: float = Field(default=3500, gt=0, description="Длина цилиндра, мм")

    # Жаровая труба
    furnace_diameter: float = Field(default=650, gt=0, description="Диаметр жаровой трубы, мм")
    furnace_length: float = Field(default=2500, gt=0, description="Длина жаровой трубы, мм")

    # Дымогарные трубы
    smoke_tube_diameter: float = Field(default=51, gt=0, description="Диаметр дымогарных труб, мм")
    smoke_tube_count: int = Field(default=50, gt=0, description="Количество дымогарных труб")
    smoke_tube_rows: int = Field(default=4, ge=1, description="Количество рядов")

    # Паросборник (верхний барабан)
    steam_drum_diameter: float = Field(default=400, gt=0, description="Диаметр паросборника, мм")
    steam_drum_length: float = Field(default=2000, gt=0, description="Длина паросборника, мм")
    steam_drum_offset_y: float = Field(default=200, description="Смещение паросборника вверх, мм")

    # Предохранительный клапан
    safety_valve_diameter: float = Field(default=50, gt=0, description="Диаметр предохранительного клапана, мм")
    safety_valve_count: int = Field(default=2, ge=1, description="Количество предохранительных клапанов")

    # Уровнемер
    level_gauge_position_x: float = Field(default=500, description="Позиция уровнемера по длине, мм")

    # Днища
    front_head_thickness: float = Field(default=14, gt=0, description="Толщина переднего днища, мм")
    rear_head_thickness: float = Field(default=14, gt=0, description="Толщина заднего днища, мм")

    # Положение патрубков
    inlet_position_x: float = Field(default=600, description="Позиция входа воды, мм")
    outlet_position_x: float = Field(default=2800, description="Позиция выхода пара, мм")

    @property
    def inner_diameter(self) -> float:
        return self.outer_diameter - 2 * self.wall_thickness


# ═══════════════════════════════════════════════════════════════
#  ТВЁРДОТОПЛИВНЫЙ (ОВТ, КВГ)
# ═══════════════════════════════════════════════════════════════

class SolidFuelBoilerParams(BaseBoilerParams):
    """ОВТ / КВГ — горизонтальный твёрдотопливный"""
    boiler_type: BoilerType = BoilerType.SOLID_FUEL
    fuel_type: FuelType = FuelType.SOLID

    # Корпус
    outer_diameter: float = Field(default=1000, gt=0, description="Наружный диаметр, мм")
    wall_thickness: float = Field(default=8, gt=0, description="Толщина стенки, мм")
    total_length: float = Field(default=3000, gt=0, description="Длина корпуса, мм")

    # Топка
    furnace_width: float = Field(default=800, gt=0, description="Ширина топки, мм")
    furnace_height: float = Field(default=600, gt=0, description="Высота топки, мм")
    furnace_length: float = Field(default=1500, gt=0, description="Длина топки / глубина, мм")

    # Загрузочная дверца
    door_width: float = Field(default=400, gt=0, description="Ширина загрузочной дверцы, мм")
    door_height: float = Field(default=350, gt=0, description="Высота загрузочной дверцы, мм")
    door_position_z: float = Field(default=400, description="Высота дверцы от пола, мм")

    # Колосниковая решётка
    grate_width: float = Field(default=700, gt=0, description="Ширина колосниковой решётки, мм")
    grate_length: float = Field(default=1200, gt=0, description="Длина колосниковой решётки, мм")
    grate_position_z: float = Field(default=300, description="Высота колосника от основания, мм")

    # Зольник
    ash_pit_height: float = Field(default=250, gt=0, description="Высота зольника, мм")
    ash_door_width: float = Field(default=350, gt=0, description="Ширина дверцы зольника, мм")
    ash_door_height: float = Field(default=200, gt=0, description="Высота дверцы зольника, мм")

    # Дымогарные трубы
    smoke_tube_diameter: float = Field(default=51, gt=0, description="Диаметр дымогарных труб, мм")
    smoke_tube_count: int = Field(default=30, gt=0, description="Количество труб")
    smoke_tube_rows: int = Field(default=3, ge=1, description="Количество рядов")

    # Днища
    front_head_thickness: float = Field(default=12, gt=0, description="Толщина переднего днища, мм")
    rear_head_thickness: float = Field(default=12, gt=0, description="Толщина заднего днища, мм")

    # Положение патрубков
    inlet_position_x: float = Field(default=500, description="Позиция входа воды, мм")
    outlet_position_x: float = Field(default=2500, description="Позиция выхода воды, мм")

    @property
    def inner_diameter(self) -> float:
        return self.outer_diameter - 2 * self.wall_thickness


# ═══════════════════════════════════════════════════════════════
#  ПРОЕКТ КОТЕЛЬНОЙ (МТУ)
# ═══════════════════════════════════════════════════════════════

class BoilerUnit(BaseModel):
    """Один котёл в составе котельной"""
    boiler_series: str = Field(default="КВа-Гн", description="Серия котла")
    power_kw: float = Field(default=300, gt=0, description="Мощность котла, кВт")
    count: int = Field(default=2, ge=1, description="Количество котлов данной серии")
    length_mm: float = Field(default=2200, gt=0, description="Длина котла, мм")
    width_mm: float = Field(default=1000, gt=0, description="Ширина/диаметр котла, мм")
    height_mm: float = Field(default=1200, gt=0, description="Высота котла, мм")
    flue_diameter: float = Field(default=300, gt=0, description="Диаметр дымохода котла, мм")
    burner_type: str = Field(default="газовая автоматическая", description="Тип горелки")


class BoilerRoomParams(BaseModel):
    """МТУ — Модульная Тепловая Установка (проект котельной)"""
    boiler_type: BoilerType = BoilerType.BOILER_ROOM
    name: str = Field(default="МТУ-600", description="Название проекта")
    fuel_type: FuelType = Field(default=FuelType.GAS)
    power_kw: float = Field(default=600, gt=0, description="Суммарная мощность, кВт")

    # Помещение котельной
    room_length: float = Field(default=6000, gt=0, description="Длина помещения, мм")
    room_width: float = Field(default=4000, gt=0, description="Ширина помещения, мм")
    room_height: float = Field(default=2200, gt=0, description="Высота помещения, мм")
    roof_height: float = Field(default=2500, gt=0, description="Высота до конька крыши, мм")

    # Котлы (группа 1)
    boiler_series: str = Field(default="КВс-300Гн", description="Серия котла")
    boiler_power: float = Field(default=300, gt=0, description="Мощность одного котла, кВт")
    boiler_count: int = Field(default=2, ge=1, le=6, description="Количество котлов")
    boiler_length: float = Field(default=1800, gt=0, description="Длина котла, мм")
    boiler_width: float = Field(default=950, gt=0, description="Ширина/диаметр котла, мм")
    boiler_height: float = Field(default=1200, gt=0, description="Высота котла, мм")

    # Котлы (группа 2 — опционально, как ТУ-1400: 1xКВа-200 + 2xКВа-600)
    boiler2_enabled: bool = Field(default=False, description="Второй тип котла")
    boiler2_series: str = Field(default="КВа-600Гн", description="Серия котла 2")
    boiler2_power: float = Field(default=600, gt=0, description="Мощность котла 2, кВт")
    boiler2_count: int = Field(default=2, ge=1, le=4, description="Количество котлов 2")
    boiler2_length: float = Field(default=2500, gt=0, description="Длина котла 2, мм")
    boiler2_width: float = Field(default=1200, gt=0, description="Ширина котла 2, мм")
    boiler2_height: float = Field(default=1400, gt=0, description="Высота котла 2, мм")

    # Дымоходы
    chimney_diameter: float = Field(default=300, gt=0, description="Диаметр дымовой трубы, мм")
    chimney_height: float = Field(default=4000, gt=0, description="Высота дымовой трубы, мм")
    chimney_count: int = Field(default=2, ge=1, description="Количество дымовых труб")

    # Фундаменты
    boiler_foundation_length: float = Field(default=2400, gt=0, description="Длина фундамента под котёл, мм")
    boiler_foundation_width: float = Field(default=1400, gt=0, description="Ширина фундамента под котёл, мм")
    boiler_foundation_height: float = Field(default=150, gt=0, description="Высота фундамента, мм")
    pump_foundation_length: float = Field(default=600, gt=0, description="Длина фундамента под насосы, мм")
    pump_foundation_width: float = Field(default=400, gt=0, description="Ширина фундамента под насосы, мм")

    # Оборудование
    has_heat_exchanger: bool = Field(default=True, description="Теплообменник (ГВС)")
    heat_exchanger_power: float = Field(default=200, gt=0, description="Мощность теплообменника, кВт")
    expansion_tank_volume: float = Field(default=100, gt=0, description="Объём расш. бака, л")
    expansion_tank_count: int = Field(default=2, ge=1, description="Количество расш. баков")

    # Насосы
    pump_winter_count: int = Field(default=2, ge=1, description="Насосы зимние (1 раб + 1 рез)")
    pump_summer_count: int = Field(default=2, ge=1, description="Насосы летние")
    pump_gvs_count: int = Field(default=2, ge=1, description="Насосы ГВС")
    pump_makeup_count: int = Field(default=1, ge=1, description="Насос подпиточный")

    # Арматура
    mud_filter_dn: int = Field(default=150, description="Грязевик Ду, мм")
    water_meter_dn: int = Field(default=25, description="Водомер Ду, мм")

    # Трубопроводы
    pipe_main_dn: str = Field(default="108x3.5", description="Основной трубопровод")
    pipe_branch_dn: str = Field(default="57x3.5", description="Отводы к котлам")
    pipe_gvs_dn: str = Field(default="89x3.5", description="Трубопровод ГВС")

    # Газоснабжение
    gas_pipe_entry: str = Field(default="left", description="Ввод газа: left/right/top")

    # Жалюзийная решётка
    louver_width: float = Field(default=500, gt=0, description="Ширина жалюзийной решётки, мм")
    louver_height: float = Field(default=300, gt=0, description="Высота жалюзийной решётки, мм")
    louver_count: int = Field(default=2, ge=0, description="Количество жалюзийных решёток")


# ═══════════════════════════════════════════════════════════════
#  УНИВЕРСАЛЬНЫЙ ЗАПРОС
# ═══════════════════════════════════════════════════════════════

class DrawingRequest(BaseModel):
    boiler_type: BoilerType
    params: dict  # Будет валидироваться по типу
    format: str = Field(default="svg", pattern="^(svg|dxf|pdf)$")
    scale: float = Field(default=1.0, gt=0)