#!/usr/bin/env python3
"""抓取知网研学窗口的区域截图（只取窗口，不读整块虚拟桌面，省读取开销/速度更快）。
用法: python grab_window.py <输出png路径>
输出到 stdout: "<left> <top> <width> <height>"（物理屏幕坐标，供换算点击坐标用）
"""
import ctypes, sys
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
target = []
@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def cb(h, l):
    n = user32.GetWindowTextLengthW(h)
    if n:
        b = ctypes.create_unicode_buffer(n + 1); user32.GetWindowTextW(h, b, n + 1)
        if user32.IsWindowVisible(h) and '研学' in b.value:
            target.append((h, b.value))
    return True
user32.EnumWindows(cb, 0)
if not target:
    print('NO_WIN'); sys.exit(1)

hwnd = target[0][0]
user32.ShowWindow(hwnd, 9)
import time; time.sleep(0.4)
user32.SetForegroundWindow(hwnd)
time.sleep(0.6)

class RECT(ctypes.Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG),
                ('right', wintypes.LONG), ('bottom', wintypes.LONG)]
r = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
w = r.right - r.left; h = r.bottom - r.top

out = sys.argv[1] if len(sys.argv) > 1 else 'D:/exue_win.png'
img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True)
img.save(out)
print(f'{r.left} {r.top} {w} {h}')
