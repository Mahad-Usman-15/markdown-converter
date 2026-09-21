import os
import shutil
import signal
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import Settings


@asynccontextmanager
async def lifespan(app):
    settings = app.state.settings
    processes = app.state.processes

    if not (settings.frontend_dir / "index.html").is_file():
        raise RuntimeError("Build frontend/dist before starting the server.")

    if settings.pdf_enabled and not (settings.model_dir / "ready.json").is_file():
        raise RuntimeError(
            "PDF models are missing. Run backend/scripts/prepare_models.py, "
            "or set MC_PDF_ENABLED=false for website-only work."
        )

    app.state.temp_root = Path(
        tempfile.mkdtemp(prefix="markdown-converter-")
    )

    yield

    for proc in list(processes.values()):
        if proc.poll() is None:
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except ProcessLookupError:
                pass
            proc.wait()

    if app.state.temp_root:
        shutil.rmtree(app.state.temp_root, ignore_errors=True)
