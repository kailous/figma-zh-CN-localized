function FindProxyForURL(url, host) {
    // 把所有 figma.com 流量交给 mitmproxy
    if (dnsDomainIs(host, "figma.com") ||
        shExpMatch(host, "*.figma.com")) {
        return "PROXY 127.0.0.1:8888";
    }
    // 其余直连
    return "DIRECT";
}