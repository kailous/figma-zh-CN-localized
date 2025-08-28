# injector.py
import os, re, json
from mitmproxy import http, ctx

CONF_FILE = os.path.join(os.path.dirname(__file__), "redirects.json")

class Redirector:
    def __init__(self):
        self.rules = []
        try:
            with open(CONF_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for r in raw:
                pat = re.compile(r["pattern"], re.I)
                host = r.get("host")
                url = r["redirect"]
                self.rules.append((pat, host, url))
            ctx.log.info(f"[figma-307] Loaded {len(self.rules)} redirect rules from {CONF_FILE}")
        except Exception as e:
            ctx.log.error(f"[figma-307] Failed to load {CONF_FILE}: {e}")

    def request(self, flow: http.HTTPFlow):
        req = flow.request
        for pat, host, target in self.rules:
            if (not host or req.host == host or req.host.endswith("." + host)) and pat.match(req.path):
                ctx.log.info(f"[figma-307] {req.url} -> {target}")
                flow.response = http.Response.make(
                    307,
                    b"",
                    {
                        "Location": target,
                        "Cache-Control": "no-store",
                        "Content-Length": "0",
                    },
                )
                return

addons = [Redirector()]