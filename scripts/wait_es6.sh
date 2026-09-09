#!/usr/bin/env bash
# 等待下载目录出现【新的】es6 文件（mtime 比参考值新）。替代固定 sleep 6。
# 用法: wait_es6.sh <参考mtime> [目录] [最大秒数]
#   参考mtime 用「点下载前」最新 es6 的 stat -c %Y 之值；ret=0 且打印新文件名即成功，超时退出码1。
ref="$1"; dir="${2:-D:/下载}"; max="${3:-30}"
start=$(date +%s)
while [ $(( $(date +%s) - start )) -le "$max" ]; do
  f=$(ls -t "$dir"/*.es6 2>/dev/null | head -1)
  if [ -n "$f" ] && [ "$(stat -c %Y "$f")" -gt "$ref" ]; then
    echo "$f"
    exit 0
  fi
  sleep 0.5
done
echo "TIMEOUT: 30s 内未等到新 es6"
exit 1
