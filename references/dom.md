# 策略B：DOM 模式（单模态模型）

> 适用条件：运行会话的模型**没有视觉能力**，无法通过截图看屏幕。靠 DOM JS 判断状态、ref 定位点击、硬编码坐标兜底。
> 若走这里，说明策略选择的运行时自测判定本会话无视觉能力，或用户手动指定 `--strategy dom`。

---

## 第3步：清除（验证！）+ 排序 + 重新勾选

**清除必须先于勾选**，否则会混入残留已选（见 SKILL.md「勾选/导出铁律」）。用 `#selectCount` 旁的 `filenameClear()` 清成 0，再勾选；勾选用可靠事件链并核对 `#selectCount`：

```bash
# ① 真正清除已选（用 CNKI 的 filenameClear，不是筛选栏"清除"）
bb-browser eval "(function(){var a=document.querySelectorAll('a,#selectCount a');var clr=Array.from(document.querySelectorAll('a')).find(x=>/filenameClear/.test(x.getAttribute('href')||''));if(clr){clr.click();return 'clicked';}var el=document.querySelector('#selectCount');if(el){var p=el.closest('div');var a2=p&&p.querySelector('a');if(a2){a2.click();return 'clicked-parent';}}return 'none';})()" --tab <tab>
sleep 1
bb-browser eval "document.querySelector('#selectCount')?.innerText" --tab <tab>
# 必须显示 0，否则再点一次清除

# ② 排序（可选）
bb-browser eval "document.evaluate(\"//*[text()='被引']\",document,null,9,null).singleNodeValue.click()" --tab <tab>
sleep 3  # DOM 全作废

# ③ 重新勾选（可靠事件链：checked=false → dispatchEvent(click) → onclick()）
bb-browser eval "(async function(){var cbs=document.querySelectorAll('.result-table-list tbody input.cbItem');var indices=[0,1,2];for(var k=0;k<indices.length;k++){var cb=cbs[indices[k]];if(!cb.checked){cb.checked=false;cb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await new Promise(r=>setTimeout(r,120));if(typeof cb.onclick==='function')cb.onclick();}}return 'done';})()" --tab <tab>
sleep 1
bb-browser eval "document.querySelector('#selectCount')?.innerText" --tab <tab>
# 核对 CNKI 自己的已选计数 == 预期篇数（不是只看 checkbox.checked）
```

**关键：清空用 `#selectCount` 旁的 `filenameClear()`；勾选触发完整事件链；以 `#selectCount` 判据为准。**

---

## 第4步：导出到研学

```bash
# snap 找"批量操作" ref
bb-browser snap -i -c --tab <tab> | grep "批量操作"

# 原生点击打开下拉（等待 1.5s，CNKI 菜单有过渡动画）
bb-browser click @<ref> --tab <tab>
sleep 1.5

# jQuery 触发"下载到研学"（CNKI 自己创建 batch tab）
bb-browser eval "jQuery(document.evaluate(\"//*[text()='下载到研学']\",document,null,9,null).singleNodeValue).trigger('click')" --tab <tab>
sleep 3

# 确认新 batch tab
bb-browser tab | grep "manage/batch"
```

---

## 第5步：批量下载

```bash
bb-browser snap -i -c --tab <batch> | grep "批量下载"
# 确认 "批量下载已选 N篇 文献"
REF=$(stat -c %Y /d/下载/*.es6 2>/dev/null | sort -n | tail -1)
bb-browser click @<ref> --tab <batch>
# 等新 es6 落地（替代固定 sleep 3）
bash scripts/wait_es6.sh "$REF" || echo "没等到新es6，用 ls 兜底"
ls -lt /d/下载/ | head -1
```

---

## 第6步：打开 es6 + 研学导入

> **此步执行期间，用户手不要碰鼠标。** 模拟点击会被物理鼠标操作打断。

### ① 打开最新 es6（跨平台）

```bash
# Windows
python3 -c "import os,subprocess; d=r'D:\下载'; f=max([x for x in os.listdir(d) if x.endswith('.es6')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run([r'C:\ProgramData\CNKI\CNKI E-Study\知网研学.exe', '-o', os.path.join(d,f)])"
# ⚠️ 用研学 exe 的 -o 显式打开，别只靠 os.startfile（研学已在跑时不弹窗）。exe路径见下。

# Mac
python3 -c "import os,subprocess; d=os.path.expanduser('~/Downloads'); f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run(['open',os.path.join(d,f)])"

sleep 2   # 只等2s，随后点坐标导入；多屏用 ctypes 点击（见下）
```

### ② 点击"导入并获取全文"

**Windows**（pywinauto + ctypes）：

```bash
REF=$(date +%s)   # 记录导入开始时间，供第7步轮询
python3 -c "
import time, ctypes, subprocess, re
from pywinauto.mouse import click
out=subprocess.check_output(['powershell','-Command','Get-Process -Name *知网* | Where MainWindowHandle | Select -First 1 MainWindowHandle'],shell=True).decode()
hwnd=int(re.findall(r'\d+',out)[0])
ctypes.windll.user32.ShowWindow(hwnd,9)
time.sleep(0.3)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(0.5)
class RECT(ctypes.Structure):
    _fields_=[('left',ctypes.c_long),('top',ctypes.c_long),('right',ctypes.c_long),('bottom',ctypes.c_long)]
r=RECT(); ctypes.windll.user32.GetWindowRect(hwnd,ctypes.byref(r))
w=r.right-r.left; h=r.bottom-r.top
if w<100 or h<100:
    print(f'窗口异常({w}x{h})')
else:
    click(coords=(r.left+533,r.top+1241))
    print(f'已点击 ({r.left+533},{r.top+1241})')
"
```

**Mac**（osascript AppleScript）：

```bash
# 方法A：cliclick（需 brew install cliclick）
cliclick c:<x> <y>

# 方法B：osascript（系统自带，推荐）
osascript -e 'tell application "知网研学" to activate'
osascript -e 'tell application "System Events" to click at {<x>,<y>}'
```

> Mac 坐标需预先校准：用户悬停鼠标到按钮上，终端执行 `python3 -c "import pyautogui; print(pyautogui.position())"` 获取绝对坐标。

> Windows 相对坐标 (533, 1241) 经多次验证稳定。窗口最小化时会先恢复再点击。

---

## 第7步：轮询验证（等新 PDF 落库，快）

后台正在取全文。用 `scripts/wait_papers.py` 轮询，新 PDF 一到 N 篇就返回，不用固定等 30s。

```bash
# ref 用「点击导入前」记录的 REF（date +%s）；N=预期篇数；默认等120s
python3 scripts/wait_papers.py "$REF" <N篇数> 120
# 输出 OK N篇 即全部到位；TIMEOUT 说明有下载失败/未收录，人工查看
```

---

## DOM + 路径参考

| 元素 | 选择器/值 |
|------|---------|
| 搜索框 | `input.search-input` |
| 搜索按钮 | `input.search-btn` |
| 结果行/复选框/标题 | `.result-table-list tbody tr` / `input.cbItem` / `td.name a.fz14` |
| 登录检查 | `!document.body.innerText.includes('机构登录')` |
| 清除/被引排序 | XPath: `//*[text()='清除']` / `//*[text()='被引']` |
| 批量操作/下载到研学 | XPath: `//*[text()='批量操作']` / `//*[text()='下载到研学']` |
| 批量下载按钮 | `#btn-download-all` |
| es6目录 | `D:\下载\`（取浏览器默认下载路径） |
| 研学库根目录 | `D:\E-StudyData\<用户ID>\Literature\`（研学→设置→文献库位置） |
| 导入按钮相对坐标 | `(window.left+533, window.top+1241)` — 需在新电脑上重校准 |

## 故障速查

| 症状 | 原因 | 解决 |
|------|------|------|
| 排序后勾选全 false | DOM 过期 | 等3s后重新 querySelectorAll |
| 下载含旧文献 | 清除未生效 | 清除后验证 checked=0 |
| 导出后无 batch tab | 旧 tab 占用了窗口名 | 关闭所有 manage/batch tab，重新导出 |
| batch 页显示 0 篇 | jQuery trigger 未触发跳转 | 确认原生 click 打开了菜单；重试导出 |
| jQuery trigger 不生效 | 菜单未用原生点击打开 | snap → click @ref → jQuery trigger |
| 登录误判"未登录" | 检查字符串错误 | 用 `includes('机构登录')` |
| 导入坐标不准 | 窗口位置/DPI变了 | 在新电脑上重校准相对坐标 |
| 研学PID找不到 | 进程名可能是乱码 | `Get-Process -Name '*知网*'` + MainWindowHandle过滤 |
| 遇到验证码 | CNKI高频操作触发 | 提示用户手动完成验证码 |
| 验证脚本没输出 | 根目录mtime太旧 | 改用 `time.time() - 3600` 过滤1小时内修改的 |
| 勾选后批量页0篇 | jQuery trigger未跳转，疑似弹窗被拦截 | 先关闭旧batch tab，再重试导出 |
| 下拉菜单展开后找不到下载到研学 | 等待时间不够 | `sleep 1` 改为 `sleep 1.5` |

## 迁移到其他电脑的适配清单

本 skill 深度绑定了当前电脑环境。迁移到新电脑时，以下项需要逐一适配：

### 必须用户手动完成的
| 项目 | 说明 | 适配方法 |
|------|------|---------|
| **安装知网研学** | 桌面软件，Windows/Mac 均有 | [官网](https://estudy.cnki.net/) 下载，安装后登录机构账号 |
| **设置优先PDF** | 研学→设置→知网获取全文设置→其他设置→勾选"默认优先获取PDF格式文献" | 否则下载的全是 CAJ 格式，后续无法用 mdtrans/PDF skill 处理 |
| **研学中创建专题** | 导入时论文进入"最近使用的专题"，需事先存在 | 提醒用户先在研学中创建目标专题 |
| **浏览器登录知网** | CNKI 机构/个人登录态 | 首次使用需手动登录一次 |
| **注意下载额度** | 每日 100 篇，校园网 IP 绑定 | 校外/VPN 可能无法批量下载；超出限额当天不可再用 |

### 需要修改硬编码路径的
| 项目 | 当前值 | 如何获取 |
|------|--------|---------|
| es6下载目录 | `D:\下载\` | 取用户浏览器默认下载路径，或通过 `chrome://downloads/` 获取 |
| 研学库根目录 | `D:\E-StudyData\15760463670\Literature\` | 研学→设置→文献库位置，不同用户ID不同 |
| Python/工具链 | Windows: `python3`, `bb-browser`, `pywinauto`<br>Mac: `python3`, `bb-browser`, `pyautogui` + `cliclick`(可选) | 需一并安装 |
| es6下载目录 | Windows: `D:\下载\` / Mac: `~/Downloads/` | 取浏览器默认下载路径 |

### 可能需要重新校准的
| 项目 | 风险 | 校准方法 |
|------|------|---------|
| **导入按钮坐标** | **高** | **Windows**：用户悬停→ `pyautogui.position()` → 减窗口左上角。<br>**Mac**：`osascript` + `cliclick`，坐标用 `pyautogui.position()` 获取。 |
| 研学窗口类名 `CSimpleFrame` | 低 — 研学版本升级可能改类名 | `pywinauto` 扫描所有窗口，找 title 含"知网研学"的 |
| bb-browser 登录检测 | 中 — 不同机构登录后页面元素可能不同 | 用 `snap` 查看登录后页面特征文字 |

### 不需要改的
| 项目 | 原因 |
|------|------|
| CNKI DOM 选择器 | 知网页面结构全国统一 |
| JS 搜索/勾选/清除逻辑 | 纯 DOM 操作，与电脑环境无关 |
| jQuery 导出 trigger | CNKI 本身加载了 jQuery，不依赖本地环境 |
| 批量下载按钮 `#btn-download-all` | CNKI 固定 ID |
