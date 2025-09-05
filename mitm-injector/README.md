# MITM 注入器

基于 mitmproxy 的 Figma 语言包拦截和替换工具，适合开发者和高级用户使用。

## ✨ 功能特性

- 🎯 **精准拦截** - 使用正则表达式匹配 Figma 语言包请求
- 🔄 **实时替换** - 动态替换英文语言包为中文版本

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 网络访问权限
- 管理员权限（安装证书）

### 安装和运行

```bash
# 克隆项目
git clone https://github.com/your-username/figma-zh-CN-localized.git
cd figma-zh-CN-localized

# 运行注入器（自动创建虚拟环境）
bash mitm-injector/run.sh
```

### 配置步骤

1. **安装证书**
   - 访问 <http://mitm.it>
   - 下载对应平台的证书
   - 安装并设为信任

2. **设置代理**
   - HTTP/HTTPS 代理：`127.0.0.1:8888`
   - 或使用系统代理设置

3. **验证效果**
   - 打开 <https://app.figma.com>
   - 检查界面是否显示中文

## ⚙️ 配置说明

### config.yaml

```yaml

# 上游代理设置
upstream_http: 127.0.0.1:8234 # 改为你现有代理工具的 HTTP 代理端口
upstream_socks5: 127.0.0.1:8235 # 改为你现有代理工具的 SOCKS 代理端口

```
## 🛠️ 高级用法

### 开发模式

启用详细日志：

```bash
# 在 injector.py 中修改日志级别
ctx.log.info("[figma-localize] Development mode enabled")
```

### 自定义语言包

1. 将语言文件上传到 GitHub Pages 或其他 CDN
2. 修改 `config.yaml` 中的 `lang_file` 为远程 URL
3. 重启注入器

## 📊 监控和调试
### 命令行输出

注入器会显示：
- 启动信息
- 拦截统计
- 错误日志

```log
[figma-localize] Starting mitm-injector on port 8888
[figma-localize] Loaded 1 redirect rules
[figma-localize] Total requests: 42, Redirected: 5
```

## 🔧 故障排除

### 常见问题

**Q: 看不到中文界面**
- 清除浏览器缓存
- 检查代理设置
- 确认证书已信任
- 查看控制台日志

**Q: 证书错误**
- 重新安装证书
- 确保证书在信任列表中
- 重启浏览器

**Q: 端口被占用**
- 修改 `config.yaml` 中的 `listen_port`
- 或停止占用端口的程序

**Q: 代理冲突**
- 检查其他代理软件
- 配置上游代理设置

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License