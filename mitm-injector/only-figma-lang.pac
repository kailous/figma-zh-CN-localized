function FindProxyForURL(url, host) {
    if (shExpMatch(url, "https://www.figma.com/webpack-artifacts/assets/figma_app-*.min.en.json.br")) {
        return "PROXY 127.0.0.1:8888";   // 走 mitmproxy 做替换
    }
    return "PROXY 127.0.0.1:8234";       // 其它走 Surge
}