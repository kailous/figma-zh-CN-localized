function FindProxyForURL(url, host) {
  var MITM   = "PROXY 127.0.0.1:8888";
  var SURGEH = "PROXY 127.0.0.1:8234";
  var SURGES = "SOCKS5 127.0.0.1:8235";

  if (dnsDomainIs(host, "www.figma.com") &&
      shExpMatch(url, "https://www.figma.com/webpack-artifacts/assets/figma_app-????????????????.min.en.json.br*")) {
    return MITM + "; " + SURGEH + "; " + SURGES + "; DIRECT";
  }

  return SURGEH + "; " + SURGES + "; DIRECT";
}