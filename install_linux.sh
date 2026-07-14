#!/bin/bash
# ============================================================
# Cloudflare Bypass Tool - Linux 环境安装脚本
# 支持 Ubuntu/Debian 系统（Chrome deb 为 amd64）
# ============================================================

set -e

echo "=============================================="
echo "Cloudflare Bypass Tool - Linux 环境安装"
echo "=============================================="

# 检测是否为 root
if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 root 权限运行: sudo bash install_linux.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/5] 更新软件源..."
apt-get update -qq

echo "[2/5] 安装系统依赖..."
apt-get install -y -qq \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    wget \
    curl \
    unzip \
    python3-pip \
    python3-venv

echo "[3/5] 安装 Google Chrome (amd64)..."
if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null; then
    ARCH="$(uname -m)"
    if [ "$ARCH" != "x86_64" ]; then
        echo "[!] 官方 Chrome deb 仅提供 amd64。当前架构: $ARCH"
        echo "[!] 请自行安装 Chromium 或对应架构的 Chrome"
    else
        wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        apt-get install -y -qq /tmp/chrome.deb || apt-get install -f -y -qq
        rm -f /tmp/chrome.deb
        echo "[+] Chrome 安装完成"
    fi
else
    echo "[+] Chrome 已安装"
fi

echo "[4/5] 安装 Python 依赖 (requirements.txt)..."
python3 -m pip install -U pip -q
python3 -m pip install -r requirements.txt -q

echo "[5/5] 验证安装..."
echo -n "  Chrome: "
google-chrome --version 2>/dev/null || google-chrome-stable --version 2>/dev/null || echo "未找到"
echo -n "  Xvfb: "
which Xvfb &>/dev/null && echo "已安装" || echo "未安装"
echo -n "  Python: "
python3 --version
python3 -c "import seleniumbase; print('  seleniumbase:', seleniumbase.__version__)" 2>/dev/null || echo "  seleniumbase: 未导入"
python3 -c "import nodriver; print('  nodriver: OK')" 2>/dev/null || echo "  nodriver: 未导入"
python3 -c "import curl_cffi; print('  curl_cffi:', curl_cffi.__version__)" 2>/dev/null || echo "  curl_cffi: 未导入"

echo ""
echo "=============================================="
echo "安装完成"
echo "=============================================="
echo ""
echo "推荐用法:"
echo "  python3 bypass.py https://example.com"
echo "  python3 bypass_cdp.py https://example.com"
echo "  python3 bypass_nodriver.py https://example.com"
echo ""
