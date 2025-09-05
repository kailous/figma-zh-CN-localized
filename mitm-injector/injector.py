# injector.py
import os
import re
import json
import yaml
import time
import logging
from pathlib import Path
from mitmproxy import http
from typing import List, Tuple, Optional, Pattern

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.redirects_file = Path(__file__).parent / "redirects.json"
        self.config_file = Path(__file__).parent / "config.yaml"
        self.lang_file = ""
        self.force_lang = False
        self.url_patterns = []
        self.listen_port = 8888
        self.load_config()

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                
                self.lang_file = config.get("lang_file", "")
                self.force_lang = config.get("force_lang", False)
                self.url_patterns = config.get("url_patterns", [])
                self.listen_port = config.get("listen_port", 8888)
                
                logger.info(f"[figma-localize] Loaded config from {self.config_file}")
        except Exception as e:
            logger.error(f"[figma-localize] Failed to load config: {e}")


class Redirector:
    def __init__(self):
        self.config = Config()
        self.rules: List[Tuple[Pattern[str], Optional[str], str]] = []
        self.stats = {
            "total_requests": 0,
            "redirected_requests": 0,
            "last_reload": 0
        }
        self.load_rules()

    def load_rules(self):
        try:
            with open(self.config.redirects_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            
            self.rules.clear()
            for r in raw:
                pat = re.compile(r["pattern"], re.I)
                host = r.get("host")
                url = r["redirect"]
                self.rules.append((pat, host, url))
            
            self.stats["last_reload"] = time.time()
            logger.info(f"[figma-localize] Loaded {len(self.rules)} redirect rules")
            
        except FileNotFoundError:
            logger.error(f"[figma-localize] Config file not found: {self.config.redirects_file}")
        except json.JSONDecodeError as e:
            logger.error(f"[figma-localize] Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"[figma-localize] Failed to load rules: {e}")

    def request(self, flow: http.HTTPFlow):
        self.stats["total_requests"] += 1
        
        req = flow.request
        
        for pat, host, target in self.rules:
            if self.should_redirect(req, pat, host):
                self.stats["redirected_requests"] += 1
                logger.info(f"[figma-localize] Redirecting: {req.url} -> {target}")
                
                flow.response = http.Response.make(
                    307,
                    b"",
                    {
                        "Location": target,
                        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                        "Content-Length": "0",
                        "Connection": "close",
                    },
                )
                return

    def should_redirect(self, req: http.Request, pat: Pattern[str], host: Optional[str]) -> bool:
        if host and req.host != host and not req.host.endswith("." + host):
            return False
        
        if not pat.match(req.path):
            return False
        
        return True

    def get_stats(self) -> dict:
        uptime = time.time() - self.stats["last_reload"]
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "rules_count": len(self.rules)
        }


class ForceLanguageHeader:
    def __init__(self, config: Config):
        self.config = config

    def request(self, flow: http.HTTPFlow):
        if self.config.force_lang and flow.request.host.endswith("figma.com"):
            if "Accept-Language" not in flow.request.headers:
                flow.request.headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
            else:
                lang_header = flow.request.headers["Accept-Language"]
                if "zh-CN" not in lang_header:
                    flow.request.headers["Accept-Language"] = "zh-CN,zh;q=0.9," + lang_header


class LocalLanguageServer:
    def __init__(self, config: Config):
        self.config = config

    def request(self, flow: http.HTTPFlow):
        if not self.config.lang_file:
            return
            
        lang_path = Path(self.config.lang_file)
        if not lang_path.exists():
            return
            
        req = flow.request
        for pattern in self.config.url_patterns:
            if re.search(pattern, req.url, re.I):
                try:
                    with open(lang_path, "r", encoding="utf-8") as f:
                        content = f.read().encode("utf-8")
                    
                    logger.info(f"[figma-localize] Serving local language file: {req.url}")
                    flow.response = http.Response.make(
                        200,
                        content,
                        {
                            "Content-Type": "application/json; charset=utf-8",
                            "Cache-Control": "no-store, no-cache, must-revalidate",
                            "Access-Control-Allow-Origin": "*",
                            "Content-Length": str(len(content)),
                        },
                    )
                    return
                except Exception as e:
                    logger.error(f"[figma-localize] Failed to serve local language file: {e}")


redirector = Redirector()
config = redirector.config
force_lang = ForceLanguageHeader(config)
local_server = LocalLanguageServer(config)


def print_stats():
    stats = redirector.get_stats()
    logger.info(f"[figma-localize] Stats: {stats}")


def load(ctx):
    logger.info("[figma-localize] Figma Chinese Localization addon loaded")
    logger.info(f"[figma-localize] Config: lang_file={config.lang_file}, force_lang={config.force_lang}")


addons = [
    redirector,
    force_lang,
    local_server,
]