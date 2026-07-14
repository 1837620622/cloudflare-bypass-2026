# Cloudflare Bypass Tool 2026

基于多技术方案的 Cloudflare Turnstile 验证绕过工具集

A multi-technique Cloudflare Turnstile bypass toolkit

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Mac%20%7C%20Windows%20%7C%20Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 免责声明 / Disclaimer

本工具仅供学习研究与**已授权**的自动化测试使用，请遵守相关法律法规和目标网站服务条款。

不承诺任何站点、任何环境下的成功率；机房 IP、真 headless、Docker 无显示环境会显著降低通过率。

This tool is for educational and authorized testing only. No success-rate guarantees.

## 2026 技术现状（摘要）

| 层级 | 检测信号 | 开源应对 |
|:---|:---|:---|
| 网络 | IP 信誉 / ASN / 住宅 vs 机房 | 住宅代理或家庭宽带 |
| TLS/HTTP2 | JA3/JA4 等 | `curl_cffi` 可仿，**不足以过 Turnstile** |
| Challenge / Turnstile | JS、PoW、交互、Web API | **真实浏览器 + 有头 + OS/CDP 交互** |
| 自动化指纹 | WebDriver / 部分 CDP 特征 | UC 断连重连、纯 CDP（nodriver / SB CDP） |

**当前更稳妥的开源组合：** 有头真实 Chrome +（可选）住宅 IP + `uc_open_with_reconnect` / CDP + OS 级点击。

**不推荐：** 真 headless 硬刚 Managed Turnstile、纯 `curl_cffi` 打 Turnstile、playwright-stealth 单独指望。

## 方案对比 / Comparison

本仓库提供 **5 种方案**（4 可跑浏览器/HTTP + 1 类封装）：

| # | 文件 | 方案 | Turnstile | 说明 |
|:---:|:---|:---|:---:|:---|
| 1 | `bypass.py` | SeleniumBase **UC Mode** | ✅ | **默认主力**：`uc_open_with_reconnect` + `uc_gui_click_captcha` |
| 2 | `simple_bypass.py` | UC + 并行/代理轮换 | ✅ | 批量场景；并行时 OS 鼠标可能互抢 |
| 3 | `bypass_nodriver.py` | nodriver 纯 CDP | ✅ | `verify_cf()`（需 OpenCV）；**AGPL-3.0** |
| 4 | `bypass_curl_cffi.py` | TLS 指纹 / Cookie 复用 | ❌ | **不能**过 Turnstile；旧 JS Challenge 或复用 cookie |
| 5 | `bypass_cdp.py` | SeleniumBase **CDP Mode** | ✅ | 2026 UC 后继路径：`solve_captcha` / `gui_click_captcha` |
| - | `bypass_seleniumbase.py` | UC 类封装详细版 | ✅ | 独立可 import，便于二次开发 |

### 推荐优先级

```
首选:  bypass.py（UC）或 bypass_cdp.py（CDP）
并列:  bypass_nodriver.py（纯 CDP，注意 AGPL）
批量:  simple_bypass.py（注意 GUI 点击互斥）
加速:  浏览器拿 cf_clearance → curl_cffi 复用（同 UA/同出口 IP）
放弃:  纯 HTTP 硬刚 Turnstile
```

### curl_cffi 限制

1. 无 JS 运行时，无法完成 Turnstile / 现代 Challenge  
2. 无 DOM / Web API 指纹环境  
3. 无法完成 Managed 模式点击  
4. TLS 指纹只是检测的一部分  

## 功能特点 / Features

| 功能 | 说明 |
|:---|:---|
| SeleniumBase UC Mode | 断连重连 + OS 级点击 |
| SeleniumBase CDP Mode | 纯 CDP 路径，减少 WebDriver 特征 |
| nodriver CDP | 无 chromedriver；`verify_cf` 图像点击 |
| 并行 / 代理轮换 | `simple_bypass.py` |
| 超时控制 | 主流程支持 timeout |
| Cookie 导出 | JSON + Netscape |
| 跨平台 | Mac / Windows / Linux（Linux 需 Xvfb） |

## 快速开始 / Quick Start

```bash
# 安装依赖
pip install -r requirements.txt

# 方案1 UC（推荐）
python bypass.py https://example.com
python bypass.py https://example.com -p http://127.0.0.1:7890 -t 90

# 方案5 CDP（2026）
python bypass_cdp.py https://example.com

# 方案3 nodriver
python bypass_nodriver.py https://example.com
```

## 安装部署 / Installation

### Mac / Windows

```bash
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
pip install -r requirements.txt
```

需要已安装 **Google Chrome**。

### Linux (Ubuntu/Debian)

```bash
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
sudo bash install_linux.sh
# 或:
# sudo apt-get install -y xvfb ...
# python3 -m pip install -r requirements.txt
```

> Chrome 官方 deb 主要为 **amd64**。ARM 请自备 Chromium/Chrome。

## 使用方法 / Usage

### 1. UC 单浏览器 `bypass.py`（推荐）

```bash
python bypass.py https://example.com
python bypass.py https://example.com -p http://127.0.0.1:7890
python bypass.py https://example.com -t 90 --incognito
```

| 参数 | 说明 | 默认 |
|:---|:---|:---:|
| `url` | 目标 URL | 必填 |
| `-p, --proxy` | 代理 | 无 |
| `-t, --timeout` | 总超时（秒） | 60 |
| `-r, --reconnect` | 断连秒数 | 5 |
| `--incognito` | 无痕 | 否 |
| `--no-save` | 不存 Cookie | 否 |

### 2. 并行 / 代理轮换 `simple_bypass.py`

```bash
python simple_bypass.py https://example.com
python simple_bypass.py https://example.com -r -f proxy.txt -c
python simple_bypass.py https://example.com -P -b 3 -t 30 -n 5 -c
```

| 参数 | 说明 | 默认 |
|:---|:---|:---:|
| `-r, --rotate` | 顺序代理轮换 | 否 |
| `-P, --parallel` | 并行 | 否 |
| `-b, --batch` | 每批浏览器数 | 3 |
| `-c, --check-proxy` | 预检代理 | 否 |
| `-n, --retries` | 批次数/代理数 | 3 |

> 并行时多个窗口会争抢系统鼠标，GUI 点击可能互相干扰。

### 3. nodriver `bypass_nodriver.py`

```bash
pip install "nodriver>=0.50.0" opencv-python-headless
python bypass_nodriver.py https://example.com
```

- API：`verify_cf()`（兼容旧名 `cf_verify`）  
- 许可：**AGPL-3.0**（闭源商用请评估）  
- 无头模式不推荐  

### 4. curl_cffi `bypass_curl_cffi.py`（非 Turnstile）

```bash
python bypass_curl_cffi.py https://example.com -f chrome146
```

仅适用于低防护 / 旧 Challenge，或**浏览器 cookie 复用**。

### 5. CDP Mode `bypass_cdp.py`（2026）

```bash
python bypass_cdp.py https://example.com
```

基于 `seleniumbase.sb_cdp`：`solve_captcha()` + `gui_click_captcha()`。

### 6. 类封装 `bypass_seleniumbase.py`

```python
from bypass_seleniumbase import bypass_and_get_cookies

result = bypass_and_get_cookies("https://example.com", proxy="http://127.0.0.1:7890")
if result["success"]:
    print(result["cf_clearance"])
```

### Python API（UC）

```python
from bypass import bypass_cloudflare

result = bypass_cloudflare("https://example.com", timeout=90)
if result["success"]:
    print(result["cf_clearance"])
    print(result["user_agent"])
```

## 代理文件格式 / Proxy Format

`proxy.txt` 每行一个：

```
127.0.0.1:7890
http://127.0.0.1:7890
socks5://127.0.0.1:1080
http://user:pass@host:port
```

公共免费代理大多不支持 HTTPS 隧道；生产请使用可靠住宅代理。

## 输出文件 / Output

Cookie 写入 `output/cookies/`：

| 前缀 | 来源 |
|:---|:---|
| `cookies_*.json/txt` | UC `bypass.py` / `simple_bypass.py` |
| `cookies_cdp_*.json` | CDP |
| `cookies_nodriver_*.json/txt` | nodriver |
| `cookies_curl_*.json/txt` | curl_cffi |

## 项目结构 / Structure

```
cloudflare-bypass-2026/
├── bypass.py                 # 方案1: SeleniumBase UC（推荐）
├── simple_bypass.py          # 方案2: 并行 + 代理轮换
├── bypass_nodriver.py        # 方案3: nodriver CDP
├── bypass_curl_cffi.py       # 方案4: TLS 指纹（非 Turnstile）
├── bypass_cdp.py             # 方案5: SeleniumBase CDP Mode
├── bypass_seleniumbase.py    # UC 类封装详细版
├── install_linux.sh          # Linux 安装
├── requirements.txt
├── proxy.txt
├── output/                   # Cookie 输出
└── README.md
```

## 常见问题 / FAQ

**Q: 应该用哪个方案？**  
> `bypass.py` 或 `bypass_cdp.py` 优先；难站可试 `bypass_nodriver.py`；批量用 `simple_bypass.py`。Turnstile **不要**用 curl_cffi。

**Q: 为什么不要无头模式？**  
> Cloudflare 对自动化无头更敏感。Linux 无桌面请用 **Xvfb**（`install_linux.sh` / `pyvirtualdisplay` / SB `xvfb=True`），而不是真 headless。

**Q: cf_clearance 多久失效？**  
> 通常数十分钟到数小时，且常与 **IP + UA** 绑定，换代理常需重解。

**Q: Linux 报 X11 / display？**  
> `sudo bash install_linux.sh` 或安装 `xvfb` + `pyvirtualdisplay`。

**Q: 代理不工作？**  
> 确认支持 HTTPS CONNECT；公共代理大量失效。

**Q: nodriver 报 OpenCV？**  
> `pip install opencv-python-headless`

**Q: 有没有“最新一键通杀”？**  
> 没有。对抗持续升级；成功率取决于目标策略、IP、浏览器环境与时机。

## 技术参考 / References

- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)
- [SeleniumBase UC Mode](https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/uc_mode.md)
- [SeleniumBase CDP Mode](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/cdp_mode/ReadMe.md)
- [nodriver](https://github.com/ultrafunkamsterdam/nodriver)
- [curl_cffi](https://github.com/lexiforest/curl_cffi)

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

- 本仓库代码默认按 **MIT License** 分发（见 `LICENSE`）。
- **nodriver** 上游为 **AGPL-3.0**，使用方案 3 时请遵守其许可证。

---

**如果这个项目对你有帮助，请给个 Star!**

**If this project helps you, please give it a Star!**
