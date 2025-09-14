# injector.py (multi-rule, per-rule remote_url, local/remote serve, CORS-safe)
import os
import re
import json
import yaml
import time
import logging
from pathlib import Path
from typing import List, Optional, Pattern, Dict, Any

from mitmproxy import http

try:
    import requests
except Exception:
    requests = None

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("figma-localize")


# -----------------------------
# Config loader
# -----------------------------
class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = (
            config_path
            or os.environ.get("FIGMA_LOCALIZE_CONFIG")
            or str(Path(__file__).with_name("config.yaml"))
        )

        self.version = None
        self.first_start = None

        self.language_pack: Dict[str, Any] = {}
        self.web_admin_host = None
        self.web_admin_port = None
        self.web_admin_open = None

        self.listen_port = None
        self.upstream_proxy = None
        self.upstream_http = None
        self.upstream_socks5 = None

        # New: list of rules (compat: single dict also supported)
        self.interception_rules: List[Dict[str, Any]] = []

        # Optional: force language header (default True if missing)
        self.force_lang = True

        self._load()

    def _load(self):
        path = Path(self.config_path)
        if not path.exists():
            logger.warning(f"[figma-localize] config not found: {path}")
            return
        try:
            cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"[figma-localize] failed to load config: {e}")
            return

        self.version = cfg.get("version")
        self.first_start = cfg.get("first_start")

        self.language_pack = cfg.get("language_pack", {}) or {}
        self.web_admin_host = cfg.get("web_admin_host")
        self.web_admin_port = cfg.get("web_admin_port")
        self.web_admin_open = cfg.get("web_admin_open")

        self.listen_port = cfg.get("listen_port")
        self.upstream_proxy = cfg.get("upstream_proxy")
        self.upstream_http = cfg.get("upstream_http")
        self.upstream_socks5 = cfg.get("upstream_socks5")

        # force_lang is optional in config; default True
        if "force_lang" in cfg:
            self.force_lang = bool(cfg.get("force_lang"))

        # Interception rules: accept dict or list
        rules_cfg = cfg.get("interception_rule", [])
        if isinstance(rules_cfg, dict):  # compat old single-rule
            self.interception_rules = [rules_cfg]
        elif isinstance(rules_cfg, list):
            self.interception_rules = rules_cfg
        else:
            self.interception_rules = []

        # Normalize/validate
        cleaned = []
        for r in self.interception_rules:
            if not isinstance(r, dict):
                continue
            pat = r.get("pattern")
            if not pat:
                continue
            cleaned.append({
                "pattern": str(pat),
                "host": r.get("host"),
                # Per-rule remote_url is optional; fallback to global remote later
                "remote_url": r.get("remote_url"),
            })
        self.interception_rules = cleaned

        logger.info(f"[figma-localize] loaded {len(self.interception_rules)} interception rule(s) from {path}")


# -----------------------------
# Localization Handler
# -----------------------------
class LocalizationHandler:
    def __init__(self, config: Config):
        self.config = config
        self.rules: List[Dict[str, Any]] = []
        self._compile_rules()

    def _compile_rules(self):
        self.rules = []
        for r in (self.config.interception_rules or []):
            try:
                compiled = re.compile(r["pattern"], re.I)
                self.rules.append({
                    "pattern": compiled,
                    "host": r.get("host"),
                    "remote_url": r.get("remote_url"),
                })
            except Exception as e:
                logger.error(f"[figma-localize] bad rule pattern: {r.get('pattern')} -> {e}")
        if not self.rules:
            logger.warning("[figma-localize] no valid interception rules loaded")

    # Return matched rule dict or None
    def _match_rule(self, req: http.Request) -> Optional[Dict[str, Any]]:
        for r in self.rules:
            host = r.get("host")
            if host and (req.host != host and not req.host.endswith("." + host)):
                continue
            if r["pattern"].match(req.path):
                return r
        return None

    # Serve local file if configured and exists
    def _serve_local(self, flow: http.HTTPFlow, local_path: str) -> bool:
        if not local_path:
            return False
        p = Path(local_path)
        if not p.exists():
            logger.warning(f"[figma-localize] local file not found: {p}")
            return False
        try:
            data = p.read_bytes()
        except Exception as e:
            logger.error(f"[figma-localize] read local file error: {e}")
            return False

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        flow.response = http.Response.make(200, data, headers)
        logger.info(f"[figma-localize] served local file -> 200 ({p.name})")
        return True

    # Try to fetch remote_url (server-side) and inline respond 200 to avoid CORS
    def _serve_remote_inline(self, flow: http.HTTPFlow, remote_url: str) -> bool:
        if not remote_url:
            return False
        if requests is None:
            return False
        try:
            # A small timeout to avoid blocking
            resp = requests.get(remote_url, timeout=6)
            if resp.status_code == 200 and resp.content:
                body = resp.content
                # Try to ensure UTF-8 if it's text
                ctype = resp.headers.get("Content-Type", "application/json; charset=utf-8")
                headers = {
                    "Content-Type": ctype,
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                flow.response = http.Response.make(200, body, headers)
                logger.info(f"[figma-localize] fetched remote and inlined -> 200 ({remote_url})")
                return True
            else:
                logger.warning(f"[figma-localize] remote fetch non-200 ({resp.status_code}) {remote_url}")
        except Exception as e:
            logger.warning(f"[figma-localize] remote fetch error: {e} ({remote_url})")
        return False

    # Fallback: 302 redirect to remote (may hit CORS; kept as last resort)
    def _redirect_to_remote(self, flow: http.HTTPFlow, remote_url: str) -> bool:
        if not remote_url:
            return False
        flow.response = http.Response.make(
            302, b"", {"Location": remote_url}
        )
        logger.info(f"[figma-localize] fallback redirect -> 302 {remote_url}")
        return True

    def request(self, flow: http.HTTPFlow):
        matched = self._match_rule(flow.request)
        if not matched:
            return

        # Prefer per-rule remote_url; fallback to global
        per_rule_remote = matched.get("remote_url")
        global_remote = (self.config.language_pack or {}).get("remote_url")
        remote_url = per_rule_remote or global_remote

        # Prefer local file if provided
        local_path = (self.config.language_pack or {}).get("local_path") or ""

        # 1) Local file
        if self._serve_local(flow, local_path):
            return

        # 2) Remote fetch and inline (CORS-safe)
        if self._serve_remote_inline(flow, remote_url):
            return

        # 3) Fallback 302 redirect
        self._redirect_to_remote(flow, remote_url)


# -----------------------------
# Optional: Force Accept-Language
# -----------------------------
class ForceLanguageHeader:
    def __init__(self, config: Config):
        self.config = config

    def request(self, flow: http.HTTPFlow):
        if not self.config.force_lang:
            return
        # Only touch figma domains to be conservative
        if not flow.request.host.endswith("figma.com"):
            return
        lang_header = flow.request.headers.get("Accept-Language", "")
        if "zh-CN" not in lang_header:
            new = f"zh-CN,zh;q=0.9,{lang_header}" if lang_header else "zh-CN,zh;q=0.9"
            flow.request.headers["Accept-Language"] = new
            logger.debug("[figma-localize] Accept-Language forced to zh-CN")


# -----------------------------
# mitmproxy addon instances
# -----------------------------
config = Config()
localization_handler = LocalizationHandler(config)
force_lang_handler = ForceLanguageHeader(config)

addons = [
    localization_handler,
    force_lang_handler,
]