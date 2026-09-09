#!/usr/bin/env python3
"""轮询研学文献库，直到【导入之后】新落库的 PDF 数量达到 N（或在超时内报告当前数）。
替代固定 sleep 20 盲等，下载快就早返回，慢也有超时兜底。
用法: wait_papers.py <导入开始epoch秒> <期望篇数N> [最大秒数=120]
   导入开始epoch用「点击导入并获取全文前」的 date +%s 记录；只统计 mtime>ref 的 PDF，避免把预存论文算进去。
"""
import os, glob, sys, time

ref = float(sys.argv[1])
want = int(sys.argv[2])
maxs = int(sys.argv[3]) if len(sys.argv) > 3 else 120
start = time.time()
roots = glob.glob(r'D:\E-StudyData\*\Literature\*')

while time.time() - start < maxs:
    cnt = 0
    for folder in roots:
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if f.lower().endswith('.pdf'):
                if os.path.getmtime(os.path.join(folder, f)) > ref:
                    cnt += 1
    if cnt >= want:
        print(f'OK {cnt}篇')
        sys.exit(0)
    time.sleep(1)
print(f'TIMEOUT 只到 {cnt}篇')
sys.exit(1)
