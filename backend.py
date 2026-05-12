from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, make_response, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
TABLET_COOKIE = "nf2026_tablet"
ADMIN_PATH = "/admin-pilotage-rsk"

ALLOWED_COLORS = {"green", "blue"}
ALLOWED_IDS = {1, 2}

app = Flask(__name__)

_tablet_configs: dict[str, dict[str, Any]] = {}
_clients_by_host: dict[str, Any] = {}
_clients_lock = threading.Lock()


def _get_or_create_tablet_id() -> str:
    tablet_id = request.cookies.get(TABLET_COOKIE)
    if tablet_id:
        return tablet_id
    return uuid.uuid4().hex


def _validate_config(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    host = str(payload.get("host", "")).strip()
    color = str(payload.get("color", "")).strip().lower()

    raw_id = payload.get("id")
    try:
        robot_id = int(raw_id)
    except (TypeError, ValueError):
        return None, "Le champ 'id' doit etre 1 ou 2."

    if not host:
        return None, "Le champ 'host' est obligatoire."
    if color not in ALLOWED_COLORS:
        return None, "Le champ 'color' doit etre 'green' ou 'blue'."
    if robot_id not in ALLOWED_IDS:
        return None, "Le champ 'id' doit etre 1 ou 2."

    return {"host": host, "color": color, "id": robot_id}, None


def _execute_control(host: str, color: str, robot_id: int, dx: float, dy: float, dalpha: float) -> None:
    try:
        import rsk  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Le module 'rsk' est introuvable. Installez la dependance cote backend."
        ) from exc

    with _clients_lock:
        client = _clients_by_host.get(host)
        if client is None:
            client = rsk.Client(host=host)
            _clients_by_host[host] = client

    client.robots[color][robot_id].control(dx, dy, dalpha)


@app.after_request
def _attach_cookie(response):
    if not request.cookies.get(TABLET_COOKIE):
        response.set_cookie(TABLET_COOKIE, _get_or_create_tablet_id(), max_age=60 * 60 * 24 * 365)
    return response


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get(ADMIN_PATH)
def admin_page():
    return send_from_directory(BASE_DIR, "admin.html")


@app.get("/api/config")
def get_config():
    tablet_id = _get_or_create_tablet_id()
    config = _tablet_configs.get(tablet_id)
    if not config:
        return jsonify({"configured": False, "config": None})
    return jsonify({"configured": True, "config": config})


@app.post("/api/config")
def set_config():
    tablet_id = _get_or_create_tablet_id()
    payload = request.get_json(silent=True) or {}

    config, error = _validate_config(payload)
    if error:
        return jsonify({"ok": False, "error": error}), 400

    _tablet_configs[tablet_id] = config
    return jsonify({"ok": True, "config": config})


@app.post("/api/control")
def control():
    tablet_id = _get_or_create_tablet_id()
    config = _tablet_configs.get(tablet_id)
    if not config:
        return jsonify({
            "ok": False,
            "error": "Tablette non configuree. Ouvrez la page admin cachee pour definir host/color/id.",
            "adminPath": ADMIN_PATH,
        }), 409

    payload = request.get_json(silent=True) or {}

    try:
        dx = float(payload.get("dx", 0))
        dy = float(payload.get("dy", 0))
        dalpha = float(payload.get("dalpha", 0))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "dx, dy et dalpha doivent etre numeriques."}), 400

    try:
        _execute_control(config["host"], config["color"], config["id"], dx, dy, dalpha)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Echec d'envoi commande robot: {exc}"}), 500

    return jsonify({"ok": True})


@app.get("/<path:filename>")
def static_files(filename: str):
    target = BASE_DIR / filename
    if not target.is_file():
        return make_response("Not found", 404)
    return send_from_directory(BASE_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
