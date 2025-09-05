# MITM 注入器

基于 mitmproxy 的 Figma 语言包拦截和替换工具，适合开发者和高级用户使用。

## ✨ 功能特性

- 🎯 **精准拦截** - 使用正则表达式匹配 Figma 语言包请求
- 🔄 **实时替换** - 动态替换英文语言包为中文版本
- 📊 **流量统计** - 提供请求拦截统计信息
- ⚙️ **灵活配置** - 支持自定义语言文件和代理设置
- 🔄 **热重载** - 配置修改后自动重载规则

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

#### 方式一：使用 PAC 文件（推荐）

只代理 Figma 语言包请求，不影响其他网络流量。

1. **安装证书**
   - 访问 <http://mitm.it>
   - 下载对应平台的证书
   - 安装并设为信任

2. **配置 PAC 代理**
   - 使用项目中的 `only-figma-lang.pac` 文件
   - **macOS**: 系统偏好设置 > 网络 > 高级 > 代理 > 自动代理配置
     - 输入：`file:///path/to/mitm-injector/only-figma-lang.pac`
   - **Windows**: 设置 > 网络和 Internet > 代理 > 使用设置脚本
     - 输入：`file:///C:/path/to/mitm-injector/only-figma-lang.pac`

3. **验证效果**
   - 打开 <https://app.figma.com>
   - 检查界面是否显示中文

#### 方式二：全局代理

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
# 远程语言包地址（GitHub Pages）
lang_file: "https://kailous.github.io/figma-zh-CN-localized/lang/zh.json"

# 是否强制浏览器使用中文
force_lang: true

# URL 匹配模式
url_patterns:
  - "https://.*figma\\.com/.*(i18n|locale|locales?).*\\.json(\\?.*)?$"

# 监听端口
listen_port: 8888

# 上游代理设置
upstream_http: 127.0.0.1:8234
upstream_socks5: 127.0.0.1:8235
```

### redirects.json

定义重定向规则，支持多个规则：

```json
[
  {
    "pattern": "^/webpack-artifacts/assets/figma_app-[a-f0-9]{16}\\.min\\.en\\.json(\\.br)?$",
    "host": "www.figma.com",
    "redirect": "https://kailous.github.io/figma-zh-CN-localized/lang/zh.json"
  }
]
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

### 多规则支持

在 `redirects.json` 中添加多个重定向规则：

```json
[
  {
    "pattern": "规则1",
    "host": "host1",
    "redirect": "目标URL1"
  },
  {
    "pattern": "规则2",
    "host": "host2",
    "redirect": "目标URL2"
  }
]
```

## 📊 监控和调试

### Web 界面

访问 <http://127.0.0.1:8081> 查看：
- 实时请求流
- 拦截统计
- 请求详情

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

### 调试技巧

1. **查看请求详情**
   ```bash
   # 启用详细模式
   mitmdump -s injector.py -v
   ```

2. **测试规则**
   ```bash
   # 使用 curl 测试
   curl --proxy http://127.0.0.1:8888 https://www.figma.com/webpack-artifacts/...
   ```

3. **检查配置**
   ```bash
   # 验证 YAML 语法
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

## 📝 更新日志

### v1.3.0
- 支持远程语言包地址
- 优化 GitHub Pages 集成
- 改进缓存处理

### v1.2.0
- 支持热重载配置
- 添加请求统计
- 优化性能

### v1.1.0
- 支持多规则匹配
- 添加上游代理
- 改进错误处理

### v1.0.0
- 初始版本
- 基本拦截功能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License