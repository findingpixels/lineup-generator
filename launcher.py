from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

import streamlit.web.cli as stcli

_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_PATH = _ROOT / "app.py"
LOG_PATH = Path(tempfile.gettempdir()) / "lineup_generator.log"
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "127.0.0.1"


def _write_log(text: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def main() -> None:
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(STREAMLIT_PORT))
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", STREAMLIT_HOST)
    os.environ.setdefault("STREAMLIT_BROWSER_SERVER_ADDRESS", STREAMLIT_HOST)
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")

    sys.argv = [
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.port",
        str(STREAMLIT_PORT),
        "--server.address",
        STREAMLIT_HOST,
        "--browser.serverAddress",
        STREAMLIT_HOST,
        "--global.developmentMode",
        "false",
    ]
    try:
        stcli.main()
    except SystemExit as exc:
        if exc.code:
            msg = f"Streamlit exited with code {exc.code}. Log: {LOG_PATH}"
            print(msg)
            _write_log(msg)
            input("Press Enter to close...")
    except Exception:
        tb = traceback.format_exc()
        print("Streamlit failed to start. See log:", LOG_PATH)
        _write_log(tb)
        input("Press Enter to close...")


if __name__ == "__main__":
    main()
