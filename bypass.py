# ============================================================
# Cloudflare Turnstile 绕过工具 - 单浏览器版本（推荐）
# 基于 SeleniumBase UC Mode
# 支持 Mac / Windows / Linux
# ============================================================

import os
import sys
import time
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from seleniumbase import SB


# Cloudflare 挑战页常见特征（避免用过宽的 "cloudflare" 单独匹配）
CF_INDICATORS = (
    "turnstile",
    "challenges.cloudflare",
    "just a moment",
    "verify you are human",
    "checking your browser",
    "cf-browser-verification",
    "cf-challenge",
)


def is_linux() -> bool:
    """检测是否为 Linux 系统"""
    return platform.system().lower() == "linux"


def setup_display():
    """
    设置 Linux 虚拟显示。
    优先依赖 SeleniumBase 内置 xvfb；此处作为无 DISPLAY 时的兜底。
    """
    if is_linux() and not os.environ.get("DISPLAY"):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ["DISPLAY"] = display.new_display_var
            print("[*] Linux: 已启动虚拟显示 (Xvfb)")
            return display
        except ImportError:
            print("[!] 请安装: pip install pyvirtualdisplay")
            print("[!] 以及: apt-get install -y xvfb")
            print("[!] 或使用: with SB(uc=True, xvfb=True) 由 SeleniumBase 管理显示")
            sys.exit(1)
        except Exception as e:
            print(f"[!] 启动虚拟显示失败: {e}")
            sys.exit(1)
    return None


def _page_has_cf_challenge(page_source: str) -> bool:
    """判断页面源码是否仍像 Cloudflare 挑战页"""
    text = (page_source or "").lower()
    return any(x in text for x in CF_INDICATORS)


def _try_click_captcha(sb) -> None:
    """
    尝试 OS 级点击验证码。
    优先 uc_gui_click_captcha（更隐蔽），失败再试 uc_gui_handle_captcha。
    """
    try:
        sb.uc_gui_click_captcha()
        return
    except Exception as e:
        print(f"[!] uc_gui_click_captcha: {e}")
    try:
        if hasattr(sb, "uc_gui_handle_captcha"):
            sb.uc_gui_handle_captcha()
    except Exception as e:
        print(f"[!] uc_gui_handle_captcha: {e}")


def _save_cookies(url: str, cookies_list: list, user_agent: Optional[str]) -> Path:
    """保存 Cookie 为 JSON + Netscape 双格式"""
    save_dir = Path("output/cookies")
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cookies_dict = {c["name"]: c["value"] for c in cookies_list}

    with open(save_dir / f"cookies_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "url": url,
                "cookies": cookies_dict,
                "user_agent": user_agent,
                "timestamp": ts,
                "method": "seleniumbase_uc",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(save_dir / f"cookies_{ts}.txt", "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for c in cookies_list:
            domain = c.get("domain", "")
            # host-only cookie：domain 不以 . 开头时 flag 应为 FALSE
            domain_flag = "FALSE" if domain and not domain.startswith(".") else "TRUE"
            secure = "TRUE" if c.get("secure") else "FALSE"
            expiry = int(c.get("expiry", 0) or 0)
            f.write(
                f"{domain}\t{domain_flag}\t{c.get('path', '/')}\t{secure}\t"
                f"{expiry}\t{c['name']}\t{c['value']}\n"
            )

    print(f"[+] Cookie已保存到: {save_dir}")
    return save_dir


def bypass_cloudflare(
    url: str,
    proxy: Optional[str] = None,
    timeout: float = 60.0,
    save_cookies: bool = True,
    reconnect_time: float = 5.0,
    incognito: bool = False,
) -> Dict[str, Any]:
    """
    绕过 Cloudflare 验证并获取 Cookie（单浏览器 UC Mode）

    参数:
        url: 目标网站 URL
        proxy: 代理地址（可选，格式: http://host:port）
        timeout: 整体超时时间（秒），含打开页面与点击重试
        save_cookies: 是否保存 Cookie 到文件
        reconnect_time: uc_open_with_reconnect 断连时长
        incognito: 是否无痕模式（部分站点需要）

    返回:
        success / cookies / cf_clearance / user_agent / error
    """
    result: Dict[str, Any] = {
        "success": False,
        "cookies": {},
        "cf_clearance": None,
        "user_agent": None,
        "error": None,
        "method": "seleniumbase_uc",
    }

    deadline = time.monotonic() + max(5.0, float(timeout))

    try:
        print(f"[*] 目标: {url}")
        if proxy:
            print(f"[*] 代理: {proxy}")
        print(f"[*] 超时: {timeout}s | reconnect: {reconnect_time}s")

        sb_kwargs = {
            "uc": True,
            "test": True,
            "locale": "en",
            "proxy": proxy,
        }
        if incognito:
            sb_kwargs["incognito"] = True
        # Linux 无 DISPLAY 时交给 SB 虚拟显示（与 setup_display 互补）
        if is_linux() and not os.environ.get("DISPLAY"):
            sb_kwargs["xvfb"] = True

        with SB(**sb_kwargs) as sb:
            print("[*] 浏览器已启动，正在加载页面...")
            if time.monotonic() >= deadline:
                result["error"] = f"操作超时 ({timeout}秒)"
                return result

            sb.uc_open_with_reconnect(url, reconnect_time=reconnect_time)
            time.sleep(2)

            # 在超时窗口内轮询：检测挑战 → 点击 → 等待 cf_clearance
            attempt = 0
            while time.monotonic() < deadline:
                attempt += 1
                cookies_list = sb.get_cookies()
                cookies = {c["name"]: c["value"] for c in cookies_list}
                cf_clearance = cookies.get("cf_clearance")
                page_source = sb.get_page_source()

                if cf_clearance and not _page_has_cf_challenge(page_source):
                    result["cookies"] = cookies
                    result["cf_clearance"] = cf_clearance
                    result["user_agent"] = sb.execute_script("return navigator.userAgent")
                    result["success"] = True
                    print(f"[+] 成功获取 cf_clearance! (第 {attempt} 轮检测)")
                    if save_cookies:
                        _save_cookies(url, cookies_list, result["user_agent"])
                    return result

                if cf_clearance:
                    # 有 cookie 但仍像挑战页：再等一会
                    print("[*] 已有 cf_clearance，等待页面稳定...")
                    result["cookies"] = cookies
                    result["cf_clearance"] = cf_clearance
                    result["user_agent"] = sb.execute_script("return navigator.userAgent")
                    time.sleep(2)
                    page_source = sb.get_page_source()
                    if not _page_has_cf_challenge(page_source):
                        result["success"] = True
                        print("[+] 页面已通过验证")
                        if save_cookies:
                            _save_cookies(url, sb.get_cookies(), result["user_agent"])
                        return result

                if _page_has_cf_challenge(page_source):
                    print(f"[*] 检测到 Cloudflare 验证，尝试点击 (#{attempt})...")
                    _try_click_captcha(sb)
                    time.sleep(3)
                else:
                    # 无挑战特征也无 cf_clearance：可能是低防护站
                    result["cookies"] = cookies
                    result["user_agent"] = sb.execute_script("return navigator.userAgent")
                    if cookies:
                        print("[*] 未检测到挑战页；站点可能无需 Turnstile")
                        # 低防护站：有任意 cookie 也算部分成功，但标记无 cf_clearance
                        result["error"] = "未获取到 cf_clearance（页面可能无需 Cloudflare 验证）"
                        return result
                    time.sleep(1.5)

            result["error"] = f"操作超时 ({timeout}秒)，未获取到有效 cf_clearance"
            print(f"[-] {result['error']}")

    except Exception as e:
        result["error"] = str(e)
        print(f"[-] 错误: {e}")

    return result


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cloudflare Turnstile 绕过工具 (单浏览器 UC Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bypass.py https://example.com
  python bypass.py https://example.com -p http://127.0.0.1:7890
  python bypass.py https://example.com -t 90 --incognito
        """,
    )
    parser.add_argument("url", help="目标URL")
    parser.add_argument("-p", "--proxy", help="代理地址")
    parser.add_argument("-t", "--timeout", type=float, default=60.0, help="超时时间 (默认: 60秒)")
    parser.add_argument(
        "-r",
        "--reconnect",
        type=float,
        default=5.0,
        help="uc_open_with_reconnect 断连秒数 (默认: 5)",
    )
    parser.add_argument("--incognito", action="store_true", help="无痕模式（部分站点需要）")
    parser.add_argument("--no-save", action="store_true", help="不保存Cookie")
    args = parser.parse_args()

    display = setup_display()

    print("\n" + "=" * 50)
    print("Cloudflare Turnstile 绕过工具")
    print(f"系统: {platform.system()} {platform.release()}")
    print("=" * 50 + "\n")

    result = bypass_cloudflare(
        url=args.url,
        proxy=args.proxy,
        timeout=args.timeout,
        save_cookies=not args.no_save,
        reconnect_time=args.reconnect,
        incognito=args.incognito,
    )

    print("\n" + "-" * 50)
    if result["success"]:
        print(f"[OK] 成功 | Cookie数: {len(result['cookies'])}")
        print(f"[OK] cf_clearance: {result['cf_clearance'][:50]}...")
    else:
        print(f"[FAIL] 失败: {result['error']}")
    print("-" * 50 + "\n")

    if display:
        display.stop()
