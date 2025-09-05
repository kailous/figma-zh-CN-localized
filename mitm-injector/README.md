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
# 上游代理 
# 如果有另外的代理服务器那么你需要启用上游代理，
# 让 mitm-injector 的代理服务将语言包无关的流量转发到你原本的代理上。
upstream_proxy: "true" # 是否启用上游代理 如果没有上游代理可以设置为 false

# 如果你没有上游代理请注释这两行
upstream_http: 127.0.0.1:6152
upstream_socks5: 127.0.0.1:6153
```

#### 第二步 运行主程序 & 应用代理

1. 在终端输入命令
```bash
# 运行注入器（自动创建虚拟环境）
cd figma-zh-CN-localized/mitm-injector # 进入项目目录
bash ./run.sh
```
2. 自动化程序会在设置好代理后自动启动 mitm-injector，如果你是第一次使用，会先安装证书。
3. 安装证书后，会自动启动 mitm-injector。

#### 第三步 验证效果

1. 打开 Figma 应用
2. 检查界面是否显示中文
3. 检查控制台是否没有错误日志
4. 如果不生效，请清理一下缓存。

#### 关于手动安装证书

1. 第一次使用需要安装证书，自动化程序如果不生效，需要手动安装证书
   - 访问 <http://mitm.it>
   - 下载对应平台的证书
   - 安装并设为信任
   - 或者使用脚本安装证书，安装过程中需要输入电脑密码和验证指纹，仅做鉴权，可以放心输入。
```bash
# 安装证书
bash ./install_mitm_ca.sh
```

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