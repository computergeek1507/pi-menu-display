import shutil
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, RedirectResponse

from server.services.config import BASE_DIR

router = APIRouter()

ALLOWED_EXTENSIONS: set[str] = set()
MAX_UPLOAD_BYTES: int = 0


def _init_limits(config: dict):
    global ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
    ALLOWED_EXTENSIONS = set(config["images"]["allowed_extensions"])
    MAX_UPLOAD_BYTES = config["images"]["max_upload_mb"] * 1024 * 1024


def _image_dir_for(target: str, config: dict) -> Path | None:
    if target.startswith("specials-"):
        screen_id = target[len("specials-"):]
        if screen_id in config["screens"]:
            return BASE_DIR / config["specials"]["image_dir"] / screen_id
        return None
    screen = config["screens"].get(target)
    if screen:
        return BASE_DIR / screen["image_dir"]
    return None


def _list_images(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    results = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
            results.append({"name": f.name, "size": f.stat().st_size})
    return results


@router.get("/admin")
async def admin_page(request: Request):
    config = request.app.state.config
    _init_limits(config)

    screens = {}
    for sid, scfg in config["screens"].items():
        d = BASE_DIR / scfg["image_dir"]
        screens[sid] = {
            "name": scfg["name"],
            "images": _list_images(d),
        }

    specials = {}
    for sid in config["screens"]:
        specials_dir = BASE_DIR / config["specials"]["image_dir"] / sid
        specials[sid] = _list_images(specials_dir)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "screens": screens,
            "specials": specials,
            "config": config,
        },
    )


@router.post("/api/upload/{target}")
async def upload_image(target: str, request: Request, file: UploadFile = File(...)):
    config = request.app.state.config
    _init_limits(config)

    image_dir = _image_dir_for(target, config)
    if image_dir is None:
        return JSONResponse({"error": "invalid target"}, status_code=400)

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {"error": f"file type {ext} not allowed"},
            status_code=400,
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            {"error": f"file exceeds {config['images']['max_upload_mb']}MB limit"},
            status_code=400,
        )

    image_dir.mkdir(parents=True, exist_ok=True)
    dest = image_dir / file.filename
    dest.write_bytes(content)

    return {"status": "ok", "filename": file.filename, "size": len(content)}


@router.delete("/api/image/{target}/{filename}")
async def delete_image(target: str, filename: str, request: Request):
    config = request.app.state.config
    _init_limits(config)

    image_dir = _image_dir_for(target, config)
    if image_dir is None:
        return JSONResponse({"error": "invalid target"}, status_code=400)

    filepath = (image_dir / filename).resolve()
    if not str(filepath).startswith(str(image_dir.resolve())):
        return JSONResponse({"error": "invalid path"}, status_code=400)

    if not filepath.exists():
        return JSONResponse({"error": "file not found"}, status_code=404)

    filepath.unlink()
    return {"status": "ok", "deleted": filename}
