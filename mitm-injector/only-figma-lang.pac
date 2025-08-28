function FindProxyForURL(url, host) {
  // 只把语言包这个 URL 交给本机 mitmproxy
  if (shExpMatch(url, "https://www.figma.com/webpack-artifacts/assets/figma_app-*.min.en.json*")) {
    return "PROXY 127.0.0.1:8888";
  }
  // 其它全部走你原来的代理（示例：本机 7890）
  return "PROXY 127.0.0.1:8234";
}