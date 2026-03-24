#!/bin/bash
# 网络连接检查脚本

MAX_RETRIES=5
RETRY_INTERVAL=10

echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始网络连接检查..."

for i in $(seq 1 $MAX_RETRIES); do
    echo "  尝试 $i/$MAX_RETRIES..."

    # 检查能否访问钉钉
    if curl -s --connect-timeout 5 --max-time 10 https://alidocs.dingtalk.com > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 网络连接正常"
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        echo "  ❌ 网络不可达，等待 ${RETRY_INTERVAL} 秒后重试..."
        sleep $RETRY_INTERVAL
    fi
done

echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ 网络连接检查失败，已达最大重试次数"
exit 1
