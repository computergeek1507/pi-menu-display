import asyncio
import time
import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from server.services.config import BASE_DIR
from server.routes.events import broadcast


class _ImageChangeHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, config: dict):
        self._loop = loop
        self._config = config
        self._allowed = set(config["images"]["allowed_extensions"])
        self._debounce: dict[str, float] = {}
        self._debounce_lock = threading.Lock()
        self._debounce_seconds = 2.0

    def _screen_from_path(self, path: str) -> tuple[str | None, str]:
        """Returns (screen_id, event_type)."""
        try:
            rel = Path(path).relative_to(BASE_DIR / "images")
        except ValueError:
            return None, "refresh"
        parts = rel.parts
        if not parts:
            return None, "refresh"
        folder = parts[0]
        if folder == "specials" and len(parts) >= 2:
            screen_id = parts[1]
            if screen_id in self._config["screens"]:
                return screen_id, "specials"
            return None, "specials"
        if folder in self._config["screens"]:
            return folder, "refresh"
        return None, "refresh"

    def _is_allowed(self, path: str) -> bool:
        return Path(path).suffix.lower() in self._allowed

    def on_any_event(self, event):
        if event.is_directory:
            return
        src = event.src_path
        if not self._is_allowed(src):
            return

        screen, event_type = self._screen_from_path(src)
        if not screen:
            return

        now = time.time()
        key = f"{event_type}:{screen}"
        with self._debounce_lock:
            last = self._debounce.get(key, 0)
            if now - last < self._debounce_seconds:
                self._debounce[key] = now
                return
            self._debounce[key] = now

        asyncio.run_coroutine_threadsafe(
            broadcast({"type": event_type, "screen": screen, "ts": now}),
            self._loop,
        )


def start_watcher(config: dict) -> Observer:
    loop = asyncio.get_event_loop()
    handler = _ImageChangeHandler(loop, config)
    observer = Observer()
    watch_path = str(BASE_DIR / "images")
    observer.schedule(handler, watch_path, recursive=True)
    observer.daemon = True
    observer.start()
    return observer
