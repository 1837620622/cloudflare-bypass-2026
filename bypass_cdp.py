# ============================================================
# Cloudflare Turnstile 绕过工具 - SeleniumBase CDP Mode（2026 推荐）
# UC Mode 后继路径：直连 CDP，减少 WebDriver 特征
# 支持 Mac / Windows / Linux
# ============================================================

import os
import sys
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from seleniumbase import sb_cdp


def is_linux() -> bool:
    return platform.system().lower() == "linux"


def setup_display():
    """Linux 无 DISPLAY 时启动 Xvfb"""
    if is_linux() and not os.environ.get("DISPLAY"):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ["DISPLAY"] = display.new_display_var
            print("[*] Linux: 已启动虚拟显示 (Xvfb)")
            return display
        except ImportError:
            print("[!] 请安装: pip install pyvirtualdisplay && apt-get install -y xvfb")
            sys.exit(1)
        except Exception as e:
            print(f"[!] 启动虚拟显示失败: {e}")
            sys.exit(1)
    return None


def _cookies_to_dict(cookies: Any) -> Dict[str, str]:
    """将 get_all_cookies 返回值转为 name->value"""
    out: Dict[str, str] = {}
    if not cookies:
        return out
    if isinstance(cookies, dict):
        # 可能已是 name:value 或 cookie 结构
        if all(isinstance(v, str) for v in cookies.values()):
            return dict(cookies)
        for k, v in cookies.items():
            if isinstance(v, dict) and "value" in v:
                out[str(v.get("name", k))] = str(v.get("value", ""))
            else:
                out[str(k)] = str(v)
        return out
    if isinstance(cookies, list):
        for c in cookies:
            if isinstance(c, dict):
                name = c.get("name")
                if name:
                    out[str(name)] = str(c.get("value", ""))
            else:
                name = getattr(c, "name", None)
                if name:
                    out[str(name)] = str(getattr(c, "value", ""))
    return out


def _save_cookies(url: str, cookies: Dict[str, str], user_agent: Optional[str]) -> Path:
    save_dir = Path("output/cookies")
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = save_dir / f"cookies_cdp_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "url": url,
                "cookies": cookies,
                "user_agent": user_agent,
                "timestamp": ts,
                "method": "seleniumbase_cdp",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[+] Cookie已保存: {path}")
    return save_dir


def bypass_cloudflare_cdp(
    url: str,
    proxy: Optional[str] = None,
    timeout: float = 60.0,
    save_cookies: bool = True,
) -> Dict[str, Any]:
    """
    使用 SeleniumBase CDP Mode 绕过 Cloudflare。

    核心 API:
      - sb_cdp.Chrome() 纯 CDP 启动
      - sb.solve_captcha() / sb.gui_click_captcha()
    """
    result: Dict[str, Any] = {
        "success": False,
        "cookies": {},
        "cf_clearance": None,
        "user_agent": None,
        "error": None,
        "method": "seleniumbase_cdp",
    }

    sb = None
    try:
        print(f"[*] 目标: {url}")
        if proxy:
            print(f"[*] 代理: {proxy}")
        print("[*] 方案: SeleniumBase CDP Mode")
        print(f"[*] 超时参考: {timeout}s")

        # sb_cdp.Chrome 支持 proxy 参数（字符串）
        chrome_kwargs: Dict[str, Any] = {}
        if proxy:
            chrome_kwargs["proxy"] = proxy

        try:
            sb = sb_cdp.Chrome(**chrome_kwargs)
        except TypeError:
            # 旧版可能不接受 proxy kwargs
            sb = sb_cdp.Chrome()
            if proxy:
                print("[!] 当前 sb_cdp.Chrome 可能不支持 proxy 参数，请改用系统代理或 UC 方案")

        import time as _time

        deadline = _time.monotonic() + max(5.0, float(timeout))
        sb.open(url)
        sb.sleep(2)

        # 在超时窗口内：solve → GUI 点击 → 轮询 cf_clearance
        attempt = 0
        cookies: Dict[str, str] = {}
        while _time.monotonic() < deadline:
            attempt += 1
            try:
                if hasattr(sb, "solve_captcha"):
                    sb.solve_captcha()
                    print(f"[*] solve_captcha() #{attempt}")
            except Exception as e:
                print(f"[!] solve_captcha: {e}")

            try:
                if hasattr(sb, "gui_click_captcha"):
                    sb.gui_click_captcha()
                    print(f"[*] gui_click_captcha() #{attempt}")
            except Exception as e:
                print(f"[!] gui_click_captcha: {e}")

            sb.sleep(2)
            raw_cookies = None
            if hasattr(sb, "get_all_cookies"):
                raw_cookies = sb.get_all_cookies()
            elif hasattr(sb, "get_cookies"):
                raw_cookies = sb.get_cookies()
            cookies = _cookies_to_dict(raw_cookies)
            if cookies.get("cf_clearance"):
                break
            sb.sleep(1.5)

        result["cookies"] = cookies
        result["cf_clearance"] = cookies.get("cf_clearance")

        try:
            result["user_agent"] = sb.get_user_agent() if hasattr(sb, "get_user_agent") else None
        except Exception:
            result["user_agent"] = None

        if result["cf_clearance"]:
            result["success"] = True
            print("[+] 成功获取 cf_clearance!")
            if save_cookies:
                _save_cookies(url, cookies, result["user_agent"])
        else:
            if _time.monotonic() >= deadline:
                result["error"] = f"操作超时 ({timeout}秒)，未获取到 cf_clearance"
            else:
                result["error"] = "未获取到 cf_clearance"
            print(f"[-] {result['error']}")
            print(f"[-] Cookie keys: {list(cookies.keys())}")

    except Exception as e:
        result["error"] = str(e)
        print(f"[-] 错误: {e}")
    finally:
        if sb is not None:
            try:
                # CDP Chrome 通常用 driver.quit 或内部 stop
                if hasattr(sb, "driver") and sb.driver:
                    sb.driver.quit()
                elif hasattr(sb, "quit"):
                    sb.quit()
            except Exception:
                pass

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cloudflare Turnstile 绕过工具 (SeleniumBase CDP Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bypass_cdp.py https://example.com
  python bypass_cdp.py https://example.com -p http://127.0.0.1:7890

说明:
  CDP Mode 是 SeleniumBase UC Mode 的后继路径，减少 WebDriver 附着特征。
  有头模式 + 住宅 IP 成功率更高；请勿使用真 headless 硬刚 Turnstile。
        """,
    )
    parser.add_argument("url", help="目标URL")
    parser.add_argument("-p", "--proxy", help="代理地址")
    parser.add_argument("-t", "--timeout", type=float, default=60.0, help="超时参考秒数")
    parser.add_argument("--no-save", action="store_true", help="不保存Cookie")
    args = parser.parse_args()

    display = setup_display()

    print("\n" + "=" * 50)
    print("Cloudflare Turnstile 绕过工具 - CDP Mode")
    print(f"系统: {platform.system()} {platform.release()}")
    print("=" * 50 + "\n")

    result = bypass_cloudflare_cdp(
        url=args.url,
        proxy=args.proxy,
        timeout=args.timeout,
        save_cookies=not args.no_save,
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
