#!/usr/bin/env bash
# 状态等待：轮询执行一段 JS，直到结果包含期望子串（或超时）。替代固定 sleep，更快更稳。
# 用法: wait.sh '<js表达式>' '<期望子串>' [最大次数]
#   最大次数 默认 20，每次间隔 0.5s（即默认最多约 10s）。成功输出 OK，超时输出 TIMEOUT 并退出码1。
expr="$1"; want="$2"; max="${3:-20}"; session="${CNKI_BROWSER_SESSION:-cnki-batch}"
for i in $(seq 1 "$max"); do
  out=$(agent-browser --session "$session" eval "$expr" 2>/dev/null)
  if echo "$out" | grep -q "$want"; then
    echo "OK"
    exit 0
  fi
  sleep 0.5
done
echo "TIMEOUT: 未等到 [$want]"
exit 1
