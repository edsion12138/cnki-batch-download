#!/usr/bin/env python3
"""自动点击"导入并获取全文"。前提：知网研学放在【主屏】(不然弹窗位置不稳、坐标不可复用)。
用法: click_import.py [RELX] [RELY]
  找到研学主窗(导入弹窗所在) → 前置 → 在 (窗口left+RELX, 窗口top+RELY) 用 ctypes 物理坐标点击。
  RELX/RELY = "导入并获取全文"按钮在弹窗内的相对偏移，默认按主屏标准弹窗校准。
  若点不准 → 主屏弹出导入弹窗后，跑下面的"校准"再得到准确值。
"""
import ctypes, sys, time
from ctypes import wintypes
user32 = ctypes.windll.user32

def find_dialog():
    res = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        cl = ctypes.create_unicode_buffer(64); user32.GetClassNameW(h, cl, 64)
        n = user32.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1) if n else None
        if n: user32.GetWindowTextW(h, b, n + 1)
        if user32.IsWindowVisible(h) and 'CSimpleFrame' in cl.value:
            res.append((h, (b.value if b else '')))
        return True
    user32.EnumWindows(cb, 0)
    # 优先标题含"研学"/"导入题录"，否则取第一个非空窗口
    for h, t in res:
        if '研学' in t or '题录' in t:
            return h
    for h, t in res:
        if t:
            return h
    return res[0][0] if res else None

hwnd = find_dialog()
if not hwnd:
    print('NO_DIALOG: 找不到研学弹窗，确认已打开es6'); sys.exit(1)
user32.ShowWindow(hwnd, 9); time.sleep(0.3)
user32.SetForegroundWindow(hwnd); time.sleep(0.5)

class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
r = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
RELX = int(sys.argv[1]) if len(sys.argv) > 1 else 520   # 校准值：按钮在弹窗内的相对x
RELY = int(sys.argv[2]) if len(sys.argv) > 2 else 1250  # 校准值：按钮在弹窗内的相对y
bx, by = r.left + RELX, r.top + RELY
user32.SetCursorPos(bx, by); time.sleep(0.3)
user32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.1)
user32.mouse_event(4, 0, 0, 0, 0)
print(f'clicked {bx} {by} （窗口left={r.left} top={r.top} 尺寸={r.right-r.left}x{r.bottom-r.top}）')

# ── 校准（一次性，仅在研学弹窗处于主屏、显示导入按钮时跑）──
# 运行 `python3 scripts/grab_window.py D:/cal.png` → 读图 → 看"导入并获取全文"中心在
# 图内的 (cx, cy)。则 RELX=cx, RELY=cy。之后把默认值改成这个 RELX/RELY。
