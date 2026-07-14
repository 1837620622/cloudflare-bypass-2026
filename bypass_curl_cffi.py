# ============================================================
# Cloudflare 绕过工具 - curl_cffi 方案 (仅限简单场景)
# 基于 TLS/JA3 指纹仿冒，HTTP 协议层，无需浏览器
# 支持 Mac / Windows / Linux
# ============================================================
#
# 重要限制:
#   1. 无法执行 JavaScript — Turnstile 必须依赖浏览器 JS 环境
#   2. 无法运行 Web API 探测 — Turnstile 会检查 navigator/webgl 等
#   3. 无法完成 PoW 计算 — Turnstile 后台运行 proof-of-work
#   4. 无法处理交互式验证 — Managed/Interactive 模式需要点击
#
# 适用:
#   - 旧版 Cloudflare "Under Attack" JS Challenge / 低防护站点
#   - 浏览器已拿到 cf_clearance 后的 Cookie 复用（混合架构）
#
# 不适用: Cloudflare Turnstile（任何模式）
# 建议: Turnstile 请用 bypass.py / bypass_cdp.py / bypass_nodriver.py
# ============================================================

import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from curl_cffi import requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False


# 与 curl_cffi 0.15+ 对齐的常用指纹（去掉已不存在的 firefox121 等）
BROWSER_FINGERPRINTS = {
    "chrome120": {"impersonate": "chrome120", "name": "Chrome 120"},
    "chrome124": {"impersonate": "chrome124", "name": "Chrome 124"},
    "chrome131": {"impersonate": "chrome131", "name": "Chrome 131"},
    "chrome136": {"impersonate": "chrome136", "name": "Chrome 136"},
    "chrome142": {"impersonate": "chrome142", "name": "Chrome 142"},
    "chrome146": {"impersonate": "chrome146", "name": "Chrome 146"},
    "firefox135": {"impersonate": "firefox135", "name": "Firefox 135"},
    "firefox144": {"impersonate": "firefox144", "name": "Firefox 144"},
    "safari17_0": {"impersonate": "safari17_0", "name": "Safari 17.0"},
    "safari18_0": {"impersonate": "safari18_0", "name": "Safari 18.0"},
    "edge101": {"impersonate": "edge101", "name": "Edge 101"},
}

# 与指纹大致匹配的 UA（避免 TLS 仿 Chrome 却发 Firefox UA）
FINGERPRINT_UA = {
    "chrome120": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "chrome124": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "chrome131": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "chrome136": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "chrome142": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "chrome146": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "firefox135": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "firefox144": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "safari17_0": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "safari18_0": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "edge101": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47",
}


def make_headers(user_agent: str, fingerprint: str) -> Dict[str, str]:
    """生成与所选指纹大致匹配的请求头"""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }
    if fingerprint.startswith("chrome") or fingerprint.startswith("edge"):
        ver = "120"
        for token in ("146", "142", "136", "131", "124", "120", "101"):
            if token in fingerprint:
                ver = token
                break
        brand = "Microsoft Edge" if fingerprint.startswith("edge") else "Google Chrome"
        headers["Sec-Ch-Ua"] = f'"Not_A Brand";v="8", "Chromium";v="{ver}", "{brand}";v="{ver}"'
        headers["Sec-Ch-Ua-Mobile"] = "?0"
        headers["Sec-Ch-Ua-Platform"] = '"Windows"'
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "none"
        headers["Sec-Fetch-User"] = "?1"
    return headers


def save_cookies_to_file(
    cookies_dict: Dict[str, str],
    url: str,
    user_agent: str,
    output_dir: str = "output/cookies",
) -> str:
    """保存 Cookie 到 JSON 和 Netscape 格式"""
    save_dir = Path(output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = save_dir / f"cookies_curl_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "url": url,
                "cookies": cookies_dict,
                "user_agent": user_agent,
                "timestamp": ts,
                "method": "curl_cffi",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    txt_path = save_dir / f"cookies_curl_{ts}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lstrip(".")
        for name, value in cookies_dict.items():
            f.write(f"{domain}\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n")

    print(f"[+] Cookie已保存: {json_path}")
    return ts


def bypass_cloudflare_http(
    url: str,
    proxy: Optional[str] = None,
    fingerprint: str = "chrome136",
    timeout: float = 30.0,
    max_retries: int = 3,
    save_cookies: bool = True,
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    使用 curl_cffi 在 HTTP/TLS 层访问受保护站点。

    注意: 无法绕过 Cloudflare Turnstile。
    可选传入已有 cookies（如浏览器解出的 cf_clearance）做会话复用。

    参数:
        url: 目标 URL
        proxy: 代理
        fingerprint: 浏览器指纹类型
        timeout: 超时秒数
        max_retries: 最大重试
        save_cookies: 是否保存 Cookie
        cookies: 预置 Cookie（混合架构复用）
    """
    if not HAS_CURL_CFFI:
        return {
            "success": False,
            "cookies": {},
            "cf_clearance": None,
            "user_agent": None,
            "error": "curl_cffi 未安装，请执行: pip install curl_cffi",
            "method": "curl_cffi",
        }

    result: Dict[str, Any] = {
        "success": False,
        "cookies": {},
        "cf_clearance": None,
        "user_agent": None,
        "error": None,
        "method": "curl_cffi",
    }

    fp_config = BROWSER_FINGERPRINTS.get(fingerprint, BROWSER_FINGERPRINTS["chrome136"])
    print(f"[*] 目标: {url}")
    print("[*] 方案: curl_cffi (TLS指纹仿冒，非 Turnstile)")
    print(f"[*] 指纹: {fp_config['name']}")
    if proxy:
        print(f"[*] 代理: {proxy}")
    if cookies:
        print(f"[*] 预置 Cookie: {list(cookies.keys())}")

    retry_fingerprints = list(BROWSER_FINGERPRINTS.keys())
    if fingerprint in retry_fingerprints:
        retry_fingerprints.remove(fingerprint)
    retry_fingerprints.insert(0, fingerprint)

    for attempt in range(max_retries):
        current_fp = retry_fingerprints[attempt % len(retry_fingerprints)]
        current_fp_config = BROWSER_FINGERPRINTS[current_fp]

        if attempt > 0:
            print(f"\n[*] 第 {attempt + 1}/{max_retries} 次重试...")
            print(f"[*] 切换指纹: {current_fp_config['name']}")
            time.sleep(1)

        session = None
        try:
            user_agent = FINGERPRINT_UA.get(current_fp, FINGERPRINT_UA["chrome136"])
            headers = make_headers(user_agent, current_fp)

            session = requests.Session()
            proxies = None
            if proxy:
                proxies = {"http": proxy, "https": proxy}

            print(f"[*] 发送请求 (指纹: {current_fp_config['name']})...")
            response = session.get(
                url,
                headers=headers,
                impersonate=current_fp,
                proxies=proxies,
                timeout=timeout,
                allow_redirects=True,
                verify=False,
                cookies=cookies,
            )

            result["status_code"] = response.status_code
            page_text = response.text.lower() if response.text else ""

            cf_blocked = any(
                indicator in page_text
                for indicator in (
                    "just a moment",
                    "checking your browser",
                    "verify you are human",
                    "turnstile",
                )
            )

            cookies_dict: Dict[str, str] = {}
            try:
                for cookie in response.cookies:
                    name = getattr(cookie, "name", None) or (cookie[0] if isinstance(cookie, tuple) else None)
                    value = getattr(cookie, "value", None) or (cookie[1] if isinstance(cookie, tuple) else None)
                    if name:
                        cookies_dict[str(name)] = str(value)
            except Exception:
                pass

            # 合并预置 cookie
            if cookies:
                for k, v in cookies.items():
                    cookies_dict.setdefault(k, v)

            set_cookie = response.headers.get("Set-Cookie", "") or ""
            cf_clearance = cookies_dict.get("cf_clearance")
            if not cf_clearance and set_cookie:
                match = re.search(r"cf_clearance=([^;]+)", set_cookie)
                if match:
                    cf_clearance = match.group(1)
                    cookies_dict["cf_clearance"] = cf_clearance

            result["cookies"] = cookies_dict
            result["cf_clearance"] = cf_clearance
            result["user_agent"] = user_agent

            if response.status_code == 200 and not cf_blocked:
                result["success"] = True
                print("[+] HTTP 200 且未检测到挑战页")
                print(f"[+] 状态码: {response.status_code}")
                print(f"[+] 响应大小: {len(response.content)} bytes")
                if save_cookies and cookies_dict:
                    save_cookies_to_file(cookies_dict, url, user_agent)
                break

            if cf_clearance and not cf_blocked:
                result["success"] = True
                print("[+] 成功获取/复用 cf_clearance")
                if save_cookies:
                    save_cookies_to_file(cookies_dict, url, user_agent)
                break

            if cf_blocked:
                print("[!] 页面仍为 Cloudflare 挑战（curl_cffi 无法执行 JS/Turnstile）")
                print("[!] 请改用: python bypass.py / bypass_cdp.py / bypass_nodriver.py")
                result["error"] = "需要浏览器环境执行 Challenge/Turnstile"
            else:
                print(f"[-] 状态码: {response.status_code} | 未确认通过")
                result["error"] = f"HTTP {response.status_code}: 未通过或未获取 cf_clearance"

        except Exception as e:
            # curl_cffi 异常类型可能是 requests.exceptions.*
            err_name = type(e).__name__
            result["error"] = f"{err_name}: {e}"
            print(f"[-] {result['error']}")
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass

        if attempt >= max_retries - 1:
            break

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cloudflare HTTP/TLS 访问工具 (curl_cffi，非 Turnstile 方案)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  python bypass_curl_cffi.py https://example.com
  python bypass_curl_cffi.py https://example.com -p http://127.0.0.1:7890
  python bypass_curl_cffi.py https://example.com -f chrome146

可用指纹:
  {', '.join(BROWSER_FINGERPRINTS.keys())}

警告:
  本工具不能绕过 Cloudflare Turnstile。Turnstile 请用浏览器方案。
        """,
    )
    parser.add_argument("url", help="目标URL")
    parser.add_argument("-p", "--proxy", help="代理地址")
    parser.add_argument(
        "-f",
        "--fingerprint",
        default="chrome136",
        choices=list(BROWSER_FINGERPRINTS.keys()),
        help="浏览器指纹类型 (默认: chrome136)",
    )
    parser.add_argument("-t", "--timeout", type=float, default=30.0, help="超时时间 (默认: 30秒)")
    parser.add_argument("-n", "--retries", type=int, default=3, help="最大重试次数 (默认: 3)")
    parser.add_argument("--no-save", action="store_true", help="不保存Cookie到文件")
    args = parser.parse_args()

    if not HAS_CURL_CFFI:
        print("[!] curl_cffi 未安装")
        print("[!] 请执行: pip install curl_cffi")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Cloudflare 访问工具 - curl_cffi (非 Turnstile)")
    print("方案: TLS/JA3 指纹仿冒")
    print("=" * 50 + "\n")

    result = bypass_cloudflare_http(
        url=args.url,
        proxy=args.proxy,
        fingerprint=args.fingerprint,
        timeout=args.timeout,
        max_retries=args.retries,
        save_cookies=not args.no_save,
    )

    print("\n" + "-" * 50)
    if result["success"]:
        print(f"[OK] 成功 | Cookie数: {len(result['cookies'])} | 状态码: {result.get('status_code')}")
        if result.get("cf_clearance"):
            print(f"[OK] cf_clearance: {result['cf_clearance'][:50]}...")
    else:
        print(f"[FAIL] 失败: {result['error']}")
        print("\n[*] 提示:")
        print("[*] - 浏览器 UC:   python bypass.py " + args.url)
        print("[*] - 浏览器 CDP:  python bypass_cdp.py " + args.url)
        print("[*] - nodriver:    python bypass_nodriver.py " + args.url)
    print("-" * 50 + "\n")
