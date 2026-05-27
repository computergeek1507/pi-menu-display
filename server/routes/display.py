import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from server.services.config import BASE_DIR, MONTH_NAMES

router = APIRouter()


def _find_images(directory: Path, allowed: list[str]) -> list[str]:
    if not directory.exists():
        return []
    return sorted(
        f.name for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in allowed
    )


@router.get("/display/{screen_id}")
async def display_page(screen_id: str, request: Request):
    config = request.app.state.config
    screen_cfg = config["screens"].get(screen_id)
    if not screen_cfg:
        return JSONResponse({"error": "unknown screen"}, status_code=404)

    image_dir = BASE_DIR / screen_cfg["image_dir"]
    allowed = config["images"]["allowed_extensions"]
    images = _find_images(image_dir, allowed)

    specials_cfg = config["specials"]
    current_special = None
    if specials_cfg["enabled"]:
        current_special = _get_current_special(
            BASE_DIR / specials_cfg["image_dir"] / screen_id, allowed
        )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="display.html",
        context={
            "screen_id": screen_id,
            "screen_name": screen_cfg["name"],
            "images": images,
            "image_base": f"/{screen_cfg['image_dir']}",
            "rotation_interval": screen_cfg.get("rotation_interval", 0),
            "specials": {
                "enabled": specials_cfg["enabled"],
                "current": current_special,
                "image_base": f"/{specials_cfg['image_dir']}/{screen_id}",
                "interval_ms": specials_cfg["interval_minutes"] * 60 * 1000,
                "duration_ms": specials_cfg["display_duration_seconds"] * 1000,
                "fade_ms": specials_cfg["fade_duration_seconds"] * 1000,
                "max_opacity": specials_cfg["max_opacity"],
            },
        },
    )


def _get_current_special(specials_dir: Path, allowed: list[str]) -> str | None:
    month = MONTH_NAMES[datetime.datetime.now().month - 1]
    if not specials_dir.exists():
        return None
    for f in specials_dir.iterdir():
        if f.stem.lower() == month and f.suffix.lower() in allowed:
            return f.name
    return None


@router.get("/api/specials/{screen_id}/current")
async def current_special(screen_id: str, request: Request):
    config = request.app.state.config
    specials_cfg = config["specials"]
    allowed = config["images"]["allowed_extensions"]
    if screen_id not in config["screens"]:
        return JSONResponse({"error": "unknown screen"}, status_code=404)
    special = _get_current_special(
        BASE_DIR / specials_cfg["image_dir"] / screen_id, allowed
    )
    if not special:
        return JSONResponse({"error": "no special for this month"}, status_code=404)
    return {"url": f"/{specials_cfg['image_dir']}/{screen_id}/{special}"}


@router.get("/api/images/{screen_id}")
async def list_images(screen_id: str, request: Request):
    config = request.app.state.config
    screen_cfg = config["screens"].get(screen_id)
    if not screen_cfg:
        return JSONResponse({"error": "unknown screen"}, status_code=404)
    allowed = config["images"]["allowed_extensions"]
    images = _find_images(BASE_DIR / screen_cfg["image_dir"], allowed)
    return {"screen_id": screen_id, "images": images}
