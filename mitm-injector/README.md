# MITM 注入器

基于 mitmproxy 的 Figma 语言包拦截和替换工具，没有高级代理工具的可以用这个汉化你的 Figma。

## ✨ 功能特性

- 🎯 **精准拦截** - 使用正则表达式匹配 Figma 语言包请求
- 🔄 **实时替换** - 动态替换英文语言包为中文版本

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 网络访问权限
- 管理员权限（安装证书）
- 目前仅限 macOS 系统

### 安装和运行

#### 第一步 克隆项目&修改配置
```bash
# 克隆项目
git clone https://github.com/lipeng2018/figma-zh-CN-localized.git # 或者直接下载项目压缩包解压
cd figma-zh-CN-localized/mitm-injector # 进入项目目录

# 给所有的脚本添加可执行权限
find . -type f -name "*.sh" -exec chmod +x {} \;
ls -l *.sh
```

1. 找到 mitm-injector/config.yaml 文件
2. 修改 upstream_http 和 upstream_socks5 为你当前使用的代理工具的端口
3. 如果你不使用代理工具，请在这两行前面加 “# 注释”

```yaml
# 上游代理设置
upstream_http: 127.0.0.1:8234 # 改为你现有代理工具的 HTTP 代理端口
upstream_socks5: 127.0.0.1:8235 # 改为你现有代理工具的 SOCKS 代理端口
```

#### 第二步 运行主程序 & 应用代理

1. 在终端输入命令
```bash
# 运行注入器（自动创建虚拟环境）
cd figma-zh-CN-localized/mitm-injector # 进入项目目录
bash ./run.sh
```
2. 等待注入器启动完成后，进入代理设置，在macOS系统设置 > Wi-Fi > 详细信息 > 代理
   将 HTTP 代理和 HTTPS & SOCKS 代理都设置为 127.0.0.1:8888
   我也给你提供了一个脚本，你可以直接运行这个脚本，它会自动帮你设置代理，以下是脚本的说明。

```bash
# 应用代理
sudo bash ./set_proxy.sh --start

# 移除代理
sudo bash ./set_proxy.sh --stop

# 检查代理状态
sudo bash ./set_proxy.sh --check
```
#### 第三部 安装证书

1. 第一次使用需要安装证书
   - 访问 <http://mitm.it>
   - 下载对应平台的证书
   - 安装并设为信任
   - 或者使用脚本安装证书，安装过程中需要输入电脑密码和验证指纹，仅做鉴权，可以放心输入。
```bash
# 安装证书
bash ./install_mitm_ca.sh
```

#### 第四部 验证效果

1. 打开 Figma 应用
2. 检查界面是否显示中文
3. 检查控制台是否没有错误日志
4. 如果不生效，请清理一下缓存。

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

## 🔧 故障排除

### 常见问题

**Q: 看不到中文界面**
- 清除浏览器缓存
- 检查代理设置 config.yaml 上游代理的端口号和地址是否设置正确
- 确认证书已信任
- 查看控制台日志

**Q: 证书错误**
- 手动重新安装证书
- 确保证书在信任列表中
- 重启浏览器

**Q: 证书网站无法访问**
- 检查代理设置 需要先连接上注入器的代理
- 重启浏览器


## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License