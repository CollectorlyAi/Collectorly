#!/usr/bin/env python3
"""
Numismatic Coin Analysis Agent
Searches Heritage, eBay, Sedwick, Christie's, Great Collections, Sotheby's.
Tracks metal prices from Kitco/metals.live.
Integrates NGC/PCGS population data.
Flags undervalued, crossover, old-holder, and regrade opportunities.

Dependencies:
    pip install requests beautifulsoup4
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TK_OK = True
except (ImportError, RuntimeError):
    TK_OK = False
    # Stub out the entire tkinter namespace so GUI class definitions don't
    # crash at import time when running headless (e.g. on Render/Linux).
    class _Stub:
        """Absorbs any attribute access and any call."""
        def __init__(self, *a, **kw): pass
        def __call__(self, *a, **kw): return self
        def __getattr__(self, name): return self
        def pack(self, *a, **kw): pass
        def grid(self, *a, **kw): pass
        def place(self, *a, **kw): pass
        def config(self, *a, **kw): pass
        def configure(self, *a, **kw): pass
        def bind(self, *a, **kw): pass
        def bind_all(self, *a, **kw): pass
        def unbind_all(self, *a, **kw): pass
        def insert(self, *a, **kw): pass
        def delete(self, *a, **kw): pass
        def get(self, *a, **kw): return ""
        def set(self, *a, **kw): pass
        def destroy(self, *a, **kw): pass
        def title(self, *a, **kw): pass
        def geometry(self, *a, **kw): pass
        def resizable(self, *a, **kw): pass
        def minsize(self, *a, **kw): pass
        def transient(self, *a, **kw): pass
        def grab_set(self, *a, **kw): pass
        def update_idletasks(self, *a, **kw): pass
        def winfo_screenwidth(self, *a, **kw): return 1920
        def winfo_screenheight(self, *a, **kw): return 1080
        def mainloop(self, *a, **kw): pass
        def after(self, *a, **kw): pass
        def protocol(self, *a, **kw): pass
        def create_window(self, *a, **kw): return 0
        def create_text(self, *a, **kw): return 0
        def bbox(self, *a, **kw): return (0, 0, 0, 0)
        def itemconfig(self, *a, **kw): pass
        def yview_scroll(self, *a, **kw): pass
        def tag_configure(self, *a, **kw): pass
        def tag_add(self, *a, **kw): pass
        def index(self, *a, **kw): return "1.0"
        def see(self, *a, **kw): pass

    class _TkModule:
        """Mimics the tkinter module namespace."""
        Tk       = _Stub
        Toplevel = _Stub
        Frame    = _Stub
        LabelFrame = _Stub
        Canvas   = _Stub
        Label    = _Stub
        Button   = _Stub
        Entry    = _Stub
        Text     = _Stub
        Scrollbar = _Stub
        StringVar = _Stub
        BooleanVar = _Stub
        IntVar   = _Stub
        DoubleVar = _Stub
        PhotoImage = _Stub
        Menu     = _Stub
        Menubutton = _Stub
        OptionMenu = _Stub
        Checkbutton = _Stub
        Radiobutton = _Stub
        Listbox  = _Stub
        Scale    = _Stub
        Spinbox  = _Stub
        PanedWindow = _Stub
        # Constants
        END = "end"; X = "x"; Y = "y"; BOTH = "both"; N = "n"; S = "s"
        E = "e"; W = "w"; NW = "nw"; NE = "ne"; SW = "sw"; SE = "se"
        LEFT = "left"; RIGHT = "right"; TOP = "top"; BOTTOM = "bottom"
        CENTER = "center"; FLAT = "flat"; WORD = "word"; CHAR = "char"
        HORIZONTAL = "horizontal"; VERTICAL = "vertical"
        NORMAL = "normal"; DISABLED = "disabled"; HIDDEN = "hidden"
        RAISED = "raised"; SUNKEN = "sunken"; RIDGE = "ridge"; GROOVE = "groove"
        SOLID = "solid"; ROUND = "round"; BUTT = "butt"
        FIRST = "first"; LAST = "last"; NONE = "none"; ALL = "all"
        INSERT = "insert"; SEL = "sel"; SEL_FIRST = "sel.first"; SEL_LAST = "sel.last"
        ACTIVE = "active"; CURRENT = "current"
        BROWSE = "browse"; MULTIPLE = "multiple"; EXTENDED = "extended"; SINGLE = "single"
        READABLE = "readable"; WRITABLE = "writable"; EXCEPTION = "exception"
        CASCADE = "cascade"; CHECKBUTTON = "checkbutton"; COMMAND = "command"
        RADIOBUTTON = "radiobutton"; SEPARATOR = "separator"
        TRUE = True; FALSE = False
        def __getattr__(self, name): return _Stub()

    class _TtkModule:
        Button   = _Stub; Entry    = _Stub; Label    = _Stub; Frame    = _Stub
        LabelFrame = _Stub; Combobox = _Stub; Scrollbar = _Stub; Treeview = _Stub
        Notebook = _Stub; PanedWindow = _Stub; Scale   = _Stub; Spinbox  = _Stub
        Progressbar = _Stub; Separator = _Stub; Sizegrip = _Stub
        Style    = _Stub
        def __getattr__(self, name): return _Stub()

    class _MsgboxModule:
        @staticmethod
        def showinfo(*a, **kw): pass
        @staticmethod
        def showerror(*a, **kw): pass
        @staticmethod
        def showwarning(*a, **kw): pass
        @staticmethod
        def askyesno(*a, **kw): return False
        @staticmethod
        def askokcancel(*a, **kw): return False
        @staticmethod
        def askyesnocancel(*a, **kw): return False

    class _ScrolledModule:
        ScrolledText = _Stub

    tk           = _TkModule()   # type: ignore
    ttk          = _TtkModule()  # type: ignore
    messagebox   = _MsgboxModule()  # type: ignore
    scrolledtext = _ScrolledModule()  # type: ignore
import asyncio
import threading
import queue
import re
import statistics
import logging
import time
import os
import json
import base64
import hashlib
import socket
import uuid
import sqlite3
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urlencode, urlparse

logging.basicConfig(level=logging.WARNING,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("numismatic")

try:
    import requests
    from requests.exceptions import (
        ConnectionError as ReqConnectionError,
        Timeout as ReqTimeout,
        HTTPError as ReqHTTPError,
        RequestException,
    )
    from bs4 import BeautifulSoup
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import keyring as _keyring
    KEYRING_OK = True
except ImportError:
    KEYRING_OK = False

try:
    from PIL import Image as PILImage, ImageTk, ImageDraw
    from io import BytesIO
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

try:
    import pdfplumber as _pdfplumber
    PDFPLUMBER_OK = True
except ImportError:
    PDFPLUMBER_OK = False

try:
    from playwright.sync_api import sync_playwright as _sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

try:
    import Vision as _Vision
    import Foundation as _Foundation
    MACOS_OCR_OK = True
except ImportError:
    MACOS_OCR_OK = False

try:
    import anthropic as _anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False

# ── Custom exceptions ─────────────────────────────────────────────────────────

class FetchError(Exception):
    """Raised by fetchers for known, reportable network / HTTP failures."""
    def __init__(self, source: str, reason: str, retryable: bool = False):
        self.source = source
        self.reason = reason
        self.retryable = retryable
        super().__init__(f"{source}: {reason}")

# ── Credential storage ────────────────────────────────────────────────────────

_CRED_SERVICE  = "numismatic_agent"
_CRED_DIR      = Path.home() / ".numismatic"
_CRED_FILE     = _CRED_DIR / "credentials.json"      # legacy plaintext (migrated away)
_CRED_ENC_FILE = _CRED_DIR / "credentials.enc"        # Fernet-encrypted store

# Supported auction sites
SITES: Dict[str, str] = {
    "heritage":         "Heritage Auctions",
    "ebay":             "eBay",
    "sedwick":          "Sedwick Coins",
    "christies":        "Christie's",
    "greatcollections": "Great Collections",
    "sothebys":         "Sotheby's",
    "coinstrail":       "Coinstrail",
    "ngc":              "NGC",
    "pcgs":             "PCGS",
    "anthropic":        "Anthropic (AI Vision)",
}


def _fernet_key() -> bytes:
    """
    Returns a 32-byte Fernet key.
    Strategy (best → fallback):
      1. keyring  — random key generated once, stored in macOS Keychain
      2. machine  — key derived from MAC address + hostname (AES-level, machine-bound)
    """
    if KEYRING_OK and CRYPTO_OK:
        stored = _keyring.get_password(_CRED_SERVICE, "fernet_key")
        if stored:
            return stored.encode()
        key = Fernet.generate_key().decode()
        _keyring.set_password(_CRED_SERVICE, "fernet_key", key)
        return key.encode()
    # Deterministic machine-bound key (no external dependency)
    raw = hashlib.sha256(
        str(uuid.getnode()).encode() +
        socket.gethostname().encode() +
        b"numismatic_v2"
    ).digest()
    return base64.urlsafe_b64encode(raw)


class CredentialStore:
    """
    Stores site login credentials encrypted with AES-128 (Fernet).

    Key storage priority:
      1. macOS Keychain via keyring  — random key, never written to disk
      2. Machine-derived key         — SHA-256 of MAC + hostname, machine-bound
    Credential file: ~/.numismatic/credentials.enc  (chmod 0o600)
    """

    # ── internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _load_all() -> dict:
        if not CRYPTO_OK:
            # Legacy base64 JSON fallback
            if _CRED_FILE.exists():
                try:
                    raw = json.loads(_CRED_FILE.read_text())
                    return {
                        k: {
                            "u": v.get("u", ""),
                            "p": base64.b64decode(v.get("p", "")).decode()
                                 if v.get("p") else "",
                        }
                        for k, v in raw.items()
                    }
                except Exception:
                    pass
            return {}
        if not _CRED_ENC_FILE.exists():
            return {}
        try:
            token = _CRED_ENC_FILE.read_bytes()
            plaintext = Fernet(_fernet_key()).decrypt(token)
            return json.loads(plaintext)
        except Exception as e:
            log.warning("CredentialStore decrypt failed: %s", e)
            return {}

    @staticmethod
    def _save_all(data: dict):
        _CRED_DIR.mkdir(exist_ok=True)
        if not CRYPTO_OK:
            encoded = {
                k: {"u": v["u"], "p": base64.b64encode(v["p"].encode()).decode()}
                for k, v in data.items()
            }
            _CRED_FILE.write_text(json.dumps(encoded, indent=2))
            try:
                _CRED_FILE.chmod(0o600)
            except OSError:
                pass
            return
        token = Fernet(_fernet_key()).encrypt(json.dumps(data).encode())
        _CRED_ENC_FILE.write_bytes(token)
        try:
            _CRED_ENC_FILE.chmod(0o600)
        except OSError:
            pass

    # ── public API ───────────────────────────────────────────────────────────

    @staticmethod
    def save(site: str, username: str, password: str):
        data = CredentialStore._load_all()
        data[site] = {"u": username, "p": password}
        CredentialStore._save_all(data)

    @staticmethod
    def load(site: str) -> Tuple[str, str]:
        entry = CredentialStore._load_all().get(site, {})
        return entry.get("u", ""), entry.get("p", "")

    @staticmethod
    def has_credentials(site: str) -> bool:
        u, _ = CredentialStore.load(site)
        return bool(u)

    @staticmethod
    def delete(site: str):
        data = CredentialStore._load_all()
        data.pop(site, None)
        CredentialStore._save_all(data)

    @staticmethod
    def migrate_legacy():
        """One-time migration: encrypt credentials.json → credentials.enc, then delete json."""
        if not CRYPTO_OK or not _CRED_FILE.exists() or _CRED_ENC_FILE.exists():
            return
        try:
            raw = json.loads(_CRED_FILE.read_text())
            data = {
                k: {
                    "u": v.get("u", ""),
                    "p": base64.b64decode(v["p"]).decode() if v.get("p") else "",
                }
                for k, v in raw.items()
            }
            CredentialStore._save_all(data)
            _CRED_FILE.unlink()
            log.info("CredentialStore: migrated credentials.json → credentials.enc")
        except Exception as e:
            log.warning("CredentialStore migration failed: %s", e)


class SessionManager:
    """Holds one requests.Session per site; tracks login state in-process."""
    _pool:      Dict[str, "requests.Session"] = {}
    _logged_in: Dict[str, bool]               = {}

    @classmethod
    def session(cls, site: str) -> "requests.Session":
        if site not in cls._pool:
            s = requests.Session()
            s.headers.update(HTTP_HEADERS)
            cls._pool[site] = s
            cls._logged_in[site] = False
        return cls._pool[site]

    @classmethod
    def is_logged_in(cls, site: str) -> bool:
        return cls._logged_in.get(site, False)

    @classmethod
    def set_logged_in(cls, site: str, value: bool = True):
        cls._logged_in[site] = value

    @classmethod
    def reset(cls, site: str):
        cls._pool.pop(site, None)
        cls._logged_in[site] = False

    @classmethod
    def reset_all(cls):
        cls._pool.clear()
        cls._logged_in.clear()


# ── Constants ────────────────────────────────────────────────────────────────

GRADES = [
    "",
    # Poor / Fair / About Good
    "P-1", "FR-2", "AG-3",
    # Good
    "G-4", "G-6",
    # Very Good
    "VG-8", "VG-10",
    # Fine
    "F-12", "F-15",
    # Very Fine
    "VF-20", "VF-25", "VF-30", "VF-35",
    # Extremely Fine / Extra Fine
    "EF-40", "EF-45", "XF-40", "XF-45",
    # About Uncirculated
    "AU-50", "AU-55", "AU-58",
    # Mint State
    "MS-60", "MS-61", "MS-62", "MS-63", "MS-64", "MS-65",
    "MS-66", "MS-67", "MS-68", "MS-69", "MS-70",
    # Proof (PR)
    "PR-60", "PR-61", "PR-62", "PR-63", "PR-64", "PR-65",
    "PR-66", "PR-67", "PR-68", "PR-69", "PR-70",
    # Proof (PF — PCGS designation)
    "PF-60", "PF-61", "PF-62", "PF-63", "PF-64", "PF-65",
    "PF-66", "PF-67", "PF-68", "PF-69", "PF-70",
    # Specimen (SP — struck as specimen, not circulation or proof)
    "SP-60", "SP-61", "SP-62", "SP-63", "SP-64", "SP-65",
    "SP-66", "SP-67", "SP-68", "SP-69", "SP-70",
    # Proof-Like (PL) and Deep Mirror Proof-Like (DMPL)
    "MS-63 PL", "MS-64 PL", "MS-65 PL", "MS-66 PL", "MS-67 PL",
    "MS-63 DMPL", "MS-64 DMPL", "MS-65 DMPL", "MS-66 DMPL", "MS-67 DMPL",
]

HOLDERS = ["", "NGC", "PCGS", "ANACS", "ICG", "Raw", "CAC-NGC", "CAC-PCGS",
           "NCI", "SEGS", "PCI", "FICO", "SGS", "ACG", "ACCGS"]

CROSSOVER_CANDIDATES = {"ANACS", "ICG", "Raw", "NCI", "SEGS", "PCI", "FICO", "SGS", "ACG", "ACCGS"}

OLD_HOLDERS_INFO: Dict[str, tuple] = {
    "nci":   ("NCI",   "Defunct early-1990s service. Graded leniently. ~70% upgrade at NGC/PCGS."),
    "segs":  ("SEGS",  "Defunct service. Inconsistent standards. ~65% upgrade rate at NGC/PCGS."),
    "pci":   ("PCI",   "Defunct. Frequently upgrades 1–2 points at NGC/PCGS (~75% rate)."),
    "fico":  ("FICO",  "Defunct. Very lenient grading. Often upgrades significantly (~80% rate)."),
    "sgs":   ("SGS",   "Low grading standards. ~80% upgrade rate at major services."),
    "acg":   ("ACG",   "Defunct. Treat as borderline raw. High upgrade probability (~70%)."),
    "accgs": ("ACCGS", "Defunct/inconsistent. Treat as raw for crossover analysis (~68%)."),
    "anacs": ("ANACS", "Conservative grader. ~50% same-grade or better crossover to NGC/PCGS."),
    "icg":   ("ICG",   "Conservative grader. ~55% upgrade rate at NGC/PCGS."),
    "raw":   ("Raw",   "Ungraded. Certify with NGC or PCGS before selling at full market value."),
}

CROSSOVER_RATES: Dict[str, Dict[str, float]] = {
    "nci":   {"ms": 0.70, "au": 0.72, "vf_ef": 0.75, "low": 0.78},
    "segs":  {"ms": 0.62, "au": 0.65, "vf_ef": 0.68, "low": 0.70},
    "pci":   {"ms": 0.72, "au": 0.75, "vf_ef": 0.78, "low": 0.80},
    "fico":  {"ms": 0.75, "au": 0.78, "vf_ef": 0.80, "low": 0.82},
    "sgs":   {"ms": 0.78, "au": 0.80, "vf_ef": 0.82, "low": 0.85},
    "acg":   {"ms": 0.68, "au": 0.70, "vf_ef": 0.72, "low": 0.75},
    "accgs": {"ms": 0.65, "au": 0.67, "vf_ef": 0.70, "low": 0.72},
    "anacs": {"ms": 0.48, "au": 0.50, "vf_ef": 0.52, "low": 0.55},
    "icg":   {"ms": 0.50, "au": 0.52, "vf_ef": 0.55, "low": 0.58},
    "raw":   {"ms": 0.42, "au": 0.40, "vf_ef": 0.38, "low": 0.35},
}

NGC_PREFERRED_KEYWORDS = {
    "bust", "colonial", "territorial", "seated", "trade", "flowing hair",
    "draped bust", "capped bust", "gobrecht", "pattern", "proof",
    "early american", "pioneer", "world coin", "half cent", "large cent",
    "two cent", "three cent",
}
PCGS_PREFERRED_KEYWORDS = {
    "morgan", "peace", "barber", "walking liberty", "franklin",
    "kennedy", "eisenhower", "saint gaudens", "liberty double eagle",
    "commemorative", "american eagle", "buffalo",
}

SILVER_CONTENT = {
    "morgan dollar": 0.7734, "peace dollar": 0.7734,
    "walking liberty half": 0.3617, "franklin half": 0.3617,
    "kennedy half 40%": 0.1479, "silver dime": 0.0723, "barber dime": 0.0723,
    "standing liberty quarter": 0.1808, "washington quarter": 0.1808,
    "barber quarter": 0.1808, "trade dollar": 0.7874,
    "seated liberty dollar": 0.7734, "silver eagle": 1.0,
    "silver dollar": 0.7734, "bust dollar": 0.7734, "flowing hair dollar": 0.7734,
}

GOLD_CONTENT = {
    "saint-gaudens double eagle": 0.9675, "liberty double eagle": 0.9675,
    "$20 liberty": 0.9675, "$20 saint gaudens": 0.9675,
    "$10 liberty eagle": 0.48375, "$10 indian eagle": 0.48375,
    "$5 half eagle": 0.24187, "$5 indian": 0.24187,
    "$2.5 quarter eagle": 0.12094, "$1 gold": 0.04837,
    "american gold eagle 1oz": 1.0,
}

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15  # seconds

# ── Collectorly × Coinstrail Design System ───────────────────────────────────
# Warm numismatic gold palette from Collectorly.us  +
# Clean card-based layout language from Coinstrail.com

BG      = "#FAFAF8"   # warm off-white canvas
BG2     = "#F2EFE9"   # warm surface / card
BG3     = "#1A1714"   # dark masthead (deep charcoal)
FG      = "#1A1714"   # primary text — warm near-black
FG2     = "#6B6057"   # secondary / muted text
ACCENT  = "#B8924A"   # Collectorly Gold (primary accent)
ACCENT2 = "#8B6A2E"   # Gold dark — hover states
GOLD_LT = "#F0E4C8"   # light gold tint — hover backgrounds
BORDER  = "#E0D8CC"   # warm border
GREEN   = "#1A6B3E"   # positive / realized price
YELLOW  = "#B07D00"   # caution
RED     = "#C0392B"   # alert / danger
ORANGE  = "#C45000"   # warning
PURPLE  = "#5A3E8C"   # crossover
TEAL    = "#006D77"   # informational / NGC
BLUE    = "#1E4E8C"   # PCGS / authority blue

# Coinstrail-inspired status pill colors
STATUS_LIVE    = "#E53E3E"   # red  — live auction
STATUS_SOLD    = "#718096"   # gray — sold
STATUS_BUYNOW  = "#2B6CB0"   # blue — buy now
STATUS_RESERVE = "#D97706"   # amber — reserve not met

# Asset paths
_LOGO_FULL = os.path.expanduser("~/.numismatic/collectorly_logo_full.png")
_LOGO_ICON = os.path.expanduser("~/.numismatic/collectorly_logo_icon.png")


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class AuctionResult:
    source: str
    description: str
    grade: str
    holder: str
    price: float
    date: str
    url: str = ""
    old_holder_key: str = ""

@dataclass
class CoinAnalysis:
    crossover_potential: str = "—"
    crossover_success_rate: float = 0.0
    crossover_details: List[str] = field(default_factory=list)
    recommended_service: str = ""
    old_holders_found: List[Dict] = field(default_factory=list)
    regrade_potential: str = "—"
    roi_1yr: float = 0.0
    roi_3yr: float = 0.0
    roi_5yr: float = 0.0
    melt_value: float = 0.0
    undervalued: bool = False
    flags: List[str] = field(default_factory=list)


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def _safe_get(url: str, source: str,
              session: "Optional[requests.Session]" = None, **kwargs) -> "requests.Response":
    """
    Wraps requests.get (or session.get) with uniform error translation.
    Pass session= to use an authenticated requests.Session.
    Raises FetchError for connection/timeout/HTTP errors.
    """
    try:
        timeout = kwargs.pop("timeout", REQUEST_TIMEOUT)
        if session is not None:
            resp = session.get(url, timeout=timeout, **kwargs)
        else:
            resp = requests.get(url, timeout=timeout, headers=HTTP_HEADERS, **kwargs)
        resp.raise_for_status()
        return resp
    except ReqTimeout:
        raise FetchError(source, f"request timed out ({REQUEST_TIMEOUT}s)", retryable=True)
    except ReqConnectionError as e:
        raise FetchError(source, f"connection error — {e}", retryable=True)
    except ReqHTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        if code == 403:
            raise FetchError(source, "access denied (403) — site blocks scrapers", retryable=False)
        if code == 429:
            raise FetchError(source, "rate-limited (429) — too many requests", retryable=True)
        raise FetchError(source, f"HTTP {code} error", retryable=False)
    except RequestException as e:
        raise FetchError(source, f"network error — {e}", retryable=True)


def _parse_price(text: str) -> float:
    m = re.search(r"\$?([\d,]+(?:\.\d{2})?)", text.replace(",", ""))
    return float(m.group(1).replace(",", "")) if m else 0.0


MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds; doubles each attempt (1s → 2s → 4s)


def _retry_get(url: str, source: str,
               session: "Optional[requests.Session]" = None,
               max_retries: int = MAX_RETRIES,
               base_delay: float = BASE_RETRY_DELAY, **kwargs) -> "requests.Response":
    """
    Wraps _safe_get with exponential-backoff retry for transient failures.
    Pass session= to use an authenticated requests.Session.
    """
    for attempt in range(max_retries + 1):
        try:
            return _safe_get(url, source, session=session, **kwargs)
        except FetchError as e:
            if not e.retryable or attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            log.warning("%s transient error (attempt %d/%d), retrying in %.1fs: %s",
                        source, attempt + 1, max_retries, delay, e.reason)
            time.sleep(delay)
    raise FetchError(source, "max retries exceeded")


_LOGIN_SUCCESS = frozenset({
    "sign out", "log out", "logout", "my account", "account settings",
    "welcome back", "your account", "my profile",
})
_LOGIN_FAIL = frozenset({
    "invalid password", "incorrect password", "login failed",
    "authentication failed", "wrong password", "account not found",
})


class PlaywrightLoginManager:
    """Headless Chromium login to bypass bot detection and JS-only login flows."""
    _pw = None
    _browser = None
    _lock = threading.Lock()

    @classmethod
    def _ensure_browser(cls):
        if cls._browser is None:
            try:
                cls._pw = _sync_playwright().start()
                cls._browser = cls._pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled",
                          "--no-sandbox", "--disable-dev-shm-usage"],
                )
            except Exception:
                # Clean up partial state so the next call can start fresh.
                # If we leave cls._pw running but cls._browser=None, the next
                # call's _sync_playwright().start() raises "Sync API inside
                # asyncio loop" because the first instance's loop is still live.
                try:
                    if cls._pw:
                        cls._pw.stop()
                except Exception:
                    pass
                cls._pw = None
                cls._browser = None
                raise
        return cls._browser

    @classmethod
    def login(cls, site_key: str, login_url: str,
              username: str, password: str,
              session: "requests.Session") -> bool:
        """
        Navigate to login_url, fill credentials, submit.
        Extracts cookies and injects them into the requests.Session.
        Returns True on apparent success.
        """
        if not PLAYWRIGHT_OK:
            return False
        with cls._lock:
            try:
                browser = cls._ensure_browser()
                ctx = browser.new_context(
                    user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/120.0.0.0 Safari/537.36"),
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                )
                page = ctx.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
                    Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});
                """)
                page.goto(login_url, wait_until="networkidle", timeout=25000)

                # Fill username field (try common selectors)
                for sel in ["input[name='email']", "input[name='username']",
                            "input[name='customer[email]']", "input[type='email']",
                            "#email", "#username", "#user_email"]:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.click()
                        page.wait_for_timeout(150)
                        page.locator(sel).first.fill(username)
                        break

                # Fill password field
                for sel in ["input[name='password']", "input[name='customer[password]']",
                            "input[type='password']", "#password", "#user_password"]:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.click()
                        page.wait_for_timeout(150)
                        page.locator(sel).first.fill(password)
                        break

                page.wait_for_timeout(400)

                # Click submit
                for sel in ["button[type='submit']", "input[type='submit']",
                            "button:has-text('Sign in')", "button:has-text('Log in')",
                            "button:has-text('Login')", ".btn-primary"]:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.click()
                        break

                page.wait_for_timeout(2500)
                page.wait_for_load_state("networkidle", timeout=12000)

                # Inject cookies into the requests session
                base_domain = urlparse(login_url).netloc
                for c in ctx.cookies():
                    try:
                        session.cookies.set(
                            c["name"], c["value"],
                            domain=c.get("domain") or base_domain,
                            path=c.get("path", "/"))
                    except Exception:
                        pass

                text_lower = page.content().lower()
                ctx.close()

                if any(f in text_lower for f in _LOGIN_FAIL):
                    log.warning("PlaywrightLoginManager %s: credentials rejected", site_key)
                    return False
                if any(s in text_lower for s in _LOGIN_SUCCESS):
                    log.info("PlaywrightLoginManager %s: login confirmed", site_key)
                    return True
                # If no login form remains on the page, assume success
                if "type=\"password\"" not in text_lower and "type='password'" not in text_lower:
                    log.info("PlaywrightLoginManager %s: login likely OK (no password field in response)", site_key)
                    return True
                log.warning("PlaywrightLoginManager %s: login result ambiguous", site_key)
                return False

            except Exception as e:
                log.warning("PlaywrightLoginManager.login(%s): %s", site_key, e)
                return False

    @classmethod
    def shutdown(cls):
        with cls._lock:
            try:
                if cls._browser:
                    cls._browser.close()
                if cls._pw:
                    cls._pw.stop()
            except Exception:
                pass
            cls._browser = None
            cls._pw = None


# ── PlaywrightRunner ──────────────────────────────────────────────────────────

class PlaywrightRunner:
    """
    All Playwright work runs on one dedicated asyncio event-loop thread.
    Callers on any thread submit coroutines via run() and block for the result.
    This avoids every thread-switching error in the sync Playwright API.
    """
    _loop:   Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread]          = None
    _browser  = None  # async_api.Browser
    _apw      = None  # AsyncPlaywright instance
    _lock     = threading.Lock()

    _STEALTH_JS = """
        Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
        Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
        Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});
        Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>8});
        Object.defineProperty(screen,'colorDepth',{get:()=>24});
        window.chrome={runtime:{},loadTimes:function(){},csi:function(){},app:{}};
        const _origPQ=window.navigator.permissions.query;
        window.navigator.permissions.query=(p)=>
            p.name==='notifications'
            ?Promise.resolve({state:Notification.permission})
            :_origPQ(p);
    """
    _UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0.0.0 Safari/537.36")

    # ── loop management ───────────────────────────────────────────────────────

    @classmethod
    def _start(cls) -> asyncio.AbstractEventLoop:
        with cls._lock:
            if cls._loop and cls._loop.is_running():
                return cls._loop
            loop = asyncio.new_event_loop()
            cls._loop = loop
            t = threading.Thread(target=loop.run_forever,
                                 daemon=True, name="pw-async-loop")
            t.start()
            cls._thread = t
            return loop

    @classmethod
    def run(cls, coro, timeout: int = 120):
        """Submit coroutine to the async loop and block until result."""
        return asyncio.run_coroutine_threadsafe(coro, cls._start()).result(timeout)

    # ── browser / context helpers ─────────────────────────────────────────────

    @classmethod
    async def _get_browser(cls):
        if cls._browser is None or not cls._browser.is_connected():
            from playwright.async_api import async_playwright as _apw_fn
            cls._apw    = await _apw_fn().__aenter__()
            cls._browser = await cls._apw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled",
                      "--no-sandbox", "--disable-dev-shm-usage",
                      "--disable-gpu", "--disable-setuid-sandbox"],
            )
        return cls._browser

    @classmethod
    async def new_context(cls):
        browser = await cls._get_browser()
        return await browser.new_context(
            user_agent=cls._UA, locale="en-US",
            timezone_id="America/New_York",
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
        )

    @classmethod
    async def stealth_page(cls, ctx=None):
        """Return (page, ctx). Creates context if not supplied."""
        if ctx is None:
            ctx = await cls.new_context()
        page = await ctx.new_page()
        await page.add_init_script(cls._STEALTH_JS)
        return page, ctx

    # ── shutdown ──────────────────────────────────────────────────────────────

    @classmethod
    def shutdown(cls):
        async def _close():
            try:
                if cls._browser:
                    await cls._browser.close()
                if cls._apw:
                    await cls._apw.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                cls._browser = None
                cls._apw     = None
        if cls._loop and cls._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(_close(), cls._loop).result(10)
            except Exception:
                pass


def _auto_login(session: "requests.Session", site_key: str,
                login_url: str) -> bool:
    """
    Login with Playwright (headless Chrome, bypasses JS/bot-detection).
    Falls back to simple HTML form POST if Playwright unavailable.
    """
    username, password = CredentialStore.load(site_key)
    if not username or not password:
        return False

    # Playwright path (preferred — handles JS, cookies, bot detection)
    if PLAYWRIGHT_OK:
        return PlaywrightLoginManager.login(site_key, login_url, username, password, session)

    # Fallback: simple HTML form POST
    try:
        r = session.get(login_url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        form = next((f for f in soup.find_all("form")
                     if f.find("input", {"type": "password"})), None)
        if form is None:
            log.warning("_auto_login %s: no password form on %s", site_key, login_url)
            return False

        data: Dict[str, str] = {}
        user_field_filled = False
        for inp in form.find_all("input"):
            name = inp.get("name", "")
            if not name:
                continue
            itype = (inp.get("type") or "text").lower()
            if itype == "password":
                data[name] = password
            elif itype in ("text", "email") and not user_field_filled:
                data[name] = username
                user_field_filled = True
            elif itype in ("hidden",):
                data[name] = inp.get("value", "")

        action = (form.get("action") or "").strip() or login_url
        if action.startswith("/"):
            p = urlparse(login_url)
            action = f"{p.scheme}://{p.netloc}{action}"

        resp = session.post(action, data=data, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        text_lower = resp.text.lower()
        if any(f in text_lower for f in _LOGIN_FAIL):
            return False
        if any(s in text_lower for s in _LOGIN_SUCCESS):
            return True
        if not BeautifulSoup(resp.text, "html.parser").find("input", {"type": "password"}):
            return True
        return False
    except Exception as e:
        log.warning("_auto_login %s failed: %s", site_key, e)
        return False


# ── Data fetchers ─────────────────────────────────────────────────────────────

class MetalPriceFetcher:
    _HDRS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.kitco.com/",
    }
    _RANGES = {
        "gold":      (1_000, 15_000),
        "silver":    (5,     500),
        "platinum":  (300,   5_000),
        "palladium": (300,   5_000),
    }
    _KITCO_MARKET_URL = "https://www.kitco.com/market/"
    _GOLDPRICE_URL    = "https://data-asg.goldprice.org/dbXRates/USD"

    @classmethod
    def fetch(cls) -> Tuple[Dict[str, float], str]:
        if not REQUESTS_OK:
            return {}, "requests not installed"

        # Primary: Kitco market page (embedded Next.js JSON)
        prices = cls._fetch_kitco()
        if prices:
            return prices, ""

        # Fallback: goldprice.org JSON
        prices = cls._fetch_goldprice()
        if prices:
            return prices, ""

        return {}, "Metal price sources unavailable — check network connection"

    @classmethod
    def _fetch_kitco(cls) -> Dict[str, float]:
        """Fetch spot prices from Kitco's market page Next.js JSON payload."""
        try:
            r = requests.get(cls._KITCO_MARKET_URL, headers=cls._HDRS, timeout=12)
            if r.status_code != 200:
                return {}

            # Kitco embeds prices in an inline <script> JSON block (Next.js dehydrated state)
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", r.text, re.S)
            for blob in scripts:
                if '"gold"' not in blob or '"bid"' not in blob:
                    continue
                try:
                    data = json.loads(blob)
                    queries = (data.get("props", {})
                                   .get("pageProps", {})
                                   .get("dehydratedState", {})
                                   .get("queries", []))
                    for q in queries:
                        metals_data = q.get("state", {}).get("data", {})
                        prices: Dict[str, float] = {}
                        for metal in ("gold", "silver", "platinum", "palladium"):
                            entry = metals_data.get(metal, {})
                            results = entry.get("results", [])
                            if not results:
                                continue
                            r0 = results[0]
                            # prefer mid (avg of bid/ask), fall back to bid
                            val = float(r0.get("mid") or r0.get("bid") or 0)
                            lo, hi = cls._RANGES[metal]
                            if lo <= val <= hi:
                                prices[metal] = val
                        if prices.get("gold"):
                            return prices
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        except Exception as e:
            log.debug("Kitco fetch failed: %s", e)
        return {}

    @classmethod
    def _fetch_goldprice(cls) -> Dict[str, float]:
        import warnings
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://goldprice.org/"}
                r = requests.get(cls._GOLDPRICE_URL, headers=hdrs, timeout=10, verify=False)
                if r.status_code == 200:
                    d = r.json()
                    prices = {
                        "gold":      float(d.get("xauPrice", 0) or 0),
                        "silver":    float(d.get("xagPrice", 0) or 0),
                        "platinum":  float(d.get("xptPrice", 0) or 0),
                        "palladium": float(d.get("xpdPrice", 0) or 0),
                    }
                    return {k: v for k, v in prices.items() if v}
        except Exception as e:
            log.debug("goldprice.org failed: %s", e)
        return {}


class HeritageFetcher:
    SOURCE    = "Heritage"
    SITE_KEY  = "heritage"

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        q = " ".join(filter(None, [year, mint, name, grade, holder]))
        api_url = f"https://coinstrail.com/api/lot/p-fast-search?keyword={quote_plus(q)}&lang=en"
        sess = SessionManager.session("coinstrail")
        sess.headers.update({"Referer": "https://coinstrail.com/", "Accept": "application/json, */*"})
        try:
            resp = _retry_get(api_url, cls.SOURCE, session=sess)
            data = resp.json()
        except Exception as e:
            log.warning("Heritage (via Coinstrail API) error: %s", e)
            return []
        results = []
        for doc in data.get("docs", [])[:25]:
            if "Heritage" not in doc.get("firm", ""):
                continue
            raw_desc = doc.get("description", "").strip()
            if not raw_desc:
                continue
            # Extract CDN wholesale price (Greysheet bid value embedded by Heritage)
            cdnm = re.search(r'CDN:\s*\$([\d,]+\.?\d*)\s*Whsle', raw_desc)
            price = float(cdnm.group(1).replace(",", "")) if cdnm else 0.0
            # Fallback: any dollar amount in description if CDN not present
            if price == 0.0:
                any_price = re.search(r'\$([\d,]+(?:\.\d{2})?)', raw_desc)
                if any_price:
                    price = float(any_price.group(1).replace(",", ""))
            # Clean description: remove long filler text after CDN line
            clean_desc = re.split(r'\s*CDN:', raw_desc)[0].strip()
            if not clean_desc:
                clean_desc = raw_desc.split(".")[0].strip()
            lot_id = doc.get("id", "")
            auction = doc.get("auction", "")
            # Fetch the Heritage direct URL from Coinstrail lot detail (fast, cached)
            lot_url = f"https://coinstrail.com/lots/{lot_id}" if lot_id else api_url
            try:
                detail_r = SessionManager.session("coinstrail").get(
                    f"https://coinstrail.com/api/lot/{lot_id}?lang=en",
                    timeout=5)
                if detail_r.status_code == 200:
                    lot_data = detail_r.json().get("lot", {})
                    ext_url = lot_data.get("lotExternalUrl", "")
                    if ext_url:
                        lot_url = ext_url
                    if not price and lot_data.get("price", {}).get("price", 0) > 0:
                        price = float(lot_data["price"]["price"])
            except Exception:
                pass
            results.append(AuctionResult(
                source=cls.SOURCE, description=clean_desc[:80],
                grade=grade, holder=holder, price=price,
                date=auction, url=lot_url,
            ))
        return results


class eBayFetcher:
    SOURCE    = "eBay"
    SITE_KEY  = "ebay"
    _session_ready: bool = False

    @staticmethod
    def build_url(name, year, mint, grade, holder) -> str:
        q = " ".join(filter(None, [year, mint, name, grade, holder]))
        params = urlencode({"_nkw": q, "LH_Sold": "1", "LH_Complete": "1"})
        return f"https://www.ebay.com/sch/i.html?{params}"

    @classmethod
    def _warm_session(cls, sess) -> None:
        if not cls._session_ready:
            try:
                sess.get("https://www.ebay.com/", timeout=REQUEST_TIMEOUT)
                cls._session_ready = True
            except Exception:
                pass

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        sess = SessionManager.session(cls.SITE_KEY)
        cls._warm_session(sess)
        url = cls.build_url(name, year, mint, grade, holder)
        resp = _retry_get(url, cls.SOURCE, session=sess)
        results = []
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li[data-listingid]"):
                img = item.select_one("img.s-card__image")
                title = img.get("alt", "").strip() if img else ""
                if not title or "shop on ebay" in title.lower():
                    continue
                # Use the dedicated price span (avoids coin denomination "$1" in titles)
                price_el = item.select_one(".s-card__price")
                price = _parse_price(price_el.get_text()) if price_el else 0.0
                if price < 5.0:
                    raw = item.get_text(" ", strip=True)
                    real = re.findall(r'\$([\d,]+\.\d{2})', raw)
                    price = float(real[0].replace(",", "")) if real else 0.0
                raw_text = item.get_text(" ", strip=True)
                date_m = re.search(
                    r'Sold\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
                    r'\s+\d+,?\s*\d*)', raw_text)
                date = date_m.group(1) if date_m else ""
                link_el = item.select_one("a.s-card__link")
                href = link_el.get("href", "") if link_el else ""
                results.append(AuctionResult(
                    source=cls.SOURCE, description=title[:80],
                    grade=grade, holder=holder, price=price, date=date,
                    url=href or url,
                ))
                if len(results) >= 20:
                    break
        except Exception as e:
            log.warning("eBay parse error: %s", e)
        return results


class SedwickFetcher:
    SOURCE    = "Sedwick"
    SITE_KEY  = "sedwick"
    LOGIN_URL = "https://www.sedwickcoins.com/account/login"

    @staticmethod
    def build_url(name, year, mint, grade, holder) -> str:
        q = " ".join(filter(None, [year, mint, name]))
        return f"https://www.sedwickcoins.com/search?type=product&q={quote_plus(q)}"

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        sess = SessionManager.session(cls.SITE_KEY)
        if (CredentialStore.has_credentials(cls.SITE_KEY)
                and not SessionManager.is_logged_in(cls.SITE_KEY)):
            ok = _auto_login(sess, cls.SITE_KEY, cls.LOGIN_URL)
            SessionManager.set_logged_in(cls.SITE_KEY, ok)
        url = cls.build_url(name, year, mint, grade, holder)
        resp = _retry_get(url, cls.SOURCE, session=sess)
        results = []
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            base = "https://www.sedwickcoins.com"
            for a in soup.select("a[href*='/products/']")[:20]:
                raw = a.get_text(strip=True)
                # Text is "DESCRIPTION.$PRICE" or "DESCRIPTION $PRICE"
                m = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)\s*$', raw)
                price = float(m.group(1).replace(",", "")) if m else 0.0
                title = re.sub(r'\.\$[\d,]+(?:\.\d{2})?$', '', raw).strip()
                if not title or len(title) < 5:
                    continue
                href = a["href"]
                if href.startswith("/"):
                    href = base + href
                results.append(AuctionResult(
                    source=cls.SOURCE, description=title[:80],
                    grade=grade, holder=holder, price=price, date="", url=href,
                ))
        except Exception as e:
            log.warning("Sedwick parse error: %s", e)
        return results


class ChristiesFetcher:
    SOURCE    = "Christie's"
    SITE_KEY  = "christies"
    LOGIN_URL = "https://www.christies.com/account/login"

    @staticmethod
    def build_url(name, year, mint, grade, holder) -> str:
        q = " ".join(filter(None, [year, mint, name]))
        return (
            f"https://www.christies.com/search"
            f"?entry={quote_plus(q)}&page=1&sortby=relevant&action=paging"
        )

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        sess = SessionManager.session(cls.SITE_KEY)
        if (CredentialStore.has_credentials(cls.SITE_KEY)
                and not SessionManager.is_logged_in(cls.SITE_KEY)):
            ok = _auto_login(sess, cls.SITE_KEY, cls.LOGIN_URL)
            SessionManager.set_logged_in(cls.SITE_KEY, ok)
        url = cls.build_url(name, year, mint, grade, holder)
        resp = _retry_get(url, cls.SOURCE, session=sess)
        results = []
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".lot-tile, .search-result, article[class*='lot']")[:15]:
                title_el = item.select_one("h2, h3, [class*='title']")
                price_el = item.select_one("[class*='price'], [class*='estimate']")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                price = _parse_price(price_el.get_text()) if price_el else 0.0
                results.append(AuctionResult(
                    source=cls.SOURCE, description=title[:80],
                    grade=grade, holder=holder, price=price, date="", url=url,
                ))
        except Exception as e:
            log.warning("Christie's parse error: %s", e)
        return results


class GreatCollectionsFetcher:
    SOURCE    = "Great Collections"
    SITE_KEY  = "greatcollections"
    BASE_URL  = "https://www.greatcollections.com"
    LOGIN_URL = "https://www.greatcollections.com/login.php"
    SEARCH_URL = "https://www.greatcollections.com/search.php"

    # Anti-bot headers that match a real browser
    _HEADERS = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.greatcollections.com/",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "upgrade-insecure-requests": "1",
    }

    @staticmethod
    def build_url(name, year, mint, grade, holder) -> str:
        q = " ".join(filter(None, [year, mint, name, grade, holder]))
        return f"https://www.greatcollections.com/search.php?mode=product&q={quote_plus(q)}"

    @classmethod
    def _ensure_session(cls) -> "requests.Session":
        """Return a warmed-up session, logging in via Playwright if credentials exist."""
        sess = SessionManager.session(cls.SITE_KEY)
        sess.headers.update(cls._HEADERS)
        if (CredentialStore.has_credentials(cls.SITE_KEY)
                and not SessionManager.is_logged_in(cls.SITE_KEY)
                and PLAYWRIGHT_OK):
            ok = cls._playwright_login(sess)
            SessionManager.set_logged_in(cls.SITE_KEY, ok)
            if not ok:
                # Fall back to requests-based login
                ok2 = _auto_login(sess, cls.SITE_KEY, cls.LOGIN_URL)
                SessionManager.set_logged_in(cls.SITE_KEY, ok2)
        return sess

    @classmethod
    def _playwright_login(cls, sess) -> bool:
        """Log in via Playwright, bypassing Cloudflare JS challenge, then sync cookies."""
        username, password = CredentialStore.load(cls.SITE_KEY)
        if not username or not password:
            return False
        try:
            browser = PlaywrightLoginManager._ensure_browser()
            ctx = browser.new_context(
                user_agent=cls._HEADERS["User-Agent"],
                locale="en-US",
                timezone_id="America/New_York",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            # Suppress webdriver fingerprint
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )
            page.goto(cls.LOGIN_URL, wait_until="networkidle", timeout=25000)
            # Fill login form
            page.fill('input[name="username"], input[name="email"], #username', username)
            page.fill('input[name="password"], input[type="password"]', password)
            page.click('input[type="submit"], button[type="submit"], .login-btn')
            page.wait_for_load_state("networkidle", timeout=15000)
            # Check for successful login (account menu or logged-in indicator)
            logged_in = bool(page.query_selector(
                'a[href*="logout"], a[href*="account"], .user-menu, #user-nav, '
                'a[href*="mygc"], .mygc-link, [class*="logout"]'
            ))
            # Inject all cookies back into requests session
            for ck in ctx.cookies():
                sess.cookies.set(ck["name"], ck["value"],
                                 domain=ck.get("domain", ".greatcollections.com"))
            ctx.close()
            log.info("GC Playwright login: %s", "OK" if logged_in else "uncertain")
            return True
        except Exception as e:
            log.warning("GC Playwright login failed: %s", e)
            return False

    @classmethod
    def _parse_search_html(cls, html: str, grade: str, holder: str,
                           is_logged_in: bool) -> List["AuctionResult"]:
        """Parse the search results page and extract all lot data."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        results: List[AuctionResult] = []
        seen: set = set()

        for row in soup.select("tr.alt1, tr.alt2"):
            # Title + lot URL
            title_a = row.select_one("span.blue a, a[href*='/Coin/']")
            if not title_a:
                continue
            title = title_a.get_text(strip=True)
            href = title_a.get("href", "")
            if not title or href in seen:
                continue
            seen.add(href)
            lot_url = href if href.startswith("http") else cls.BASE_URL + href

            # Lot ID
            lot_id_m = re.search(r"/Coin/(\d+)/", href)
            lot_id = lot_id_m.group(1) if lot_id_m else ""

            # Thumbnail image
            img = row.select_one("img[src*='photos.greatcollections']")
            img_url = img.get("src", "") if img else ""
            # Upgrade to higher-res version (replace /NxM/ with /300/x/)
            if img_url:
                img_url = re.sub(r"/\d+/\d+/", "/300/300/", img_url)

            # Full row text for parsing
            row_text = row.get_text(" ", strip=True)

            # Price — several formats:
            #   "Current Bid $X.XX" (live)
            #   "Buy Now $X.XX"     (buy-it-now)
            #   "Sold $X.XX"        (completed, logged-in)
            price_m = re.search(r"\$([\d,]+(?:\.\d{2})?)", row_text)
            price = float(price_m.group(1).replace(",", "")) if price_m else 0.0

            # Status label
            if "Current Bid" in row_text:
                status = "LIVE"
            elif "Buy Now" in row_text:
                status = "BUY NOW"
            elif "Sold" in row_text and is_logged_in:
                status = "SOLD"
            else:
                status = "LIVE"

            # Bid count
            bids_m = re.search(r"(\d+)\s+bid", row_text, re.I)
            bids = bids_m.group(1) if bids_m else ""

            # Time remaining
            time_m = re.search(r"(\d+d,?\s*\d+h|\d+h,?\s*\d+m|Ends?\s+\w+\s+\d+)", row_text, re.I)
            time_left = time_m.group(0).strip() if time_m else ""

            # Detect grading from title
            detected_grade = grade
            grade_m = re.search(
                r'\b(MS|PR|PF|SP|PL|DMPL|AU|XF|EF|VF|F|VG|G|AG|P)\s*[-\s]?(\d{2})\b'
                r'|\b(Proof|Specimen|Gem|Choice|BU|Unc)\b',
                title, re.I)
            if grade_m:
                detected_grade = grade_m.group(0)

            desc_parts = [f"[{status}]", title[:60]]
            if bids:
                desc_parts.append(f"{bids} bids")
            if time_left:
                desc_parts.append(time_left)
            description = " | ".join(desc_parts)

            results.append(AuctionResult(
                source=cls.SOURCE,
                description=description[:100],
                grade=detected_grade,
                holder=holder,
                price=price,
                date="",
                url=lot_url,
            ))
            if len(results) >= 20:
                break

        return results

    @classmethod
    def _fetch_completed_prices(cls, results: List["AuctionResult"],
                                sess) -> List["AuctionResult"]:
        """For LIVE lots with no sold price, attempt to fetch the completed lot page
        if user is logged in. Enriches with realized price and auction end date."""
        if not PLAYWRIGHT_OK:
            return results
        username, _ = CredentialStore.load(cls.SITE_KEY)
        if not username:
            return results
        try:
            browser = PlaywrightLoginManager._ensure_browser()
            ctx = browser.new_context(
                user_agent=cls._HEADERS["User-Agent"],
                locale="en-US",
            )
            # Inject session cookies into playwright context
            for ck in sess.cookies:
                try:
                    ctx.add_cookies([{
                        "name": ck.name, "value": ck.value,
                        "domain": ck.domain or ".greatcollections.com",
                        "path": ck.path or "/",
                    }])
                except Exception:
                    pass
            page = ctx.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )
            for i, result in enumerate(results):
                if i >= 8:  # Limit detail fetches to avoid slowness
                    break
                try:
                    page.goto(result.url, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_timeout(800)

                    # Sold price
                    price_el = page.query_selector("span.price b, .price-block b, span.price")
                    if price_el:
                        price_txt = price_el.inner_text()
                        pm = re.search(r"[\d,]+(?:\.\d{2})?", price_txt)
                        if pm:
                            results[i] = AuctionResult(
                                source=result.source,
                                description=result.description.replace("[LIVE]", "[SOLD]"),
                                grade=result.grade,
                                holder=result.holder,
                                price=float(pm.group(0).replace(",", "")),
                                date=result.date,
                                url=result.url,
                            )

                    # Auction end date
                    hdr = page.query_selector(".auction-header")
                    if hdr:
                        hdr_txt = hdr.inner_text()
                        date_m = re.search(
                            r"(?:Ended?|Sold)\s+\w+,\s+(\w+\s+\d+,\s+\d+)", hdr_txt, re.I)
                        if date_m:
                            results[i] = AuctionResult(
                                source=results[i].source,
                                description=results[i].description,
                                grade=results[i].grade,
                                holder=results[i].holder,
                                price=results[i].price,
                                date=date_m.group(1),
                                url=results[i].url,
                            )
                except Exception as e:
                    log.debug("GC detail fetch failed for %s: %s", result.url, e)
            ctx.close()
        except Exception as e:
            log.warning("GC completed price fetch failed: %s", e)
        return results

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List["AuctionResult"]:
        if not REQUESTS_OK:
            return []
        sess = cls._ensure_session()
        is_logged_in = SessionManager.is_logged_in(cls.SITE_KEY)

        # Build search query — try both with and without grade to get more results
        q_full  = " ".join(filter(None, [year, mint, name, grade, holder]))
        q_basic = " ".join(filter(None, [year, mint, name]))
        url = f"{cls.SEARCH_URL}?mode=product&q={quote_plus(q_full)}"
        url_basic = f"{cls.SEARCH_URL}?mode=product&q={quote_plus(q_basic)}"

        results: List[AuctionResult] = []
        try:
            resp = _retry_get(url, cls.SOURCE, session=sess)
            results = cls._parse_search_html(resp.text, grade, holder, is_logged_in)
            # If few results, fall back to basic query
            if len(results) < 5 and q_basic != q_full:
                resp2 = _retry_get(url_basic, cls.SOURCE, session=sess)
                extra = cls._parse_search_html(resp2.text, grade, holder, is_logged_in)
                seen_urls = {r.url for r in results}
                results += [r for r in extra if r.url not in seen_urls]
        except Exception as e:
            log.warning("Great Collections search error: %s", e)
            return []

        # If logged in and Playwright available, enrich with realized prices
        if is_logged_in and PLAYWRIGHT_OK and results:
            results = cls._fetch_completed_prices(results, sess)

        return results[:20]


class SothebysFileFetcher:
    SOURCE    = "Sotheby's"
    SITE_KEY  = "sothebys"
    LOGIN_URL = "https://www.sothebys.com/en/account/login"

    @staticmethod
    def build_url(name, year, mint, grade, holder) -> str:
        q = " ".join(filter(None, [year, mint, name]))
        return (
            "https://www.sothebys.com/en/results"
            f"?query={quote_plus(q)}&query_type=text&department=coins"
        )

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        sess = SessionManager.session(cls.SITE_KEY)
        if (CredentialStore.has_credentials(cls.SITE_KEY)
                and not SessionManager.is_logged_in(cls.SITE_KEY)):
            ok = _auto_login(sess, cls.SITE_KEY, cls.LOGIN_URL)
            SessionManager.set_logged_in(cls.SITE_KEY, ok)
        url = cls.build_url(name, year, mint, grade, holder)
        resp = _retry_get(url, cls.SOURCE, session=sess)
        results = []
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(
                ".SearchResult, [class*='result-'], [class*='lot-'], "
                "article, .GridView__item, [data-testid*='lot']"
            )[:15]:
                title_el = item.select_one(
                    "h2, h3, [class*='title'], [class*='name'], [data-testid*='title']"
                )
                price_el = item.select_one(
                    "[class*='price'], [class*='estimate'], [class*='hammer'], [data-testid*='price']"
                )
                link_el  = item.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                price    = _parse_price(price_el.get_text()) if price_el else 0.0
                href     = link_el.get("href", "") if link_el else ""
                lot_url  = (
                    ("https://www.sothebys.com" + href)
                    if href.startswith("/") else (href or url)
                )
                results.append(AuctionResult(
                    source=cls.SOURCE, description=title[:80],
                    grade=grade, holder=holder, price=price, date="", url=lot_url,
                ))
        except Exception as e:
            log.warning("Sotheby's parse error: %s", e)
        return results


class CoinstrailFetcher:
    SOURCE   = "Coinstrail"
    SITE_KEY = "coinstrail"
    API_URL  = "https://coinstrail.com/api/lot/p-fast-search"

    @classmethod
    def search(cls, name, year, mint, grade, holder) -> List[AuctionResult]:
        if not REQUESTS_OK:
            return []
        q = " ".join(filter(None, [year, mint, name, grade, holder]))
        url = f"{cls.API_URL}?keyword={quote_plus(q)}&lang=en"
        sess = SessionManager.session(cls.SITE_KEY)
        sess.headers.update({"Referer": "https://coinstrail.com/", "Accept": "application/json, */*"})
        try:
            resp = _retry_get(url, cls.SOURCE, session=sess)
            data = resp.json()
        except Exception as e:
            log.warning("Coinstrail API error: %s", e)
            return []
        results = []
        for doc in data.get("docs", [])[:20]:
            desc = doc.get("description", "").strip()
            if not desc:
                continue
            firm    = doc.get("firm", "")
            auction = doc.get("auction", "")
            cdnm    = re.search(r'CDN:\s*\$([\d,]+\.?\d*)\s*Whsle', desc)
            price   = float(cdnm.group(1).replace(",", "")) if cdnm else 0.0
            lot_id  = doc.get("id", "")
            display = f"[{firm}] {desc}"[:80] if firm else desc[:80]
            results.append(AuctionResult(
                source=cls.SOURCE, description=display,
                grade=grade, holder=holder, price=price,
                date=auction,
                url=f"https://coinstrail.com/lots/{lot_id}" if lot_id else url,
            ))
        return results


class NGCPopFetcher:
    SOURCE    = "NGC"
    SITE_KEY  = "ngc"
    LOGIN_URL = "https://www.ngccoin.com/account/login/"
    POP_URL   = "https://www.ngccoin.com/population-report/"
    CERT_URL  = "https://www.ngccoin.com/certlookup/"

    # Cookie storage for session persistence
    _COOKIE_PATH = os.path.expanduser("~/.numismatic/ngc_session.json")
    # Delay between navigations (seconds) — human-like pacing
    _REQUEST_DELAY = 5.0

    # Shared cached context (reused across calls to keep session alive)
    _ctx_lock: threading.Lock = threading.Lock()
    _ctx = None          # playwright BrowserContext
    _ctx_logged_in: bool = False

    # Anti-detection init script injected into every page
    _STEALTH_SCRIPT = """
        Object.defineProperty(navigator, 'webdriver',    {get: () => undefined});
        Object.defineProperty(navigator, 'plugins',      {get: () => [1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages',    {get: () => ['en-US','en']});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(screen,    'colorDepth',   {get: () => 24});
        window.chrome = {runtime: {}};
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) =>
            params.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : originalQuery(params);
    """

    _UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0.0.0 Safari/537.36")

    @staticmethod
    def build_url(name, year, mint) -> str:
        q = quote_plus(" ".join(filter(None, [year, mint, name])))
        return f"https://www.ngccoin.com/population-report/?q={q}"

    # ── Cookie persistence ────────────────────────────────────────────────────

    @classmethod
    def _save_cookies(cls, ctx) -> None:
        try:
            os.makedirs(os.path.dirname(cls._COOKIE_PATH), exist_ok=True)
            cookies = ctx.cookies()
            with open(cls._COOKIE_PATH, "w") as f:
                json.dump(cookies, f)
            log.debug("NGC: saved %d session cookies", len(cookies))
        except Exception as e:
            log.debug("NGC: cookie save failed: %s", e)

    @classmethod
    def _load_cookies(cls, ctx) -> bool:
        """Load stored cookies into ctx. Returns True if any NGC cookies found."""
        try:
            if not os.path.exists(cls._COOKIE_PATH):
                return False
            with open(cls._COOKIE_PATH) as f:
                cookies = json.load(f)
            ngc_cookies = [c for c in cookies if "ngccoin" in c.get("domain", "")]
            if not ngc_cookies:
                return False
            ctx.add_cookies(ngc_cookies)
            log.debug("NGC: loaded %d stored cookies", len(ngc_cookies))
            return True
        except Exception as e:
            log.debug("NGC: cookie load failed: %s", e)
            return False

    # ── Browser context management ────────────────────────────────────────────

    @classmethod
    def _make_context(cls):
        """Create a fresh stealth browser context."""
        browser = PlaywrightLoginManager._ensure_browser()
        ctx = browser.new_context(
            user_agent=cls._UA,
            locale="en-US",
            timezone_id="America/New_York",
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
            ignore_https_errors=False,
        )
        return ctx

    @classmethod
    def _get_context(cls, force_new: bool = False):
        """Return the cached browser context, recreating if necessary."""
        with cls._ctx_lock:
            if cls._ctx is None or force_new:
                try:
                    if cls._ctx:
                        cls._ctx.close()
                except Exception:
                    pass
                cls._ctx = cls._make_context()
                cls._ctx_logged_in = False
                # Try to restore saved session
                had_cookies = cls._load_cookies(cls._ctx)
                if had_cookies:
                    log.debug("NGC: restored session from disk")
            return cls._ctx, cls._ctx_logged_in

    @classmethod
    def _new_page(cls, ctx):
        """Open a new page in ctx with stealth script pre-injected."""
        page = ctx.new_page()
        page.add_init_script(cls._STEALTH_SCRIPT)
        return page

    # ── Login ─────────────────────────────────────────────────────────────────

    @classmethod
    def _is_logged_in(cls, page) -> bool:
        """Check whether the current page/session shows a logged-in state."""
        try:
            return bool(page.query_selector(
                'a[href*="logout"], a[href*="signout"], '
                '.user-nav__name, #user-nav .logged-in, '
                '[class*="account-nav"], a[href*="/account/"]'
            ))
        except Exception:
            return False

    @classmethod
    def _do_login(cls, page, username: str, password: str) -> bool:
        """Navigate to login page and submit credentials. Returns success."""
        try:
            log.info("NGC: logging in as %s…", username)
            page.goto(cls.LOGIN_URL, wait_until="networkidle", timeout=25000)
            page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))

            # Fill credentials
            page.fill("input[name='Username'], #Username, input[type='email']", username)
            page.wait_for_timeout(400)
            page.fill("input[name='Password'], #Password, input[type='password']", password)
            page.wait_for_timeout(600)

            # Submit
            page.click("button[type='submit'], input[type='submit'], .btn-login")
            page.wait_for_load_state("networkidle", timeout=20000)
            page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))

            ok = cls._is_logged_in(page)
            if ok:
                cls._save_cookies(page.context)
                with cls._ctx_lock:
                    cls._ctx_logged_in = True
            log.info("NGC: login %s", "succeeded" if ok else "uncertain — continuing anyway")
            return ok
        except Exception as e:
            log.warning("NGC: login error: %s", e)
            return False

    # ── Population scraping ────────────────────────────────────────────────────

    @classmethod
    def _extract_populations(cls, page) -> Dict[str, str]:
        """Extract grade → population counts from the fully-rendered NGC pop page."""
        populations: Dict[str, str] = {}

        # Wait for Angular/React data to render — look for any numeric cell content
        for wait_sel in [
            ".ui-grid-row",
            "[ui-grid-row]",
            "table.pop-report tbody tr",
            ".population-table tr",
            "tr[ng-repeat]",
            ".ngc-pop-row",
        ]:
            try:
                page.wait_for_selector(wait_sel, timeout=8000)
                break
            except Exception:
                pass

        # Extra settle time for Angular digest cycle
        page.wait_for_timeout(2000)

        # Strategy 1: Angular ui-grid rows
        rows = page.locator(".ui-grid-row, [ui-grid-row]").all()
        for row in rows[:60]:
            try:
                cells = row.locator(".ui-grid-cell").all()
                texts = [c.inner_text().strip() for c in cells]
                texts = [t for t in texts if t]
                if len(texts) >= 2:
                    grade, pop = texts[0], texts[1]
                    if re.search(r"\d", grade) and re.search(r"\d", pop):
                        populations[grade] = pop
            except Exception:
                pass

        # Strategy 2: standard HTML table (fallback if ui-grid not found)
        if not populations:
            for row in page.locator("table tr").all():
                try:
                    cells = row.locator("td, th").all()
                    texts = [c.inner_text().strip() for c in cells]
                    texts = [t for t in texts if t]
                    if len(texts) >= 2:
                        grade, pop = texts[0], texts[1]
                        if re.search(r"^(MS|PR|PF|SP|AU|EF|XF|VF|F|VG|G|AG|FR|P)[\s\-]?\d{2}",
                                     grade, re.I) and re.search(r"^\d+$", pop):
                            populations[grade] = pop
                except Exception:
                    pass

        # Strategy 3: extract from page text via regex (last resort)
        if not populations:
            try:
                body_text = page.locator("body").inner_text()
                for m in re.finditer(
                    r"((?:MS|PR|PF|SP|AU|EF|XF|VF|F[-\s]?\d{2})[^\n]{0,20}?)\s{2,}(\d{1,6})",
                    body_text
                ):
                    populations[m.group(1).strip()] = m.group(2)
            except Exception:
                pass

        return populations

    # ── Certificate lookup ────────────────────────────────────────────────────

    @classmethod
    def cert_lookup(cls, cert_number: str) -> Dict:
        """Look up a specific NGC certificate number. Returns cert details dict."""
        if not PLAYWRIGHT_OK or not cert_number.strip():
            return {"error": "Playwright required for cert lookup"}
        try:
            ctx, _ = cls._get_context()
            page = cls._new_page(ctx)
            url = f"{cls.CERT_URL}{cert_number.strip()}/"
            page.goto(url, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))

            result: Dict[str, str] = {"url": url}
            for field, selectors in {
                "description": [".cert-coin-name", "h1.coin-name", ".cert-header h1"],
                "grade":       [".cert-grade", ".grade-label", "[class*='grade']"],
                "cert_no":     [".cert-number", "[class*='cert-num']"],
                "designation": [".cert-designation", "[class*='designation']"],
                "population":  [".cert-pop", ".population-count"],
            }.items():
                for sel in selectors:
                    el = page.query_selector(sel)
                    if el:
                        result[field] = el.inner_text().strip()
                        break
            page.close()
            cls._save_cookies(ctx)
            return result
        except Exception as e:
            log.warning("NGC cert lookup error: %s", e)
            return {"error": str(e)}

    # ── Main fetch ─────────────────────────────────────────────────────────────

    @classmethod
    def fetch(cls, name: str, year: str, mint: str) -> Dict:
        url = cls.build_url(name, year, mint)

        if not PLAYWRIGHT_OK:
            return {"url": url, "populations": {},
                    "error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}

        username, password = CredentialStore.load(cls.SITE_KEY)
        q = " ".join(filter(None, [year, mint, name]))

        try:
            ctx, was_logged_in = cls._get_context()
            page = cls._new_page(ctx)

            # Step 1 — login if credentials available and not yet logged in
            if username and password and not was_logged_in:
                cls._do_login(page, username, password)
            else:
                page.goto("https://www.ngccoin.com/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))

            # Step 2 — navigate to population report
            log.info("NGC: navigating to population report for '%s'", q)
            page.goto(cls.POP_URL, wait_until="networkidle", timeout=25000)
            page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))

            # Step 3 — enter search query
            search_selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                "input[ng-model*='search']",
                "input[ng-model*='filter']",
                ".pop-search input",
                "#coinSearch",
                "input[type='search']",
            ]
            searched = False
            for sel in search_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        inp = page.locator(sel).first
                        inp.click()
                        page.wait_for_timeout(500)
                        inp.fill(q)
                        page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))
                        # Try pressing Enter or clicking search button
                        inp.press("Enter")
                        page.wait_for_load_state("networkidle", timeout=12000)
                        page.wait_for_timeout(int(cls._REQUEST_DELAY * 1000))
                        searched = True
                        break
                except Exception:
                    pass

            # Step 4 — wait for population data and extract
            populations = cls._extract_populations(page)

            # Step 5 — save updated cookies for next session
            cls._save_cookies(ctx)
            page.close()

            log.info("NGC: extracted %d population entries for '%s'", len(populations), q)
            error = "" if populations else (
                "No population data found. "
                + ("Try entering NGC credentials via ⚙ Credentials." if not username else
                   "Login may have failed — check credentials.")
            )
            return {"url": url, "populations": populations, "error": error}

        except Exception as e:
            log.warning("NGCPopFetcher.fetch error: %s", e)
            # Invalidate context so next call gets a fresh one
            with cls._ctx_lock:
                cls._ctx = None
                cls._ctx_logged_in = False
            return {"url": url, "populations": {},
                    "error": f"NGC lookup failed: {e}"}


class PCGSPopFetcher:
    SOURCE    = "PCGS"
    SITE_KEY  = "pcgs"
    LOGIN_URL = "https://app.collectors.com/signin?b=PCGS"
    POP_URL   = "https://www.pcgs.com/population"

    @staticmethod
    def build_url(name, year, mint) -> str:
        q = quote_plus(" ".join(filter(None, [year, mint, name])))
        return f"https://www.pcgs.com/population?q={q}"

    @classmethod
    def _fetch_playwright(cls, name: str, year: str, mint: str) -> Dict:
        if not PLAYWRIGHT_OK:
            return {"url": cls.POP_URL, "populations": {}, "error": "playwright not installed"}
        username, password = CredentialStore.load(cls.SITE_KEY)
        try:
            browser = PlaywrightLoginManager._ensure_browser()
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"),
            )
            page = ctx.new_page()

            if username and password:
                try:
                    page.goto(cls.LOGIN_URL, wait_until="networkidle", timeout=20000)
                    # Collectors.com login form
                    for sel in ["input[name='email']", "input[type='email']", "#email"]:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.fill(username)
                            break
                    for sel in ["input[name='password']", "input[type='password']"]:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.fill(password)
                            break
                    page.wait_for_timeout(300)
                    page.locator("button[type='submit']").first.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    log.warning("PCGS login step: %s", e)

            q = " ".join(filter(None, [year, mint, name]))
            pop_url = f"{cls.POP_URL}?q={quote_plus(q)}"
            page.goto(pop_url, wait_until="networkidle", timeout=25000)
            page.wait_for_timeout(2000)

            populations: Dict[str, str] = {}
            for row_sel in ["table tr", ".pop-row", "[class*='pop-row']",
                            "[class*='population']", ".MuiTableRow-root"]:
                rows = page.locator(row_sel).all()
                for row in rows[:60]:
                    try:
                        cells = row.locator("td, th, [class*='cell']").all()
                        if len(cells) >= 2:
                            g = cells[0].inner_text().strip()
                            p = cells[1].inner_text().strip()
                            if g and re.search(r"\d", g):
                                populations[g] = p
                    except Exception:
                        pass
                if populations:
                    break

            ctx.close()
            return {"url": pop_url, "populations": populations,
                    "error": "" if populations else "No population data — add PCGS credentials via ⚙"}
        except Exception as e:
            log.warning("PCGSPopFetcher._fetch_playwright: %s", e)
            return {"url": cls.POP_URL, "populations": {}, "error": str(e)}

    @classmethod
    def fetch(cls, name, year, mint) -> Dict:
        if PLAYWRIGHT_OK:
            return cls._fetch_playwright(name, year, mint)
        url = cls.build_url(name, year, mint)
        if not REQUESTS_OK:
            return {"url": url, "populations": {}, "error": "requests not installed"}
        try:
            resp = _retry_get(url, "PCGS Population")
            data: Dict[str, str] = {}
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.select("table tr")[:40]:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    g, p = cells[0].get_text(strip=True), cells[1].get_text(strip=True)
                    if g and p and re.search(r"\d", g):
                        data[g] = p
            return {"url": url, "populations": data,
                    "error": "" if data else "PCGS population requires JavaScript rendering — install playwright"}
        except FetchError as e:
            return {"url": url, "populations": {}, "error": str(e)}


class PCGSPriceFetcher:
    SITE_KEY = "pcgs"

    @staticmethod
    def build_url(name, year, mint) -> str:
        q = quote_plus(" ".join(filter(None, [year, mint, name])))
        return f"https://www.pcgs.com/prices/?searchquery={q}"

    @classmethod
    def _fetch_playwright(cls, name: str, year: str, mint: str) -> Dict:
        if not PLAYWRIGHT_OK:
            return {"url": "", "prices": {}, "error": "playwright not installed"}
        try:
            browser = PlaywrightLoginManager._ensure_browser()
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"),
            )
            page = ctx.new_page()
            q = " ".join(filter(None, [year, mint, name]))
            url = f"https://www.pcgs.com/prices/?searchquery={quote_plus(q)}"
            page.goto(url, wait_until="networkidle", timeout=25000)
            page.wait_for_timeout(2000)

            prices: Dict[str, str] = {}
            h1 = page.locator("h1, h2, [class*='coin-name'], [class*='coin-header']").first
            try:
                coin_name = h1.inner_text().strip()
                if coin_name:
                    prices["__coin__"] = coin_name[:80]
            except Exception:
                pass

            for row_sel in ["table tr", ".price-row", ".MuiTableRow-root", "[class*='price-row']"]:
                rows = page.locator(row_sel).all()
                for row in rows[:50]:
                    try:
                        cells = row.locator("td, th").all()
                        if len(cells) >= 2:
                            g = cells[0].inner_text().strip()
                            p = cells[1].inner_text().strip()
                            if g and p:
                                prices[g] = p
                    except Exception:
                        pass
                if len(prices) > 1:
                    break

            ctx.close()
            return {"url": url, "prices": prices,
                    "error": "" if len(prices) > 1 else "No price data returned"}
        except Exception as e:
            return {"url": "", "prices": {}, "error": str(e)}

    @classmethod
    def fetch(cls, name, year, mint) -> Dict:
        if PLAYWRIGHT_OK:
            return cls._fetch_playwright(name, year, mint)
        url = cls.build_url(name, year, mint)
        if not REQUESTS_OK:
            return {"url": url, "prices": {}, "error": "requests not installed"}
        try:
            resp = _retry_get(url, "PCGS Prices")
            prices: Dict[str, str] = {}
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.select("table tr")[:40]:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    g, p = cells[0].get_text(strip=True), cells[1].get_text(strip=True)
                    if g and p:
                        prices[g] = p
            header = soup.select_one("h1, h2, [class*='coin-name']")
            if header:
                prices["__coin__"] = header.get_text(strip=True)[:80]
            return {"url": url, "prices": prices, "error": ""}
        except FetchError as e:
            return {"url": url, "prices": {}, "error": str(e)}


class NGCCertFetcher:
    """
    Looks up an NGC certificate number using async Playwright (headless Chromium).
    NGC's cert page is Angular-rendered — plain requests returns an empty shell.
    Falls back to requests+BeautifulSoup if Playwright is unavailable.
    """
    _BASE_URL  = "https://www.ngccoin.com/certlookup/"
    _NAV_WAIT  = 2500   # ms after navigation before scraping

    @classmethod
    def fetch(cls, cert: str) -> Dict:
        cert = cert.strip()
        url  = f"{cls._BASE_URL}{quote_plus(cert)}/"
        if not cert:
            return {"url": url, "cert": cert, "data": {}, "error": "Cert number required"}
        if PLAYWRIGHT_OK:
            try:
                return PlaywrightRunner.run(cls._fetch_async(cert), timeout=90)
            except Exception as e:
                log.warning("NGCCertFetcher playwright failed: %s — falling back", e)
        # Fallback: plain HTTP (works only if NGC ever serves static HTML)
        return cls._fetch_requests(cert, url)

    @classmethod
    async def _fetch_async(cls, cert: str) -> Dict:
        url = f"{cls._BASE_URL}{quote_plus(cert)}/"
        ctx = None
        try:
            page, ctx = await PlaywrightRunner.stealth_page()

            # Navigate and wait for Angular to render
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(cls._NAV_WAIT)

            # Wait for cert data or "not found" message
            for ready_sel in [
                ".certlookup-result", ".cert-lookup-result",
                ".ngc-cert-detail",   "[class*='cert-result']",
                ".no-results",        "[class*='not-found']",
                "h1",                 ".cert-lookup",
            ]:
                try:
                    await page.wait_for_selector(ready_sel, timeout=5000)
                    break
                except Exception:
                    pass

            await page.wait_for_timeout(500)
            data = await cls._extract(page)
            images = await cls._extract_images(page)
            await ctx.close()

            return {
                "url":    url,
                "cert":   cert,
                "data":   data,
                "images": images,
                "error":  "" if data else "No certificate data found — verify the cert number",
            }
        except Exception as e:
            log.warning("NGCCertFetcher._fetch_async: %s", e)
            if ctx:
                try: await ctx.close()
                except Exception: pass
            return {"url": url, "cert": cert, "data": {}, "images": [], "error": str(e)}

    @classmethod
    async def _extract(cls, page) -> Dict[str, str]:
        data: Dict[str, str] = {}

        # Strategy 1 — named field selectors (NGC uses Angular binding names)
        field_map = {
            "Coin":          [".certlookup-coin-name", ".cert-coin-name",
                              "h1.coin-name",          "[class*='coinName']",
                              "[class*='coin-name']",  ".ngc-coin"],
            "Grade":         [".certlookup-grade",     ".cert-grade",
                              "[class*='gradeValue']", "[class*='grade-label']",
                              ".grade",                "[class*='certGrade']"],
            "Grade Modifier":["[class*='gradeModifier']", "[class*='grade-modifier']",
                              ".cert-designation",     "[class*='designation']"],
            "Year":          ["[class*='yearValue']",  "[class*='cert-year']",
                              ".cert-date",            "[class*='coinYear']"],
            "Mint":          ["[class*='mintMark']",   "[class*='mint-mark']",
                              ".cert-mint",            "[class*='mint']"],
            "Denomination":  ["[class*='denomination']",".cert-denom"],
            "Description":   ["[class*='coinDesc']",   ".cert-description",
                              "[class*='description']"],
            "Variety":       ["[class*='variety']",    ".cert-variety"],
            "Pop at Grade":  ["[class*='popGrade']",   ".pop-grade",
                              "[class*='popAtGrade']", "[class*='certPop']"],
            "Pop Finer":     ["[class*='popFiner']",   ".pop-finer"],
            "Cert #":        ["[class*='certNumber']", ".cert-number",
                              "[class*='cert-num']"],
        }
        for label, selectors in field_map.items():
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        txt = (await el.inner_text()).strip()
                        if txt and txt.lower() not in ("", "n/a", "--"):
                            data[label] = txt
                            break
                except Exception:
                    pass

        # Strategy 2 — <dl><dt>/<dd> pairs (common in Angular detail views)
        if len(data) < 3:
            try:
                dts = await page.locator("dt").all()
                for dt in dts:
                    try:
                        key = (await dt.inner_text()).strip().rstrip(":")
                        dd  = page.locator(f"dt:has-text('{key}') + dd")
                        if await dd.count() > 0:
                            val = (await dd.first.inner_text()).strip()
                            if key and val:
                                data.setdefault(key, val)
                    except Exception:
                        pass
            except Exception:
                pass

        # Strategy 3 — generic label/value pairs inside result containers
        if len(data) < 3:
            try:
                container = page.locator(
                    ".certlookup-result, .cert-lookup-result, "
                    ".ngc-cert-detail, [class*='cert-result'], "
                    "[class*='certlookup']"
                ).first
                if await container.count() > 0:
                    for row in await container.locator(
                        "[class*='label'], [class*='field'], span, p, li"
                    ).all():
                        try:
                            txt = (await row.inner_text()).strip()
                            if ":" in txt:
                                k, _, v = txt.partition(":")
                                k, v = k.strip(), v.strip()
                                if k and v and len(k) < 50:
                                    data.setdefault(k, v)
                        except Exception:
                            pass
            except Exception:
                pass

        # Strategy 4 — regex over full page text (last resort)
        if len(data) < 2:
            try:
                body = (await page.locator("body").inner_text()).strip()
                for m in re.finditer(
                    r"(Cert(?:ificate)?[#\s]*No\.?|Grade|Year|Mint|Denomination|"
                    r"Variety|Population|Description)\s*[:\-]\s*([^\n\r]{1,80})",
                    body, re.I
                ):
                    data.setdefault(m.group(1).strip(), m.group(2).strip())
            except Exception:
                pass

        return data

    @classmethod
    async def _extract_images(cls, page) -> List[str]:
        # Scroll to trigger lazy-loaded images then scroll back
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)
        except Exception:
            pass

        try:
            raw = await page.evaluate("""() => {
                const ATTRS = ['src','data-src','data-lazy','data-lazy-src',
                               'data-original','data-image','ng-src'];
                const NGC_DOMAINS = ['ngccoin.com','ngc-image','numisproxy','coinimages',
                                     'ngccert','certimages'];
                const seen = new Set();
                const urls = [];
                const base = 'https://www.ngccoin.com';

                function norm(u) {
                    if (!u) return '';
                    u = u.trim().split(' ')[0];  // handle srcset fragments
                    if (u.startsWith('//')) return 'https:' + u;
                    if (u.startsWith('/')) return base + u;
                    return u;
                }
                function push(u) {
                    if (u && u.startsWith('http') && !seen.has(u)) {
                        seen.add(u); urls.push(u);
                    }
                }

                // Priority: known coin-image selectors
                const COIN_SELS = [
                    '[class*="cert-image"] img', '[class*="coin-image"] img',
                    '.obverse img', '.reverse img', '[class*="certlookup"] img',
                    '[class*="cert-detail"] img', '[class*="ngc-cert"] img',
                    'img[alt*="obverse" i]', 'img[alt*="reverse" i]',
                ];
                for (const sel of COIN_SELS) {
                    for (const img of document.querySelectorAll(sel)) {
                        for (const attr of ATTRS) push(norm(img.getAttribute(attr)));
                    }
                }

                // Fallback: any img on an NGC domain
                if (urls.length < 2) {
                    for (const img of document.querySelectorAll('img')) {
                        for (const attr of ATTRS) {
                            const u = norm(img.getAttribute(attr));
                            if (u && NGC_DOMAINS.some(d => u.includes(d))) push(u);
                        }
                    }
                }
                return urls.slice(0, 4);
            }""")
            if raw:
                return raw
        except Exception:
            pass

        # Last-resort: attribute-by-attribute locator scan
        urls: List[str] = []
        for sel in ["[class*='cert-image'] img", "[class*='coin-image'] img",
                    ".obverse img", ".reverse img", ".certlookup img"]:
            try:
                for el in await page.locator(sel).all():
                    for attr in ["src", "data-src", "data-lazy", "ng-src"]:
                        raw_src = await el.get_attribute(attr) or ""
                        if raw_src.startswith("//"):
                            raw_src = "https:" + raw_src
                        if raw_src and raw_src.startswith("http") and raw_src not in urls:
                            urls.append(raw_src)
            except Exception:
                pass
        return urls[:4]

    @classmethod
    def _fetch_requests(cls, cert: str, url: str) -> Dict:
        if not REQUESTS_OK:
            return {"url": url, "cert": cert, "data": {}, "images": [],
                    "error": "requests not installed"}
        try:
            resp = _retry_get(url, "NGC Cert")
            data: Dict[str, str] = {}
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.select("tr, [class*='cert-row'], [class*='detail-row']"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    k = cells[0].get_text(strip=True).rstrip(":")
                    v = cells[1].get_text(strip=True)
                    if k and v:
                        data[k] = v
            for dt in soup.find_all("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    data[dt.get_text(strip=True).rstrip(":")] = dd.get_text(strip=True)
            return {"url": url, "cert": cert, "data": data, "images": [], "error": ""}
        except FetchError as e:
            return {"url": url, "cert": cert, "data": {}, "images": [], "error": str(e)}


class PCGSCertFetcher:
    """
    Looks up a PCGS certificate number using async Playwright.
    PCGS cert pages are React-rendered — requests returns an empty shell.
    Falls back to requests+BeautifulSoup if Playwright is unavailable.
    """
    _BASE_URL = "https://www.pcgs.com/cert/"
    _API_URL  = "https://www.pcgs.com/api/cert/"   # JSON API (if available)
    _NAV_WAIT = 3000   # ms — React hydration is slower than Angular

    @classmethod
    def fetch(cls, cert: str) -> Dict:
        cert = cert.strip()
        url  = f"{cls._BASE_URL}{quote_plus(cert)}"
        if not cert:
            return {"url": url, "cert": cert, "data": {}, "error": "Cert number required"}
        if PLAYWRIGHT_OK:
            try:
                return PlaywrightRunner.run(cls._fetch_async(cert), timeout=90)
            except Exception as e:
                log.warning("PCGSCertFetcher playwright failed: %s — falling back", e)
        return cls._fetch_requests(cert, url)

    @classmethod
    async def _fetch_async(cls, cert: str) -> Dict:
        url = f"{cls._BASE_URL}{quote_plus(cert)}"
        ctx = None
        try:
            page, ctx = await PlaywrightRunner.stealth_page()

            # Intercept XHR/fetch responses to grab JSON cert data directly
            json_cert: Dict = {}
            async def _on_response(resp):
                nonlocal json_cert
                if not json_cert and "pcgs.com" in resp.url and resp.status == 200:
                    if any(k in resp.url for k in ("/cert/", "/api/", "/certlookup")):
                        try:
                            ct = resp.headers.get("content-type", "")
                            if "json" in ct:
                                body = await resp.json()
                                if isinstance(body, dict) and (
                                    body.get("coinName") or body.get("grade") or
                                    body.get("certNumber") or body.get("coinDetail")
                                ):
                                    json_cert = body
                        except Exception:
                            pass
            page.on("response", _on_response)

            await page.goto(url, wait_until="networkidle", timeout=35000)
            await page.wait_for_timeout(cls._NAV_WAIT)

            # Wait for React hydration
            for ready_sel in [
                "[class*='CertDetail']", "[class*='cert-detail']",
                "[class*='CoinDetail']", "[class*='pcgs-cert']",
                ".cert-info",            ".coin-info",
                "h1",                    "[class*='grade']",
                "[class*='notFound']",   ".not-found",
            ]:
                try:
                    await page.wait_for_selector(ready_sel, timeout=5000)
                    break
                except Exception:
                    pass

            await page.wait_for_timeout(500)

            # Prefer JSON intercepted from XHR
            data = cls._parse_json_cert(json_cert) if json_cert else {}

            # Scrape DOM if JSON didn't give us enough
            if len(data) < 3:
                data = await cls._extract(page)

            images = await cls._extract_images(page)
            await ctx.close()

            return {
                "url":    url,
                "cert":   cert,
                "data":   data,
                "images": images,
                "error":  "" if data else "No certificate data found — verify the cert number",
            }
        except Exception as e:
            log.warning("PCGSCertFetcher._fetch_async: %s", e)
            if ctx:
                try: await ctx.close()
                except Exception: pass
            return {"url": url, "cert": cert, "data": {}, "images": [], "error": str(e)}

    @classmethod
    def _parse_json_cert(cls, body: dict) -> Dict[str, str]:
        """Parse JSON cert API response into a flat label→value dict."""
        detail = body.get("coinDetail") or body
        def g(*keys):
            for k in keys:
                v = detail.get(k)
                if v and str(v).strip() not in ("", "0", "None"):
                    return str(v).strip()
            return ""
        data: Dict[str, str] = {}
        for label, keys in [
            ("Coin",          ["coinName",   "name",       "title"]),
            ("Year",          ["year",       "coinYear",   "date"]),
            ("Mint",          ["mintMark",   "mint",       "mintCity"]),
            ("Denomination",  ["denomination","denom"]),
            ("Grade",         ["grade",      "gradeText",  "certGrade"]),
            ("Designation",   ["designation","gradeModifier"]),
            ("Variety",       ["variety",    "varietyName"]),
            ("Mintage",       ["mintage",    "totalMintage"]),
            ("Pop at Grade",  ["popGrade",   "popAtGrade", "gradePopulation"]),
            ("Pop Finer",     ["popFiner",   "finerPopulation"]),
            ("Price Guide",   ["priceGuide", "gradePrice", "value"]),
            ("Cert #",        ["certNumber", "certNo",     "serialNumber"]),
            ("Description",   ["description","coinDescription"]),
        ]:
            v = g(*keys)
            if v:
                data[label] = v
        return data

    @classmethod
    async def _extract(cls, page) -> Dict[str, str]:
        data: Dict[str, str] = {}

        # Strategy 1 — PCGS-specific React class selectors
        field_map = {
            "Coin":         ["[class*='CoinName']",   "[class*='coin-name']",
                             "h1",                    "[class*='coinName']"],
            "Grade":        ["[class*='Grade']:not([class*='Pop']):not([class*='Price'])",
                             "[class*='gradeText']",  ".grade-label",
                             "[class*='certGrade']"],
            "Designation":  ["[class*='Designation']","[class*='designation']",
                             "[class*='gradeModifier']"],
            "Year":         ["[class*='Year']",        "[class*='coinYear']",
                             "[class*='year']"],
            "Mint":         ["[class*='MintMark']",   "[class*='mint-mark']",
                             "[class*='mintMark']"],
            "Denomination": ["[class*='Denomination']","[class*='denom']"],
            "Variety":      ["[class*='Variety']",    "[class*='variety']"],
            "Mintage":      ["[class*='Mintage']",    "[class*='mintage']"],
            "Pop at Grade": ["[class*='PopGrade']",   "[class*='popAtGrade']",
                             "[class*='pop-grade']"],
            "Pop Finer":    ["[class*='PopFiner']",   "[class*='pop-finer']"],
            "Price Guide":  ["[class*='PriceGuide']", "[class*='price-guide']",
                             "[class*='gradePrice']"],
            "Cert #":       ["[class*='CertNumber']", "[class*='cert-number']",
                             "[class*='certNumber']"],
        }
        for label, selectors in field_map.items():
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        txt = (await el.inner_text()).strip()
                        if txt and txt.lower() not in ("", "n/a", "--", "0"):
                            data[label] = txt
                            break
                except Exception:
                    pass

        # Strategy 2 — <dl><dt>/<dd> pairs
        if len(data) < 3:
            try:
                for dt in await page.locator("dt").all():
                    try:
                        key = (await dt.inner_text()).strip().rstrip(":")
                        dd  = page.locator(f"dt:has-text('{key}') + dd")
                        if await dd.count() > 0:
                            val = (await dd.first.inner_text()).strip()
                            if key and val:
                                data.setdefault(key, val)
                    except Exception:
                        pass
            except Exception:
                pass

        # Strategy 3 — table rows inside cert container
        if len(data) < 3:
            try:
                for row in await page.locator("table tr").all():
                    try:
                        cells = await row.locator("td, th").all()
                        if len(cells) >= 2:
                            k = (await cells[0].inner_text()).strip().rstrip(":")
                            v = (await cells[1].inner_text()).strip()
                            if k and v and len(k) < 60:
                                data.setdefault(k, v)
                    except Exception:
                        pass
            except Exception:
                pass

        # Strategy 4 — regex over page body text
        if len(data) < 2:
            try:
                body = (await page.locator("body").inner_text()).strip()
                for m in re.finditer(
                    r"(Cert(?:ificate)?[#\s]*No\.?|Grade|Year|Mint(?:\s*Mark)?|"
                    r"Denomination|Variety|Mintage|Population|Price\s*Guide|"
                    r"Designation)\s*[:\-]\s*([^\n\r]{1,80})",
                    body, re.I
                ):
                    data.setdefault(m.group(1).strip(), m.group(2).strip())
            except Exception:
                pass

        return data

    @classmethod
    async def _extract_images(cls, page) -> List[str]:
        # Scroll to trigger lazy-loaded images then scroll back
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)
        except Exception:
            pass

        try:
            raw = await page.evaluate("""() => {
                const ATTRS = ['src','data-src','data-lazy','data-lazy-src',
                               'data-original','data-image','data-img'];
                const PCGS_DOMAINS = ['pcgsimages.com','pcgs.com','cloudfront.net',
                                      'certimages','coinimages','pcgscert'];
                const seen = new Set();
                const urls = [];
                const base = 'https://www.pcgs.com';

                function norm(u) {
                    if (!u) return '';
                    u = u.trim().split(' ')[0];
                    if (u.startsWith('//')) return 'https:' + u;
                    if (u.startsWith('/')) return base + u;
                    return u;
                }
                function push(u) {
                    if (u && u.startsWith('http') && !seen.has(u)) {
                        seen.add(u); urls.push(u);
                    }
                }

                const COIN_SELS = [
                    '[class*="CertImage"] img', '[class*="cert-image"] img',
                    '[class*="CoinImage"] img', '[class*="obverse"] img',
                    '[class*="reverse"] img',   '[class*="coin-photo"] img',
                    '[class*="CoinPhoto"] img', '[class*="certPhoto"] img',
                    'img[alt*="obverse" i]', 'img[alt*="reverse" i]',
                    'img[alt*="cert" i]',
                ];
                for (const sel of COIN_SELS) {
                    for (const img of document.querySelectorAll(sel)) {
                        for (const attr of ATTRS) push(norm(img.getAttribute(attr)));
                    }
                }

                // Fallback: any img from a PCGS image domain
                if (urls.length < 2) {
                    for (const img of document.querySelectorAll('img')) {
                        for (const attr of ATTRS) {
                            const u = norm(img.getAttribute(attr));
                            if (u && PCGS_DOMAINS.some(d => u.includes(d))) push(u);
                        }
                    }
                }
                return urls.slice(0, 4);
            }""")
            if raw:
                return raw
        except Exception:
            pass

        # Last-resort: attribute-by-attribute locator scan
        urls: List[str] = []
        for sel in ["[class*='CertImage'] img", "[class*='cert-image'] img",
                    "[class*='CoinImage'] img", "[class*='obverse'] img",
                    "[class*='reverse'] img",   "[class*='coin-photo'] img"]:
            try:
                for el in await page.locator(sel).all():
                    for attr in ["src", "data-src", "data-lazy", "data-original"]:
                        raw_src = await el.get_attribute(attr) or ""
                        if raw_src.startswith("//"):
                            raw_src = "https:" + raw_src
                        if raw_src and raw_src.startswith("http") and raw_src not in urls:
                            urls.append(raw_src)
            except Exception:
                pass
        return urls[:4]

    @classmethod
    def _fetch_requests(cls, cert: str, url: str) -> Dict:
        if not REQUESTS_OK:
            return {"url": url, "cert": cert, "data": {}, "images": [],
                    "error": "requests not installed"}
        try:
            resp = _retry_get(url, "PCGS Cert")
            data: Dict[str, str] = {}
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.select("tr, [class*='cert'], [class*='detail']"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    k = cells[0].get_text(strip=True).rstrip(":")
                    v = cells[1].get_text(strip=True)
                    if k and v:
                        data[k] = v
            for dt in soup.find_all("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    data[dt.get_text(strip=True).rstrip(":")] = dd.get_text(strip=True)
            return {"url": url, "cert": cert, "data": data, "images": [], "error": ""}
        except FetchError as e:
            return {"url": url, "cert": cert, "data": {}, "images": [], "error": str(e)}


class LotDetailFetcher:
    @classmethod
    def fetch(cls, url: str, source: str) -> Dict:
        if not REQUESTS_OK or not url:
            return {"url": url, "data": {}, "error": "no URL"}
        site_key = source.lower().replace("'", "").replace(" ", "")
        sess = SessionManager.session(site_key) if site_key in SITES else None
        try:
            resp = _retry_get(url, source, session=sess)
            data: Dict[str, str] = {}
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                extractors = [
                    ("Title",       "h1, h2, .lot-title, [class*='lot-name'], [class*='title']"),
                    ("Grade",       "[class*='grade'], .grade, [class*='pcgs'], [class*='ngc']"),
                    ("Price",       "[class*='price'], [class*='hammer'], [class*='realized'], "
                                    "[class*='sold'], .bid"),
                    ("Estimate",    "[class*='estimate'], [class*='pre-sale']"),
                    ("Date",        "time, [class*='date'], .sale-date, [class*='end-date']"),
                    ("Lot #",       "[class*='lot-num'], .lot-number, [class*='lotnumber']"),
                    ("Description", ".lot-description, [class*='description'], "
                                    "[class*='lot-desc'], article p"),
                ]
                for label, sel in extractors:
                    el = soup.select_one(sel)
                    if el:
                        txt = el.get_text(strip=True)
                        if txt:
                            data[label] = txt[:300]
                # Fallback: main body text excerpt
                if len(data) <= 1:
                    body = soup.find("body")
                    if body:
                        data["Page text"] = " ".join(body.get_text().split())[:600]
            except Exception as e:
                log.warning("Lot detail parse: %s", e)
            return {"url": url, "data": data, "source": source, "error": ""}
        except FetchError as e:
            return {"url": url, "data": {}, "source": source, "error": str(e)}


# ── Coin image fetcher ────────────────────────────────────────────────────────

class CoinImageFetcher:
    _IMG_H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                             "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

    @classmethod
    def fetch_urls(cls, result: "AuctionResult") -> List[str]:
        """Returns up to 2 image URLs (obverse, reverse) for a result."""
        if not REQUESTS_OK:
            return []
        url = result.url or ""
        try:
            # Coinstrail / Heritage lots have images in the detail API
            if "coinstrail.com/lots/" in url:
                lot_id = url.rstrip("/").split("/")[-1]
                r = requests.get(
                    f"https://coinstrail.com/api/lot/{lot_id}?lang=en",
                    headers={**cls._IMG_H, "Accept": "application/json", "Referer": "https://coinstrail.com/"},
                    timeout=8)
                if r.status_code == 200:
                    images = r.json().get("lot", {}).get("images", [])
                    return [img.get("large", img.get("medium", "")) for img in images[:2] if img.get("large") or img.get("medium")]
            # eBay — extract first product image from listing page
            if "ebay.com/itm/" in url:
                r = requests.get(url, headers=cls._IMG_H, timeout=8)
                if r.status_code == 200:
                    import re as _re
                    imgs = _re.findall(r'"(?:mainImageUrl|imageUrl|originalImgUrl)"\s*:\s*"([^"]+)"', r.text)
                    return [imgs[0]] if imgs else []
            # Heritage direct lot — extract image from ha.com page
            if "ha.com/itm/" in url:
                r = requests.get(url, headers=cls._IMG_H, timeout=8)
                if r.status_code == 200:
                    from bs4 import BeautifulSoup as _BS
                    soup = _BS(r.text, "html.parser")
                    img = soup.select_one(".lot-images img, .slick-slide img, #lot-image img")
                    if img:
                        src = img.get("src") or img.get("data-src") or ""
                        if src and src.startswith("http"):
                            return [src]
        except Exception as e:
            log.debug("CoinImageFetcher.fetch_urls: %s", e)
        return []

    @classmethod
    def load_image(cls, url: str, size: int = 200) -> "Optional[ImageTk.PhotoImage]":
        """Downloads an image URL and returns a resized Tk PhotoImage, or None."""
        if not PIL_OK or not url:
            return None
        try:
            r = requests.get(url, headers=cls._IMG_H, timeout=10)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                pil_img = PILImage.open(BytesIO(r.content)).convert("RGB")
                pil_img.thumbnail((size, size), PILImage.LANCZOS)
                # White background canvas — Swiss Modern: clean, no decoration
                bg = PILImage.new("RGB", (size, size), (244, 244, 244))
                x = (size - pil_img.width)  // 2
                y = (size - pil_img.height) // 2
                bg.paste(pil_img, (x, y))
                return ImageTk.PhotoImage(bg)
        except Exception as e:
            log.debug("CoinImageFetcher.load_image: %s", e)
        return None


# ── World Coin Catalog ────────────────────────────────────────────────────────

# Google Drive folder that contains all coin catalog PDFs
_GDRIVE_FOLDER_ID = "1mzLkLwW-3MMssJAksr6jPQMUyzf99epy"
_CATALOG_LOCAL_DIR = os.path.expanduser("~/.numismatic/catalogs/Coin_Catalogs")

# Only read catalogs from the local mirror of the Google Drive folder
# (never from iCloud Desktop / Downloads / Documents)
_CATALOG_SEARCH_DIRS = [
    _CATALOG_LOCAL_DIR,
    os.path.expanduser("~/.numismatic/catalogs"),
]

_CATALOG_DISCOVER_DIRS = [
    _CATALOG_LOCAL_DIR,
    os.path.expanduser("~/.numismatic/catalogs"),
]

def _discover_catalogs() -> Dict[str, str]:
    """
    Scan NUMIS_IQ catalog directories for coin catalog PDFs.
    Returns {label: path} for every readable PDF found.
    """
    seen: Dict[str, str] = {}
    search_dirs = list(_CATALOG_DISCOVER_DIRS)
    # One level of subdirectories within NUMIS_IQ
    for base in list(search_dirs):
        if not os.path.isdir(base):
            continue
        try:
            for sub in os.listdir(base):
                subpath = os.path.join(base, sub)
                if os.path.isdir(subpath) and sub not in ('__pycache__', '.git'):
                    if subpath not in search_dirs:
                        search_dirs.append(subpath)
        except OSError:
            pass
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        try:
            fnames = os.listdir(d)
        except OSError:
            continue
        for fname in fnames:
            if not fname.lower().endswith(".pdf"):
                continue
            if fname.startswith("."):
                continue
            full_path = os.path.join(d, fname)
            label = os.path.splitext(fname)[0]
            label = re.sub(r'[_-]compress$', '', label, flags=re.I)
            label = re.sub(r'[_\-]+', ' ', label).strip()
            if label not in seen:
                seen[label] = full_path
    return seen

def _find_catalog(filename: str) -> str:
    for d in _CATALOG_SEARCH_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return os.path.join(_CATALOG_SEARCH_DIRS[0], filename)

_CATALOG_PATHS: Dict[str, str] = {
    "krause 1701-1800":    _find_catalog("krause-world-coins-1701-1800-5-edition_compress.pdf"),
    "krause 1601-1700":    _find_catalog("coins-world-krause-standard-catalog-of-world-coins-1601-1700_compress.pdf"),
    "unusual world coins": _find_catalog("unusual-world-coins-3rd-edition_compress.pdf"),
    "world coins 2018":    _find_catalog("world-coins-2018_compress.pdf"),
    "errores acunacion":   _find_catalog("Errores de Acuñacion.pdf"),
}
_WORLD_DB_PATH = os.path.expanduser("~/.numismatic/world_coins.db")

_WORLD_DB_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS coins (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        catalog     TEXT,
        country     TEXT,
        km_number   TEXT,
        denomination TEXT,
        metal       TEXT,
        page_number INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS coin_prices (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        coin_id   INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        date_year TEXT,
        mintage   TEXT,
        vg        TEXT,
        f_grade   TEXT,
        vf        TEXT,
        xf        TEXT,
        unc       TEXT,
        ms63      TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS catalog_meta (
        catalog     TEXT PRIMARY KEY,
        pages_done  INTEGER DEFAULT 0,
        total_pages INTEGER DEFAULT 0,
        done        INTEGER DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS idx_wc_country ON coins(country)",
    "CREATE INDEX IF NOT EXISTS idx_wc_km      ON coins(km_number)",
    "CREATE INDEX IF NOT EXISTS idx_wc_denom   ON coins(denomination)",
]


# ── AI Coin Vision Identifier ─────────────────────────────────────────────────

class CoinVisionIdentifier:
    """
    Token-efficient Claude vision coin identifier.

    Strategy:
    - Compress every image to ≤512px JPEG q72 before sending (~170 img tokens).
    - Use claude-haiku (fastest/cheapest) by default.
    - Auto-upgrade to claude-sonnet if haiku confidence < UPGRADE_THRESHOLD.
    - Cache results by SHA-256 of compressed bytes; skips API entirely on re-use.
    - Batch API: identify_batch() sends N coins in one message (1 call instead of N).
    """

    # Fast/cheap model for standard identification
    MODEL_FAST   = "claude-haiku-4-5-20251001"
    # Higher-quality model used only when haiku is not confident
    MODEL_DETAIL = "claude-sonnet-4-6"

    # Upgrade to detail model when haiku confidence falls below this
    UPGRADE_THRESHOLD = 0.55

    # Image compression settings — 512px keeps image tokens at minimum (170)
    _MAX_PX  = 512
    _JPEG_Q  = 72

    # In-memory result cache (hash → result dict); max 100 entries
    _cache: Dict[str, dict] = {}
    _CACHE_MAX = 100

    # Compact prompt — minimal tokens, JSON schema only
    _PROMPT = (
        "Expert numismatist. Identify this coin. Return ONLY valid JSON, no other text:\n"
        '{"coin_name":"","country":"","year":"","mint":"",'
        '"denomination":"","km_number":"","metal":"",'
        '"grade_estimate":"","obverse_desc":"","reverse_desc":"",'
        '"key_features":[],"confidence":0.0,"notes":""}\n'
        "Empty string for unknown fields. confidence 0.0-1.0."
    )

    # Batch prompt wrapper
    _BATCH_PROMPT = (
        "Expert numismatist. Identify each coin image IN ORDER. "
        "Return ONLY a valid JSON array — one object per coin:\n"
        '[{"coin_name":"","country":"","year":"","mint":"",'
        '"denomination":"","km_number":"","metal":"",'
        '"grade_estimate":"","obverse_desc":"","reverse_desc":"",'
        '"key_features":[],"confidence":0.0,"notes":""}]\n'
        "Empty string for unknown fields. confidence 0.0-1.0."
    )

    @classmethod
    def _get_api_key(cls) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            _, key = CredentialStore.load("anthropic")
        return key.strip()

    @classmethod
    def _compress(cls, image_path: str) -> Tuple[bytes, str]:
        """
        Return (jpeg_bytes, media_type).
        Always outputs JPEG ≤512px at q72 to minimise image tokens.
        Falls back to raw bytes if PIL unavailable.
        """
        from io import BytesIO as _BytesIO
        with open(image_path, "rb") as f:
            raw = f.read()

        if not PIL_OK:
            # Detect type and return raw — no compression available
            if raw[:4] == b'\x89PNG':
                return raw, "image/png"
            return raw, "image/jpeg"

        img = PILImage.open(_BytesIO(raw)).convert("RGB")
        if max(img.width, img.height) > cls._MAX_PX:
            img.thumbnail((cls._MAX_PX, cls._MAX_PX), PILImage.LANCZOS)

        buf = _BytesIO()
        img.save(buf, "JPEG", quality=cls._JPEG_Q, optimize=True)
        return buf.getvalue(), "image/jpeg"

    @classmethod
    def _b64_image_block(cls, jpeg_bytes: bytes, media_type: str = "image/jpeg") -> dict:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(jpeg_bytes).decode(),
            },
        }

    @classmethod
    def _parse_json(cls, text: str) -> Optional[dict]:
        try:
            s = text.index("{"); e = text.rindex("}") + 1
            return json.loads(text[s:e])
        except (ValueError, json.JSONDecodeError):
            return None

    @classmethod
    def _cache_get(cls, key: str) -> Optional[dict]:
        return cls._cache.get(key)

    @classmethod
    def _cache_put(cls, key: str, result: dict):
        if len(cls._cache) >= cls._CACHE_MAX:
            cls._cache.pop(next(iter(cls._cache)))
        cls._cache[key] = result

    @classmethod
    def identify(cls, image_path: str) -> dict:
        """Identify a single coin image. Uses cache + haiku; upgrades to sonnet if needed."""
        if not ANTHROPIC_OK:
            raise FetchError("anthropic package not installed — run: pip install anthropic")
        api_key = cls._get_api_key()
        if not api_key:
            raise FetchError(
                "Anthropic API key not configured.\n"
                "Open CREDENTIALS → Anthropic (AI Vision) and paste your key in Password."
            )

        jpeg, mime = cls._compress(image_path)
        cache_key  = hashlib.sha256(jpeg).hexdigest()

        cached = cls._cache_get(cache_key)
        if cached:
            return dict(cached)

        client   = _anthropic.Anthropic(api_key=api_key)
        img_block = cls._b64_image_block(jpeg, mime)

        # Pass 1 — fast/cheap haiku
        msg = client.messages.create(
            model=cls.MODEL_FAST,
            max_tokens=512,
            messages=[{"role": "user", "content": [img_block, {"type": "text", "text": cls._PROMPT}]}],
        )
        result = cls._parse_json(msg.content[0].text.strip())
        if result is None:
            result = {"coin_name": msg.content[0].text[:80], "confidence": 0.0, "notes": "parse error"}

        # Pass 2 — upgrade to sonnet only when confidence is low
        if result.get("confidence", 0) < cls.UPGRADE_THRESHOLD:
            if PIL_OK:
                # Re-compress at slightly higher resolution for detail pass
                from io import BytesIO as _BytesIO
                with open(image_path, "rb") as f:
                    raw = f.read()
                img2 = PILImage.open(_BytesIO(raw)).convert("RGB")
                img2.thumbnail((768, 768), PILImage.LANCZOS)
                buf2 = _BytesIO()
                img2.save(buf2, "JPEG", quality=82, optimize=True)
                hi_jpeg = buf2.getvalue()
            else:
                hi_jpeg = jpeg

            img_block2 = cls._b64_image_block(hi_jpeg)
            msg2 = client.messages.create(
                model=cls.MODEL_DETAIL,
                max_tokens=600,
                messages=[{"role": "user", "content": [img_block2, {"type": "text", "text": cls._PROMPT}]}],
            )
            r2 = cls._parse_json(msg2.content[0].text.strip())
            if r2 and r2.get("confidence", 0) > result.get("confidence", 0):
                result = r2
            result["_model"] = cls.MODEL_DETAIL
        else:
            result["_model"] = cls.MODEL_FAST

        cls._cache_put(cache_key, result)
        return result

    @classmethod
    def identify_batch(cls, image_paths: List[str]) -> List[dict]:
        """
        Identify multiple coins in a single API call.
        Returns a list of result dicts aligned with image_paths.
        """
        if not image_paths:
            return []
        if not ANTHROPIC_OK:
            raise FetchError("anthropic package not installed")
        api_key = cls._get_api_key()
        if not api_key:
            raise FetchError("Anthropic API key not configured.")

        client   = _anthropic.Anthropic(api_key=api_key)
        content  = []
        uncached_indices: List[int] = []
        results: List[Optional[dict]] = [None] * len(image_paths)

        compressed: List[Tuple[bytes, str]] = []
        for i, path in enumerate(image_paths):
            jpeg, mime = cls._compress(path)
            compressed.append((jpeg, mime))
            key = hashlib.sha256(jpeg).hexdigest()
            hit = cls._cache_get(key)
            if hit:
                results[i] = dict(hit)
            else:
                uncached_indices.append(i)
                content.append({"type": "text", "text": f"Coin {len(uncached_indices)}:"})
                content.append(cls._b64_image_block(jpeg, mime))

        if uncached_indices:
            content.append({"type": "text", "text": cls._BATCH_PROMPT})
            msg = client.messages.create(
                model=cls.MODEL_FAST,
                max_tokens=512 * len(uncached_indices),
                messages=[{"role": "user", "content": content}],
            )
            text = msg.content[0].text.strip()
            # Parse JSON array
            batch_results: List[dict] = []
            try:
                s = text.index("["); e = text.rindex("]") + 1
                batch_results = json.loads(text[s:e])
            except (ValueError, json.JSONDecodeError):
                # Fallback: extract individual objects
                for m in re.finditer(r'\{[^{}]+\}', text, re.S):
                    r = cls._parse_json(m.group())
                    if r:
                        batch_results.append(r)

            for list_pos, orig_idx in enumerate(uncached_indices):
                r = batch_results[list_pos] if list_pos < len(batch_results) else {}
                r["_model"] = cls.MODEL_FAST
                jpeg_b = compressed[orig_idx][0]
                cls._cache_put(hashlib.sha256(jpeg_b).hexdigest(), r)
                results[orig_idx] = r

        return [r or {} for r in results]

    @classmethod
    def identify_threaded(cls, image_path: str, callback):
        """Run single identification in background thread."""
        def run():
            try:
                callback(cls.identify(image_path), None)
            except Exception as e:
                callback(None, str(e))
        threading.Thread(target=run, daemon=True).start()


class WorldCoinDB:
    @classmethod
    def connect(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(_WORLD_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(_WORLD_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        for stmt in _WORLD_DB_SCHEMA:
            conn.execute(stmt)
        # Migrate: add columns that were added after initial schema
        existing = {r[1] for r in conn.execute("PRAGMA table_info(coins)").fetchall()}
        if "page_number" not in existing:
            conn.execute("ALTER TABLE coins ADD COLUMN page_number INTEGER DEFAULT 0")
        conn.commit()
        return conn

    @classmethod
    def catalog_status(cls, catalog: str) -> Dict:
        try:
            with cls.connect() as conn:
                row = conn.execute(
                    "SELECT pages_done, total_pages, done FROM catalog_meta WHERE catalog=?",
                    (catalog,)).fetchone()
            if row:
                return {"pages_done": row[0], "total_pages": row[1], "done": bool(row[2])}
        except Exception:
            pass
        return {"pages_done": 0, "total_pages": 0, "done": False}

    @classmethod
    def search(cls, query: str, country_filter: str = "", limit: int = 300) -> List[Dict]:
        try:
            conn = cls.connect()
            q_like = f"%{query.upper()}%"
            if country_filter:
                rows = conn.execute("""
                    SELECT c.catalog, c.country, c.km_number, c.denomination, c.metal,
                           c.page_number,
                           p.date_year, p.mintage, p.vg, p.f_grade, p.vf, p.xf, p.unc, p.ms63
                    FROM coins c
                    LEFT JOIN coin_prices p ON p.coin_id = c.id
                    WHERE (UPPER(c.denomination) LIKE ? OR UPPER(c.km_number) LIKE ?)
                      AND UPPER(c.country) LIKE ?
                    ORDER BY c.country, CAST(c.km_number AS INTEGER), p.date_year
                    LIMIT ?
                """, (q_like, q_like, f"%{country_filter.upper()}%", limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT c.catalog, c.country, c.km_number, c.denomination, c.metal,
                           c.page_number,
                           p.date_year, p.mintage, p.vg, p.f_grade, p.vf, p.xf, p.unc, p.ms63
                    FROM coins c
                    LEFT JOIN coin_prices p ON p.coin_id = c.id
                    WHERE UPPER(c.denomination) LIKE ?
                       OR UPPER(c.km_number) LIKE ?
                       OR UPPER(c.country) LIKE ?
                    ORDER BY c.country, CAST(c.km_number AS INTEGER), p.date_year
                    LIMIT ?
                """, (q_like, q_like, q_like, limit)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            log.warning("WorldCoinDB.search: %s", e)
            return []

    @classmethod
    def search_by_km(cls, km_number: str, country: str = "", limit: int = 20) -> List[Dict]:
        """Exact KM# lookup, optionally filtered by country."""
        try:
            conn = cls.connect()
            if country:
                rows = conn.execute("""
                    SELECT c.catalog, c.country, c.km_number, c.denomination, c.metal,
                           c.page_number,
                           p.date_year, p.mintage, p.vg, p.f_grade, p.vf, p.xf, p.unc, p.ms63
                    FROM coins c
                    LEFT JOIN coin_prices p ON p.coin_id = c.id
                    WHERE UPPER(c.km_number) = ?
                      AND UPPER(c.country) LIKE ?
                    ORDER BY p.date_year
                    LIMIT ?
                """, (km_number.upper(), f"%{country.upper()}%", limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT c.catalog, c.country, c.km_number, c.denomination, c.metal,
                           c.page_number,
                           p.date_year, p.mintage, p.vg, p.f_grade, p.vf, p.xf, p.unc, p.ms63
                    FROM coins c
                    LEFT JOIN coin_prices p ON p.coin_id = c.id
                    WHERE UPPER(c.km_number) = ?
                    ORDER BY c.country, p.date_year
                    LIMIT ?
                """, (km_number.upper(), limit)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            log.warning("WorldCoinDB.search_by_km: %s", e)
            return []

    @classmethod
    def countries(cls) -> List[str]:
        try:
            conn = cls.connect()
            rows = conn.execute(
                "SELECT DISTINCT country FROM coins ORDER BY country").fetchall()
            conn.close()
            return [r[0] for r in rows if r[0]]
        except Exception:
            return []

    @classmethod
    def total_coins(cls) -> int:
        try:
            conn = cls.connect()
            n = conn.execute("SELECT COUNT(*) FROM coins").fetchone()[0]
            conn.close()
            return n
        except Exception:
            return 0


def _ocr_page_macos(pil_image) -> str:
    """Run macOS Vision OCR on a PIL image; returns extracted text."""
    if not MACOS_OCR_OK:
        return ""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        pil_image.save(tmp)
        img_url = _Foundation.NSURL.fileURLWithPath_(tmp)
        handler = _Vision.VNImageRequestHandler.alloc().initWithURL_options_(img_url, None)
        req = _Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(_Vision.VNRequestTextRecognitionLevelAccurate)
        ok, _ = handler.performRequests_error_([req], None)
        if not ok:
            return ""
        lines = []
        for obs in req.results():
            cands = obs.topCandidates_(1)
            if cands:
                lines.append(str(cands[0].string()))
        return "\n".join(lines)
    except Exception as e:
        log.debug("macOS OCR error: %s", e)
        return ""
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


class WorldCoinIndexer:
    _RE_KM    = re.compile(r'^KM#\s*([A-Z]?\d+[\w.]*)\s+(.+)', re.I)
    _RE_PRICE = re.compile(r'^(\d{4}(?:[/\-]\d+)?)\s+(.+)$')
    _RE_VAL   = re.compile(r'([\d,]+(?:\.\d+)?|[—–-])')
    _RE_HDR   = re.compile(r'^Date\s+Mintage\s+', re.I)
    _RE_CTRY  = re.compile(r'^[A-Z][A-Z ,()&\'-]{3,59}$')
    _METAL_KW = ("silver", "gold", "copper", "bronze", "nickel", "aluminum",
                 "zinc", "billon", "electrum", "platinum", "palladium", "brass")
    _SKIP_HDR = {"DATE", "MINTAGE", "VG", "VF", "XF", "UNC", "NOTE", "REV", "OBV",
                 "SILVER", "GOLD", "COPPER", "BRONZE", "NICKEL", "RULER", "MINT",
                 "ALUMINUM", "ZINC", "INC", "ABOVE", "BELOW", "KNOWN", "UNIQUE"}

    @classmethod
    def _page_text(cls, page) -> str:
        """Extract text from a pdfplumber page; use macOS OCR if page is image-only."""
        text = ""
        try:
            text = page.extract_text() or ""
        except Exception:
            pass
        if not text.strip() and MACOS_OCR_OK:
            try:
                pil_img = page.to_image(resolution=200).original
                text = _ocr_page_macos(pil_img)
            except Exception as e:
                log.debug("OCR fallback failed: %s", e)
        return text

    @classmethod
    def index_catalog(cls, catalog: str, path: str,
                      progress_cb=None, stop_event=None):
        if not PDFPLUMBER_OK:
            log.warning("pdfplumber not installed — cannot index catalogs")
            return

        meta = WorldCoinDB.catalog_status(catalog)
        if meta["done"]:
            if progress_cb:
                progress_cb(meta["total_pages"], meta["total_pages"], True)
            return

        start_page = meta.get("pages_done", 0)
        conn = WorldCoinDB.connect()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        try:
            with _pdfplumber.open(path) as pdf:
                total = len(pdf.pages)
                conn.execute(
                    "INSERT OR REPLACE INTO catalog_meta VALUES (?,?,?,0)",
                    (catalog, start_page, total))
                conn.commit()

                current_country = "UNKNOWN"
                current_km = current_denom = current_metal = None
                current_grades: List[str] = []
                current_coin_id: Optional[int] = None
                coin_cache: Dict[Tuple, int] = {}

                FLUSH_EVERY = 50
                pending_prices: List[Tuple] = []

                for pg_idx in range(start_page, total):
                    if stop_event and stop_event.is_set():
                        break

                    try:
                        text = cls._page_text(pdf.pages[pg_idx])
                    except Exception:
                        text = ""

                    for raw in text.split('\n'):
                        line = raw.strip()
                        if not line:
                            continue

                        # Country header
                        if cls._RE_CTRY.match(line) and not cls._RE_KM.match(line):
                            words = set(line.split())
                            if not words & cls._SKIP_HDR and len(line) >= 4:
                                current_country = line
                                continue

                        # KM# entry
                        km_m = cls._RE_KM.match(line)
                        if km_m:
                            current_km     = km_m.group(1)
                            current_denom  = km_m.group(2).strip()
                            current_metal  = ""
                            current_grades = []
                            current_coin_id = None
                            key = (catalog, current_country, current_km)
                            if key not in coin_cache:
                                cur = conn.execute(
                                    "INSERT OR IGNORE INTO coins"
                                    " (catalog,country,km_number,denomination,metal,page_number)"
                                    " VALUES (?,?,?,?,?,?)",
                                    (catalog, current_country, current_km,
                                     current_denom, "", pg_idx + 1))
                                if cur.lastrowid:
                                    coin_cache[key] = cur.lastrowid
                                else:
                                    row = conn.execute(
                                        "SELECT id FROM coins WHERE catalog=?"
                                        " AND country=? AND km_number=?",
                                        (catalog, current_country, current_km)
                                    ).fetchone()
                                    coin_cache[key] = row[0] if row else None
                            current_coin_id = coin_cache.get(key)
                            continue

                        # Grade header
                        if cls._RE_HDR.match(line):
                            after = line.split('Mintage')[-1].strip()
                            current_grades = [g for g in after.split() if g]
                            continue

                        # Metal/description (before grades seen)
                        if current_km and not current_grades:
                            if any(m in line.lower() for m in cls._METAL_KW):
                                current_metal = line[:80]
                                if current_coin_id:
                                    conn.execute(
                                        "UPDATE coins SET metal=? WHERE id=?",
                                        (current_metal, current_coin_id))
                                continue

                        # Price row
                        if current_km and current_grades and current_coin_id:
                            pr = cls._RE_PRICE.match(line)
                            if pr:
                                year_str = pr.group(1)
                                vals = cls._RE_VAL.findall(pr.group(2).strip())
                                mintage = vals[0] if vals else "—"
                                pv = vals[1:] if len(vals) > 1 else vals
                                gmap = {g.lower(): v for g, v in
                                        zip(current_grades, pv)}
                                vg  = gmap.get("vg",  gmap.get("f8",  "—"))
                                fg  = gmap.get("f",   gmap.get("f12", "—"))
                                vf  = gmap.get("vf",  gmap.get("vf20", gmap.get("vf30", "—")))
                                xf  = gmap.get("xf",  gmap.get("xf40", "—"))
                                unc = gmap.get("unc", gmap.get("ms60", "—"))
                                ms3 = gmap.get("ms63", "—")
                                pending_prices.append((
                                    current_coin_id, year_str, mintage,
                                    vg, fg, vf, xf, unc, ms3))

                    if (pg_idx + 1) % FLUSH_EVERY == 0 or pg_idx == total - 1:
                        if pending_prices:
                            conn.executemany(
                                "INSERT INTO coin_prices"
                                " (coin_id,date_year,mintage,vg,f_grade,vf,xf,unc,ms63)"
                                " VALUES (?,?,?,?,?,?,?,?,?)",
                                pending_prices)
                            pending_prices.clear()
                        conn.execute(
                            "INSERT OR REPLACE INTO catalog_meta VALUES (?,?,?,0)",
                            (catalog, pg_idx + 1, total))
                        conn.commit()
                        if progress_cb:
                            progress_cb(pg_idx + 1, total)

                if not (stop_event and stop_event.is_set()):
                    conn.execute(
                        "INSERT OR REPLACE INTO catalog_meta VALUES (?,?,?,1)",
                        (catalog, total, total))
                    conn.commit()
                    if progress_cb:
                        progress_cb(total, total, True)
                    log.info("Catalog %s indexed (%d pages)", catalog, total)
        except Exception as e:
            log.exception("WorldCoinIndexer.index_catalog(%s) failed:", catalog)
        finally:
            conn.close()


# ── Analysis engine ───────────────────────────────────────────────────────────

class AnalysisEngine:
    @staticmethod
    def grade_value(grade: str) -> int:
        m = re.search(r"(\d+)$", grade)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _grade_tier(gv: int) -> str:
        if gv >= 60: return "ms"
        if gv >= 50: return "au"
        if gv >= 20: return "vf_ef"
        return "low"

    @staticmethod
    def _recommend_service(coin_name: str) -> str:
        name_lower = coin_name.lower()
        for kw in PCGS_PREFERRED_KEYWORDS:
            if kw in name_lower:
                return "PCGS"
        for kw in NGC_PREFERRED_KEYWORDS:
            if kw in name_lower:
                return "NGC"
        return "NGC or PCGS"

    @classmethod
    def detect_old_holders(cls, results: List[AuctionResult]) -> List[Dict]:
        found = []
        seen: set = set()
        for r in results:
            combined = (r.description + " " + r.holder).lower()
            for key, (name, note) in OLD_HOLDERS_INFO.items():
                if re.search(r'\b' + re.escape(key) + r'\b', combined):
                    sig = (key, r.description[:40])
                    if sig not in seen:
                        seen.add(sig)
                        found.append({
                            "holder_key": key, "holder_name": name, "note": note,
                            "description": r.description[:70],
                            "price": r.price, "source": r.source,
                        })
                    r.old_holder_key = key
                    break
        return found

    @classmethod
    def analyze(
        cls,
        results: List[AuctionResult],
        holder: str,
        grade: str,
        metal_prices: Dict[str, float],
        coin_name: str,
    ) -> CoinAnalysis:
        analysis = CoinAnalysis()

        name_lower = coin_name.lower()
        for key, oz in SILVER_CONTENT.items():
            if key in name_lower:
                analysis.melt_value = oz * metal_prices.get("silver", 0)
                break
        if not analysis.melt_value:
            for key, oz in GOLD_CONTENT.items():
                if key in name_lower:
                    analysis.melt_value = oz * metal_prices.get("gold", 0)
                    break

        analysis.recommended_service = cls._recommend_service(coin_name)
        analysis.old_holders_found = cls.detect_old_holders(results)
        if analysis.old_holders_found:
            names = ", ".join({d["holder_name"] for d in analysis.old_holders_found})
            analysis.flags.append(
                f"OLD HOLDER DETECTED — {names} coin(s) found. Strong crossover opportunity."
            )

        prices = [r.price for r in results if r.price > 0]
        cls._set_crossover(analysis, holder, grade, coin_name, prices)
        if not prices:
            return analysis

        avg = sum(prices) / len(prices)
        lo  = min(prices)

        if lo < avg * 0.75:
            analysis.undervalued = True
            analysis.flags.append(
                f"UNDERVALUED — lowest ${lo:,.0f} is >25% below avg ${avg:,.0f}"
            )

        if analysis.melt_value > 0 and lo < analysis.melt_value * 1.15:
            analysis.flags.append(
                f"NEAR MELT — trading near melt value (${analysis.melt_value:,.2f})"
            )

        if analysis.old_holders_found:
            old_prices   = [r.price for r in results if r.price > 0 and r.old_holder_key]
            major_prices = [r.price for r in results if r.price > 0 and not r.old_holder_key
                            and r.holder in ("NGC", "PCGS", "CAC-NGC", "CAC-PCGS")]
            if old_prices and major_prices:
                old_avg   = sum(old_prices)   / len(old_prices)
                major_avg = sum(major_prices) / len(major_prices)
                prem = (major_avg / old_avg - 1) * 100
                if prem > 5:
                    analysis.crossover_details.append(
                        f"NGC/PCGS coins averaging ${major_avg:,.0f} vs old-holder "
                        f"${old_avg:,.0f} (+{prem:.0f}% premium after crossing)"
                    )
                    analysis.flags.append(
                        f"PRICE PREMIUM — NGC/PCGS +{prem:.0f}% over old-holder examples"
                    )

        if holder in ("NGC", "PCGS") and grade:
            if cls.grade_value(grade) >= 63:
                analysis.flags.append("CAC STICKER CANDIDATE — quality coin may qualify")

        if grade:
            gv = cls.grade_value(grade)
            if gv in (63, 64, 65, 66):
                analysis.regrade_potential = f"POSSIBLE — {grade} is a frequent upgrade grade"
                analysis.flags.append(f"REGRADE POTENTIAL — {grade} coins often upgrade one point")
            elif gv >= 67:
                analysis.regrade_potential = "LOW — already gem/superb gem; regrade adds risk"
            elif 0 < gv < 60:
                analysis.regrade_potential = "MINIMAL — circulated coins rarely upgrade significantly"
            else:
                analysis.regrade_potential = "STANDARD"

        if grade:
            gv = cls.grade_value(grade)
            g = 1.15 if gv >= 66 else (1.08 if gv >= 63 else 1.04)
        else:
            g = 1.05
        analysis.roi_1yr = (g     - 1) * 100
        analysis.roi_3yr = (g**3  - 1) * 100
        analysis.roi_5yr = (g**5  - 1) * 100
        return analysis

    @classmethod
    def _set_crossover(cls, analysis: "CoinAnalysis", holder: str, grade: str,
                       coin_name: str, prices: list):
        holder_key = holder.lower()
        gv   = cls.grade_value(grade) if grade else 0
        tier = cls._grade_tier(gv)
        rates = CROSSOVER_RATES.get(holder_key)
        if rates:
            rate = rates.get(tier, 0.5)
            analysis.crossover_success_rate = rate
            name, note = OLD_HOLDERS_INFO.get(holder_key, (holder, ""))
            analysis.crossover_potential = (
                f"{'HIGH' if rate >= 0.65 else 'MODERATE'} ({rate*100:.0f}% est.) "
                f"— {name} → {analysis.recommended_service}"
            )
            analysis.crossover_details += [
                f"Holder: {name}", note,
                f"Estimated upgrade success: {rate*100:.0f}%  |  "
                f"Recommended service: {analysis.recommended_service}",
            ]
            if grade:
                analysis.crossover_details.append(
                    f"Submit at: {grade}  →  target same or higher at {analysis.recommended_service}"
                )
            analysis.flags.append(
                f"CROSSOVER OPPORTUNITY — {name} ({rate*100:.0f}% upgrade rate) "
                f"→ submit to {analysis.recommended_service}"
            )
        elif holder in ("NGC", "PCGS") and grade:
            if 62 <= gv <= 64:
                analysis.crossover_potential = "MODERATE — borderline grade, may cross higher NGC↔PCGS"
                analysis.crossover_details.append(
                    f"{grade} is a common upgrade boundary crossing NGC↔PCGS."
                )
                analysis.flags.append(f"CROSSOVER — {grade} may upgrade crossing NGC↔PCGS")
            else:
                analysis.crossover_potential = "LOW-MODERATE — ~45% cross-over rate between major services"
                analysis.crossover_details.append(
                    "Major-service coins cross at ~45% overall."
                )
        else:
            analysis.crossover_potential = "N/A — no holder specified"


# ── Inline detail dialogs ─────────────────────────────────────────────────────

class CertDetailDialog(tk.Toplevel):
    """Shows NGC or PCGS cert lookup data fetched inline."""

    def __init__(self, parent, result: Dict, service: str):
        super().__init__(parent)
        self.title(f"{service} Certificate #{result.get('cert', '')}")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("560x480")
        self.transient(parent)
        self.grab_set()

        cert  = result.get("cert", "")
        url   = result.get("url", "")
        data  = result.get("data", {})
        error = result.get("error", "")

        hdr = tk.Label(self,
            text=f"{service}  •  Cert # {cert}",
            bg=BG3, fg=ACCENT, font=("Helvetica", 13, "bold"),
            anchor=tk.W, padx=12)
        hdr.pack(fill=tk.X)

        url_lbl = tk.Label(self, text=url, bg=BG, fg=TEAL,
                           font=("Helvetica", 9), anchor=tk.W)
        url_lbl.pack(fill=tk.X, padx=10, pady=(4, 0))

        txt = scrolledtext.ScrolledText(self, bg=BG2, fg=FG,
                                        font=("Courier", 11), relief=tk.FLAT, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        txt.tag_configure("label",  foreground=ACCENT, font=("Courier", 11, "bold"))
        txt.tag_configure("value",  foreground=FG)
        txt.tag_configure("error",  foreground=RED)
        txt.tag_configure("notice", foreground=YELLOW)

        if error:
            txt.insert(tk.END, f"Error: {error}\n", "error")

        if data:
            for k, v in data.items():
                txt.insert(tk.END, f"{k:<22}", "label")
                txt.insert(tk.END, f"{v}\n", "value")
        else:
            txt.insert(tk.END,
                "No structured data returned — the site likely requires JavaScript rendering.\n\n"
                "The cert number and URL above can be used for manual verification.\n",
                "notice")

        txt.config(state=tk.DISABLED)
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 10))

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")


class LotDetailDialog(tk.Toplevel):
    """Shows full lot details fetched inline on double-click."""

    def __init__(self, parent, result: "AuctionResult", extra: Dict):
        super().__init__(parent)
        self.title(f"{result.source}  —  Lot Detail")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("640x540")
        self.transient(parent)

        hdr = tk.Label(self,
            text=f"  {result.source}  |  {result.description[:70]}",
            bg=BG3, fg=ACCENT, font=("Helvetica", 12, "bold"),
            anchor=tk.W, padx=12)
        hdr.pack(fill=tk.X)

        txt = scrolledtext.ScrolledText(self, bg=BG2, fg=FG,
                                        font=("Courier", 11), relief=tk.FLAT, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        txt.tag_configure("label",  foreground=ACCENT, font=("Courier", 11, "bold"))
        txt.tag_configure("value",  foreground=FG)
        txt.tag_configure("price",  foreground=GREEN,  font=("Courier", 12, "bold"))
        txt.tag_configure("error",  foreground=RED)
        txt.tag_configure("url",    foreground=TEAL)
        txt.tag_configure("sep",    foreground=BG3)

        # Always-available cached data
        def row(label, value, tag="value"):
            if value:
                txt.insert(tk.END, f"{label:<18}", "label")
                txt.insert(tk.END, f"{value}\n", tag)

        row("Source",   result.source)
        row("Description", result.description)
        row("Grade",    result.grade)
        row("Holder",   result.holder)
        row("Price",    f"${result.price:,.2f}" if result.price else "N/A", "price")
        row("Date",     result.date)
        txt.insert(tk.END, "─" * 55 + "\n", "sep")

        err = extra.get("error", "")
        if err:
            txt.insert(tk.END, f"Fetch error: {err}\n", "error")
        for k, v in extra.get("data", {}).items():
            row(k, v)

        txt.insert(tk.END, "\n")
        txt.insert(tk.END, result.url, "url")
        txt.config(state=tk.DISABLED)

        ttk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 10))

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")


# ── Credentials Dialog ───────────────────────────────────────────────────────

class CredentialsDialog(tk.Toplevel):
    """
    Modal dialog for entering, saving, and testing site credentials.
    Credentials are persisted via CredentialStore (macOS Keychain when
    available, otherwise ~/.numismatic/credentials.json chmod 0o600).
    """
    _SITE_ORDER = [
        "heritage", "ebay", "sedwick", "christies",
        "greatcollections", "sothebys", "coinstrail",
        "ngc", "pcgs", "anthropic",
    ]
    _FETCHERS = {
        "heritage":         HeritageFetcher,
        "ebay":             eBayFetcher,
        "sedwick":          SedwickFetcher,
        "christies":        ChristiesFetcher,
        "greatcollections": GreatCollectionsFetcher,
        "sothebys":         SothebysFileFetcher,
        "coinstrail":       CoinstrailFetcher,
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Site Credentials")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        self._user_vars:   Dict[str, tk.StringVar] = {}
        self._pass_vars:   Dict[str, tk.StringVar] = {}
        self._status_vars: Dict[str, tk.StringVar] = {}
        self._pass_entries: Dict[str, ttk.Entry]   = {}
        self._show_pass = tk.BooleanVar(value=False)

        self._build()
        self._load_saved()
        self._refresh_status_labels()

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        pad = {"padx": 10, "pady": 4}

        store_type = "macOS Keychain (keyring)" if KEYRING_OK else f"~/.numismatic/credentials.json"
        tk.Label(self, text=f"Storage: {store_type}",
                 bg=BG, fg=TEAL, font=("Helvetica", 9)).grid(
            row=0, column=0, columnspan=5, sticky="w", padx=12, pady=(10, 2))
        tk.Label(self,
                 text="eBay uses JavaScript-based login; form login may fail — session cookies still help.",
                 bg=BG, fg=YELLOW, font=("Helvetica", 9)).grid(
            row=1, column=0, columnspan=5, sticky="w", padx=12, pady=(0, 8))

        # Header row
        for col, txt in enumerate(("Site", "Email / Username", "Password", "Status")):
            tk.Label(self, text=txt, bg=BG, fg=ACCENT,
                     font=("Helvetica", 10, "bold")).grid(
                row=2, column=col, sticky="w", padx=10, pady=(0, 4))

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=2)

        for i, site in enumerate(self._SITE_ORDER):
            row = i + 4
            label = SITES.get(site, site.title())
            tk.Label(self, text=label + ":", bg=BG, fg=FG,
                     font=("Helvetica", 10), anchor=tk.E, width=18).grid(
                row=row, column=0, sticky="e", **pad)

            u_var = tk.StringVar()
            p_var = tk.StringVar()
            s_var = tk.StringVar(value="—  No credentials")
            self._user_vars[site]   = u_var
            self._pass_vars[site]   = p_var
            self._status_vars[site] = s_var

            ttk.Entry(self, textvariable=u_var, width=26).grid(
                row=row, column=1, sticky="w", **pad)
            pe = ttk.Entry(self, textvariable=p_var, width=22, show="●")
            pe.grid(row=row, column=2, sticky="w", **pad)
            self._pass_entries[site] = pe

            tk.Label(self, textvariable=s_var, bg=BG, fg=TEAL,
                     font=("Helvetica", 10), width=22, anchor=tk.W).grid(
                row=row, column=3, sticky="w", **pad)

        # Show-password toggle
        last_row = len(self._SITE_ORDER) + 4
        ttk.Checkbutton(self, text="Show passwords",
                        variable=self._show_pass,
                        command=self._toggle_show_pass).grid(
            row=last_row, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 2))

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=last_row + 1, column=0, columnspan=4, sticky="ew", padx=10, pady=6)

        # Buttons
        btn_row = last_row + 2
        ttk.Button(self, text="Save & Connect All",
                   style="Accent.TButton",
                   command=self._save_and_connect).grid(
            row=btn_row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 12))
        ttk.Button(self, text="Test Connections",
                   command=self._test_connections).grid(
            row=btn_row, column=2, sticky="w", padx=10, pady=(0, 12))
        ttk.Button(self, text="Logout All",
                   command=self._logout_all).grid(
            row=btn_row + 1, column=0, sticky="w", padx=10, pady=(0, 12))
        ttk.Button(self, text="Close",
                   command=self.destroy).grid(
            row=btn_row + 1, column=3, sticky="e", padx=10, pady=(0, 12))

    def _load_saved(self):
        for site in self._SITE_ORDER:
            u, p = CredentialStore.load(site)
            self._user_vars[site].set(u)
            self._pass_vars[site].set(p)

    def _toggle_show_pass(self):
        char = "" if self._show_pass.get() else "●"
        for e in self._pass_entries.values():
            e.configure(show=char)

    def _refresh_status_labels(self):
        for site in self._SITE_ORDER:
            u = self._user_vars[site].get().strip()
            if not u:
                self._status_vars[site].set("—  No credentials")
                continue
            if SessionManager.is_logged_in(site):
                self._status_vars[site].set("✓  Active")
            else:
                self._status_vars[site].set("○  Saved, not tested")

    def _save_and_connect(self):
        for site in self._SITE_ORDER:
            u = self._user_vars[site].get().strip()
            p = self._pass_vars[site].get().strip()
            if u and p:
                CredentialStore.save(site, u, p)
            elif not u:
                CredentialStore.delete(site)
                SessionManager.reset(site)
        # Invalidate cached NGC session so it re-authenticates with new creds
        with NGCPopFetcher._ctx_lock:
            try:
                if NGCPopFetcher._ctx:
                    NGCPopFetcher._ctx.close()
            except Exception:
                pass
            NGCPopFetcher._ctx = None
            NGCPopFetcher._ctx_logged_in = False
        # Remove stale cookie file so login is forced fresh
        try:
            if os.path.exists(NGCPopFetcher._COOKIE_PATH):
                os.remove(NGCPopFetcher._COOKIE_PATH)
        except OSError:
            pass
        self._test_connections()

    def _test_connections(self):
        if not REQUESTS_OK:
            messagebox.showwarning("Missing Library",
                                   "requests is not installed — cannot test connections.",
                                   parent=self)
            return
        for site in self._SITE_ORDER:
            if not CredentialStore.has_credentials(site):
                self._status_vars[site].set("—  No credentials")
                continue
            self._status_vars[site].set("…  Testing")
            self.update_idletasks()

            def _try(s=site):
                SessionManager.reset(s)
                sess = SessionManager.session(s)
                fetcher = self._FETCHERS[s]
                ok = _auto_login(sess, s, fetcher.LOGIN_URL)
                SessionManager.set_logged_in(s, ok)
                label = "✓  Active" if ok else "✗  Login failed"
                self._status_vars[s].set(label)

            threading.Thread(target=_try, daemon=True).start()

    def _logout_all(self):
        SessionManager.reset_all()
        self._refresh_status_labels()
        messagebox.showinfo("Logged Out",
                            "All sessions reset. Credentials remain saved.",
                            parent=self)


# ── GUI ───────────────────────────────────────────────────────────────────────

class NumismaticAgent(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Numismatic — Coin Analysis")
        self.minsize(1400, 900)
        self.resizable(True, True)
        self.configure(bg=BG)
        # macOS: use white titlebar
        try:
            self.tk.call("::tk::unsupported::MacWindowStyle", "style", self._w,
                         "document", "closeBox collapseBox resizable")
        except Exception:
            pass
        # Start maximized (macOS-compatible)
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        self._results: List[AuctionResult] = []
        self._metal_prices: Dict[str, float] = {}
        self._q: queue.Queue = queue.Queue()
        self._busy = False

        CredentialStore.migrate_legacy()   # one-time: json → encrypted

        self._setup_styles()
        self._build_ui()
        self._start_metal_refresh()
        self.after(100, self._process_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not REQUESTS_OK:
            messagebox.showwarning(
                "Missing Dependencies",
                "requests / beautifulsoup4 not installed.\n"
                "Live search will open in browser only.\n\n"
                "pip install requests beautifulsoup4",
                parent=self,
            )

    def _on_close(self):
        try:
            self._wc_index_stop.set()
        except Exception:
            pass
        PlaywrightLoginManager.shutdown()
        self.destroy()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _setup_styles(self):
        # ── Collectorly × Coinstrail Design System ────────────────────────────
        # Warm numismatic gold palette (Collectorly) + card-based UX (Coinstrail)
        HN = "Helvetica Neue"
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure(".",
                     background=BG, foreground=FG,
                     fieldbackground=BG,
                     font=(HN, 11),
                     bordercolor=BORDER,
                     relief=tk.FLAT)

        s.configure("TFrame",      background=BG)
        s.configure("Dark.TFrame", background=BG3)
        s.configure("Card.TFrame", background=BG2)
        s.configure("TLabel",      background=BG, foreground=FG)
        s.configure("Muted.TLabel",background=BG, foreground=FG2, font=(HN, 9))
        s.configure("Cap.TLabel",  background=BG2, foreground=FG2, font=(HN, 8, "bold"))

        s.configure("TLabelframe", background=BG, bordercolor=BORDER,
                     relief=tk.GROOVE, borderwidth=1)
        s.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                     font=(HN, 9, "bold"))

        s.configure("TEntry",
                     fieldbackground=BG, foreground=FG,
                     insertcolor=FG, bordercolor=BORDER,
                     lightcolor=BG, darkcolor=BG,
                     relief=tk.FLAT, borderwidth=1, padding=(6, 4))
        s.configure("TCombobox",
                     fieldbackground=BG, foreground=FG,
                     selectbackground=ACCENT, selectforeground=BG,
                     bordercolor=BORDER, relief=tk.FLAT, padding=(6, 4))
        s.map("TCombobox",
              fieldbackground=[("readonly", BG2)],
              foreground=[("readonly", FG)])

        # Default button — warm gray
        s.configure("TButton",
                     background=BG2, foreground=FG,
                     padding=(10, 5), font=(HN, 9, "bold"),
                     relief=tk.FLAT, borderwidth=1, bordercolor=BORDER,
                     focuscolor=BG2)
        s.map("TButton",
              background=[("active", GOLD_LT), ("pressed", BORDER)],
              foreground=[("active", FG)])

        # Gold CTA — Collectorly primary action
        s.configure("Accent.TButton",
                     background=ACCENT, foreground="#FFFFFF",
                     font=(HN, 9, "bold"), padding=(12, 6),
                     relief=tk.FLAT, borderwidth=0)
        s.map("Accent.TButton",
              background=[("active", ACCENT2), ("pressed", ACCENT2)],
              foreground=[("active", "#FFFFFF")])

        # Dark / charcoal button
        s.configure("Dark.TButton",
                     background=BG3, foreground="#FFFFFF",
                     font=(HN, 9, "bold"), padding=(12, 6),
                     relief=tk.FLAT, borderwidth=0)
        s.map("Dark.TButton",
              background=[("active", "#2E2A26"), ("pressed", "#3A352F")],
              foreground=[("active", "#FFFFFF")])

        # Green for Search ALL
        s.configure("Green.TButton",
                     background=GREEN, foreground="#FFFFFF",
                     font=(HN, 9, "bold"), padding=(12, 6),
                     relief=tk.FLAT, borderwidth=0)
        s.map("Green.TButton",
              background=[("active", "#145C38")],
              foreground=[("active", "#FFFFFF")])

        # Notebook — Coinstrail tab bar feel
        s.configure("TNotebook",
                     background=BG2, borderwidth=0,
                     tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                     background=BG2, foreground=FG2,
                     padding=(18, 9), font=(HN, 9, "bold"),
                     borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", BG), ("active", GOLD_LT)],
              foreground=[("selected", ACCENT), ("active", FG)])

        # Treeview — warm alternating rows, gold selection
        s.configure("Treeview",
                     background=BG, foreground=FG,
                     fieldbackground=BG, rowheight=30,
                     font=(HN, 10), borderwidth=0, relief=tk.FLAT)
        s.configure("Treeview.Heading",
                     background=BG2, foreground=FG2,
                     font=(HN, 8, "bold"),
                     relief=tk.FLAT, borderwidth=0, padding=(8, 6))
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#FFFFFF")])

        s.configure("TScrollbar",
                     background=BG2, troughcolor=BG,
                     arrowcolor=FG2, borderwidth=0, relief=tk.FLAT)
        s.configure("TProgressbar",
                     background=ACCENT, troughcolor=BG2,
                     borderwidth=0, relief=tk.FLAT)
        s.configure("TSeparator", background=BORDER)

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _scrollable(self, parent, bg=None):
        """Wrap parent with a canvas+scrollbar. Returns inner frame to place content in."""
        if bg is None:
            bg = BG
        outer = tk.Frame(parent, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(outer, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0,
                           yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.config(command=canvas.yview)

        inner = tk.Frame(canvas, bg=bg)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas(e):
            canvas.itemconfig(win_id, width=e.width)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * e.delta), "units")

        inner.bind("<Configure>", _on_inner)
        canvas.bind("<Configure>", _on_canvas)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        return inner

    def _scrollable_in(self, parent, bg=None):
        """Like _scrollable but uses grid instead of pack (for grid-managed parents).
        Returns (outer_frame, inner_frame); caller must grid outer_frame."""
        if bg is None:
            bg = BG
        outer = tk.Frame(parent, bg=bg)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(outer, orient=tk.VERTICAL)
        vsb.grid(row=0, column=1, sticky="ns")

        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0,
                           yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.config(command=canvas.yview)

        inner = tk.Frame(canvas, bg=bg)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas(e):
            canvas.itemconfig(win_id, width=e.width)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * e.delta), "units")

        inner.bind("<Configure>", _on_inner)
        canvas.bind("<Configure>", _on_canvas)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        return outer, inner

    def _build_ui(self):
        HN = "Helvetica Neue"

        # ── Masthead — Collectorly branding ──────────────────────────────────
        hdr = tk.Frame(self, bg=BG3, height=68)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # Gold left accent bar
        tk.Frame(hdr, bg=ACCENT, width=5).pack(side=tk.LEFT, fill=tk.Y)

        # Load Collectorly logo
        self._logo_img = None
        if PIL_OK and os.path.exists(_LOGO_FULL):
            try:
                raw = PILImage.open(_LOGO_FULL).convert("RGBA")
                # Scale to 44px height, preserve aspect
                ratio = 44 / raw.height
                new_w = int(raw.width * ratio)
                raw = raw.resize((new_w, 44), PILImage.LANCZOS)
                # Composite onto dark background
                bg_img = PILImage.new("RGBA", (new_w, 44), (26, 23, 20, 255))
                bg_img.paste(raw, mask=raw.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img.convert("RGB"))
                tk.Label(hdr, image=self._logo_img, bg=BG3,
                         borderwidth=0).pack(side=tk.LEFT, padx=(14, 0), pady=12)
            except Exception:
                self._logo_img = None

        if not self._logo_img:
            # Fallback text logo
            tk.Label(hdr, text="COLLECTORLY", bg=BG3, fg=ACCENT,
                     font=(HN, 20, "bold")).pack(side=tk.LEFT, padx=(14, 0), pady=14)
            tk.Label(hdr, text=" NUMISMATICS", bg=BG3, fg="#FFFFFF",
                     font=(HN, 14)).pack(side=tk.LEFT, pady=18)

        # Tagline
        tk.Label(hdr, text="Curating Value, Preserving History",
                 bg=BG3, fg=FG2, font=(HN, 9, "italic")).pack(side=tk.LEFT, padx=(20, 0))

        # Metal prices bar — right aligned
        self._metal_bar_lbl = tk.Label(hdr, text="Loading metal prices…",
                                        bg=BG3, fg=FG2, font=(HN, 9))
        self._metal_bar_lbl.pack(side=tk.RIGHT, padx=20)

        # Gold rule below header
        tk.Frame(self, bg=ACCENT, height=2).pack(fill=tk.X)

        # ── Search panel ─────────────────────────────────────────────────────
        sf = tk.Frame(self, bg=BG2)
        sf.pack(fill=tk.X)

        # Top rule
        tk.Frame(sf, bg="#CCCCCC", height=1).pack(fill=tk.X)

        inner = tk.Frame(sf, bg=BG2)
        inner.pack(fill=tk.X, padx=16, pady=10)

        # ── Row 1: field inputs ───────────────────────────────────────────────
        row1 = tk.Frame(inner, bg=BG2)
        row1.pack(fill=tk.X, pady=(0, 6))

        def _lbl(parent, text):
            tk.Label(parent, text=text.upper(), bg=BG2, fg="#888888",
                     font=(HN, 8, "bold")).pack(side=tk.LEFT, padx=(0, 3))

        _lbl(row1, "Coin Name")
        self._name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._name_var, width=26).pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row1, "Year")
        self._year_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._year_var, width=7).pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row1, "Mint")
        self._mint_var = tk.StringVar()
        ttk.Combobox(row1, textvariable=self._mint_var, width=5,
                     values=["", "P", "D", "S", "O", "CC", "W", "C"]
                     ).pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row1, "Grade")
        self._grade_var = tk.StringVar()
        ttk.Combobox(row1, textvariable=self._grade_var, width=9,
                     values=GRADES, state="readonly").pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row1, "Holder")
        self._holder_var = tk.StringVar()
        ttk.Combobox(row1, textvariable=self._holder_var, width=13,
                     values=HOLDERS, state="readonly").pack(side=tk.LEFT, padx=(0, 16))

        # ── Row 2: cert / KM ─────────────────────────────────────────────────
        row2 = tk.Frame(inner, bg=BG2)
        row2.pack(fill=tk.X, pady=(0, 8))

        _lbl(row2, "KM #")
        self._km_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._km_var, width=9).pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row2, "NGC Cert #")
        self._ngc_cert_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._ngc_cert_var, width=13).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row2, text="VERIFY NGC",
                   command=self._open_ngc_cert).pack(side=tk.LEFT, padx=(0, 16))

        _lbl(row2, "PCGS Cert #")
        self._pcgs_cert_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._pcgs_cert_var, width=13).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row2, text="VERIFY PCGS",
                   command=self._open_pcgs_cert).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(row2, text="cert lookups open in browser",
                 bg=BG2, fg="#AAAAAA", font=(HN, 8)).pack(side=tk.LEFT)

        # ── Row 3: action buttons ─────────────────────────────────────────────
        tk.Frame(inner, bg="#CCCCCC", height=1).pack(fill=tk.X, pady=(2, 8))

        row3 = tk.Frame(inner, bg=BG2)
        row3.pack(fill=tk.X)

        # Auction house search buttons
        for label, src, is_primary in [
            ("HERITAGE",          "heritage",        True),
            ("EBAY",              "ebay",            False),
            ("SEDWICK",           "sedwick",         False),
            ("GREAT COLLECTIONS", "greatcollections",False),
            ("COINSTRAIL",        "coinstrail",      False),
        ]:
            style = "Accent.TButton" if is_primary else "TButton"
            ttk.Button(row3, text=label, style=style,
                       command=lambda s=src: self._search(s)
                       ).pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(row3, text="SEARCH ALL", style="Dark.TButton",
                   command=lambda: self._search("all")).pack(side=tk.LEFT, padx=(0, 20))

        tk.Frame(row3, bg="#CCCCCC", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(row3, text="NGC CENSUS",
                   command=self._fetch_ngc_pop).pack(side=tk.LEFT, padx=(6, 4))
        ttk.Button(row3, text="PCGS POP",
                   command=self._fetch_pcgs_pop).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row3, text="PCGS PRICES",
                   command=self._fetch_pcgs_price).pack(side=tk.LEFT, padx=(0, 20))

        tk.Frame(row3, bg="#CCCCCC", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(row3, text="CREDENTIALS",
                   command=self._open_credentials).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(row3, text="CLEAR",
                   command=self._clear).pack(side=tk.RIGHT)

        # Bottom rule
        tk.Frame(sf, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Status bar — MUST be packed before notebook so pack allocates space ──
        sb = tk.Frame(self, bg=BG3, height=26)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        tk.Frame(sb, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)
        self._status_var = tk.StringVar(value="Ready.")
        tk.Label(sb, textvariable=self._status_var,
                 bg=BG3, fg="#666666", font=(HN, 9),
                 anchor=tk.W).pack(side=tk.LEFT, padx=10, pady=4)
        self._progress = ttk.Progressbar(sb, mode="indeterminate", length=120)
        self._progress.pack(side=tk.RIGHT, padx=12, pady=4)

        # ── Notebook — packed AFTER status bar so it fills remaining space ──────
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill=tk.BOTH, expand=True)

        self._build_results_tab()
        self._build_analysis_tab()
        self._build_metals_tab()
        self._build_population_tab()
        self._build_world_coins_tab()
        self._build_ai_scan_tab()

    def _build_results_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  AUCTION RESULTS  ")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Horizontal paned: results list (left) + coin image viewer (right)
        paned = tk.PanedWindow(frame, orient=tk.HORIZONTAL, bg="#CCCCCC",
                               sashrelief=tk.FLAT, sashwidth=1, handlesize=0)
        paned.grid(row=0, column=0, sticky="nsew")

        # ── Left: Treeview ────────────────────────────────────────────────────
        left = tk.Frame(paned, bg=BG)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        cols = ("SOURCE", "DESCRIPTION", "GRADE", "HOLDER", "ALERT", "PRICE", "DATE")
        self._tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        widths = [90, 340, 72, 100, 90, 88, 100]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col, command=lambda c=col: self._sort_tree(c))
            self._tree.column(col, width=w, minwidth=50, anchor=tk.W)

        vsb = ttk.Scrollbar(left, orient=tk.VERTICAL,   command=self._tree.yview)
        hsb = ttk.Scrollbar(left, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        paned.add(left, stretch="always")

        # ── Right: Image viewer — Swiss card layout ───────────────────────────
        right = tk.Frame(paned, bg=BG2, width=260)
        right.pack_propagate(False)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Header strip (fixed)
        hdr_strip = tk.Frame(right, bg=FG, height=36)
        hdr_strip.pack(fill=tk.X)
        hdr_strip.pack_propagate(False)
        tk.Frame(hdr_strip, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hdr_strip, text="  COIN IMAGES", bg=FG, fg=BG,
                 font=(HN, 9, "bold")).pack(side=tk.LEFT, pady=8)

        # Scrollable image area
        right_scroll = self._scrollable(right, bg=BG2)

        # Pixel-sized placeholder image so width/height are in pixels not chars
        _blank = tk.PhotoImage(width=220, height=170)
        _blank.put("#1A1714", to=(0, 0, 220, 170))

        # Obverse
        tk.Label(right_scroll, text="OBVERSE", bg=BG2, fg="#AAAAAA",
                 font=(HN, 7, "bold")).pack(pady=(10, 2))
        self._img_obv = tk.Label(right_scroll, bg=BG3, image=_blank,
                                 text="—", compound=tk.CENTER,
                                 fg="#CCCCCC", font=(HN, 20))
        self._img_obv._blank = _blank
        self._img_obv.pack(padx=16, pady=0)

        # Thin rule between images
        tk.Frame(right_scroll, bg="#DDDDDD", height=1).pack(fill=tk.X, padx=16, pady=6)

        # Reverse
        tk.Label(right_scroll, text="REVERSE", bg=BG2, fg="#AAAAAA",
                 font=(HN, 7, "bold")).pack(pady=(0, 2))
        self._img_rev = tk.Label(right_scroll, bg=BG3, image=_blank,
                                 text="—", compound=tk.CENTER,
                                 fg="#CCCCCC", font=(HN, 20))
        self._img_rev._blank = _blank
        self._img_rev.pack(padx=16, pady=0)

        self._img_info_var = tk.StringVar(value="Select a result to view coin images")
        tk.Label(right_scroll, textvariable=self._img_info_var, bg=BG2, fg="#999999",
                 font=(HN, 8), wraplength=230, justify=tk.CENTER
                 ).pack(padx=6, pady=8)

        paned.add(right, stretch="never", minsize=260)

        # ── Row tag colours — Swiss palette (desaturated source tints) ────────
        HN10 = (HN, 10)
        HN10B = (HN, 10, "bold")
        self._tree.tag_configure("heritage",         foreground=ACCENT)
        self._tree.tag_configure("ebay",             foreground=YELLOW)
        self._tree.tag_configure("sedwick",          foreground=ORANGE)
        self._tree.tag_configure("christies",        foreground=PURPLE)
        self._tree.tag_configure("greatcollections", foreground=TEAL)
        self._tree.tag_configure("sothebys",         foreground=GREEN)
        self._tree.tag_configure("coinstrail",       foreground=PURPLE)
        self._tree.tag_configure("oldholder_high",   foreground=RED,    font=HN10B)
        self._tree.tag_configure("oldholder_mid",    foreground=ORANGE, font=HN10B)
        self._tree.tag_configure("oldholder_raw",    foreground=YELLOW)
        self._tree.tag_configure("alt_row",          background="#FAFAFA")

        self._tree.bind("<ButtonRelease-1>", self._on_tree_select)
        self._tree.bind("<Double-1>", self._on_double_click)

        self._summary_var = tk.StringVar(value="No results yet.")
        tk.Label(frame, textvariable=self._summary_var,
                 bg=BG3, fg="#666666", font=(HN, 9), anchor=tk.W
                 ).grid(row=1, column=0, sticky="ew", padx=0, pady=0, ipady=4)

    def _build_analysis_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  ANALYSIS  ")

        def _section_hdr(parent, title):
            h = tk.Frame(parent, bg=BG2)
            h.pack(fill=tk.X, padx=0, pady=(10, 0))
            tk.Frame(h, bg=ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y)
            tk.Label(h, text=f"  {title}", bg=BG2, fg=FG,
                     font=(HN, 9, "bold")).pack(side=tk.LEFT, pady=5)
            return h

        # Flags
        _section_hdr(frame, "OPPORTUNITY FLAGS")
        self._flags_text = scrolledtext.ScrolledText(
            frame, height=4, bg=BG, fg=GREEN, font=("Helvetica Neue", 10),
            relief=tk.FLAT, wrap=tk.WORD, insertbackground=FG,
            borderwidth=0, highlightthickness=1,
            highlightbackground="#DDDDDD",
        )
        self._flags_text.pack(fill=tk.X, padx=0, pady=(0, 0))

        # 3-column card row
        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill=tk.X, padx=0, pady=(8, 0))
        cards.columnconfigure((0, 1, 2), weight=1)

        def _card(parent, col, title, color, varname):
            c = tk.Frame(parent, bg=BG2, relief=tk.FLAT,
                         highlightbackground="#DDDDDD", highlightthickness=1)
            c.grid(row=0, column=col, sticky="nsew", padx=(0 if col else 0, 0), pady=0,
                   ipadx=12, ipady=8)
            tk.Frame(c, bg=color, height=3).pack(fill=tk.X)
            tk.Label(c, text=title, bg=BG2, fg="#888888",
                     font=(HN, 8, "bold")).pack(anchor=tk.W, padx=10, pady=(6, 2))
            var = tk.StringVar(value="—")
            setattr(self, varname, var)
            tk.Label(c, textvariable=var, bg=BG2, fg=color,
                     font=(HN, 10), wraplength=0, justify=tk.LEFT,
                     ).pack(anchor=tk.W, padx=10, pady=(0, 8))

        _card(cards, 0, "CROSSOVER POTENTIAL", ORANGE,  "_crossover_var")
        _card(cards, 1, "REGRADE POTENTIAL",   PURPLE,  "_regrade_var")
        _card(cards, 2, "ROI PROJECTIONS",      TEAL,    "_roi_var")

        # Crossover detail
        _section_hdr(frame, "CROSSOVER & OLD HOLDER ANALYSIS")
        self._xover_text = scrolledtext.ScrolledText(
            frame, height=6, bg=BG, fg=FG, font=("Helvetica Neue", 10),
            relief=tk.FLAT, wrap=tk.WORD,
            borderwidth=0, highlightthickness=1, highlightbackground="#DDDDDD",
        )
        self._xover_text.pack(fill=tk.X, pady=(0, 0))
        self._xover_text.tag_configure("header",    foreground=ACCENT, font=("Helvetica Neue", 10, "bold"))
        self._xover_text.tag_configure("high",      foreground=RED,    font=("Helvetica Neue", 10, "bold"))
        self._xover_text.tag_configure("mid",       foreground=ORANGE)
        self._xover_text.tag_configure("major",     foreground=YELLOW)
        self._xover_text.tag_configure("detail",    foreground=FG)
        self._xover_text.tag_configure("recommend", foreground=GREEN,  font=("Helvetica Neue", 10, "bold"))
        self._xover_text.tag_configure("note",      foreground=TEAL)
        self._xover_text.tag_configure("error",     foreground=RED)

        # Price stats
        _section_hdr(frame, "PRICE STATISTICS")
        self._stats_text = scrolledtext.ScrolledText(
            frame, height=4, bg=BG, fg=FG, font=("Helvetica Neue", 10),
            relief=tk.FLAT, wrap=tk.WORD,
            borderwidth=0, highlightthickness=1, highlightbackground="#DDDDDD",
        )
        self._stats_text.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

    def _build_metals_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  METALS  ")

        # Toolbar
        toolbar = tk.Frame(frame, bg=BG3)
        toolbar.pack(fill=tk.X)
        tk.Frame(toolbar, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(toolbar, text="↻  REFRESH",
                   command=self._refresh_metals).pack(side=tk.LEFT, padx=10, pady=6)
        self._metal_updated_var = tk.StringVar(value="")
        tk.Label(toolbar, textvariable=self._metal_updated_var,
                 bg=BG3, fg="#888888", font=(HN, 8)).pack(side=tk.LEFT, padx=4)
        tk.Frame(frame, bg="#DDDDDD", height=1).pack(fill=tk.X)

        # Scrollable content area below toolbar
        scroll_inner = self._scrollable(frame, bg=BG)

        # Metal price cards
        mf = tk.Frame(scroll_inner, bg=BG)
        mf.pack(fill=tk.X, padx=20, pady=20)
        self._metal_labels: Dict[str, tk.Label] = {}

        METALS = [
            ("gold",      "GOLD",      "XAU", "#B07D00"),
            ("silver",    "SILVER",    "XAG", "#555555"),
            ("platinum",  "PLATINUM",  "XPT", TEAL),
            ("palladium", "PALLADIUM", "XPD", ORANGE),
        ]
        for i, (key, name, sym, color) in enumerate(METALS):
            mf.columnconfigure(i, weight=1)
            card = tk.Frame(mf, bg=BG2,
                            highlightbackground="#DDDDDD", highlightthickness=1)
            card.grid(row=0, column=i, padx=(0, 12), sticky="ew")
            # Top accent rule
            tk.Frame(card, bg=color, height=3).pack(fill=tk.X)
            tk.Label(card, text=name, bg=BG2, fg="#888888",
                     font=(HN, 8, "bold")).pack(anchor=tk.W, padx=16, pady=(10, 0))
            tk.Label(card, text=sym, bg=BG2, fg="#BBBBBB",
                     font=(HN, 8)).pack(anchor=tk.W, padx=16)
            lbl = tk.Label(card, text="—", bg=BG2, fg=color,
                           font=(HN, 28, "bold"))
            lbl.pack(padx=16, pady=(4, 2))
            tk.Label(card, text="USD / troy oz", bg=BG2, fg="#AAAAAA",
                     font=(HN, 8)).pack(anchor=tk.W, padx=16, pady=(0, 12))
            self._metal_labels[key] = lbl

        # Melt calculator
        tk.Frame(scroll_inner, bg="#DDDDDD", height=1).pack(fill=tk.X, padx=20)
        mc = tk.Frame(scroll_inner, bg=BG)
        mc.pack(fill=tk.X, padx=20, pady=16)
        tk.Label(mc, text="MELT VALUE CALCULATOR", bg=BG, fg="#888888",
                 font=(HN, 8, "bold")).pack(anchor=tk.W, pady=(0, 8))
        mr = tk.Frame(mc, bg=BG)
        mr.pack(fill=tk.X)
        tk.Label(mr, text="COIN TYPE", bg=BG, fg="#888888",
                 font=(HN, 8, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self._melt_coin_var = tk.StringVar()
        ttk.Combobox(mr, textvariable=self._melt_coin_var,
                     values=sorted(list(SILVER_CONTENT) + list(GOLD_CONTENT)),
                     width=32).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(mr, text="CALCULATE", style="Accent.TButton",
                   command=self._calc_melt).pack(side=tk.LEFT)
        self._melt_result_var = tk.StringVar(value="")
        tk.Label(mc, textvariable=self._melt_result_var,
                 bg=BG, fg=GREEN, font=(HN, 14, "bold")).pack(anchor=tk.W, pady=(10, 0))

    def _build_population_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  POPULATION  ")

        toolbar = tk.Frame(frame, bg=BG3)
        toolbar.pack(fill=tk.X)
        tk.Frame(toolbar, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(toolbar, text="NGC CENSUS",
                   command=self._fetch_ngc_pop).pack(side=tk.LEFT, padx=(10, 4), pady=6)
        ttk.Button(toolbar, text="PCGS POPULATION",
                   command=self._fetch_pcgs_pop).pack(side=tk.LEFT, padx=(0, 4), pady=6)
        ttk.Button(toolbar, text="PCGS PRICE GUIDE",
                   command=self._fetch_pcgs_price).pack(side=tk.LEFT, pady=6)
        tk.Frame(frame, bg="#DDDDDD", height=1).pack(fill=tk.X)

        self._pop_text = scrolledtext.ScrolledText(
            frame, bg=BG, fg=FG, font=("Helvetica Neue", 10),
            relief=tk.FLAT, wrap=tk.NONE,
            borderwidth=0, highlightthickness=0,
        )
        self._pop_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self._pop_text.tag_configure("header", foreground=ACCENT, font=("Helvetica Neue", 10, "bold"))
        self._pop_text.tag_configure("high",   foreground=RED)
        self._pop_text.tag_configure("low",    foreground=GREEN)
        self._pop_text.tag_configure("url",    foreground=TEAL)
        self._pop_text.tag_configure("error",  foreground=RED)
        self._pop_text.tag_configure("notice", foreground=YELLOW)

    def _build_world_coins_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  WORLD COINS (KM#)  ")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        # ── Toolbar ──
        toolbar = tk.Frame(frame, bg=BG3)
        toolbar.grid(row=0, column=0, sticky="ew")
        tk.Frame(toolbar, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(toolbar, text="SEARCH", bg=BG3, fg="#888888",
                 font=(HN, 8, "bold")).pack(side=tk.LEFT, padx=(10, 4), pady=8)
        self._wc_search_var = tk.StringVar()
        wc_entry = ttk.Entry(toolbar, textvariable=self._wc_search_var, width=28)
        wc_entry.pack(side=tk.LEFT, padx=(0, 10))
        wc_entry.bind("<Return>", lambda _: self._wc_search())

        tk.Label(toolbar, text="COUNTRY", bg=BG3, fg="#888888",
                 font=(HN, 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self._wc_country_var = tk.StringVar(value="All")
        self._wc_country_cb = ttk.Combobox(toolbar, textvariable=self._wc_country_var,
                                            width=20, state="readonly")
        self._wc_country_cb["values"] = ["All"]
        self._wc_country_cb.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="SEARCH",
                   command=self._wc_search).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(toolbar, text="SYNC DRIVE",
                   command=self._wc_sync_drive).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(toolbar, text="INDEX CATALOGS", style="Accent.TButton",
                   command=self._wc_start_index).pack(side=tk.LEFT)

        tk.Frame(frame, bg="#DDDDDD", height=1).grid(row=1, column=0, sticky="ew")

        # ── Results treeview ──
        tree_frame = tk.Frame(frame, bg=BG)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        wc_cols = ("COUNTRY", "KM#", "DENOMINATION", "METAL", "YEAR",
                   "VG", "F", "VF", "XF", "UNC/MS60", "MS63")
        self._wc_tree = ttk.Treeview(tree_frame, columns=wc_cols,
                                      show="headings", selectmode="browse")
        wc_widths = [120, 70, 150, 130, 70, 55, 55, 60, 60, 80, 60]
        for col, w in zip(wc_cols, wc_widths):
            self._wc_tree.heading(col, text=col,
                                   command=lambda c=col: self._wc_sort(c))
            self._wc_tree.column(col, width=w, minwidth=30)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,  command=self._wc_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self._wc_tree.xview)
        self._wc_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._wc_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # ── Status bar ──
        status_row = tk.Frame(frame, bg=BG3)
        status_row.grid(row=3, column=0, sticky="ew")
        tk.Frame(status_row, bg=ACCENT, width=4).pack(side=tk.LEFT, fill=tk.Y)
        self._wc_progress = ttk.Progressbar(status_row, mode="determinate", length=180)
        self._wc_progress.pack(side=tk.RIGHT, padx=(0, 10), pady=4)
        self._wc_status_var = tk.StringVar(value="Ready — click INDEX CATALOGS to build the database.")
        tk.Label(status_row, textvariable=self._wc_status_var,
                 bg=BG3, fg="#666666", font=(HN, 9), anchor=tk.W
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=4)

        self._wc_index_stop = threading.Event()

        # Populate country dropdown from existing DB on startup
        self.after(500, self._wc_load_countries)

    # ── AI IMAGE SCAN TAB ─────────────────────────────────────────────────────

    def _build_ai_scan_tab(self):
        HN = "Helvetica Neue"
        frame = ttk.Frame(self._nb)
        self._nb.add(frame, text="  🔍 AI IMAGE SCAN  ")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = tk.Frame(frame, bg=BG3)
        tb.grid(row=0, column=0, sticky="ew")
        tk.Frame(tb, bg=ACCENT, width=5).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(tb, text="  AI COIN IDENTIFICATION",
                 bg=BG3, fg="#FFFFFF", font=(HN, 10, "bold")).pack(side=tk.LEFT, pady=10)
        tk.Label(tb, text="  — upload a coin photo to identify, price, and cross-reference across all sources",
                 bg=BG3, fg=FG2, font=(HN, 9)).pack(side=tk.LEFT)
        tk.Frame(frame, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew")

        # ── Main body: left upload + right results ────────────────────────────
        body = tk.Frame(frame, bg=BG)
        body.grid(row=2, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=0)   # upload panel fixed
        body.columnconfigure(1, weight=1)   # results expands

        # ── LEFT: Upload + coin image viewer ─────────────────────────────────
        left = tk.Frame(body, bg=BG2, width=320)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        # Scrollable inner area for the left panel
        left_scroll_outer, left_inner = self._scrollable_in(left, bg=BG2)
        left_scroll_outer.grid(row=0, column=0, sticky="nsew")

        # Drop zone
        dz_outer = tk.Frame(left_inner, bg=BORDER, padx=1, pady=1)
        dz_outer.pack(fill=tk.X, padx=16, pady=(20, 8))
        self._ai_dropzone = tk.Frame(dz_outer, bg=GOLD_LT, height=160, cursor="hand2")
        self._ai_dropzone.pack(fill=tk.X)
        self._ai_dropzone.pack_propagate(False)
        tk.Label(self._ai_dropzone, text="⬆", bg=GOLD_LT, fg=ACCENT,
                 font=(HN, 28)).pack(pady=(24, 4))
        tk.Label(self._ai_dropzone, text="DROP COIN IMAGE HERE",
                 bg=GOLD_LT, fg=ACCENT, font=(HN, 9, "bold")).pack()
        tk.Label(self._ai_dropzone, text="or click to browse",
                 bg=GOLD_LT, fg=FG2, font=(HN, 8)).pack(pady=(2, 0))
        self._ai_dropzone.bind("<Button-1>", lambda _: self._ai_browse())
        for child in self._ai_dropzone.winfo_children():
            child.bind("<Button-1>", lambda _: self._ai_browse())

        ttk.Button(left_inner, text="BROWSE FILE", style="Accent.TButton",
                   command=self._ai_browse).pack(padx=16, pady=4, fill=tk.X)
        ttk.Button(left_inner, text="CLEAR", command=self._ai_clear
                   ).pack(padx=16, pady=(0, 12), fill=tk.X)

        tk.Frame(left_inner, bg=BORDER, height=1).pack(fill=tk.X, padx=16)

        # Coin image display — pixel-sized via blank image
        _ai_blank = tk.PhotoImage(width=280, height=160)
        _ai_blank.put("#1A1714", to=(0, 0, 280, 160))

        tk.Label(left_inner, text="OBVERSE", bg=BG2, fg=FG2,
                 font=(HN, 7, "bold")).pack(pady=(12, 3))
        self._ai_img_obv = tk.Label(left_inner, bg=BG3, image=_ai_blank,
                                    text="—", compound=tk.CENTER,
                                    fg=BORDER, font=(HN, 18))
        self._ai_img_obv._blank = _ai_blank
        self._ai_img_obv.pack(padx=16)

        tk.Label(left_inner, text="REVERSE", bg=BG2, fg=FG2,
                 font=(HN, 7, "bold")).pack(pady=(10, 3))
        self._ai_img_rev = tk.Label(left_inner, bg=BG3, image=_ai_blank,
                                    text="—", compound=tk.CENTER,
                                    fg=BORDER, font=(HN, 18))
        self._ai_img_rev._blank = _ai_blank
        self._ai_img_rev.pack(padx=16, pady=(0, 16))

        # ── RIGHT: Identification + cross-reference ───────────────────────────
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # ID card
        id_card = tk.Frame(right, bg=BG2,
                           highlightbackground=BORDER, highlightthickness=1)
        id_card.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        # Gold top bar on ID card
        tk.Frame(id_card, bg=ACCENT, height=3).pack(fill=tk.X)

        id_top = tk.Frame(id_card, bg=BG2)
        id_top.pack(fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(id_top, text="AI IDENTIFICATION", bg=BG2, fg=FG2,
                 font=(HN, 8, "bold")).pack(side=tk.LEFT)
        self._ai_conf_lbl = tk.Label(id_top, text="", bg=BG2, fg=GREEN,
                                     font=(HN, 8, "bold"))
        self._ai_conf_lbl.pack(side=tk.RIGHT)

        # ID fields grid
        id_grid = tk.Frame(id_card, bg=BG2)
        id_grid.pack(fill=tk.X, padx=16, pady=(6, 12))

        self._ai_fields = {}
        field_defs = [
            ("COIN",        "coin_name"),
            ("COUNTRY",     "country"),
            ("YEAR",        "year"),
            ("MINT",        "mint"),
            ("DENOMINATION","denomination"),
            ("KM #",        "km_number"),
            ("METAL",       "metal"),
            ("GRADE EST.",  "grade_estimate"),
        ]
        for row_i, (label, key) in enumerate(field_defs):
            tk.Label(id_grid, text=label, bg=BG2, fg=FG2,
                     font=(HN, 8, "bold"), anchor=tk.W, width=12
                     ).grid(row=row_i, column=0, sticky="w", pady=2)
            var = tk.StringVar(value="—")
            self._ai_fields[key] = var
            tk.Label(id_grid, textvariable=var, bg=BG2, fg=FG,
                     font=(HN, 10), anchor=tk.W
                     ).grid(row=row_i, column=1, sticky="ew", padx=(8, 0), pady=2)
        id_grid.columnconfigure(1, weight=1)

        # Notes
        self._ai_notes_var = tk.StringVar(value="")
        tk.Label(id_card, textvariable=self._ai_notes_var, bg=BG2, fg=FG2,
                 font=(HN, 9, "italic"), wraplength=420, justify=tk.LEFT,
                 anchor=tk.W).pack(fill=tk.X, padx=16, pady=(0, 8))

        # Action buttons
        btn_row = tk.Frame(id_card, bg=BG2)
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 12))
        ttk.Button(btn_row, text="SEARCH ALL SOURCES", style="Accent.TButton",
                   command=self._ai_search_all).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="AUTO-FILL SEARCH FIELDS",
                   command=self._ai_autofill).pack(side=tk.LEFT)
        self._ai_spin_lbl = tk.Label(btn_row, text="", bg=BG2, fg=ACCENT,
                                     font=(HN, 11))
        self._ai_spin_lbl.pack(side=tk.LEFT, padx=12)

        # Cross-reference results panel
        xref_hdr = tk.Frame(right, bg=BG)
        xref_hdr.grid(row=1, column=0, sticky="nsew")
        xref_hdr.rowconfigure(0, weight=1)
        xref_hdr.columnconfigure(0, weight=1)

        self._ai_xref = scrolledtext.ScrolledText(
            xref_hdr, bg=BG, fg=FG, font=(HN, 10),
            relief=tk.FLAT, wrap=tk.WORD,
            borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER,
        )
        self._ai_xref.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self._ai_xref.tag_configure("section", foreground=ACCENT,
                                     font=(HN, 10, "bold"))
        self._ai_xref.tag_configure("key",     foreground=FG2,
                                     font=(HN, 9, "bold"))
        self._ai_xref.tag_configure("val",     foreground=FG, font=(HN, 10))
        self._ai_xref.tag_configure("price",   foreground=GREEN,
                                     font=(HN, 11, "bold"))
        self._ai_xref.tag_configure("source",  foreground=BLUE,
                                     font=(HN, 9))
        self._ai_xref.tag_configure("error",   foreground=RED, font=(HN, 9))
        self._ai_xref.tag_configure("rule",    foreground=BORDER)

        self._ai_path = None
        self._ai_result = {}

        # Show setup hint if API key not yet configured
        if not CoinVisionIdentifier._get_api_key():
            self._ai_xref.configure(state=tk.NORMAL)
            self._ai_xref.insert(tk.END,
                "⚠  Anthropic API key not configured.\n\n"
                "To enable AI coin identification:\n"
                "  1. Click CREDENTIALS\n"
                "  2. Find 'Anthropic (AI Vision)'\n"
                "  3. Paste your API key in the Password field\n"
                "  4. Click SAVE & CONNECT\n\n"
                "Then upload a coin image to identify it.\n",
                "error"
            )

    def _ai_browse(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Coin Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff"),
                       ("All files", "*.*")]
        )
        if path:
            self._ai_load_image(path)

    def _ai_load_image(self, path: str):
        self._ai_path = path
        # Show uploaded image in obverse slot; reset reverse
        if PIL_OK:
            try:
                img = PILImage.open(path).convert("RGB")
                img.thumbnail((260, 200), PILImage.LANCZOS)
                bg = PILImage.new("RGB", (260, 200), (232, 228, 220))
                x = (260 - img.width)  // 2
                y = (200 - img.height) // 2
                bg.paste(img, (x, y))
                self._ai_tk_obv = ImageTk.PhotoImage(bg)
                self._ai_img_obv.configure(image=self._ai_tk_obv, text="")
            except Exception:
                self._ai_img_obv.configure(image=self._ai_img_obv._blank, text="?", fg=RED)
        self._ai_img_rev.configure(image=self._ai_img_rev._blank, text="reverse\nafter ID", fg=FG2)
        # Reset fields and run identification
        for var in self._ai_fields.values():
            var.set("…")
        self._ai_notes_var.set("")
        self._ai_conf_lbl.configure(text="Identifying…", fg=ACCENT)
        self._ai_spin_lbl.configure(text="⏳")
        self._ai_xref_clear()
        self._ai_xref.insert(tk.END, "Running AI identification…\n", "key")
        CoinVisionIdentifier.identify_threaded(path, self._ai_on_identified)

    def _ai_on_identified(self, result: dict, error: str):
        self._q.put(("ai_identified", (result, error)))

    def _ai_clear(self):
        self._ai_path = None
        self._ai_result = {}
        self._ai_img_obv.configure(image=self._ai_img_obv._blank, text="—", fg=BORDER)
        self._ai_img_rev.configure(image=self._ai_img_rev._blank, text="—", fg=BORDER)
        self._ai_conf_lbl.configure(text="")
        self._ai_spin_lbl.configure(text="")
        for var in self._ai_fields.values():
            var.set("—")
        self._ai_notes_var.set("")
        self._ai_xref_clear()

    def _ai_xref_clear(self):
        self._ai_xref.configure(state=tk.NORMAL)
        self._ai_xref.delete("1.0", tk.END)

    def _ai_autofill(self):
        if not self._ai_result:
            return
        r = self._ai_result
        if r.get("coin_name"):    self._name_var.set(r["coin_name"])
        if r.get("year"):         self._year_var.set(r["year"])
        if r.get("mint"):         self._mint_var.set(r["mint"])
        if r.get("km_number"):    self._km_var.set(r["km_number"])
        if r.get("grade_estimate"):
            # Extract the grade code only e.g. "VF-30" from "VF-30 (estimated...)"
            g = r["grade_estimate"].split()[0]
            self._grade_var.set(g)

    def _ai_search_all(self):
        self._ai_autofill()
        self._search("all")

    def _ai_populate_result(self, result: dict):
        self._ai_result = result
        conf = result.get("confidence", 0)
        self._ai_conf_lbl.configure(
            text=f"Confidence: {conf*100:.0f}%",
            fg=GREEN if conf >= 0.8 else (YELLOW if conf >= 0.5 else RED)
        )
        for key, var in self._ai_fields.items():
            var.set(result.get(key) or "—")
        self._ai_notes_var.set(result.get("notes", ""))
        self._ai_spin_lbl.configure(text="✓", fg=GREEN)

        # Cross-reference
        self._ai_xref_clear()
        t = self._ai_xref

        def ins(txt, tag="val"): t.insert(tk.END, txt, tag)

        model_used = result.get("_model", "")
        cached     = result.get("_cached", False)
        model_lbl  = " [cached]" if cached else (f" [{model_used.split('-')[1]}]" if model_used else "")
        ins(f"─── COIN IDENTIFIED{model_lbl} ───────────────────────────\n", "rule")
        ins(f"  {result.get('coin_name','?')}  ", "section")
        ins(f"{result.get('year','')}  {result.get('country','')}\n\n", "val")

        if result.get("obverse_desc"):
            ins("OBV  ", "key"); ins(result["obverse_desc"] + "\n", "val")
        if result.get("reverse_desc"):
            ins("REV  ", "key"); ins(result["reverse_desc"] + "\n", "val")
        if result.get("key_features"):
            ins("FEATURES  ", "key")
            ins(", ".join(result["key_features"]) + "\n", "val")
        ins("\n")

        # Catalog lookup — KM# exact match first, then broader search
        ins("─── CATALOG LOOKUP ─────────────────────────────────────\n", "rule")
        km        = result.get("km_number", "").strip()
        coin_name = result.get("coin_name", "").strip()
        country   = result.get("country",   "").strip()
        if km or coin_name:
            def do_catalog_lookup():
                rows: List[Dict] = []
                if km:
                    rows = WorldCoinDB.search_by_km(km, country=country, limit=12)
                if not rows and coin_name:
                    rows = WorldCoinDB.search(coin_name, country_filter=country, limit=12)
                if not rows and coin_name:
                    rows = WorldCoinDB.search(coin_name, limit=12)
                self._q.put(("ai_catalog", rows))
            threading.Thread(target=do_catalog_lookup, daemon=True).start()
            ins("Searching catalogs…\n", "key")
        else:
            ins("No KM# or coin name to search catalogs.\n", "error")

        # NGC + PCGS cross-reference
        ins("\n─── POPULATION CROSS-REFERENCE ────────────────────────\n", "rule")
        ins("Fetching NGC & PCGS data via main search…\n", "key")

    def _wc_load_countries(self):
        """Load country list from existing DB (if any) into the dropdown."""
        def run():
            countries = WorldCoinDB.countries()
            total = WorldCoinDB.total_coins()
            self._q.put(("wc_countries", (countries, total)))
        threading.Thread(target=run, daemon=True).start()

    def _wc_sync_drive(self):
        """Download / refresh coin catalog PDFs from the Google Drive folder."""
        try:
            import gdown as _gdown
        except ImportError:
            messagebox.showerror("Missing Library",
                "gdown is not installed.\n\nRun:\n  pip install gdown",
                parent=self)
            return

        os.makedirs(_CATALOG_LOCAL_DIR, exist_ok=True)
        self._wc_status_var.set("Syncing catalogs from Google Drive…")
        self._wc_progress.config(mode="indeterminate")
        self._wc_progress.start(12)

        def run():
            try:
                url = f"https://drive.google.com/drive/folders/{_GDRIVE_FOLDER_ID}"
                _gdown.download_folder(url=url, output=_CATALOG_LOCAL_DIR,
                                       quiet=False, use_cookies=False)
                files = [f for f in os.listdir(_CATALOG_LOCAL_DIR)
                         if f.lower().endswith(".pdf")]
                self._q.put(("wc_sync_done", f"Drive sync complete — {len(files)} PDF(s) in catalog folder."))
            except Exception as exc:
                self._q.put(("wc_sync_done", f"Drive sync error: {exc}"))

        threading.Thread(target=run, daemon=True).start()

    def _wc_start_index(self):
        """Start background indexing of all available catalogs."""
        if not PDFPLUMBER_OK:
            messagebox.showerror("Missing Library",
                "pdfplumber is not installed.\n\nRun:\n  pip install pdfplumber",
                parent=self)
            return

        # Merge known catalogs with any additional PDFs discovered on disk
        catalogs = dict(_CATALOG_PATHS)
        catalogs.update({k: v for k, v in _discover_catalogs().items()
                         if k not in catalogs and v not in catalogs.values()})

        available = {cat: path for cat, path in catalogs.items()
                     if os.path.exists(path)}
        missing   = [cat for cat, path in catalogs.items()
                     if not os.path.exists(path)]

        if not available:
            messagebox.showerror("No Catalogs Found",
                "No PDF catalogs found. Expected locations:\n" +
                "\n".join(f"  {p}" for p in list(catalogs.values())[:3]) +
                "\n\nDownload PDFs from iCloud first (right-click → Download Now).",
                parent=self)
            return

        ocr_note = " (macOS OCR enabled for scanned pages)" if MACOS_OCR_OK else ""
        if missing:
            self._wc_status_var.set(
                f"Note: {len(missing)} catalog(s) not found. "
                f"Indexing {len(available)} available catalog(s){ocr_note}…")
        else:
            self._wc_status_var.set(f"Indexing {len(available)} catalog(s){ocr_note}…")

        self._wc_index_stop.clear()
        self._wc_progress["value"] = 0

        def run():
            cat_list = list(available.items())
            for i, (cat, path) in enumerate(cat_list):
                meta = WorldCoinDB.catalog_status(cat)
                if meta["done"]:
                    self._q.put(("wc_progress", (cat, meta["total_pages"],
                                                  meta["total_pages"], True,
                                                  i, len(cat_list))))
                    continue

                def make_cb(catalog=cat, idx=i, total_cats=len(cat_list)):
                    def cb(done, total, done_flag=False):
                        self._q.put(("wc_progress", (catalog, done, total,
                                                       done_flag, idx, total_cats)))
                    return cb

                WorldCoinIndexer.index_catalog(
                    cat, path,
                    progress_cb=make_cb(),
                    stop_event=self._wc_index_stop)

                if self._wc_index_stop.is_set():
                    break

            countries = WorldCoinDB.countries()
            total = WorldCoinDB.total_coins()
            self._q.put(("wc_countries", (countries, total)))

        threading.Thread(target=run, daemon=True).start()

    def _wc_search(self):
        query = self._wc_search_var.get().strip()
        country = self._wc_country_var.get()
        if country == "All":
            country = ""
        if not query:
            self._wc_status_var.set("Enter a denomination, KM# or country to search.")
            return
        self._wc_status_var.set(f"Searching for '{query}'…")

        def run():
            results = WorldCoinDB.search(query, country_filter=country)
            self._q.put(("wc_results", results))

        threading.Thread(target=run, daemon=True).start()

    def _wc_sort(self, col: str):
        items = [(self._wc_tree.set(k, col), k)
                 for k in self._wc_tree.get_children("")]
        try:
            items.sort(key=lambda t: float(t[0].replace(",", "").replace("—", "0")))
        except ValueError:
            items.sort(key=lambda t: t[0].lower())
        for idx, (_, k) in enumerate(items):
            self._wc_tree.move(k, "", idx)

    def _wc_display_results(self, rows: List[Dict]):
        self._wc_tree.delete(*self._wc_tree.get_children())
        for r in rows:
            vf  = r.get("vf") or "—"
            xf  = r.get("xf") or "—"
            unc = r.get("unc") or "—"
            ms3 = r.get("ms63") or "—"
            vg  = r.get("vg") or "—"
            fg  = r.get("f_grade") or "—"
            self._wc_tree.insert("", tk.END, values=(
                r.get("country", ""),
                r.get("km_number", ""),
                r.get("denomination", ""),
                (r.get("metal") or "")[:28],
                r.get("date_year", ""),
                vg, fg, vf, xf, unc, ms3,
            ))
        self._wc_status_var.set(f"{len(rows)} record(s) found.")

    # ── Params / validation ───────────────────────────────────────────────────

    def _params(self):
        return (
            self._name_var.get().strip(),
            self._year_var.get().strip(),
            self._mint_var.get().strip(),
            self._grade_var.get().strip(),
            self._holder_var.get().strip(),
            self._km_var.get().strip(),
            self._ngc_cert_var.get().strip(),
            self._pcgs_cert_var.get().strip(),
        )

    def _validate(self) -> bool:
        if not self._name_var.get().strip():
            messagebox.showwarning("Missing Field", "Enter a coin name.", parent=self)
            return False
        return True

    # ── Search ────────────────────────────────────────────────────────────────

    def _search(self, source: str):
        if not self._validate() or self._busy:
            return
        self._busy = True
        self._progress.start(12)
        name, year, mint, grade, holder, km, ngc_cert, pcgs_cert = self._params()

        augmented_name = name
        if km:
            augmented_name += f" KM#{km}"
        if ngc_cert:
            augmented_name += f" {ngc_cert}"
        if pcgs_cert:
            augmented_name += f" {pcgs_cert}"

        self._status(f"Searching {source.title()}…")

        FETCHERS = {
            "heritage":          HeritageFetcher,
            "ebay":              eBayFetcher,
            "sedwick":           SedwickFetcher,
            "christies":         ChristiesFetcher,
            "greatcollections":  GreatCollectionsFetcher,
            "sothebys":          SothebysFileFetcher,
            "coinstrail":        CoinstrailFetcher,
        }

        def run():
            new: List[AuctionResult] = []
            fetch_errors: List[str] = []
            try:
                for key, fetcher in FETCHERS.items():
                    if source not in (key, "all"):
                        continue
                    try:
                        r = fetcher.search(augmented_name, year, mint, grade, holder)
                        if not r:
                            fetch_errors.append(
                                f"{fetcher.SOURCE}: no results found (try different search terms)"
                            )
                        new.extend(r)
                    except FetchError as fe:
                        fetch_errors.append(str(fe))
                        log.warning("Fetch error: %s", fe)
                    except Exception as e:
                        fetch_errors.append(f"{key.title()}: unexpected error — {e}")
                        log.exception("Unexpected fetch error (%s):", key)
            except Exception as e:
                fetch_errors.append(f"Search loop error: {e}")
                log.exception("Search loop crashed:")
            finally:
                self._results.extend(new)
                try:
                    analysis = AnalysisEngine.analyze(
                        self._results, holder, grade, self._metal_prices, name
                    )
                except Exception as e:
                    analysis = CoinAnalysis()
                    fetch_errors.append(f"Analysis error: {e}")
                    log.exception("Analysis crashed:")
                self._q.put(("results", (new, analysis, fetch_errors)))

        threading.Thread(target=run, daemon=True).start()

    # ── Metal prices ──────────────────────────────────────────────────────────

    def _refresh_metals(self):
        if self._busy:
            return
        self._status("Refreshing metal prices…")
        threading.Thread(target=self._fetch_metals_worker, daemon=True).start()

    def _start_metal_refresh(self):
        threading.Thread(target=self._fetch_metals_worker, daemon=True).start()
        self.after(300_000, self._start_metal_refresh)

    def _fetch_metals_worker(self):
        prices, err = MetalPriceFetcher.fetch()
        if prices:
            self._metal_prices.update(prices)
        self._q.put(("metals", (prices, err)))

    # ── NGC / PCGS lookups ────────────────────────────────────────────────────

    def _fetch_ngc_pop(self):
        name, year, mint, *_ = self._params()
        if not name:
            messagebox.showwarning("Missing Field", "Enter a coin name first.", parent=self)
            return
        self._status("Fetching NGC population…")

        def run():
            data = NGCPopFetcher.fetch(name, year, mint)
            self._q.put(("ngc_pop", data))

        threading.Thread(target=run, daemon=True).start()

    def _fetch_pcgs_pop(self):
        name, year, mint, *_ = self._params()
        if not name:
            messagebox.showwarning("Missing Field", "Enter a coin name first.", parent=self)
            return
        self._status("Fetching PCGS population…")
        def run():
            data = PCGSPopFetcher.fetch(name, year, mint)
            self._q.put(("pcgs_pop", data))
        threading.Thread(target=run, daemon=True).start()

    def _fetch_pcgs_price(self):
        name, year, mint, *_ = self._params()
        if not name:
            messagebox.showwarning("Missing Field", "Enter a coin name first.", parent=self)
            return
        self._status("Fetching PCGS prices…")
        def run():
            data = PCGSPriceFetcher.fetch(name, year, mint)
            self._q.put(("pcgs_price", data))
        threading.Thread(target=run, daemon=True).start()

    def _open_ngc_cert(self):
        cert = self._ngc_cert_var.get().strip()
        if not cert:
            messagebox.showwarning("Missing Cert #", "Enter an NGC certificate number.", parent=self)
            return
        self._status(f"Looking up NGC cert #{cert}…")
        def run():
            data = NGCCertFetcher.fetch(cert)
            self._q.put(("ngc_cert", data))
        threading.Thread(target=run, daemon=True).start()

    def _open_pcgs_cert(self):
        cert = self._pcgs_cert_var.get().strip()
        if not cert:
            messagebox.showwarning("Missing Cert #", "Enter a PCGS certificate number.", parent=self)
            return
        self._status(f"Looking up PCGS cert #{cert}…")
        def run():
            data = PCGSCertFetcher.fetch(cert)
            self._q.put(("pcgs_cert", data))
        threading.Thread(target=run, daemon=True).start()

    def _open_credentials(self):
        CredentialsDialog(self)

    # ── Melt calculator ───────────────────────────────────────────────────────

    def _calc_melt(self):
        coin = self._melt_coin_var.get().lower().strip()
        if not coin:
            return
        oz = SILVER_CONTENT.get(coin) or GOLD_CONTENT.get(coin)
        if oz is None:
            self._melt_result_var.set("Coin type not found in database.")
            return
        metal = "silver" if coin in SILVER_CONTENT else "gold"
        spot = self._metal_prices.get(metal, 0)
        if not spot:
            self._melt_result_var.set("Metal price not yet loaded — click Refresh.")
            return
        self._melt_result_var.set(
            f"Melt Value: ${oz * spot:,.2f}   ({oz} oz {metal.title()} × ${spot:,.2f}/oz)"
        )

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _clear(self):
        self._results.clear()
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._summary_var.set("Results cleared.")
        self._flags_text.delete("1.0", tk.END)
        self._xover_text.delete("1.0", tk.END)
        self._crossover_var.set("—")
        self._regrade_var.set("—")
        self._roi_var.set("—")
        self._stats_text.delete("1.0", tk.END)
        self._status("Results cleared.")

    # ── Tree sort / click ─────────────────────────────────────────────────────

    def _sort_tree(self, col: str):
        items = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        try:
            items.sort(key=lambda t: float(t[0].replace("$", "").replace(",", "")))
        except ValueError:
            items.sort(key=lambda t: t[0].lower())
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)

    def _on_tree_select(self, _event):
        """Single-click: load coin images for the selected row."""
        item = self._tree.focus()
        if not item:
            return
        idx = self._tree.index(item)
        if idx >= len(self._results):
            return
        result = self._results[idx]
        price_str = f"${result.price:,.0f}" if result.price > 0 else "N/A"
        self._img_info_var.set(
            f"{result.source}\n{result.description[:45]}\n{price_str}"
        )
        if not PIL_OK or not result.url:
            return
        # Reset panels to loading state
        self._img_obv.configure(image=self._img_obv._blank, text="⏳", fg=TEAL)
        self._img_rev.configure(image=self._img_rev._blank, text="⏳", fg=TEAL)
        r = result
        def _fetch():
            urls = CoinImageFetcher.fetch_urls(r)
            imgs = [CoinImageFetcher.load_image(u, size=205) for u in urls]
            self._q.put(("coin_images", imgs))
        threading.Thread(target=_fetch, daemon=True).start()

    def _display_coin_images(self, imgs: list):
        """Update the image panel labels with fetched PhotoImages."""
        placeholders = [self._img_obv, self._img_rev]
        for label, img in zip(placeholders, imgs):
            if img:
                label.configure(image=img, text="")
                label._img_ref = img  # prevent GC
            else:
                label.configure(image=label._blank, text="—", fg=FG)
        for label in placeholders[len(imgs):]:
            label.configure(image=label._blank, text="—", fg=FG)

    def _on_double_click(self, _event):
        item = self._tree.focus()
        if not item:
            return
        idx = self._tree.index(item)
        if idx >= len(self._results):
            return
        result = self._results[idx]
        # Show cached data immediately, then fetch extra details async
        placeholder: Dict = {"url": result.url, "data": {}, "error": ""}
        dlg = LotDetailDialog(self, result, placeholder)
        if result.url:
            def run():
                extra = LotDetailFetcher.fetch(result.url, result.source)
                self._q.put(("lot_detail", (dlg, result, extra)))
            threading.Thread(target=run, daemon=True).start()

    # ── Queue processor ───────────────────────────────────────────────────────

    def _process_queue(self):
        try:
            while True:
                msg_type, data = self._q.get_nowait()
                if msg_type == "results":
                    new_results, analysis, errors = data
                    self._display_results(new_results, analysis, errors)
                    self._busy = False
                    self._progress.stop()
                elif msg_type == "metals":
                    prices, err = data
                    self._display_metals(prices, err)
                elif msg_type == "ngc_pop":
                    self._display_ngc_pop(data)
                elif msg_type == "pcgs_pop":
                    self._display_pcgs_pop(data)
                elif msg_type == "pcgs_price":
                    self._display_pcgs_price(data)
                elif msg_type == "ngc_cert":
                    CertDetailDialog(self, data, "NGC")
                    self._status(f"NGC cert #{data.get('cert','')} — "
                                 + ("loaded" if data.get("data") else data.get("error", "no data")))
                elif msg_type == "pcgs_cert":
                    CertDetailDialog(self, data, "PCGS")
                    self._status(f"PCGS cert #{data.get('cert','')} — "
                                 + ("loaded" if data.get("data") else data.get("error", "no data")))
                elif msg_type == "coin_images":
                    self._display_coin_images(data)
                elif msg_type == "wc_sync_done":
                    try:
                        self._wc_progress.stop()
                    except Exception:
                        pass
                    self._wc_progress.config(mode="determinate")
                    self._wc_progress["value"] = 100
                    self._wc_status_var.set(data)
                elif msg_type == "wc_progress":
                    cat, done, total, is_done, cat_idx, cat_count = data
                    pct = int(done / total * 100) if total else 0
                    self._wc_progress["value"] = pct
                    if is_done:
                        self._wc_status_var.set(
                            f"[{cat_idx+1}/{cat_count}] {cat}: complete ({total:,} pages). "
                            + ("All catalogs indexed!" if cat_idx+1 == cat_count else "")
                        )
                    else:
                        self._wc_status_var.set(
                            f"Indexing {cat} [{cat_idx+1}/{cat_count}]: {done:,}/{total:,} pages ({pct}%)")
                elif msg_type == "wc_countries":
                    countries, total_coins = data
                    if countries:
                        self._wc_country_cb["values"] = ["All"] + countries
                        self._wc_country_var.set("All")
                        self._wc_status_var.set(
                            f"Catalog ready: {total_coins:,} coins from {len(countries)} countries.")
                        self._wc_progress["value"] = 100
                elif msg_type == "wc_results":
                    self._wc_display_results(data)
                elif msg_type == "ai_identified":
                    result, error = data
                    if error:
                        self._ai_spin_lbl.configure(text="✗", fg=RED)
                        self._ai_conf_lbl.configure(text=f"Error: {error[:60]}", fg=RED)
                        self._ai_xref_clear()
                        self._ai_xref.insert(tk.END, f"Identification failed:\n{error}\n", "error")
                    else:
                        self._ai_populate_result(result)
                elif msg_type == "ai_catalog":
                    rows = data
                    t = self._ai_xref
                    t.configure(state=tk.NORMAL)
                    try:
                        idx = t.search("Searching catalogs", "1.0", tk.END)
                        if idx:
                            t.delete(idx, f"{idx} lineend+1c")
                    except Exception:
                        pass
                    if rows:
                        seen = set()
                        for row in rows:
                            catalog  = row.get("catalog",      "")
                            country  = row.get("country",      "")
                            km       = row.get("km_number",    "")
                            denom    = row.get("denomination", "")
                            metal    = row.get("metal",        "")
                            page_num = row.get("page_number",  0)
                            year     = row.get("date_year",    "")
                            mintage  = row.get("mintage",      "")
                            vg       = row.get("vg",           "")
                            vf       = row.get("vf",           "")
                            xf       = row.get("xf",           "")
                            ms60     = row.get("unc",          "")
                            ms63     = row.get("ms63",         "")
                            coin_key = (catalog, km, country)
                            header_needed = coin_key not in seen
                            seen.add(coin_key)
                            if header_needed:
                                t.insert(tk.END, f"\n  KM#{km}  ", "section")
                                t.insert(tk.END, f"{denom}  —  {country}\n", "val")
                                if catalog:
                                    pg = f"  p.{page_num}" if page_num else ""
                                    t.insert(tk.END, f"  Catalog: {catalog}{pg}\n", "source")
                                if metal:
                                    t.insert(tk.END, f"  Metal:   {metal}\n", "key")
                            if year:
                                parts = [f"  {year}"]
                                if mintage and mintage not in ("—", "0"):
                                    parts.append(f"  Mintage: {mintage}")
                                price_parts = []
                                for lbl, val in [("VG", vg), ("VF", vf), ("XF", xf),
                                                  ("MS-60", ms60), ("MS-63", ms63)]:
                                    if val and str(val).strip() not in ("", "—", "0", "0.0"):
                                        price_parts.append(f"{lbl}=${val}")
                                if price_parts:
                                    parts.append("  " + "  ".join(price_parts))
                                t.insert(tk.END, "".join(parts) + "\n", "price")
                    else:
                        t.insert(tk.END,
                            "  No catalog entries found.\n"
                            "  Tip: index catalogs in the World Coins tab first.\n",
                            "error")
                elif msg_type == "lot_detail":
                    dlg, result, extra = data
                    try:
                        if dlg.winfo_exists():
                            dlg.destroy()
                    except Exception:
                        pass
                    LotDetailDialog(self, result, extra)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _status(self, msg: str):
        self._status_var.set(msg)

    # ── Display helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _holder_alert_tag(holder_key: str) -> str:
        if holder_key in ("nci", "segs", "pci", "fico", "sgs", "acg", "accgs"):
            return "oldholder_high"
        if holder_key in ("anacs", "icg"):
            return "oldholder_mid"
        if holder_key == "raw":
            return "oldholder_raw"
        return ""

    def _display_results(self, new_results: List[AuctionResult],
                          analysis: CoinAnalysis, errors: List[str]):
        prices = [r.price for r in self._results if r.price > 0]

        for r in new_results:
            src_tag   = r.source.lower().replace("'", "").replace(" ", "")
            alert_tag = self._holder_alert_tag(r.old_holder_key)
            alert_txt = ""
            if r.old_holder_key:
                name, _ = OLD_HOLDERS_INFO.get(r.old_holder_key, (r.old_holder_key.upper(), ""))
                rates    = CROSSOVER_RATES.get(r.old_holder_key, {})
                gv       = AnalysisEngine.grade_value(r.grade)
                rate     = rates.get(AnalysisEngine._grade_tier(gv), 0)
                alert_txt = f"★ {name} {rate*100:.0f}%"

            price_str = f"${r.price:,.0f}" if r.price > 0 else "N/A"
            row_idx = len(self._tree.get_children())
            base_tags = [alert_tag if alert_tag else src_tag]
            if row_idx % 2 == 1:
                base_tags.append("alt_row")
            self._tree.insert("", tk.END,
                               values=(r.source, r.description, r.grade,
                                       r.holder, alert_txt, price_str, r.date),
                               tags=tuple(base_tags))

        n = len(self._results)
        if prices:
            avg = sum(prices) / len(prices)
            self._summary_var.set(
                f"{n} result(s)  —  Low: ${min(prices):,.0f}   "
                f"Avg: ${avg:,.0f}   High: ${max(prices):,.0f}"
            )
        else:
            self._summary_var.set(f"{n} result(s) found  (no prices parsed)")

        self._crossover_var.set(analysis.crossover_potential)
        self._regrade_var.set(analysis.regrade_potential)

        roi_txt = (
            f"1-Year:  +{analysis.roi_1yr:.1f}%\n"
            f"3-Year:  +{analysis.roi_3yr:.1f}%\n"
            f"5-Year:  +{analysis.roi_5yr:.1f}%"
        )
        if analysis.melt_value:
            roi_txt += f"\n\nMelt Value: ${analysis.melt_value:,.2f}"
        self._roi_var.set(roi_txt)

        self._xover_text.delete("1.0", tk.END)
        self._render_crossover_panel(analysis, errors)

        self._stats_text.delete("1.0", tk.END)
        if prices:
            lines = [
                f"Results:  {n}   Priced: {len(prices)}",
                f"Low:      ${min(prices):>12,.2f}",
                f"High:     ${max(prices):>12,.2f}",
                f"Average:  ${sum(prices)/len(prices):>12,.2f}",
            ]
            if len(prices) >= 2:
                lines += [
                    f"Median:   ${statistics.median(prices):>12,.2f}",
                    f"Std Dev:  ${statistics.stdev(prices):>12,.2f}",
                ]
            if analysis.melt_value:
                prem = (sum(prices)/len(prices) / analysis.melt_value - 1) * 100
                lines += [
                    f"Melt:     ${analysis.melt_value:>12,.2f}",
                    f"Avg melt premium: {prem:.1f}%",
                ]
            self._stats_text.insert(tk.END, "\n".join(lines))

        self._flags_text.delete("1.0", tk.END)
        if analysis.flags:
            for flag in analysis.flags:
                self._flags_text.insert(tk.END, f"  ★  {flag}\n")
        else:
            self._flags_text.insert(tk.END, "  No opportunity flags detected for this coin.\n")

        if errors:
            status = f"Done with {len(errors)} error(s): {errors[0]}"
            if len(errors) > 1:
                status += f" (+{len(errors)-1} more)"
        else:
            status = f"Done — {len(new_results)} new result(s) fetched."
        self._status(status)
        if new_results:
            self._nb.select(0)

    def _render_crossover_panel(self, analysis: CoinAnalysis, errors: List[str]):
        t = self._xover_text
        t.insert(tk.END, "CROSSOVER ANALYSIS\n", "header")
        t.insert(tk.END, "─" * 60 + "\n", "detail")

        if errors:
            t.insert(tk.END, "FETCH ERRORS:\n", "error")
            for e in errors:
                t.insert(tk.END, f"  ✗ {e}\n", "error")
            t.insert(tk.END, "\n")

        if analysis.recommended_service:
            t.insert(tk.END, "Recommended service: ", "detail")
            t.insert(tk.END, f"{analysis.recommended_service}\n", "recommend")

        if analysis.crossover_success_rate > 0:
            rate_pct = analysis.crossover_success_rate * 100
            color = "high" if rate_pct >= 65 else ("mid" if rate_pct >= 48 else "major")
            t.insert(tk.END, "Estimated upgrade success rate: ", "detail")
            t.insert(tk.END, f"{rate_pct:.0f}%\n", color)

        if analysis.crossover_details:
            t.insert(tk.END, "\n")
            for line in analysis.crossover_details:
                if "NGC/PCGS coins averaging" in line:
                    t.insert(tk.END, f"  {line}\n", "recommend")
                else:
                    t.insert(tk.END, f"  {line}\n", "note")

        if analysis.old_holders_found:
            t.insert(tk.END, "\nOLD / LESSER HOLDER COINS IN RESULTS:\n", "header")
            t.insert(tk.END, "─" * 60 + "\n", "detail")
            for item in analysis.old_holders_found:
                key      = item["holder_key"]
                name     = item["holder_name"]
                rates    = CROSSOVER_RATES.get(key, {})
                avg_rate = sum(rates.values()) / len(rates) if rates else 0
                color    = "high" if avg_rate >= 0.65 else ("mid" if avg_rate >= 0.48 else "major")
                t.insert(tk.END, f"\n  ◉ {name}  (~{avg_rate*100:.0f}% upgrade rate)\n", color)
                t.insert(tk.END, f"     {item['description'][:65]}\n", "detail")
                if item["price"]:
                    t.insert(tk.END, f"     Listed: ${item['price']:,.0f}  via {item['source']}\n", "detail")
                t.insert(tk.END, f"     {item['note']}\n", "note")
                t.insert(tk.END, f"     → Submit to: {analysis.recommended_service}\n", "recommend")
        elif not analysis.crossover_details:
            t.insert(tk.END, "\nNo old/lesser holder coins detected in current results.\n", "note")

    def _display_metals(self, prices: Dict[str, float], err: str):
        if not prices:
            self._metal_bar_lbl.config(text=f"  Metal prices unavailable — {err}", fg=RED)
            return
        parts = []
        for key, sym in (("gold", "Au"), ("silver", "Ag"),
                          ("platinum", "Pt"), ("palladium", "Pd")):
            p = prices.get(key, 0)
            if p:
                parts.append(f"{sym}: ${p:,.2f}")
                if key in self._metal_labels:
                    self._metal_labels[key].config(text=f"${p:,.2f}")
        if parts:
            self._metal_bar_lbl.config(text="  " + "   |   ".join(parts), fg=YELLOW)
        now = datetime.now().strftime("%H:%M:%S")
        self._metal_updated_var.set(f"  Last updated: {now}  (source: Kitco)")
        if self._melt_coin_var.get():
            self._calc_melt()

    def _display_ngc_pop(self, data: Dict):
        self._pop_text.delete("1.0", tk.END)
        url  = data.get("url", "")
        pops = data.get("populations", {})
        err  = data.get("error", "")

        self._pop_text.insert(tk.END, "NGC CENSUS DATA\n", "header")
        self._pop_text.insert(tk.END, f"URL: {url}\n\n", "url")

        if err:
            self._pop_text.insert(tk.END, f"Error: {err}\n\n", "error")

        if pops:
            self._pop_text.insert(tk.END, f"{'Grade':<14}{'Population':>12}\n", "header")
            self._pop_text.insert(tk.END, "─" * 28 + "\n")
            for grade, pop in sorted(pops.items()):
                try:
                    pop_n = int(re.sub(r"[^0-9]", "", pop))
                    tag = "high" if pop_n > 1000 else ("low" if pop_n < 50 else "")
                except ValueError:
                    tag = ""
                self._pop_text.insert(tk.END, f"{grade:<14}{pop:>12}\n", tag)
        else:
            self._pop_text.insert(tk.END,
                "No population data returned — NGC census uses JavaScript rendering.\n"
                "Try adding a session cookie via ⚙ Credentials if you have an NGC account.\n\n"
                "Population research tips:\n"
                "  ★  Low pop (< 50 coins graded) = scarce coin\n"
                "  ★  Compare pop at your grade vs. the grade above\n"
                "  ★  If next-grade pop is tiny, regrade risk is higher\n"
                "  ★  CAC stickers require exceptional eye appeal\n",
                "notice" if not err else "error",
            )

        self._nb.select(3)
        self._status("NGC population data loaded." if not err else f"NGC census: {err}")

    def _display_pcgs_pop(self, data: Dict):
        self._pop_text.delete("1.0", tk.END)
        url  = data.get("url", "")
        pops = data.get("populations", {})
        err  = data.get("error", "")

        self._pop_text.insert(tk.END, "PCGS POPULATION DATA\n", "header")
        self._pop_text.insert(tk.END, f"URL: {url}\n\n", "url")

        if err:
            self._pop_text.insert(tk.END, f"Error: {err}\n\n", "error")

        if pops:
            self._pop_text.insert(tk.END, f"{'Grade':<14}{'Population':>12}\n", "header")
            self._pop_text.insert(tk.END, "─" * 28 + "\n")
            for grade, pop in sorted(pops.items()):
                try:
                    pop_n = int(re.sub(r"[^0-9]", "", pop))
                    tag = "high" if pop_n > 1000 else ("low" if pop_n < 50 else "")
                except ValueError:
                    tag = ""
                self._pop_text.insert(tk.END, f"{grade:<14}{pop:>12}\n", tag)
        else:
            self._pop_text.insert(tk.END,
                "No population data returned — PCGS population uses JavaScript rendering.\n"
                "Try adding a session cookie via ⚙ Credentials if you have a PCGS account.\n",
                "notice",
            )

        self._nb.select(3)
        self._status("PCGS population data loaded." if not err else f"PCGS pop: {err}")

    def _display_pcgs_price(self, data: Dict):
        self._pop_text.delete("1.0", tk.END)
        url    = data.get("url", "")
        prices = data.get("prices", {})
        err    = data.get("error", "")

        coin_name = prices.pop("__coin__", "")
        self._pop_text.insert(tk.END, "PCGS PRICE GUIDE\n", "header")
        if coin_name:
            self._pop_text.insert(tk.END, f"{coin_name}\n", "header")
        self._pop_text.insert(tk.END, f"URL: {url}\n\n", "url")

        if err:
            self._pop_text.insert(tk.END, f"Error: {err}\n\n", "error")

        if prices:
            self._pop_text.insert(tk.END, f"{'Grade':<14}{'Price':>14}\n", "header")
            self._pop_text.insert(tk.END, "─" * 30 + "\n")
            for grade, price in prices.items():
                self._pop_text.insert(tk.END, f"{grade:<14}{price:>14}\n")
        else:
            self._pop_text.insert(tk.END,
                "No price data returned — PCGS prices page may require JavaScript.\n",
                "notice",
            )

        self._nb.select(3)
        self._status("PCGS prices loaded." if not err else f"PCGS prices: {err}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = NumismaticAgent()
    app.mainloop()
