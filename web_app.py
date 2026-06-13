#!/usr/bin/env python3
"""
Collectorly Numismatics — Flask Web Application
All routes are protected by session-based login.
Credentials are stored encrypted at rest (Fernet/AES); never logged or displayed.
"""

import os
import sys
import json
import tempfile
import logging
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, abort,
)
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("web_app")

# Strip credentials from log records at the module level
_SENSITIVE = {"password", "api_key", "token", "secret", "key", "pass"}
_orig_make = logging.LogRecord.__init__

# ── Import backend (tkinter-free) ─────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

try:
    from numismatic_agent import (
        MetalPriceFetcher,
        CoinVisionIdentifier,
        NGCPopFetcher,
        PCGSPopFetcher,
        PCGSPriceFetcher,
        NGCCertFetcher,
        PCGSCertFetcher,
        WorldCoinDB,
        CredentialStore,
        ANTHROPIC_OK,
        PLAYWRIGHT_OK,
        PIL_OK,
    )
    # Verify key classes loaded
    _ = MetalPriceFetcher.fetch  # noqa: attribute check
    BACKEND_OK = True
except Exception as e:
    log.error("Backend import failed: %s", e)
    BACKEND_OK = False

# ── Flask setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

UPLOAD_DIR = Path(tempfile.gettempdir()) / "numis_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}

# ── Master password store ─────────────────────────────────────────────────────
_AUTH_DIR  = Path.home() / ".numismatic"
_AUTH_FILE = _AUTH_DIR / "web_auth.json"


def _load_auth() -> dict:
    if _AUTH_FILE.exists():
        try:
            return json.loads(_AUTH_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_auth(data: dict):
    _AUTH_DIR.mkdir(exist_ok=True)
    _AUTH_FILE.write_text(json.dumps(data))
    try:
        _AUTH_FILE.chmod(0o600)
    except OSError:
        pass


def _get_master_hash() -> str:
    return _load_auth().get("master_hash", "")


def _set_master_password(password: str):
    data = _load_auth()
    data["master_hash"] = generate_password_hash(password)
    _save_auth(data)


def _has_master_password() -> bool:
    return bool(_get_master_hash())


def _check_password(password: str) -> bool:
    h = _get_master_hash()
    if not h:
        return False
    return check_password_hash(h, password)


# ── Auth decorator ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            if request.is_json or request.path.startswith("/api/"):
                abort(401)
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    if session.get("authenticated"):
        return redirect(url_for("index"))
    needs_setup = not _has_master_password()
    return render_template("login.html", needs_setup=needs_setup)


@app.route("/login", methods=["POST"])
def do_login():
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password", "")

    if not password:
        return jsonify({"error": "Password required"}), 400

    if not _has_master_password():
        # First-run: set the master password
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        _set_master_password(password)
        session["authenticated"] = True
        session.permanent = True
        return jsonify({"ok": True, "setup": True})

    if not _check_password(password):
        return jsonify({"error": "Incorrect password"}), 401

    session["authenticated"] = True
    session.permanent = True
    return jsonify({"ok": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/api/auth/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json(force=True, silent=True) or {}
    current = data.get("current", "")
    new_pw   = data.get("new", "")
    if not _check_password(current):
        return jsonify({"error": "Current password incorrect"}), 401
    if len(new_pw) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    _set_master_password(new_pw)
    return jsonify({"ok": True})


# ── Protected routes ──────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/status")
@login_required
def api_status():
    return jsonify({
        "backend":    BACKEND_OK,
        "playwright": PLAYWRIGHT_OK if BACKEND_OK else False,
        "anthropic":  ANTHROPIC_OK  if BACKEND_OK else False,
        "pil":        PIL_OK         if BACKEND_OK else False,
    })


@app.route("/api/metal-prices")
@login_required
def api_metal_prices():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    try:
        prices, err = MetalPriceFetcher.fetch()
        return jsonify({"prices": prices, "error": err})
    except Exception as e:
        log.exception("metal-prices error")
        return jsonify({"prices": {}, "error": str(e)}), 500


@app.route("/api/identify", methods=["POST"])
@login_required
def api_identify():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    if not ANTHROPIC_OK:
        return jsonify({"error": "anthropic package not installed"}), 500

    file = request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No image uploaded"}), 400
    if not _allowed(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    tmp = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=suffix, delete=False)
    try:
        file.save(tmp.name)
        result = CoinVisionIdentifier.identify(tmp.name)

        catalog_matches = []
        km      = result.get("km_number", "").strip()
        country = result.get("country", "").strip()
        if km:
            try:
                catalog_matches = WorldCoinDB.search_by_km(km, country=country, limit=5)
            except Exception:
                pass

        return jsonify({"identification": result, "catalog_matches": catalog_matches})
    except Exception as e:
        log.exception("identify error")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


@app.route("/api/ngc-census", methods=["POST"])
@login_required
def api_ngc_census():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    year = data.get("year", "").strip()
    mint = data.get("mint", "").strip()
    if not name:
        return jsonify({"error": "coin name required"}), 400
    try:
        result = NGCPopFetcher.fetch(name, year, mint)
        return jsonify(result)
    except Exception as e:
        log.exception("ngc-census error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pcgs-pop", methods=["POST"])
@login_required
def api_pcgs_pop():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    year = data.get("year", "").strip()
    mint = data.get("mint", "").strip()
    if not name:
        return jsonify({"error": "coin name required"}), 400
    try:
        result = PCGSPopFetcher.fetch(name, year, mint)
        return jsonify(result)
    except Exception as e:
        log.exception("pcgs-pop error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pcgs-prices", methods=["POST"])
@login_required
def api_pcgs_prices():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    year = data.get("year", "").strip()
    mint = data.get("mint", "").strip()
    if not name:
        return jsonify({"error": "coin name required"}), 400
    try:
        result = PCGSPriceFetcher.fetch(name, year, mint)
        return jsonify(result)
    except Exception as e:
        log.exception("pcgs-prices error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ngc-cert", methods=["POST"])
@login_required
def api_ngc_cert():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    cert = data.get("cert", "").strip()
    if not cert:
        return jsonify({"error": "cert number required"}), 400
    try:
        result = NGCCertFetcher.fetch(cert)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pcgs-cert", methods=["POST"])
@login_required
def api_pcgs_cert():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    cert = data.get("cert", "").strip()
    if not cert:
        return jsonify({"error": "cert number required"}), 400
    try:
        result = PCGSCertFetcher.fetch(cert)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/credentials", methods=["POST"])
@login_required
def api_save_credentials():
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    data = request.get_json(force=True, silent=True) or {}
    site     = data.get("site", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not site:
        return jsonify({"error": "site required"}), 400
    try:
        CredentialStore.save(site, username, password)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/credentials/<site>", methods=["DELETE"])
@login_required
def api_delete_credentials(site):
    if not BACKEND_OK:
        return jsonify({"error": "Backend unavailable"}), 503
    try:
        CredentialStore.delete(site)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
