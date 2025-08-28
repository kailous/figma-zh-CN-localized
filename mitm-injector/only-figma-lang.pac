function FindProxyForURL(url, host) {
  // 任何 *.figma.com 都走本地 mitmproxy:8888
  if (dnsDomainIs(host, "figma.com") || shExpMatch(host, "*.figma.com")) {
    return "PROXY 127.0.0.1:8888";
  }
  // 其余一律直连/按你原来的代理走
  return "DIRECT";
}