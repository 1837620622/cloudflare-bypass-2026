# ============================================================
# SeleniumBase UC Mode 详细版（独立可运行，类封装）
# 用于绕过 Cloudflare Turnstile 验证
# ============================================================

import time
import random
import json
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass

from seleniumbase import SB


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    proxy: Optional[str] = None
    window_width: int = 1280
    window_height: int = 900
    page_load_timeout: int = 60
    user_agent: Optional[str] = None
    incognito: bool = False
    reconnect_time: float = 4.0


@dataclass
class TurnstileConfig:
    """Turnstile 点击配置"""
    max_retries: int = 5
    retry_interval: float = 2.0
    click_delay_min: float = 0.4
    click_delay_max: float = 1.2


CF_INDICATORS = (
    "turnstile",
    "challenges.cloudflare",
    "just a moment",
    "verify you are human",
    "checking your browser",
    "cf-browser-verification",
)


class CloudflareBypassSeleniumBase:
    """
    基于 SeleniumBase UC Mode 的 Cloudflare 绕过工具（独立版）

    主要功能:
    1. 自动检测并处理 Cloudflare Turnstile
    2. OS 级 GUI 点击（uc_gui_click_captcha）
    3. 保存 Cookie（JSON）
    """

    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        turnstile_config: Optional[TurnstileConfig] = None,
        session_name: str = "seleniumbase_session",
    ):
        self.browser_config = browser_config or BrowserConfig()
        self.turnstile_config = turnstile_config or TurnstileConfig()
        self.session_name = session_name
        self._sb_cm = None
        self.sb = None
        self._is_initialized = False
        self._turnstile_passed = False
        self._last_cookies: List[Dict[str, Any]] = []

    def start(self) -> "CloudflareBypassSeleniumBase":
        """启动浏览器（支持链式调用）"""
        if self._is_initialized:
            return self

        kwargs: Dict[str, Any] = {
            "uc": True,
            "test": True,
            "locale": "en",
            "proxy": self.browser_config.proxy,
        }
        if self.browser_config.headless:
            # 官方不推荐 UC + 真 headless；仅按用户显式要求开启
            kwargs["headless"] = True
        if self.browser_config.incognito:
            kwargs["incognito"] = True
        if platform.system().lower() == "linux" and not __import__("os").environ.get("DISPLAY"):
            kwargs["xvfb"] = True

        self._sb_cm = SB(**kwargs)
        self.sb = self._sb_cm.__enter__()
        try:
            self.sb.set_window_size(
                self.browser_config.window_width,
                self.browser_config.window_height,
            )
        except Exception:
            pass
        self._is_initialized = True
        print(f"[*] 浏览器已启动 (session={self.session_name})")
        return self

    def open_with_bypass(
        self,
        url: str,
        wait_time: Optional[float] = None,
        auto_click_turnstile: bool = True,
    ) -> bool:
        """打开 URL 并尝试绕过 Cloudflare"""
        if not self._is_initialized:
            self.start()

        reconnect = wait_time if wait_time is not None else self.browser_config.reconnect_time
        print(f"[*] 打开: {url}")
        try:
            self.sb.uc_open_with_reconnect(url, reconnect_time=reconnect)
        except Exception as e:
            print(f"[-] 打开页面失败: {e}")
            return False

        self._human_delay(1.0, 2.0)

        if auto_click_turnstile:
            for attempt in range(self.turnstile_config.max_retries):
                print(f"[*] 检测验证 ({attempt + 1}/{self.turnstile_config.max_retries})")
                if self._detect_challenge():
                    print("[*] 检测到挑战，尝试 GUI 点击...")
                    if self._click_turnstile():
                        self._turnstile_passed = True
                        print("[+] 验证处理完成")
                        break
                    time.sleep(self.turnstile_config.retry_interval)
                else:
                    print("[*] 未检测到挑战特征，可能已通过")
                    self._turnstile_passed = True
                    break

        self._capture_cookies()
        # 有 cf_clearance 或已无挑战页，视为成功路径
        if self.get_cf_clearance():
            self._turnstile_passed = True
        return self._turnstile_passed

    def _detect_challenge(self) -> bool:
        """检测是否仍在 Cloudflare 挑战页"""
        try:
            if self.sb.is_element_present("iframe[src*='challenges.cloudflare.com']"):
                return True
            if self.sb.is_element_present("iframe[src*='turnstile']"):
                return True
            if self.sb.is_element_present("div.cf-turnstile"):
                return True
        except Exception:
            pass
        try:
            page = (self.sb.get_page_source() or "").lower()
            return any(x in page for x in CF_INDICATORS)
        except Exception:
            return False

    def _click_turnstile(self) -> bool:
        """OS 级点击 Turnstile / CAPTCHA"""
        self._human_delay(
            self.turnstile_config.click_delay_min,
            self.turnstile_config.click_delay_max,
        )
        try:
            self.sb.uc_gui_click_captcha()
            time.sleep(3)
            if not self._detect_challenge():
                return True
        except Exception as e:
            print(f"[!] uc_gui_click_captcha: {e}")

        try:
            if hasattr(self.sb, "uc_gui_handle_captcha"):
                self.sb.uc_gui_handle_captcha()
                time.sleep(3)
                if not self._detect_challenge():
                    return True
        except Exception as e:
            print(f"[!] uc_gui_handle_captcha: {e}")

        # 键盘 Tab + Space 兜底
        try:
            for _ in range(5):
                self.sb.uc_gui_press_key("\t")
                self._human_delay(0.1, 0.25)
            self.sb.uc_gui_press_key(" ")
            time.sleep(3)
            if not self._detect_challenge():
                return True
        except Exception as e:
            print(f"[!] 键盘导航失败: {e}")

        return False

    def _human_delay(self, min_sec: float, max_sec: float) -> None:
        time.sleep(random.uniform(min_sec, max_sec))

    def _capture_cookies(self) -> None:
        try:
            self._last_cookies = self.sb.get_cookies() or []
            print(f"[*] 捕获 Cookie: {len(self._last_cookies)} 个")
        except Exception as e:
            print(f"[-] 捕获 Cookie 失败: {e}")
            self._last_cookies = []

    def get_cookies(self) -> List[Dict[str, Any]]:
        if self.sb:
            try:
                self._last_cookies = self.sb.get_cookies() or []
            except Exception:
                pass
        return list(self._last_cookies)

    def get_cookie_dict(self) -> Dict[str, str]:
        return {c["name"]: c["value"] for c in self.get_cookies()}

    def get_cf_clearance(self) -> Optional[str]:
        return self.get_cookie_dict().get("cf_clearance")

    def save_session(self, filename_prefix: Optional[str] = None) -> Dict[str, Path]:
        self._capture_cookies()
        save_dir = Path("output/cookies")
        save_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = filename_prefix or self.session_name
        path = save_dir / f"{prefix}_{ts}.json"
        ua = None
        try:
            ua = self.sb.execute_script("return navigator.userAgent")
        except Exception:
            pass
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "cookies": self.get_cookie_dict(),
                    "user_agent": ua,
                    "session": self.session_name,
                    "timestamp": ts,
                    "method": "seleniumbase_uc_class",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"[+] 会话已保存: {path}")
        return {"json": path}

    def close(self) -> None:
        if self._sb_cm is not None:
            try:
                self._sb_cm.__exit__(None, None, None)
            except Exception as e:
                print(f"[-] 关闭浏览器: {e}")
            finally:
                self._sb_cm = None
                self.sb = None
                self._is_initialized = False

    def __enter__(self) -> "CloudflareBypassSeleniumBase":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def bypass_and_get_cookies(
    url: str,
    proxy: Optional[str] = None,
    headless: bool = False,
    session_name: str = "quick_bypass",
    incognito: bool = False,
) -> Dict[str, Any]:
    """便捷函数：绕过 Cloudflare 并获取 Cookie"""
    config = BrowserConfig(proxy=proxy, headless=headless, incognito=incognito)
    result: Dict[str, Any] = {
        "success": False,
        "url": url,
        "cookies": {},
        "cf_clearance": None,
        "saved_files": {},
        "error": None,
        "method": "seleniumbase_uc_class",
    }
    try:
        with CloudflareBypassSeleniumBase(
            browser_config=config,
            session_name=session_name,
        ) as bypass:
            ok = bypass.open_with_bypass(url)
            result["cookies"] = bypass.get_cookie_dict()
            result["cf_clearance"] = bypass.get_cf_clearance()
            if result["cf_clearance"] or ok:
                result["success"] = bool(result["cf_clearance"])
                result["saved_files"] = bypass.save_session()
                if not result["cf_clearance"]:
                    result["error"] = "流程完成但未获取到 cf_clearance"
            else:
                result["error"] = "未能成功绕过 Cloudflare 验证"
    except Exception as e:
        result["error"] = str(e)
        print(f"[-] 绕过过程出错: {e}")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cloudflare Turnstile 绕过工具 (SeleniumBase 类封装)")
    parser.add_argument("url", help="目标URL")
    parser.add_argument("--proxy", "-p", help="代理地址")
    parser.add_argument("--headless", "-hl", action="store_true", help="无头模式（不推荐）")
    parser.add_argument("--incognito", action="store_true", help="无痕模式")
    parser.add_argument("--session", "-s", default="cli_session", help="会话名称")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Cloudflare Turnstile 绕过工具 (SeleniumBase UC Mode 类封装)")
    print("=" * 60 + "\n")

    result = bypass_and_get_cookies(
        url=args.url,
        proxy=args.proxy,
        headless=args.headless,
        session_name=args.session,
        incognito=args.incognito,
    )

    if result["success"]:
        print("\n[OK] 绕过成功")
        print(f"cf_clearance: {result['cf_clearance']}")
        print(f"Cookies: {len(result['cookies'])}")
        for file_type, path in (result.get("saved_files") or {}).items():
            print(f"  {file_type}: {path}")
    else:
        print(f"\n[FAIL] {result['error']}")
