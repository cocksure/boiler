from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from backend.models import (
    BoilerType, HorizontalFireTubeParams, VerticalBoilerParams,
    SteamBoilerParams, SolidFuelBoilerParams, BoilerRoomParams
)
from drawing_engine.horizontal import HorizontalFireTubeDrawing
from drawing_engine.vertical import VerticalBoilerDrawing
from drawing_engine.steam import SteamBoilerDrawing
from drawing_engine.solid_fuel import SolidFuelBoilerDrawing
from drawing_engine.boiler_room import BoilerRoomDrawing
from drawing_engine.export import DXFExporter

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Маппинг типов
PARAM_MODELS = {
    BoilerType.HORIZONTAL_FIRE_TUBE: HorizontalFireTubeParams,
    BoilerType.VERTICAL: VerticalBoilerParams,
    BoilerType.STEAM: SteamBoilerParams,
    BoilerType.SOLID_FUEL: SolidFuelBoilerParams,
    BoilerType.BOILER_ROOM: BoilerRoomParams,
}

DRAWING_CLASSES = {
    BoilerType.HORIZONTAL_FIRE_TUBE: HorizontalFireTubeDrawing,
    BoilerType.VERTICAL: VerticalBoilerDrawing,
    BoilerType.STEAM: SteamBoilerDrawing,
    BoilerType.SOLID_FUEL: SolidFuelBoilerDrawing,
    BoilerType.BOILER_ROOM: BoilerRoomDrawing,
}


def _parse_and_draw(data: dict) -> str:
    """Парсит параметры по типу и генерирует SVG"""
    btype = BoilerType(data.get("boiler_type", "horizontal_fire_tube"))
    model = PARAM_MODELS[btype]
    params = model(**data)
    drawing_cls = DRAWING_CLASSES[btype]
    scale = 0.15 if btype == BoilerType.BOILER_ROOM else 0.1
    drawing = drawing_cls(params, scale=scale)
    return drawing.generate()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/preview")
async def preview_drawing(data: dict):
    svg = _parse_and_draw(data)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/api/export/svg")
async def export_svg(data: dict):
    from urllib.parse import quote
    svg = _parse_and_draw(data)
    name = data.get("name", "boiler")
    encoded = quote(f"{name}.svg")
    return Response(
        content=svg, media_type="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"}
    )


@router.post("/api/export/dxf")
async def export_dxf(data: dict):
    btype = BoilerType(data.get("boiler_type", "horizontal_fire_tube"))
    model = PARAM_MODELS[btype]
    params = model(**data)
    exporter = DXFExporter(params)
    dxf_bytes = exporter.generate()
    from urllib.parse import quote
    name = data.get("name", "boiler")
    encoded = quote(f"{name}.dxf")
    return Response(
        content=dxf_bytes, media_type="application/dxf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"}
    )


def _register_cyrillic_font():
    """Register DejaVu font for Cyrillic support in reportlab"""
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", fp))
            except Exception:
                pass
            return True
    return False


@router.post("/api/export/pdf")
async def export_pdf(data: dict):
    import io
    import tempfile
    import os
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF

    svg = _parse_and_draw(data)

    if _register_cyrillic_font():
        svg = svg.replace("ISOCPEUR, Arial, sans-serif", "DejaVuSans")
        svg = svg.replace("ISOCPEUR,Arial,sans-serif", "DejaVuSans")

    tmp_svg = tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w", encoding="utf-8")
    tmp_svg.write(svg)
    tmp_svg.close()

    try:
        drawing = svg2rlg(tmp_svg.name)
        if drawing is None:
            return Response(content="Ошибка конвертации SVG", status_code=500)

        tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp_pdf.close()
        renderPDF.drawToFile(drawing, tmp_pdf.name, fmt="PDF")

        with open(tmp_pdf.name, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp_pdf.name)
    finally:
        os.unlink(tmp_svg.name)

    from urllib.parse import quote
    name = data.get("name", "boiler")
    encoded = quote(f"{name}.pdf")
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"}
    )


@router.get("/api/defaults/{boiler_type}")
async def get_defaults(boiler_type: str):
    btype = BoilerType(boiler_type)
    model = PARAM_MODELS[btype]
    return model().model_dump()