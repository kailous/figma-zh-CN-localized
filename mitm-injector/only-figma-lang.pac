function FindProxyForURL(url, host) {
  if (shExpMatch(
        url,
        "https://www.figma.com/webpack-artifacts/assets/figma_app-????????????????.min.en.json.br"
      )) {
    return "PROXY 127.0.0.1:8888";
  }
  return "DIRECT";
}