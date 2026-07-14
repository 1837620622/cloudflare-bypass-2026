# Cloudflare Bypass Tool 2026

基于多技术方案的 Cloudflare Turnstile 验证绕过工具集

A multi-technique Cloudflare Turnstile bypass toolkit

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Mac%20%7C%20Windows%20%7C%20Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 免责声明 / Disclaimer

本工具仅供学习研究使用，请遵守相关法律法规和目标网站的服务条款。

This tool is for educational purposes only. Please comply with applicable laws and website terms of service.

## 方案对比与可行性分析 / Comparison & Viability

本仓库提供 **4 种不同技术方案**，针对 Cloudflare Turnstile 的可行性和适用场景如下：

| # | 文件 | 方案 | 原理 | Turnstile 可行 | 适用场景 |
|:---:|:---|:---|:---|:---:|:---|
| 1 | `bypass.py` | SeleniumBase UC Mode | OS 级鼠标模拟 + Chrome | ✅ 最高 | **主力推荐**，Turnstile Managed/Interactive |
| 2 | `simple_bypass.py` | SeleniumBase + 并行 | 多浏览器并发 + 代理轮换 | ✅ 高 | 批量采集、大规模任务 |
| 3 | `bypass_nodriver.py` | CDP 直连 | 无 WebDriver，CDP 协议直控 | ✅ 高 | SeleniumBase 替代方案，`cf_verify()` 自动处理 |
| 4 | `bypass_curl_cffi.py` | TLS 指纹仿冒 | HTTP 层 JA3/JA4 指纹修改 | ❌ 不可用 | **仅限旧版 JS Challenge**，无法用于 Turnstile |

### curl_cffi 方案的重要限制

`bypass_curl_cffi.py` **无法绕过 Cloudflare Turnstile**（含 Managed / Non-Interactive / Invisible 三种模式），原因如下：

1. **无 JavaScript 执行环境** — Turnstile 必须在浏览器中运行 JS 完成 PoW 计算和 API 探测
2. **无 DOM / Web API** — Turnstile 检查 `navigator`、`webgl`、`canvas` 等浏览器指纹
3. **无法交互** — Managed 模式需要用户点击复选框，纯 HTTP 客户端无法完成
4. TLS 指纹仅为 Turnstile 检测的**众多信号之一**，不是决定性因素

该方案仅适用于**旧版 Cloudflare "Under Attack" JS Challenge** 或低防护站点。如需绕过 Turnstile，请使用方案 1、2 或 3。

## 功能特点 / Features

| 功能 | 说明 |
|:---|:---|
| SeleniumBase UC Mode | 操作系统级鼠标模拟，绕过率最高 |
| nodriver CDP 直连 | 无 WebDriver 依赖，`cf_verify()` 自动点击 |
| 单浏览器模式 | 简单可靠，资源占用低 |
| 并行模式 | 多浏览器同时运行，提高效率 |
| 代理轮换 | 支持从文件批量加载代理 |
| HTTPS 隧道检测 | 自动验证代理是否支持 HTTPS |
| 跨平台 | Mac / Windows / Linux |
| Cookie 保存 | JSON + Netscape 双格式 |

## 快速开始 / Quick Start

```bash
# 安装依赖
pip install -r requirements.txt

# 方案1: 基础用法（推荐，绕过率最高）
python bypass.py https://example.com

# 方案1: 使用代理
python bypass.py https://example.com -p http://127.0.0.1:7890

# 方案3: nodriver CDP 直连
python bypass_nodriver.py https://example.com
```

## 安装部署 / Installation

### Mac / Windows

```bash
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

```bash
# 方式1: 一键安装
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
sudo bash install_linux.sh

# 方式2: 手动安装
sudo apt-get update
sudo apt-get install -y xvfb libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libgbm1 libasound2

# 安装Chrome
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y

# Python依赖
pip install seleniumbase pyvirtualdisplay
```

## 使用方法 / Usage

### 1. 简单模式 (bypass.py) —— 主力推荐，绕过率最高

单浏览器，SeleniumBase UC Mode，最简单可靠：

```bash
# 直连
python bypass.py https://example.com

# 使用代理
python bypass.py https://example.com -p http://127.0.0.1:7890

# 设置超时
python bypass.py https://example.com -t 60
```

**参数：**

| 参数 | 说明 | 默认值 |
|:---|:---|:---:|
| `url` | 目标URL | 必填 |
| `-p, --proxy` | 代理地址 | 无 |
| `-t, --timeout` | 超时(秒) | 60 |
| `--no-save` | 不保存Cookie | 否 |

### 2. 完整模式 (simple_bypass.py) —— 并行 + 代理轮换

支持并行浏览器和代理批量轮换：

```bash
# 直连模式
python simple_bypass.py https://example.com

# 指定代理
python simple_bypass.py https://example.com -p http://127.0.0.1:7890

# 代理轮换模式（顺序尝试proxy.txt中的代理）
python simple_bypass.py https://example.com -r -f proxy.txt

# 并行模式（3个浏览器同时运行）
python simple_bypass.py https://example.com -P -b 3 -t 60

# 并行 + 代理检测 + 30批次
python simple_bypass.py https://example.com -P -c -b 3 -t 15 -n 30 -f proxy.txt
```

**参数：**

| 参数 | 说明 | 默认值 |
|:---|:---|:---:|
| `url` | 目标URL | 必填 |
| `-p, --proxy` | 指定代理地址 | 无 |
| `-f, --proxy-file` | 代理文件路径 | proxy.txt |
| `-r, --rotate` | 顺序代理轮换模式 | 否 |
| `-P, --parallel` | 并行模式 | 否 |
| `-b, --batch` | 并行浏览器数量 | 3 |
| `-t, --timeout` | 超时时间(秒) | 60 |
| `-n, --retries` | 最大批次/重试数 | 3 |
| `-c, --check-proxy` | 预检测代理存活 | 否 |
| `--no-save` | 不保存Cookie | 否 |

### 3. Python API

```python
# 简单模式
from bypass import bypass_cloudflare

result = bypass_cloudflare("https://example.com")
if result["success"]:
    print(f"cf_clearance: {result['cf_clearance']}")
    print(f"User-Agent: {result['user_agent']}")

# 完整模式
from simple_bypass import bypass_cloudflare, bypass_parallel

# 单次绕过
result = bypass_cloudflare("https://example.com", proxy="http://127.0.0.1:7890")

# 并行绕过
result = bypass_parallel(
    url="https://example.com",
    proxy_file="proxy.txt",
    batch_size=3,
    timeout=15.0,
    max_batches=30
)
```

### 4. nodriver 方案 (bypass_nodriver.py) —— CDP 直连

基于 CDP 协议直连 Chrome，无需 WebDriver。nodriver 是 undetected-chromedriver 的官方继任者。支持 Turnstile。

```bash
# 安装
pip install nodriver

# 直连
python bypass_nodriver.py https://example.com

# 使用代理
python bypass_nodriver.py https://example.com -p http://127.0.0.1:7890

# 启用无头模式 (不推荐，Cloudflare可检测)
python bypass_nodriver.py https://example.com --headless
```

**特点：** 不依赖 Selenium/WebDriver，内置 `cf_verify()` 通过 OpenCV 图像识别自动定位并点击验证复选框。异步架构，性能更优。

### 5. TLS 指纹方案 (bypass_curl_cffi.py) —— 超轻量（非 Turnstile）

> ⚠️ **注意：本方案无法绕过 Cloudflare Turnstile。** 仅适用于旧版 "Under Attack" JS Challenge 或低防护站点。如需绕过 Turnstile 请使用方案 1、2 或 3。

在 HTTP/TLS 层仿冒真实浏览器的 JA3/JA4 指纹，无需启动浏览器。

```bash
# 安装
pip install curl_cffi

# 基础使用
python bypass_curl_cffi.py https://example.com

# 使用代理
python bypass_curl_cffi.py https://example.com -p http://127.0.0.1:7890

# 切换指纹类型 (chrome120/chrome124/chrome131/firefox121/safari17_0/edge101)
python bypass_curl_cffi.py https://example.com -f firefox121
```

**特点：** 极速、零浏览器依赖、资源占用极低。适用于简单防护场景，不适合 Turnstile。

## 代理文件格式 / Proxy Format

`proxy.txt` 每行一个代理：

```
# 支持的格式
127.0.0.1:7890
http://127.0.0.1:7890
socks5://127.0.0.1:1080
http://user:pass@host:port
```

## 输出文件 / Output

Cookie保存到 `output/cookies/` 目录：

| 文件 | 格式 | 用途 |
|:---|:---|:---|
| `cookies_*.json` | JSON | 编程使用 |
| `cookies_*.txt` | Netscape | curl -b 使用 |

**JSON示例：**
```json
{
  "url": "https://example.com",
  "cookies": {
    "cf_clearance": "xxx..."
  },
  "user_agent": "Mozilla/5.0...",
  "timestamp": "20260122_103000"
}
```

## 项目结构 / Structure

```
cloudflare-bypass-2026/
├── bypass.py              # 方案1: SeleniumBase 单浏览器（主力推荐）
├── simple_bypass.py       # 方案2: SeleniumBase 并行 + 代理轮换
├── bypass_nodriver.py     # 方案3: nodriver CDP 直连
├── bypass_curl_cffi.py    # 方案4: curl_cffi TLS 指纹（非Turnstile）
├── bypass_seleniumbase.py # 详细版（类封装，含鼠标轨迹模拟）
├── install_linux.sh       # Linux 一键安装脚本
├── requirements.txt       # Python 依赖清单
├── proxy.txt              # 代理列表
├── output/                # Cookie 输出目录
└── README.md
```

## 常见问题 / FAQ

**Q: 应该用哪个方案?**
> 推荐优先级：bypass.py (方案1) > bypass_nodriver.py (方案3) > simple_bypass.py (方案2)。方案4 (curl_cffi) 不适用于 Turnstile，仅用于旧版简单验证。

**Q: 为什么不用无头模式?**
> Cloudflare 可检测无头浏览器，建议保持可视化模式以获得最高成功率。

**Q: cf_clearance 有效期?**
> 通常 30 分钟到数小时，与 Turnstile 的 Challenge Passage 设置有关。建议过期前重新获取。

**Q: Linux 报错 "X11 display failed"?**
> 运行 `sudo bash install_linux.sh` 安装 Xvfb 等依赖。

**Q: 代理不工作?**
> 大部分公共代理不支持 HTTPS 隧道。建议使用直连模式或购买高质量住宅代理。

**Q: curl_cffi 方案为什么不能用于 Turnstile?**
> Turnstile 需要在浏览器环境执行 JavaScript 并进行 Web API 探测（navigator、webgl、canvas 等），纯 HTTP 客户端无法完成这些操作。详见本文「方案对比」章节。

**Q: Chrome 启动多个进程?**
> 这是 Chrome 正常架构（主进程 + 渲染进程 + GPU 进程），非代码问题。

## 技术参考 / References

- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)
- [Cloudflare Challenges](https://developers.cloudflare.com/cloudflare-challenges/)
- [SeleniumBase UC Mode](https://seleniumbase.com/)
- [nodriver - undetected-chromedriver 继任者](https://github.com/ultrafunkamsterdam/nodriver)
- [curl_cffi - TLS 指纹仿冒](https://github.com/lexiforest/curl_cffi)

---

## 商务合作 / Business

欢迎代理商、企业、开发者洽谈赞助展示、定制开发、技术咨询等合作。

| 渠道 | 联系方式 |
|:---|:---|
| 微信 | `1837620622`（传康Kk） |
| 邮箱 | `2040168455@qq.com` |
| 闲鱼 / B站 | 万能程序员 |

合作说明：赞助位档期、定制需求、批量技术支持等，请优先微信联系并备注「商务合作」。

---

## License

MIT License

---

**如果这个项目对你有帮助，请给个 Star!**

**If this project helps you, please give it a Star!**
