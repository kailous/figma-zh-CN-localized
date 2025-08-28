function FindProxyForURL(url, host) {
  var MITM   = "PROXY 127.0.0.1:8888";
  var SURGEH = "PROXY 127.0.0.1:8234";
  var SURGES = "SOCKS5 127.0.0.1:8235";

  // 只拦截语言包
  var re = /^https:\/\/www\.figma\.com\/webpack-artifacts\/assets\/figma_app-[a-f0-9]{16}\.min\.en\.json\.br$/;
  if (re.test(url)) {
    return MITM + "; " + SURGEH + "; " + SURGES + "; DIRECT";
  }

  // 其它全部走 Surge（先 HTTP 再 SOCKS5，再直连）
  return SURGEH + "; " + SURGES + "; DIRECT";
}