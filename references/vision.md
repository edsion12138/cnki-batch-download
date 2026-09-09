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
# 等新 batch tab 出现（原 sleep 3，改轮询 tab 列表，最多 ~10s）
for i in $(seq 1 20); do
  bb-browser tab 2>/dev/null | grep -q "manage/batch" && break
  sleep 0.5
done
bb-browser tab | grep "manage/batch"
```

---

## 第5步：批量下载（视觉确认）

```bash
# ① 截 batch tab，看"批量下载已选 N篇"和按钮
bb-browser screenshot /tmp/step5_batch.png --tab <batch>   # → Read：确认 N 篇数量正确、按钮可见
bb-browser snap -i -c --tab <batch> | grep "批量下载"
# 记下下载前最新 es6 的 mtime，作为"新文件"的参照
REF=$(stat -c %Y /d/下载/*.es6 2>/dev/null | sort -n | tail -1)
bb-browser click @<ref> --tab <batch>
# 等新 es6 落地（替代固定 sleep 3，等文件出现即返回）
bash scripts/wait_es6.sh "$REF" || echo "没等到新es6，用 ls 兜底查看"
ls -lt /d/下载/ | head -1
```

---

## 第6步：打开 es6 + 研学导入（★核心：用截图替代硬编码坐标）

> **此步执行期间，用户手不要碰鼠标。** 模拟点击会被物理鼠标操作打断。
> 这一步**不再用**策略B的 `(window.left+533, window.top+1241)` 硬编码坐标，改为**全屏截图 → 定位按钮 → 点击 → 验证**，跨机/DPI 不再需要手动校准。

### ① 打开最新 es6

```bash
# Windows（用研学 exe 的 -o 打开，研学已在跑时才不会静默不弹窗）
python3 -c "import os,subprocess; d=r'D:\下载'; f=max([x for x in os.listdir(d) if x.endswith('.es6')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run([r'C:\ProgramData\CNKI\CNKI E-Study\知网研学.exe', '-o', os.path.join(d,f)])"

# Mac
python3 -c "import os,subprocess; d=os.path.expanduser('~/Downloads'); f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run(['open',os.path.join(d,f)])"

sleep 2   # 只等 2s，②的 grab_window 会检测对话框是否出现，没出现就再等重试
```

### ② 用脚本抓研学窗口区域（只读这块小图，速度快很多）

```bash
python3 scripts/grab_window.py D:/exue_full.png
# 输出 "<left> <top> <w> <h>"（研学窗口的物理屏幕坐标），记下 LW=left、LT=top
```
> 只抓**窗口区域**（约 1000×1100，而非整块 4480×1600 虚拟桌面）——少读几兆像素，Read 更快更省。用 Read 打开 `D:/exue_full.png` 看清内容。
> 多屏要点：窗口可能弹在第二块屏（`LW` 可能 > 主屏宽 2560）。脚本用 `all_screens` 抓取，能正确取到；别以为 `LW` 超宽就是错了。
> 若 Read 后看到的**不是"导入题录"对话框**（还是搜索页/主界面），说明 es6 还没被加工成弹窗：等 2 秒后重跑本步。

### ③ 定位"导入并获取全文"按钮

**Read `D:/exue_full.png`**（仅窗口区域），在图上找到"导入并获取全文"按钮，记它在**这张作物图里的坐标** `(cx, cy)`。
> 换算成物理屏幕坐标：**`bx = LW + cx`，`by = LT + cy`**（用②打印的 LW/LT 偏移）。
> 多屏注意：如果窗口在第二块屏，`bx` 会比主屏宽度大（如 ≈3500），这是正常的，直接用于点击。
> 点击仍用 ctypes `SetCursorPos`+`mouse_event` 送物理坐标——`pyautogui.click` 只覆盖主屏，点不到扩展屏。

### ④ 点击 + 截图验证（自校正闭环）

```bash
REF=$(date +%s)   # 记录导入开始时间，供第7步轮询"新落库PDF"用
python3 -c "import ctypes,time; u=ctypes.windll.user32; u.SetCursorPos(bx,by); time.sleep(0.3); u.mouse_event(2,0,0,0,0); u.mouse_event(4,0,0,0,0)"
python3 scripts/grab_window.py D:/exue_after.png
# → Read D:/exue_after.png：确认按钮被点中（对话框关闭/出现"正在获取全文"提示/无弹窗拦截）。
#   若没点中：从这张图看当前按钮实际在哪，修正 (bx,by) 再点，最多重试 2-3 次。
```

**Mac**：同样思路，用全屏截图定位，点击用 `cliclick c:<bx> <by>` 或 `osascript -e 'tell application "System Events" to click at {<bx>,<by>}'`。截图用 `pyautogui.screenshot().save(...)`（Mac 无 DPI 缩放，且单屏）。

---

## 第7步：轮询验证（等新 PDF 落库，快）

> 后台正在取全文。用 wait_papers.py 轮询，新 PDF 一到 N 篇就返回，**不用固定等 30s**（快则几秒返回，慢则有超时兜底）。

```bash
# ① 轮询等新 PDF 落库（ref 用第6步④记录的 REF；N=预期篇数；默认等120s）
python3 scripts/wait_papers.py "$REF" <N篇数> 120
# 输出 OK N篇 即全部到位；TIMEOUT 说明有下载失败/未收录，人工查看
```

```bash
# ② 截图确认研学界面已显示新入库文献（双保险，含扩展屏）
python3 scripts/grab_window.py D:/exue_library.png
# → Read D:/exue_library.png：列表里应能看到刚下载的 PDF / 无异常弹窗
```

---

## 坐标与截图要点

- **浏览器内**：一律用 `snap` 的 ref 点击，不手动算浏览器内坐标（浏览器页面有缩放/DPI，ref 才是准的）。
- **原生窗口**：`scripts/grab_window.py` 只抓窗口区域（小图快）→ 图上定位 → 按钮物理坐标 = 窗口偏移(LW/LT) + 图内坐标 → **ctypes `SetCursorPos`+`mouse_event`** 送物理坐标点击。别用 `pyautogui.click`（只覆盖主屏，点不到扩展屏）。
- **自校正闭环**：任何一次点击后都要截图确认；没点中就根据新图修正重试，而不是死守第一次的坐标。
- **多屏坐标**：`bx,by` 是整块虚拟桌面的物理坐标，可能大于主屏宽度（如主屏2560+扩展屏 → 目标在扩展屏 `bx≈3500`）。直接用，不要按主屏裁剪或取模。
- 截图路径统一放临时目录（Windows `D:\\`，Mac `~`），大小写/中文路径注意转义。

## 降级指引

如果视觉模式执行中遇到以下情况，**回退策略B**（`references/dom.md`）：
1. Read 截图后你实际看不到内容（空白/占位）→ 本会话其实无视觉能力。
2. 重复截图确认仍无法判断状态，且尝试 2 次无果 → 别硬耗，改用 DOM 判断。
3. `ImageGrab` / `ctypes` 缺失 → 降级策略B 的硬编码坐标（需先校准）。
