# injector.py (修改后的版本)
import os
import re
import json
import yaml
import time
import logging
from pathlib import Path
from mitmproxy import http
from typing import List, Tuple, Optional, Pattern

# 日志设置 (保持不变)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """
    用于加载和解析新的统一 config.yaml 文件。
    """
    def __init__(self):
        self.config_file = Path(__file__).parent / "config.yaml"
        self.language_pack = {}
        self.listen_port = 8888
        self.interception_rule = {}
        self.force_lang = False
        self.load_config()

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                
                # 读取新的配置结构
                self.language_pack = config.get("language_pack", {})
                self.listen_port = config.get("listen_port", 8888)
                self.interception_rule = config.get("interception_rule", {})
                self.force_lang = config.get("force_lang", False)
                
                logger.info(f"[figma-localize] Loaded unified config from {self.config_file}")
        except Exception as e:
            logger.error(f"[figma-localize] Failed to load config: {e}")


class LocalizationHandler:
    """
    合并了 Redirector 和 LocalLanguageServer 的功能。
    根据配置决定是重定向到远程URL还是直接提供本地文件。
    """
    def __init__(self, config: Config):
        self.config = config
        self.rule_pattern = None
        self.rule_host = None
        self.load_rule()

    def load_rule(self):
        rule = self.config.interception_rule
        if rule and "pattern" in rule:
            try:
                self.rule_pattern = re.compile(rule["pattern"], re.I)
                self.rule_host = rule.get("host")
                logger.info(f"[figma-localize] Loaded interception rule for host: {self.rule_host}")
            except Exception as e:
                logger.error(f"[figma-localize] Failed to compile rule pattern: {e}")

    def request(self, flow: http.HTTPFlow):
        # 如果规则没有被正确加载，则直接跳过
        if not self.rule_pattern:
            return

        req = flow.request
        
        # 1. 检查请求是否匹配规则
        if self.should_intercept(req):
            logger.info(f"[figma-localize] Intercepted Figma language request: {req.url}")
            
            # 2. 检查本地文件路径配置
            local_path_str = self.config.language_pack.get("local_path", "")
            if local_path_str:
                local_path = Path(local_path_str)
                if local_path.exists() and local_path.is_file():
                    # 3. 如果本地文件有效，则直接提供文件内容
                    self.serve_local_file(flow, local_path)
                    return

            # 4. 如果本地文件无效或未配置，则重定向到远程URL
            remote_url = self.config.language_pack.get("remote_url")
            if remote_url:
                self.redirect_to_remote(flow, remote_url)
            else:
                logger.warning("[figma-localize] No valid local_path or remote_url found in config.")


    def should_intercept(self, req: http.Request) -> bool:
        if self.rule_host and req.host != self.rule_host and not req.host.endswith("." + self.rule_host):
            return False
        if not self.rule_pattern.match(req.path):
            return False
        return True

    def serve_local_file(self, flow: http.HTTPFlow, file_path: Path):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            logger.info(f"[figma-localize] Serving local language file: {file_path}")
            flow.response = http.Response.make(
                200,
                content,
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Access-Control-Allow-Origin": "*",
                },
            )
        except Exception as e:
            logger.error(f"[figma-localize] Failed to serve local file {file_path}: {e}")

    def redirect_to_remote(self, flow: http.HTTPFlow, target_url: str):
        logger.info(f"[figma-localize] Redirecting to remote URL: {target_url}")
        flow.response = http.Response.make(
            307,
            b"",
            {
                "Location": target_url,
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            },
        )

# ForceLanguageHeader 类保持不变
class ForceLanguageHeader:
    def __init__(self, config: Config):
        self.config = config

    def request(self, flow: http.HTTPFlow):
        if self.config.force_lang and flow.request.host.endswith("figma.com"):
            lang_header = flow.request.headers.get("Accept-Language", "")
            if "zh-CN" not in lang_header:
                flow.request.headers["Accept-Language"] = "zh-CN,zh;q=0.9," + lang_header


# 实例化新的类
config = Config()
localization_handler = LocalizationHandler(config)
force_lang_handler = ForceLanguageHeader(config)


# 更新 mitmproxy 的 addons 列表
addons = [
    localization_handler,
    force_lang_handler,
]