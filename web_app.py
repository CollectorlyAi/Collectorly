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
from datetime import timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("web_app")

# ── Import backend (tkinter-free) ─────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

BACKEND_OK   = False
ANTHROPIC_OK = False
PLAYWRIGHT_OK = False
PIL_OK        = False

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
    )
    import numismatic_agent as _na
    ANTHROPIC_OK  = getattr(_na, "ANTHROPIC_OK",  False)
    PLAYWRIGHT_OK = getattr(_na, "PLAYWRIGHT_OK", False)
    PIL_OK        = getattr(_na, "PIL_OK",         False)
    BACKEND_OK    = True
    log.info("Backend loaded OK (anthropic=%s playwright=%s pil=%s)",
             ANTHROPIC_OK, PLAYWRIGHT_OK, PIL_OK)
except Exception as exc:
    log.error("Backend import failed: %s", exc, exc_info=True)

# ── Flask setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)

# SECRET_KEY must be stable across restarts or all sessions are invalidated.
# On Render: set SECRET_KEY as a secret environment variable.
# Locally: a random fallback is fine (sessions don't need to survive restarts).
_SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not _SECRET_KEY:
    # Derive a stable key from the machine if env var is missing.
    # This survives process restarts on the same machine but not deploys.
    import hashlib, socket, uuid as _uuid
    _SECRET_KEY = hashlib.sha256(
        socket.gethostname().encode() + str(_uuid.getnode()).encode() + b"numis_web_v1"
    ).hexdigest()

app.config["SECRET_KEY"]              = _SECRET_KEY
app.config["MAX_CONTENT_LENGTH"]      = 16 * 1024 * 1024   # 16 MB
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = bool(os.environ.get("RENDER"))  # HTTPS on Render
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "numis_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}


# ── Master password store ─────────────────────────────────────────────────────
#
# Priority (first wins):
#   1. APP_PASSWORD env var  — set this in Render's "Secret Files" or env vars.
#      The app uses it directly; nothing is written to disk.
#   2. web_auth.json file    — written on first-run setup, works on persistent
#      disks or local installs. Wiped on Render's ephemeral filesystem.
#
# On Render free tier you MUST set APP_PASSWORD (and SECRET_KEY) as env vars.

_AUTH_DIR  = Path(os.environ.get("HOME", str(Path.home()))) / ".numismatic"
_AUTH_FILE = _AUTH_DIR / "web_auth.json"


def _load_auth() -> dict:
    if _AUTH_FILE.exists():
        try:
            return json.loads(_AUTH_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_auth(data: dict):
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_FILE.write_text(json.dumps(data))
    try:
        _AUTH_FILE.chmod(0o600)
    except OSError:
        pass


def _env_password() -> str:
    """Return APP_PASSWORD env var (stripped), or empty string."""
    return os.environ.get("APP_PASSWORD", "").strip()


def _has_master_password() -> bool:
    if _env_password():
        return True
    return bool(_load_auth().get("master_hash"))


def _check_password(password: str) -> bool:
    env_pw = _env_password()
    if env_pw:
        # Timing-safe comparison to prevent timing attacks on plain-text env pw
        return secrets.compare_digest(password.encode(), env_pw.encode())
    h = _load_auth().get("master_hash", "")
    if not h:
        return False
    return check_password_hash(h, password)


def _set_master_password(password: str):
    """Hash and persist password to disk (file-based mode only)."""
    data = _load_auth()
    data["master_hash"] = generate_password_hash(password, method="pbkdf2:sha256")
    _save_auth(data)


# ── Startup config check ──────────────────────────────────────────────────────

def _log_startup_config():
    on_render = bool(os.environ.get("RENDER"))
    has_secret = bool(os.environ.get("SECRET_KEY"))
    has_pw     = bool(_env_password())
    has_file   = bool(_load_auth().get("master_hash"))

    if on_render:
        if not has_secret:
            log.warning(
                "SECRET_KEY env var not set — a random key is used, so ALL "
                "sessions are invalidated on every Render restart. "
                "Set SECRET_KEY to a fixed random string in Render environment."
            )
        if not has_pw:
            if has_file:
                log.warning(
                    "APP_PASSWORD env var not set — password is stored in "
                    "web_auth.json which is wiped on Render restarts. "
                    "Set APP_PASSWORD in Render environment variables."
                )
            else:
                log.warning(
                    "No APP_PASSWORD env var and no web_auth.json. "
                    "First-run setup will work but the password will be lost "
                    "on the next Render restart. Set APP_PASSWORD now."
                )
    log.info(
        "Auth config — env_password=%s file_hash=%s secret_key_fixed=%s",
        bool(has_pw), has_file, has_secret,
    )


_log_startup_config()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _json_error(message: str, status: int):
    return jsonify({"error": message}), status


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            # API calls always get JSON 401, never an HTML redirect
            if request.path.startswith("/api/"):
                return _json_error("Authentication required", 401)
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(_e):
    if request.path.startswith("/api/"):
        return _json_error("File too large (max 16 MB)", 413)
    return render_template("login.html", needs_setup=False), 413


@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith("/api/"):
        return _json_error("Not found", 404)
    return redirect(url_for("index"))


@app.errorhandler(500)
def server_error(_e):
    if request.path.startswith("/api/"):
        return _json_error("Internal server error", 500)
    return redirect(url_for("index"))


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    if session.get("authenticated"):
        return redirect(url_for("index"))
    needs_setup = not _has_master_password()
    return render_template("login.html", needs_setup=needs_setup)


@app.route("/login", methods=["POST"])
def do_login():
    data     = request.get_json(force=True, silent=True) or {}
    password = data.get("password", "")

    if not password:
        return _json_error("Password required", 400)

    if not _has_master_password():
        # First-run: create master password
        if len(password) < 8:
            return _json_error("Password must be at least 8 characters", 400)
        _set_master_password(password)
        session["authenticated"] = True
        session.permanent = True
        on_render  = bool(os.environ.get("RENDER"))
        ephemeral  = on_render and not _env_password()
        return jsonify({
            "ok":      True,
            "setup":   True,
            "warning": (
                "Your password was saved to disk. On Render's free tier this "
                "file is wiped on restarts. Set APP_PASSWORD in your Render "
                "environment variables to make it permanent."
            ) if ephemeral else None,
        })

    if not _check_password(password):
        return _json_error("Incorrect password", 401)

    session["authenticated"] = True
    session.permanent = True
    return jsonify({"ok": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/api/auth/config")
def api_auth_config():
    """Public endpoint — tells the frontend what auth mode is active."""
    return jsonify({
        "needs_setup":    not _has_master_password(),
        "env_password":   bool(_env_password()),
        "file_password":  bool(_load_auth().get("master_hash")),
        "render":         bool(os.environ.get("RENDER")),
        "secret_key_env": bool(os.environ.get("SECRET_KEY")),
        "authenticated":  bool(session.get("authenticated")),
    })


@app.route("/api/auth/change-password", methods=["POST"])
@login_required
def api_change_password():
    data    = request.get_json(force=True, silent=True) or {}
    current = data.get("current", "")
    new_pw  = data.get("new", "")
    if not _check_password(current):
        return _json_error("Current password incorrect", 401)
    if len(new_pw) < 8:
        return _json_error("New password must be at least 8 characters", 400)
    if _env_password():
        return _json_error(
            "Password is set via APP_PASSWORD env var — change it there, not here.", 400
        )
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
        "playwright": PLAYWRIGHT_OK,
        "anthropic":  ANTHROPIC_OK,
        "pil":        PIL_OK,
    })


@app.route("/api/metal-prices")
@login_required
def api_metal_prices():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    try:
        prices, err = MetalPriceFetcher.fetch()
        return jsonify({"prices": prices, "error": err})
    except Exception as exc:
        log.exception("metal-prices")
        return _json_error(str(exc), 500)


@app.route("/api/identify", methods=["POST"])
@login_required
def api_identify():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    if not ANTHROPIC_OK:
        return _json_error("anthropic package not installed — run: pip install anthropic", 500)

    file = request.files.get("image")
    if not file or not file.filename:
        return _json_error("No image uploaded", 400)
    if not _allowed(file.filename):
        return _json_error("Unsupported file type", 400)

    suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    tmp = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=suffix, delete=False)
    try:
        file.save(tmp.name)
        result = CoinVisionIdentifier.identify(tmp.name)

        catalog_matches = []
        km      = (result.get("km_number") or "").strip()
        country = (result.get("country")   or "").strip()
        if km:
            try:
                catalog_matches = WorldCoinDB.search_by_km(km, country=country, limit=5)
            except Exception:
                pass

        return jsonify({"identification": result, "catalog_matches": catalog_matches})
    except Exception as exc:
        log.exception("identify")
        return _json_error(str(exc), 500)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


@app.route("/api/ngc-census", methods=["POST"])
@login_required
def api_ngc_census():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("coin name required", 400)
    try:
        return jsonify(NGCPopFetcher.fetch(
            name,
            (data.get("year") or "").strip(),
            (data.get("mint") or "").strip(),
        ))
    except Exception as exc:
        log.exception("ngc-census")
        return _json_error(str(exc), 500)


@app.route("/api/pcgs-pop", methods=["POST"])
@login_required
def api_pcgs_pop():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("coin name required", 400)
    try:
        return jsonify(PCGSPopFetcher.fetch(
            name,
            (data.get("year") or "").strip(),
            (data.get("mint") or "").strip(),
        ))
    except Exception as exc:
        log.exception("pcgs-pop")
        return _json_error(str(exc), 500)


@app.route("/api/pcgs-prices", methods=["POST"])
@login_required
def api_pcgs_prices():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("coin name required", 400)
    try:
        return jsonify(PCGSPriceFetcher.fetch(
            name,
            (data.get("year") or "").strip(),
            (data.get("mint") or "").strip(),
        ))
    except Exception as exc:
        log.exception("pcgs-prices")
        return _json_error(str(exc), 500)


@app.route("/api/ngc-cert", methods=["POST"])
@login_required
def api_ngc_cert():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data = request.get_json(force=True, silent=True) or {}
    cert = (data.get("cert") or "").strip()
    if not cert:
        return _json_error("cert number required", 400)
    try:
        return jsonify(NGCCertFetcher.fetch(cert))
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.route("/api/pcgs-cert", methods=["POST"])
@login_required
def api_pcgs_cert():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data = request.get_json(force=True, silent=True) or {}
    cert = (data.get("cert") or "").strip()
    if not cert:
        return _json_error("cert number required", 400)
    try:
        return jsonify(PCGSCertFetcher.fetch(cert))
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.route("/api/credentials", methods=["POST"])
@login_required
def api_save_credentials():
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    data     = request.get_json(force=True, silent=True) or {}
    site     = (data.get("site")     or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not site:
        return _json_error("site required", 400)
    try:
        CredentialStore.save(site, username, password)
        return jsonify({"ok": True})
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.route("/api/credentials/<site>", methods=["DELETE"])
@login_required
def api_delete_credentials(site):
    if not BACKEND_OK:
        return _json_error("Backend unavailable", 503)
    try:
        CredentialStore.delete(site)
        return jsonify({"ok": True})
    except Exception as exc:
        return _json_error(str(exc), 500)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
