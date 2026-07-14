# Cloudflare Bypass Tool 2026

A multi-strategy toolkit for researching and testing **Cloudflare Turnstile / Challenge** flows on **macOS, Windows, and Linux**.

面向 Cloudflare Turnstile / Challenge 的多方案研究与授权测试工具集，支持 **Mac / Windows / Linux**。

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#installation--安装)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents / 目录

| English | 中文 |
|:---|:---|
| [Disclaimer](#disclaimer--免责声明) | [免责声明](#disclaimer--免责声明) |
| [Overview](#overview--项目概述) | [项目概述](#overview--项目概述) |
| [Method Comparison](#method-comparison--方案对比) | [方案对比](#method-comparison--方案对比) |
| [Features](#features--功能特性) | [功能特性](#features--功能特性) |
| [Requirements](#requirements--环境要求) | [环境要求](#requirements--环境要求) |
| [Installation](#installation--安装) | [安装](#installation--安装) |
| [Quick Start](#quick-start--快速开始) | [快速开始](#quick-start--快速开始) |
| [Usage](#usage--使用说明) | [使用说明](#usage--使用说明) |
| [Python API](#python-api) | [Python API](#python-api) |
| [Proxy Format](#proxy-format--代理格式) | [代理格式](#proxy-format--代理格式) |
| [Output](#output--输出) | [输出](#output--输出) |
| [Project Layout](#project-layout--项目结构) | [项目结构](#project-layout--项目结构) |
| [FAQ](#faq--常见问题) | [常见问题](#faq--常见问题) |
| [References](#references--参考资料) | [参考资料](#references--参考资料) |
| [Business](#business--商务合作) | [商务合作](#business--商务合作) |
| [License](#license--许可证) | [许可证](#license--许可证) |

---

## Disclaimer / 免责声明

**English**

This project is intended for **educational research** and **authorized automation testing** only. You must comply with applicable laws and the terms of service of any target website.

- No warranty of fitness for any particular site or environment.
- Success rates vary with IP reputation, browser environment, target policy, and timing.
- Datacenter IPs, true headless mode, and display-less containers typically reduce success rates.

**中文**

本项目仅供**学习研究**与**已授权**的自动化测试使用。使用时须遵守当地法律法规及目标站点服务条款。

- 不对任何站点、任何环境提供通过率保证。
- 实际效果受 IP 信誉、浏览器环境、目标策略与时机影响。
- 机房 IP、真无头模式、无图形界面的容器环境通常会显著降低成功率。

---

## Overview / 项目概述

**English**

Cloudflare defenses in 2025–2026 are layered: network reputation, TLS/HTTP fingerprinting, JavaScript challenges, Turnstile interaction, and automation-protocol signals. A single HTTP client is not sufficient for Turnstile.

This repository provides **five runnable strategies** plus one class-based wrapper, so you can choose the right path for single-session research, batch jobs, pure CDP control, or TLS-level reuse of an already-solved session.

**Recommended baseline (open-source path):**

```text
Headed real Chrome
  + optional residential / high-quality egress IP
  + UC reconnect or pure CDP
  + OS-level captcha click when interaction is required
```

**Not recommended as a primary Turnstile path:**

```text
True headless hard-target Managed Turnstile
Pure curl_cffi / tls-client against Turnstile
playwright-stealth alone as a “one-click” solution
```

**中文**

2025–2026 年 Cloudflare 检测已分层：网络信誉、TLS/HTTP 指纹、JS Challenge、Turnstile 交互，以及自动化协议特征。单靠 HTTP 客户端无法完成 Turnstile。

本仓库提供 **5 套可运行方案** 与 1 个类封装入口，覆盖单会话研究、批量任务、纯 CDP 控制，以及浏览器解出后的 TLS 层会话复用。

**开源场景下更稳妥的基线：**

```text
有头真实 Chrome
  + 可选住宅或高质量出口 IP
  + UC 断连重连 或 纯 CDP
  + 需要交互时使用操作系统级点击
```

**不建议作为 Turnstile 主路径：**

```text
真无头模式硬刚 Managed Turnstile
纯 curl_cffi / tls-client 直打 Turnstile
单独依赖 playwright-stealth 作为“一键方案”
```

---

## Method Comparison / 方案对比

| # | Script | Strategy / 策略 | Turnstile | Best for / 适用场景 |
|:---:|:---|:---|:---:|:---|
| 1 | `bypass.py` | SeleniumBase **UC Mode** | Yes | Default single-session path / 默认单会话主路径 |
| 2 | `simple_bypass.py` | UC + parallel / proxy rotation | Yes | Batch jobs; GUI click contention possible / 批量任务；并行时可能争抢系统鼠标 |
| 3 | `bypass_nodriver.py` | nodriver pure CDP | Yes | Chromedriver-free CDP; needs OpenCV; **AGPL-3.0** / 无 chromedriver；需 OpenCV；注意 AGPL |
| 4 | `bypass_curl_cffi.py` | TLS fingerprint / cookie reuse | **No** | Legacy JS Challenge or post-solve cookie reuse only / 仅旧版 Challenge 或 Cookie 复用 |
| 5 | `bypass_cdp.py` | SeleniumBase **CDP Mode** | Yes | 2026 successor path to plain UC / UC 后继路径 |
| — | `bypass_seleniumbase.py` | UC class wrapper | Yes | Embeddable API for secondary development / 可 import 的二次开发封装 |

### Priority guide / 选择优先级

| Priority / 优先级 | Choice / 选择 | Notes / 说明 |
|:---:|:---|:---|
| 1 | `bypass.py` or `bypass_cdp.py` | Primary research entry / 主入口 |
| 2 | `bypass_nodriver.py` | Strong CDP alternative; check AGPL / 强备选；注意许可证 |
| 3 | `simple_bypass.py` | Throughput / rotation; serialize GUI clicks if needed / 吞吐与轮换；GUI 点击宜串行 |
| 4 | Browser solve then `curl_cffi` reuse | Keep the same UA and egress IP / 须保持 UA 与出口 IP 一致 |
| Avoid | Pure HTTP against Turnstile | Will not execute JS / interact / 无法执行 JS 与交互 |

### Why curl_cffi cannot pass Turnstile / 为何 curl_cffi 无法过 Turnstile

| Limitation / 限制 | Detail / 说明 |
|:---|:---|
| No JS runtime | Cannot complete Turnstile / modern Challenge PoW |
| No DOM / Web APIs | Missing navigator, WebGL, canvas signals |
| No interaction | Managed mode requires a real checkbox click |
| TLS is only one signal | JA3/JA4 matching is not sufficient alone |

---

## Features / 功能特性

| Feature / 功能 | Description / 说明 |
|:---|:---|
| SeleniumBase UC Mode | Driver disconnect-reconnect + OS-level captcha click |
| SeleniumBase CDP Mode | Pure CDP path with reduced WebDriver attachment signals |
| nodriver CDP | No chromedriver; `verify_cf()` template click (OpenCV) |
| Parallel / proxy rotation | Batch workers and proxy file rotation in `simple_bypass.py` |
| Timeout control | End-to-end timeout on primary flows |
| Cookie export | JSON and Netscape formats where applicable |
| Cross-platform | macOS, Windows, Linux (Linux needs Xvfb when headless host) |

---

## Requirements / 环境要求

| Item / 项目 | Requirement / 要求 |
|:---|:---|
| Python | 3.9+ |
| Browser | Google Chrome (or Chromium on non-amd64 Linux) |
| Display | Headed GUI preferred; Linux servers: Xvfb / virtual display |
| OS | macOS, Windows, Linux |
| Optional proxy | HTTP / HTTPS / SOCKS5 with working HTTPS CONNECT |

Python packages are listed in `requirements.txt` (SeleniumBase, nodriver, curl_cffi, OpenCV headless, pyvirtualdisplay, etc.).

Python 依赖见 `requirements.txt`（含 SeleniumBase、nodriver、curl_cffi、OpenCV headless、pyvirtualdisplay 等）。

---

## Installation / 安装

### macOS / Windows

```bash
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
pip install -r requirements.txt
```

Install **Google Chrome** before running browser-based scripts.

请先安装 **Google Chrome**，再运行浏览器方案。

### Linux (Ubuntu / Debian)

```bash
git clone https://github.com/1837620622/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
sudo bash install_linux.sh
```

Manual alternative / 手动安装：

```bash
sudo apt-get update
sudo apt-get install -y xvfb libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libgbm1 libasound2
python3 -m pip install -r requirements.txt
```

**Notes / 说明**

- Official Chrome `.deb` packages are primarily **amd64**. On ARM hosts, install a matching Chromium/Chrome build yourself.
- 官方 Chrome deb 主要为 **amd64**。ARM 环境请自行准备对应架构的 Chromium/Chrome。

---

## Quick Start / 快速开始

```bash
# Install dependencies / 安装依赖
pip install -r requirements.txt

# Method 1 — UC Mode (recommended default) / 方案1 默认推荐
python bypass.py https://example.com
python bypass.py https://example.com -p http://127.0.0.1:7890 -t 90

# Method 5 — CDP Mode / 方案5 CDP
python bypass_cdp.py https://example.com

# Method 3 — nodriver / 方案3
python bypass_nodriver.py https://example.com
```

Replace `https://example.com` with a target you are authorized to test.

请将示例 URL 替换为**你有权测试**的目标地址。

---

## Usage / 使用说明

### 1. UC single browser — `bypass.py` (default)

Single Chrome session via SeleniumBase UC Mode: `uc_open_with_reconnect` + `uc_gui_click_captcha` / `uc_gui_handle_captcha`.

单浏览器 UC 模式：断连打开页面，并在检测到挑战时进行系统级点击。

```bash
python bypass.py https://example.com
python bypass.py https://example.com -p http://127.0.0.1:7890
python bypass.py https://example.com -t 90 --incognito
```

| Argument / 参数 | Description / 说明 | Default / 默认 |
|:---|:---|:---:|
| `url` | Target URL / 目标 URL | required |
| `-p, --proxy` | Proxy URL / 代理地址 | none |
| `-t, --timeout` | Overall timeout (seconds) / 总超时秒数 | 60 |
| `-r, --reconnect` | Reconnect disconnect window / 断连秒数 | 5 |
| `--incognito` | Incognito profile / 无痕模式 | off |
| `--no-save` | Do not write cookies / 不保存 Cookie | off |

---

### 2. Parallel / rotation — `simple_bypass.py`

For multi-proxy or multi-browser batches. OS-level GUI clicks are **not** multi-window safe on one desktop; parallel workers may contend for the mouse.

适用于多代理或多浏览器批处理。操作系统级点击在同一桌面上**不具备多窗口安全**；并行时可能互相干扰。

```bash
python simple_bypass.py https://example.com
python simple_bypass.py https://example.com -r -f proxy.txt -c
python simple_bypass.py https://example.com -P -b 3 -t 30 -n 5 -c
```

| Argument / 参数 | Description / 说明 | Default / 默认 |
|:---|:---|:---:|
| `-p, --proxy` | Fixed proxy / 固定代理 | none |
| `-f, --proxy-file` | Proxy list file / 代理列表文件 | `proxy.txt` |
| `-r, --rotate` | Sequential proxy rotation / 顺序轮换 | off |
| `-P, --parallel` | Parallel browsers / 并行浏览器 | off |
| `-b, --batch` | Browsers per batch / 每批浏览器数 | 3 |
| `-t, --timeout` | Timeout (seconds) / 超时秒数 | 60 |
| `-n, --retries` | Max batches or proxy attempts / 批次数或代理尝试数 | 3 |
| `-c, --check-proxy` | Preflight proxy liveness / 代理存活预检 | off |
| `-w, --wait` | Page wait / reconnect wait / 页面等待 | 5 |
| `--no-save` | Do not write cookies / 不保存 Cookie | off |

---

### 3. nodriver pure CDP — `bypass_nodriver.py`

Chromedriver-free CDP control. Challenge click uses `verify_cf()` (OpenCV template match). Upstream license is **AGPL-3.0**.

无 chromedriver 的 CDP 控制。挑战点击使用 `verify_cf()`（OpenCV 模板匹配）。上游许可证为 **AGPL-3.0**。

```bash
pip install "nodriver>=0.50.0" opencv-python-headless
python bypass_nodriver.py https://example.com
python bypass_nodriver.py https://example.com -p http://127.0.0.1:7890
```

| Argument / 参数 | Description / 说明 | Default / 默认 |
|:---|:---|:---:|
| `-p, --proxy` | Proxy URL / 代理 | none |
| `-t, --timeout` | Overall timeout / 总超时 | 60 |
| `--headless` | Headless (not recommended) / 无头（不推荐） | off |
| `--no-save` | Do not write cookies / 不保存 Cookie | off |

Commercial closed-source redistribution of AGPL components requires a separate compliance review.

闭源商用分发 AGPL 组件前请自行完成合规评估。

---

### 4. TLS client — `bypass_curl_cffi.py` (not for Turnstile)

HTTP/TLS fingerprint impersonation only. Suitable for weak or legacy challenges, or for replaying cookies obtained by a browser solver **with matching User-Agent and egress IP**.

仅 HTTP/TLS 指纹仿冒。适用于低防护或旧版 Challenge，或在 **UA 与出口 IP 一致** 的前提下复用浏览器解出的 Cookie。

```bash
python bypass_curl_cffi.py https://example.com
python bypass_curl_cffi.py https://example.com -f chrome146
python bypass_curl_cffi.py https://example.com -p http://127.0.0.1:7890
```

| Argument / 参数 | Description / 说明 | Default / 默认 |
|:---|:---|:---:|
| `-p, --proxy` | Proxy URL / 代理 | none |
| `-f, --fingerprint` | Impersonation profile / 指纹配置 | `chrome136` |
| `-t, --timeout` | Request timeout / 请求超时 | 30 |
| `-n, --retries` | Retry count / 重试次数 | 3 |
| `--no-save` | Do not write cookies / 不保存 Cookie | off |

Common fingerprints include: `chrome120`, `chrome124`, `chrome131`, `chrome136`, `chrome142`, `chrome146`, `firefox135`, `firefox144`, `safari17_0`, `safari18_0`, `edge101`.

---

### 5. CDP Mode — `bypass_cdp.py`

SeleniumBase CDP Mode (`sb_cdp`): `solve_captcha()` with `gui_click_captcha()` fallback. Preferred upgrade path alongside UC Mode in 2026.

SeleniumBase CDP 模式：优先 `solve_captcha()`，失败时回退 `gui_click_captcha()`。2026 年与 UC 并列的升级路径。

```bash
python bypass_cdp.py https://example.com
python bypass_cdp.py https://example.com -p http://127.0.0.1:7890 -t 90
```

| Argument / 参数 | Description / 说明 | Default / 默认 |
|:---|:---|:---:|
| `-p, --proxy` | Proxy URL / 代理 | none |
| `-t, --timeout` | Overall timeout budget / 总超时预算 | 60 |
| `--no-save` | Do not write cookies / 不保存 Cookie | off |

---

### 6. Class wrapper — `bypass_seleniumbase.py`

Object-oriented UC wrapper for embedding in larger projects.

面向对象的 UC 封装，便于嵌入更大工程。

```bash
python bypass_seleniumbase.py https://example.com -p http://127.0.0.1:7890
```

---

## Python API

### UC Mode (`bypass.py`)

```python
from bypass import bypass_cloudflare

result = bypass_cloudflare(
    "https://example.com",
    proxy="http://127.0.0.1:7890",
    timeout=90,
    save_cookies=True,
)

if result["success"]:
    print(result["cf_clearance"])
    print(result["user_agent"])
    print(result["cookies"])
else:
    print(result["error"])
```

### Class wrapper (`bypass_seleniumbase.py`)

```python
from bypass_seleniumbase import bypass_and_get_cookies

result = bypass_and_get_cookies(
    "https://example.com",
    proxy="http://127.0.0.1:7890",
    session_name="demo",
)

if result["success"]:
    print(result["cf_clearance"])
```

### nodriver (sync helper)

```python
from bypass_nodriver import bypass_sync

result = bypass_sync("https://example.com", timeout=60.0)
```

### curl_cffi (non-Turnstile)

```python
from bypass_curl_cffi import bypass_cloudflare_http

# Optional: reuse browser-solved cookies
result = bypass_cloudflare_http(
    "https://example.com",
    fingerprint="chrome146",
    cookies={"cf_clearance": "..."},  # optional
)
```

### Result shape / 返回字段

| Field / 字段 | Type / 类型 | Meaning / 含义 |
|:---|:---|:---|
| `success` | `bool` | Whether a usable clearance path was obtained / 是否获得可用通过结果 |
| `cookies` | `dict` | Name to value map / Cookie 字典 |
| `cf_clearance` | `str` or `None` | Cloudflare clearance cookie when present |
| `user_agent` | `str` or `None` | Browser UA used for the session / 会话 UA |
| `error` | `str` or `None` | Failure reason / 失败原因 |
| `method` | `str` | Strategy identifier / 方案标识 |

---

## Proxy Format / 代理格式

File: `proxy.txt` (one entry per line) / 每行一个代理：

```text
127.0.0.1:7890
http://127.0.0.1:7890
socks5://127.0.0.1:1080
http://user:pass@host:port
```

Most free public proxies do not support HTTPS CONNECT reliably. Prefer verified residential or high-quality providers for production research.

绝大多数免费公共代理无法稳定支持 HTTPS 隧道。研究与生产环境请使用经验证的住宅或高质量代理。

---

## Output / 输出

Cookies are written under `output/cookies/` when saving is enabled.

启用保存时，Cookie 写入 `output/cookies/`。

| Prefix / 前缀 | Source / 来源 |
|:---|:---|
| `cookies_*.json` / `cookies_*.txt` | `bypass.py`, `simple_bypass.py` |
| `cookies_cdp_*.json` | `bypass_cdp.py` |
| `cookies_nodriver_*.json` / `cookies_nodriver_*.txt` | `bypass_nodriver.py` |
| `cookies_curl_*.json` / `cookies_curl_*.txt` | `bypass_curl_cffi.py` |

**JSON example / JSON 示例**

```json
{
  "url": "https://example.com",
  "cookies": {
    "cf_clearance": "..."
  },
  "user_agent": "Mozilla/5.0 ...",
  "timestamp": "20260714_120000",
  "method": "seleniumbase_uc"
}
```

`cf_clearance` is frequently bound to **IP + User-Agent**. Changing either often requires a new solve.

`cf_clearance` 常与 **IP + User-Agent** 绑定。更换任一端通常需要重新求解。

---

## Project Layout / 项目结构

```text
cloudflare-bypass-2026/
├── bypass.py                 # Method 1: SeleniumBase UC (default)
├── simple_bypass.py          # Method 2: parallel + proxy rotation
├── bypass_nodriver.py        # Method 3: nodriver CDP
├── bypass_curl_cffi.py       # Method 4: TLS fingerprint (non-Turnstile)
├── bypass_cdp.py             # Method 5: SeleniumBase CDP Mode
├── bypass_seleniumbase.py    # UC class wrapper
├── install_linux.sh          # Linux bootstrap
├── requirements.txt          # Python dependencies
├── proxy.txt                 # Sample proxy list
├── LICENSE
├── README.md
└── output/                   # Runtime cookie exports (created on use)
```

---

## FAQ / 常见问题

**Which method should I use first?**  
**优先使用哪个方案？**

Start with `bypass.py` or `bypass_cdp.py`. Use `bypass_nodriver.py` when you want a chromedriver-free CDP stack. Use `simple_bypass.py` for batch/proxy rotation. Do **not** use `bypass_curl_cffi.py` for Turnstile.

优先 `bypass.py` 或 `bypass_cdp.py`。需要无 chromedriver 的 CDP 时用 `bypass_nodriver.py`。批量与代理轮换用 `simple_bypass.py`。Turnstile **不要**使用 `bypass_curl_cffi.py`。

---

**Why avoid true headless mode?**  
**为什么避免真无头模式？**

Automation headless profiles are easier to fingerprint. On Linux servers without a desktop, use **Xvfb** / virtual display (`install_linux.sh`, `pyvirtualdisplay`, or SeleniumBase `xvfb=True`) instead of Chrome headless.

无头自动化特征更容易被识别。无桌面的 Linux 请使用 **Xvfb** / 虚拟显示，而不是 Chrome 真无头。

---

**How long does `cf_clearance` last?**  
**`cf_clearance` 有效期多久？**

Typically tens of minutes to several hours, depending on site policy. It is often tied to IP and UA; proxy changes frequently invalidate it.

通常数十分钟到数小时，取决于站点策略；常与 IP、UA 绑定，换代理后往往需要重解。

---

**Linux error: X11 / display failed**  
**Linux 报 X11 / display 失败**

```bash
sudo bash install_linux.sh
# or / 或
sudo apt-get install -y xvfb
pip install pyvirtualdisplay
```

---

**Proxy does not work**  
**代理不可用**

Confirm HTTPS CONNECT support and authentication. Public free lists are mostly unusable for this workload.

确认代理支持 HTTPS CONNECT 与鉴权。公开免费列表对本场景大多不可用。

---

**nodriver reports missing OpenCV**  
**nodriver 提示缺少 OpenCV**

```bash
pip install opencv-python-headless
```

---

**Is there a universal bypass?**  
**是否存在通杀方案？**

No. Defenses evolve continuously. Outcomes depend on target configuration, egress reputation, browser fidelity, and timing. This toolkit does not claim universal success.

没有。防御持续演进。结果取决于目标配置、出口信誉、浏览器还原度与时机。本工具不宣称通杀。

---

## References / 参考资料

- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)
- [Cloudflare Challenges](https://developers.cloudflare.com/cloudflare-challenges/)
- [SeleniumBase UC Mode](https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/uc_mode.md)
- [SeleniumBase CDP Mode](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/cdp_mode/ReadMe.md)
- [nodriver](https://github.com/ultrafunkamsterdam/nodriver)
- [curl_cffi](https://github.com/lexiforest/curl_cffi)

---

## Business / 商务合作

Sponsorship placement, custom development, and technical consulting are welcome.

欢迎洽谈赞助展示、定制开发与技术咨询。

| Channel / 渠道 | Contact / 联系方式 |
|:---|:---|
| WeChat / 微信 | `1837620622` (传康Kk) |
| Email / 邮箱 | `2040168455@qq.com` |
| Xianyu / Bilibili | 万能程序员 |

Please contact via WeChat first and note **Business** / **商务合作**.

请优先微信联系，并备注「商务合作」。

---

## License / 许可证

- Repository code is distributed under the **MIT License** (see `LICENSE`).
- **nodriver** is licensed under **AGPL-3.0**. Using Method 3 requires compliance with that license.

- 本仓库代码按 **MIT License** 分发（见 `LICENSE`）。
- **nodriver** 上游为 **AGPL-3.0**。使用方案 3 时须遵守其许可证。

---

If this project is useful, consider starring the repository.

如果本项目对你有帮助，欢迎 Star 支持。
