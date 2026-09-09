# 策略A：视觉模式（多模态模型）

> 适用条件：运行会话的模型**有视觉能力**，能通过截图看清屏幕内容和状态。这是本 skill 的**首选策略**。
> 走这里的前提：策略选择的运行时自测里，你（模型）通过一张截图确认了自己**真的能看到页面内容**。

## 核心思路

把"从前的盲目试错"换成"**看清再动手，动完验证**"。两个关键原则：

1. **截图负责"看清与验证"，精确点击仍用可靠手段**：
   - 浏览器内 → 用 `snap` 的 ref 点击（精准、无 DPI 误差），截图用来**确认状态对不对**（勾选框清没清、下拉展开没、tab 跳没跳）。
   - 原生研学窗口 → 用**桌面全屏截图 + pyautogui 点击**（见第6步）。
2. **每次动作后必截图确认**，形成"截图→点击→截图"的**自校正闭环**。一次没点中就从截图看出偏了多少，再调，而不是改一刀硬编码坐标。

## 重要：怎么"看"截图

`bb-browser screenshot <路径>` 或 `pyautogui.screenshot().save(<路径>)` 只负责把画面存成 png。**你必须用 Read 工具打开这个 png，才真正看到内容**。看不到图就谈不上视觉模式——如果 Read 后仍是空白/尺寸占位，说明本会话其实无视觉能力，立即降级到策略B（`references/dom.md`）。

---

## 第3步：清除 + 排序 + 重新勾选（视觉确认）

```bash
# ① 强制清除（同策略B的 JS，纯JS不依赖页面按钮）
bb-browser eval "(function(){var cbs=document.querySelectorAll('.result-table-list tbody input.cbItem:checked');for(var i=cbs.length-1;i>=0;i--){cbs[i].click();}var n=0;document.querySelectorAll('.result-table-list tbody input.cbItem').forEach(function(c){if(c.checked)n++;});if(n>0){var all=document.querySelectorAll('.result-table-list tbody input.cbItem');all.forEach(function(c){if(c.checked)c.click();});var m=0;all.forEach(function(c){if(c.checked)m++;});return'retry:'+m;}return 0;})()" --tab <tab>
# ⚠️ 必须返回 0，否则再执行一次

# ② 截图确认清除成功
bb-browser screenshot /tmp/step3_cleared.png --tab <tab>   # Mac 换 /tmp 为 ~/Downloads
# → Read /tmp/step3_cleared.png：目视结果表左列复选框应全部未勾选。若还有勾选 → 重跑①

# ③ 排序（可选）：先点"被引"
bb-browser eval "document.evaluate(\"//*[text()='被引']\",document,null,9,null).singleNodeValue.click()" --tab <tab>
sleep 3  # DOM 全作废，重新查询

# ④ 重新勾选想下载的 N 篇
bb-browser eval "(function(){var cbs=document.querySelectorAll('.result-table-list tbody input.cbItem');var indices=[0,1,2];indices.forEach(function(i){cbs[i].click();});return{ok:[cbs[0].checked,cbs[1].checked,cbs[2].checked]};})()" --tab <tab>

# ⑤ 截图确认勾选
bb-browser screenshot /tmp/step3_checked.png --tab <tab>
# → Read：前几行应呈勾选态（勾选框打勾或行高亮）。ok=[true,true,true] 且截图一致 → 进入下一步
```

---

## 第4步：导出到研学（视觉确认）

```bash
# ① 看"批量操作"按钮在哪
bb-browser screenshot /tmp/step4_menu.png --tab <tab>   # → Read：确认结果表上方有"批量操作"

# ② snap 拿"批量操作"的 ref，原生点击展开下拉（等1.5s，CNKI菜单有过渡动画）
bb-browser snap -i -c --tab <tab> | grep "批量操作"
bb-browser click @<ref> --tab <tab>
sleep 1.5

# ③ 截图确认下拉已展开、能看到"下载到研学"
bb-browser screenshot /tmp/step4_dropdown.png --tab <tab>   # → Read：确认菜单展开且含"下载到研学"。没展开→重点或换ref
bb-browser eval "jQuery(document.evaluate(\"//*[text()='下载到研学']\",document,null,9,null).singleNodeValue).trigger('click')" --tab <tab>
sleep 3

# ④ 确认新 batch tab（做最可靠的结构性确认，截图作为补充）
bb-browser tab | grep "manage/batch"
```

---

## 第5步：批量下载（视觉确认）

```bash
# ① 截 batch tab，看"批量下载已选 N篇"和按钮
bb-browser screenshot /tmp/step5_batch.png --tab <batch>   # → Read：确认 N 篇数量正确、按钮可见
bb-browser snap -i -c --tab <batch> | grep "批量下载"
bb-browser click @<ref> --tab <batch>
sleep 3

# ② 确认 es6 已落地 + 截图看下载提示
ls -lt /d/下载/ | head -1
bb-browser screenshot /tmp/step5_done.png --tab <batch>    # → Read：确认下载中/完成提示
```

---

## 第6步：打开 es6 + 研学导入（★核心：用截图替代硬编码坐标）

> **此步执行期间，用户手不要碰鼠标。** 模拟点击会被物理鼠标操作打断。
> 这一步**不再用**策略B的 `(window.left+533, window.top+1241)` 硬编码坐标，改为**全屏截图 → 定位按钮 → 点击 → 验证**，跨机/DPI 不再需要手动校准。

### ① 打开最新 es6

```bash
# Windows
python3 -c "import os; d=r'D:\下载'; f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); os.startfile(os.path.join(d,f))"

# Mac
python3 -c "import os,subprocess; d=os.path.expanduser('~/Downloads'); f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run(['open',os.path.join(d,f)])"

sleep 4
```

### ② 把研学窗口带到前台 + 全屏截图（Windows）

```bash
python3 -c "
import time, ctypes, subprocess, re, pyautogui
out=subprocess.check_output(['powershell','-Command','Get-Process -Name *知网* | Where MainWindowHandle | Select -First 1 MainWindowHandle'],shell=True).decode()
hwnd=int(re.findall(r'\d+',out)[0])
ctypes.windll.user32.ShowWindow(hwnd,9)   # 最小化则恢复
time.sleep(0.3)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(0.5)
img=pyautogui.screenshot()
img.save('D:/exue_full.png')
print('size=', img.size)
"
```

> 关键：用 `pyautogui` 的**全屏截图**和 `pyautogui.click` ——两者共享同一坐标系，**天然免疫 DPI 缩放错位**。截图后 Read 得到的像素坐标，可直接作为点击坐标，无需做任何换算。

### ③ 定位"导入并获取全文"按钮

**Read `D:/exue_full.png`**，在图上找到"导入并获取全文"按钮，记下它的屏幕坐标 `(bx, by)`（把图当画布，直接用像素坐标）。

### ④ 点击 + 截图验证（自校正闭环）

```bash
python3 -c "import pyautogui,time; pyautogui.click(bx, by); time.sleep(2)"
python3 -c "import pyautogui; pyautogui.screenshot().save('D:/exue_after.png'); print('saved')"
# → Read D:/exue_after.png：确认按钮被点中（状态变化/出现"正在获取全文"提示/无弹窗拦截）。
#   若没点中：从第二张图看当前按钮实际在哪，修正 (bx,by) 再点，最多重试 2-3 次。
```

**Mac**：同样思路，用全屏截图定位，点击用 `cliclick c:<bx> <by>` 或 `osascript -e 'tell application "System Events" to click at {<bx>,<by>}'`。截图用 `pyautogui.screenshot().save(...)`（Mac 无 DPI 缩放问题）。

---

## 第7步：等待 + 验证（截图 + 文件夹双保险）

提示用户：
> 已触发导入，正在后台下载。约30秒后告诉我"继续"。

用户确认后：

```bash
# ① 文件夹硬核校验（跨平台，最可靠）
python3 -c "
import os, time; from datetime import datetime
base = r'D:\E-StudyData\15760463670\Literature'
cutoff = time.time() - 3600  # 1小时内修改过的
for d in os.listdir(base):
    full = os.path.join(base, d)
    if os.path.isdir(full):
        mtime = os.path.getmtime(full)
        if mtime > cutoff:
            pdfs = [f for f in os.listdir(full) if f.endswith('.pdf')]
            fmtime = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
            print(f'{fmtime} | {d[:60]}: {len(pdfs)}篇')
            for p in pdfs[-5:]:
                print(f'  - {p[:70]}')
"
```

```bash
# ② 截图确认研学界面已显示新入库文献（双保险）
python3 -c "import pyautogui,ctypes,subprocess,re,time
out=subprocess.check_output(['powershell','-Command','Get-Process -Name *知网* | Where MainWindowHandle | Select -First 1 MainWindowHandle'],shell=True).decode()
hwnd=int(re.findall(r'\d+',out)[0]); ctypes.windll.user32.SetForegroundWindow(hwnd); time.sleep(0.5)
pyautogui.screenshot().save('D:/exue_library.png'); print('saved')"
# → Read D:/exue_library.png：列表里应能看到刚下载的 PDF / 无异常弹窗
```

---

## 坐标与截图要点

- **浏览器内**：一律用 `snap` 的 ref 点击，不手动算浏览器内坐标（浏览器页面有缩放/DPI，ref 才是准的）。
- **原生窗口**：用 `pyautogui` 全屏截图 + `pyautogui.click`，共享坐标系，免换算。
- **自校正闭环**：任何一次点击后都要截图确认；没点中就根据新图修正重试，而不是死守第一次的坐标。
- 截图路径统一放临时目录（Windows `D:\\`，Mac `~`），大小写/中文路径注意转义。

## 降级指引

如果视觉模式执行中遇到以下情况，**回退策略B**（`references/dom.md`）：
1. Read 截图后你实际看不到内容（空白/占位）→ 本会话其实无视觉能力。
2. 重复截图确认仍无法判断状态，且尝试 2 次无果 → 别硬耗，改用 DOM 判断。
3. `pyautogui` 缺失 → 降级策略B 的硬编码坐标（需先校准）。
