from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from server.services.config import load_config, BASE_DIR
from server.services.watcher import start_watcher
from server.routes import display, admin, events


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    app.state.config = config
    app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

    observer = start_watcher(config)
    yield
    observer.stop()
    observer.join()


app = FastAPI(title="Pi Menu Display", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")

app.include_router(display.router)
app.include_router(admin.router)
app.include_router(events.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
