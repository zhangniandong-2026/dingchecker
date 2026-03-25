#!/bin/bash
# Chrome 远程调试模式启动脚本（项目自管专用实例）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CDP_PORT="${DINGCHECK_CDP_PORT:-9222}"
CDP_HOST="${DINGCHECK_CDP_HOST:-127.0.0.1}"
PROFILE_DIR="${DINGCHECK_CHROME_PROFILE_DIR:-$PROJECT_ROOT/data/chrome_profiles/cdp_${CDP_PORT}}"
OPEN_URL="${DINGCHECK_OPEN_URL:-about:blank}"
RESET_PROFILE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reset-profile)
            RESET_PROFILE=1
            shift
            ;;
        --port)
            CDP_PORT="$2"
            PROFILE_DIR="${DINGCHECK_CHROME_PROFILE_DIR:-$PROJECT_ROOT/data/chrome_profiles/cdp_${CDP_PORT}}"
            shift 2
            ;;
        --profile-dir)
            PROFILE_DIR="$2"
            shift 2
            ;;
        --url)
            OPEN_URL="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 1
            ;;
    esac
done

echo "启动 Chrome 远程调试模式..."
echo "端口: ${CDP_PORT}"
echo "配置目录: ${PROFILE_DIR}"
echo "打开页面: ${OPEN_URL}"
echo ""
echo "说明："
echo "1. 这是项目自管的专用 Chrome 实例"
echo "2. 首次使用请在该实例里手动登录钉钉"
echo "3. 登录态会持久保存在上述 profile 目录"
echo ""

if [[ ! -x "$CHROME_BIN" ]]; then
    echo "❌ 未找到 Chrome: $CHROME_BIN" >&2
    exit 1
fi

mkdir -p "$(dirname "$PROFILE_DIR")"

if [[ "$RESET_PROFILE" == "1" ]]; then
    ts="$(date +%Y%m%d-%H%M%S)"
    if [[ -d "$PROFILE_DIR" ]]; then
        backup_dir="${PROFILE_DIR}.bak.${ts}"
        mv "$PROFILE_DIR" "$backup_dir"
        echo "已备份旧 profile: $backup_dir"
    fi
fi

mkdir -p "$PROFILE_DIR"

existing_pid="$(pgrep -f "remote-debugging-port=${CDP_PORT}" | head -1 || true)"
if [[ -n "$existing_pid" ]]; then
    echo "发现已有远程调试实例 (PID: ${existing_pid})，直接复用"
else
    "$CHROME_BIN" \
      --remote-debugging-port="${CDP_PORT}" \
      --user-data-dir="${PROFILE_DIR}" \
      --no-first-run \
      --no-default-browser-check \
      --disable-background-networking \
      --disable-component-update \
      --new-window \
      "${OPEN_URL}" \
      >/tmp/dingchecker-chrome-${CDP_PORT}.log 2>&1 &

    chrome_pid=$!
    echo "Chrome 已启动 (PID: ${chrome_pid})"
fi

echo "等待远程调试端口就绪..."
for _ in {1..20}; do
    if python3 - <<PY >/dev/null 2>&1
import json
import urllib.request
url = "http://${CDP_HOST}:${CDP_PORT}/json/version"
with urllib.request.urlopen(url, timeout=2) as response:
    payload = json.load(response)
print(payload.get("Browser", "unknown"))
PY
    then
        echo "✓ Chrome 远程调试已就绪"
        echo "💡 后续请在这个 Chrome 实例中完成钉钉登录，登录态会保存在:"
        echo "   ${PROFILE_DIR}"
        exit 0
    fi
    sleep 1
done

echo "❌ Chrome 远程调试启动超时，请检查 /tmp/dingchecker-chrome-${CDP_PORT}.log" >&2
exit 1
