// Figma 语言包专用 PAC 文件
// 功能：只将 Figma 语言包请求转发到 MITM 代理，其他所有请求直连

function FindProxyForURL(url, host) {
    // Figma 语言包 URL 模式
    var figmaLangPattern = /https:\/\/www\.figma\.com\/webpack-artifacts\/assets\/figma_app(?:_beta)?-[a-f0-9]+\.min\.en\.json(?:\.br)?/;
    
    // 检查是否匹配 Figma 语言包
    if (figmaLangPattern.test(url)) {
        return "PROXY 127.0.0.1:8888";
    }
    
    // 其他所有请求直连（不使用代理）
    return "DIRECT";
}

/*
使用说明：

1. 将此文件保存为 only-figma-lang.pac

2. 在系统中配置 PAC 文件：
   - macOS: 系统偏好设置 > 网络 > 高级 > 代理 > 自动代理配置
   - Windows: 设置 > 网络和 Internet > 代理 > 使用设置脚本
   - 输入：file:///path/to/only-figma-lang.pac

3. 确保 MITM 代理运行在 127.0.0.1:8888

4. 启动 MITM 注入器：
   bash mitm-injector/run.sh

5. 清除浏览器缓存并刷新 Figma

特点：
- 只代理语言包请求，不影响其他 Figma 功能
- 不影响 VPN 和其他网络流量
- 无需安装额外软件
- 系统级代理，所有浏览器都生效
*/
