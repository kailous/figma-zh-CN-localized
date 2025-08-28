# Figma 语言包 MITM 注入器

一个小白友好的工具，基于 mitmproxy，将 Figma 拉取的语言包替换为你本地的 `dist/zh-CN.json`。

## 使用方法

1. **准备环境**
   - 确保已安装 Python 3.8+
   - 仓库根目录下已有 `dist/zh-CN.json`

2. **运行**
   - macOS/Linux:
     ```bash
     bash mitm-injector/run.sh
     ```
   - Windows:
     ```
     mitm-injector\run.bat
     ```

3. **首次使用**
   - 启动后访问 <http://mitm.it>
   - 安装并信任 mitmproxy 根证书

4. **设置浏览器代理**
   - HTTP/HTTPS 代理：`127.0.0.1:8888`
   - 打开 <https://app.figma.com>，即可看到替换效果

## 配置

见 `mitm-injector/config.yaml`：
- `lang_file`：要注入的 JSON 文件路径（相对仓库根目录）
- `upstream_proxy`：如果你用 Clash/Surge，填它的代理地址
- `listen_port`：本地监听端口，默认 8888

## 常见问题

- **看不到中文**：禁用浏览器缓存，或在 mitmweb (http://127.0.0.1:8081) 检查请求是否被替换  
- **证书错误**：证书没安装或没设为信任  
- **端口冲突**：修改 `listen_port`  