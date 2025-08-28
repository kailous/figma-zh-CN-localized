function FindProxyForURL(url, host) {
    if (shExpMatch(url, "https://www.figma.com/webpack-artifacts/assets/figma_app-*.min.en.json.br")) {
        return "PROXY 127.0.0.1:8888";
    }
    // 先走 Surge HTTP 代理，如果失败再走 SOCKS5
    return "PROXY 127.0.0.1:8234; SOCKS5 127.0.0.1:8235";
}