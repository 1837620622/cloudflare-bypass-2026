# ============================================================
# Cloudflare Turnstile 绕过工具 - nodriver 方案
# 基于 CDP 协议直连，无需 WebDriver，SeleniumBase 替代方案
# 支持 Mac / Windows / Linux
# ============================================================
# 方案说明:
#   nodriver 是 undetected-chromedriver 的官方继任者
#   通过 Chrome DevTools Protocol (CDP) 直接通信，不依赖 Selenium
#   使用 verify_cf()（OpenCV 模板匹配）自动点击 Cloudflare 复选框
#   基于 asyncio 异步架构
# 许可注意: nodriver 为 AGPL-3.0，商用闭源前请评估合规
# ============================================================

import os
import sys
import json
import platform
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import nodriver as uc
except ImportError:
    print("[!] 请安装 nodriver: pip install 'nodriver>=0.50.0'")
    sys.exit(1)


CF_INDICATORS = (
    "turnstile",
    "challenges.cloudflare",
    "just a moment",
    "verify you are human",
    "checking your browser",
    "cf-browser-verification",
)


def is_linux() -> bool:
    """检测是否为 Linux 系统"""
    return platform.system().lower() == "linux"


def setup_linux_display():
    """设置 Linux 虚拟显示（无桌面服务器）"""
    if is_linux() and not os.environ.get("DISPLAY"):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ["DISPLAY"] = display.new_display_var
            print("[*] Linux: 已启动虚拟显示 (Xvfb)")
            return display
        except ImportError:
            print("[!] Linux无显示环境，请安装:")
            print("    apt-get install -y xvfb && pip install pyvirtualdisplay")
            sys.exit(1)
        except Exception as e:
            print(f"[!] 启动虚拟显示失败: {e}")
            sys.exit(1)
    return None


def load_proxies(filepath: str = "proxy.txt") -> List[str]:
    """从文件加载代理列表"""
    proxies = []
    path = Path(filepath)
    if not path.exists():
        return proxies

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if not line.startswith(("http://", "https://", "socks5://")):
                    line = f"http://{line}"
                proxies.append(line)
    return proxies


def _cookie_to_dict(c) -> Dict[str, Any]:
    """将 nodriver Cookie 对象或 dict 统一转为 dict"""
    if isinstance(c, dict):
        return c
    return {
        "name": getattr(c, "name", "") or "",
        "value": getattr(c, "value", "") or "",
        "domain": getattr(c, "domain", "") or "",
        "path": getattr(c, "path", "/") or "/",
        "secure": bool(getattr(c, "secure", False)),
        "expires": getattr(c, "expires", 0) or 0,
    }


def save_cookies_to_file(
    cookies_list: List[Any],
    url: str,
    user_agent: str,
    output_dir: str = "output/cookies",
) -> str:
    """保存 Cookie 到 JSON 和 Netscape 格式文件"""
    save_dir = Path(output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    normalized = [_cookie_to_dict(c) for c in cookies_list]
    cookies_dict = {c["name"]: c["value"] for c in normalized if c.get("name")}

    json_path = save_dir / f"cookies_nodriver_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "url": url,
                "cookies": cookies_dict,
                "user_agent": user_agent,
                "timestamp": ts,
                "method": "nodriver",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    txt_path = save_dir / f"cookies_nodriver_{ts}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for c in normalized:
            domain = c.get("domain", "")
            domain_flag = "FALSE" if domain and not str(domain).startswith(".") else "TRUE"
            secure = "TRUE" if c.get("secure") else "FALSE"
            path = c.get("path", "/") or "/"
            expiry = int(c.get("expires", 0) or 0)
            name = c.get("name", "")
            value = c.get("value", "")
            if not name:
                continue
            f.write(f"{domain}\t{domain_flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

    print(f"[+] Cookie已保存: {json_path}")
    return ts


async def _fetch_cookies(browser, tab) -> List[Any]:
    """
    获取 Cookie 列表。
    nodriver 的 tab.send(network.get_cookies()) 返回 List[Cookie]，不是 dict。
    """
    # 优先使用 Browser.cookies 高阶 API（若存在）
    try:
        if browser is not None and hasattr(browser, "cookies"):
            jar = browser.cookies
            if hasattr(jar, "get_all"):
                items = await jar.get_all()
                if items:
                    return list(items)
    except Exception as e:
        print(f"[*] browser.cookies 不可用: {e}")

    cookies_raw = await tab.send(uc.cdp.network.get_cookies())
    if isinstance(cookies_raw, dict):
        return list(cookies_raw.get("cookies") or [])
    if isinstance(cookies_raw, list):
        return cookies_raw
    return []


async def _fetch_user_agent(tab) -> str:
    """获取 navigator.userAgent"""
    try:
        if hasattr(tab, "evaluate"):
            ua = await tab.evaluate("navigator.userAgent")
            if isinstance(ua, str) and ua:
                return ua
    except Exception:
        pass
    try:
        ua_result = await tab.send(
            uc.cdp.runtime.evaluate(expression="navigator.userAgent", return_by_value=True)
        )
        # 兼容对象 / dict 两种返回
        if isinstance(ua_result, dict):
            result_obj = ua_result.get("result") or ua_result
            if isinstance(result_obj, dict):
                return str(result_obj.get("value") or "")
        value = getattr(getattr(ua_result, "result", None), "value", None)
        if value:
            return str(value)
    except Exception:
        pass
    return "unknown"


async def _click_cf_challenge(tab) -> None:
    """
    点击 Cloudflare 验证。
    当前 nodriver API 为 verify_cf()；兼容旧名 cf_verify。
    需要 opencv-python。
    """
    # 检查 opencv
    try:
        import cv2  # noqa: F401
    except ImportError:
        print("[!] verify_cf 需要 opencv: pip install opencv-python-headless")
        raise RuntimeError("缺少 opencv-python-headless") from None

    if hasattr(tab, "verify_cf"):
        await tab.verify_cf()
        print("[+] verify_cf() 执行完成")
        return
    if hasattr(tab, "cf_verify"):
        await tab.cf_verify()
        print("[+] cf_verify() 执行完成")
        return
    raise RuntimeError("当前 nodriver 版本无 verify_cf / cf_verify 方法")


async def bypass_cloudflare_nodriver(
    url: str,
    proxy: Optional[str] = None,
    headless: bool = False,
    timeout: float = 60.0,
    save_cookies: bool = True,
) -> Dict[str, Any]:
    """
    使用 nodriver 绕过 Cloudflare 验证

    参数:
        url: 目标网站 URL
        proxy: 代理地址 (http://host:port)
        headless: 无头模式（默认 False，Cloudflare 易检测）
        timeout: 整体超时（秒）
        save_cookies: 是否保存 Cookie
    """
    result: Dict[str, Any] = {
        "success": False,
        "cookies": {},
        "cf_clearance": None,
        "user_agent": None,
        "error": None,
        "method": "nodriver",
    }

    async def _run() -> Dict[str, Any]:
        browser = None
        try:
            print(f"[*] 目标: {url}")
            if proxy:
                print(f"[*] 代理: {proxy}")
            print("[*] 方案: nodriver (CDP直连)")

            browser_args = [
                "--no-first-run",
                "--disable-features=Translate",
                "--disable-blink-features=AutomationControlled",
            ]
            if proxy:
                browser_args.append(f"--proxy-server={proxy}")

            browser = await uc.start(
                headless=headless,
                browser_args=browser_args,
                lang="en-US",
            )

            tab = await browser.get(url)
            print("[*] 页面已加载，等待渲染...")
            await asyncio.sleep(3)

            page_content = await tab.get_content()
            page_text = (page_content or "").lower()

            if any(indicator in page_text for indicator in CF_INDICATORS):
                print("[*] 检测到 Cloudflare 验证页面")
                try:
                    await _click_cf_challenge(tab)
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"[!] 自动点击异常: {e}")
                    # 备用：文本查找
                    try:
                        el = await tab.find("verify you are human", best_match=True)
                        if el:
                            await el.click()
                            print("[*] 备用: 文本点击已尝试")
                            await asyncio.sleep(5)
                    except Exception as e2:
                        print(f"[!] 备用交互失败: {e2}")

            cookies_list = await _fetch_cookies(browser, tab)
            normalized = [_cookie_to_dict(c) for c in cookies_list]
            result["cookies"] = {c["name"]: c["value"] for c in normalized if c.get("name")}
            result["cf_clearance"] = result["cookies"].get("cf_clearance")
            result["user_agent"] = await _fetch_user_agent(tab)

            if result["cf_clearance"]:
                result["success"] = True
                print("[+] 成功获取 cf_clearance!")
                ua_preview = (result["user_agent"] or "")[:80]
                print(f"[+] User-Agent: {ua_preview}...")
                if save_cookies:
                    save_cookies_to_file(normalized, url, result["user_agent"] or "")
            else:
                result["error"] = "未获取到 cf_clearance"
                print(f"[-] {result['error']}")
                print(f"[-] 获取到的Cookie: {list(result['cookies'].keys())}")

        except Exception as e:
            result["error"] = str(e)
            print(f"[-] 错误: {e}")
        finally:
            if browser:
                try:
                    browser.stop()
                    print("[*] 浏览器已关闭")
                except Exception:
                    pass
        return result

    try:
        return await asyncio.wait_for(_run(), timeout=max(5.0, float(timeout)))
    except asyncio.TimeoutError:
        result["error"] = f"操作超时 ({timeout}秒)"
        print(f"[-] {result['error']}")
        return result


def bypass_sync(
    url: str,
    proxy: Optional[str] = None,
    headless: bool = False,
    timeout: float = 60.0,
    save_cookies: bool = True,
) -> Dict[str, Any]:
    """同步包装器，方便在非异步环境中调用"""
    return asyncio.run(
        bypass_cloudflare_nodriver(
            url=url,
            proxy=proxy,
            headless=headless,
            timeout=timeout,
            save_cookies=save_cookies,
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cloudflare Turnstile 绕过工具 (nodriver / CDP直连)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bypass_nodriver.py https://example.com
  python bypass_nodriver.py https://example.com -p http://127.0.0.1:7890
  python bypass_nodriver.py https://example.com --headless

注意:
  - verify_cf 需要: pip install opencv-python-headless
  - nodriver 许可证为 AGPL-3.0
        """,
    )
    parser.add_argument("url", help="目标URL")
    parser.add_argument("-p", "--proxy", help="代理地址 (格式: http://host:port)")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="启用无头模式 (不推荐，Cloudflare可检测)",
    )
    parser.add_argument("-t", "--timeout", type=float, default=60.0, help="超时时间 (默认: 60秒)")
    parser.add_argument("--no-save", action="store_true", help="不保存Cookie到文件")
    args = parser.parse_args()

    display = setup_linux_display()

    print("\n" + "=" * 50)
    print("Cloudflare Turnstile 绕过工具 - nodriver 方案")
    print(f"系统: {platform.system()} {platform.release()}")
    print("方案: CDP 直连 (nodriver)")
    print("=" * 50 + "\n")

    result = asyncio.run(
        bypass_cloudflare_nodriver(
            url=args.url,
            proxy=args.proxy,
            headless=args.headless,
            timeout=args.timeout,
            save_cookies=not args.no_save,
        )
    )

    print("\n" + "-" * 50)
    if result["success"]:
        print(f"[OK] 成功 | Cookie数: {len(result['cookies'])}")
        if result["cf_clearance"]:
            print(f"[OK] cf_clearance: {result['cf_clearance'][:50]}...")
    else:
        print(f"[FAIL] 失败: {result['error']}")
    print("-" * 50 + "\n")

    if display:
        display.stop()
