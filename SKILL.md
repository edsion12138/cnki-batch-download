---
name: cnki-batch-download
description: 批量下载知网文献并导入知网研学。支持关键词检索、高级检索（CSSCI/北大核心）、按被引排序。使用bb-browser操控浏览器（勾选→导出研学→es6落地） + pywinauto自动导入。
argument-hint: "[检索主题] [筛选条件] [下载数量]"
---

# CNKI 批量下载 + 导入研学

## 核心流程

搜索 → 清除+验证 → 排序 → 重新勾选 → 导出研学 → 下载es6 → 打开→导入→等待→验证入库

## 使用前必读

### 前置条件
1. **安装知网研学桌面端**：[官网下载](https://estudy.cnki.net/)，Windows/Mac 均支持。安装后登录机构账号
2. **浏览器已登录知网**：在 Chrome 中提前登录一次（机构登录或 IP 登录）
3. **创建目标专题**：在研学中新建一个专题（如"文献下载"），论文导入时自动进入最近使用的专题

### 每日下载额度
- 知网批量下载每日上限 **100 篇**，与校园网 IP 绑定
- 校外访问（VPN/机构SSO）可能无法使用批量下载功能
- 超出限额或 IP 不符时，批量页会提示下载失败

### 平台兼容性

| 步骤 | Windows | Mac |
|------|---------|-----|
| 搜索→导出→es6落地 | bb-browser（跨平台） | bb-browser（跨平台） |
| 打开es6 | `os.startfile` | `open` 命令 |
| 点击"导入并获取全文" | pywinauto + ctypes | `osascript`（AppleScript）或 `cliclick` |
| 验证PDF入库 | Python（跨平台） | Python（跨平台） |

Mac 导入用的坐标和工具链不同，详见第6步的分支代码。

## 关键规则（每次执行前过一遍）

0. **首次使用自检**：确认 `bb-browser`、`pywinauto`、`python3` 可用；下载目录 `D:\下载\` 存在
1. 登录检查用 `!innerText.includes('机构登录')`，不是 `includes('退出')`
2. 清除不靠页面按钮，直接 JS uncheck + 验证 checked=0。新/旧版知网页面都适用
3. 排序后等待 3s，再重新 `querySelectorAll`（DOM 全作废）
4. "批量操作"下拉菜单必须用 `bb-browser click @ref`，JS click 无效
5. **每次导出前，先 `bb-browser tab | grep batch` 关闭旧批量页**，让 CNKI 自己创建新的
6. 下载/导入按钮都用 native click（`bb-browser click @ref`）
7. 导入后提示用户等待下载，用户说"继续"后再验证
8. 中途遇到验证码：暂停并提示用户手动完成

---

## 第0步：首次自检 + 打开浏览器

```bash
# 首次运行时确认工具链
which bb-browser && python3 -c "import pywinauto" && echo "OK" || echo "请先安装 bb-browser 和 pywinauto"
ls /d/下载/ > /dev/null || echo "下载目录不存在"
```

```bash
bb-browser open https://kns.cnki.net/kns8s/search
bb-browser eval "document.body.innerText.includes('机构登录')?'未登录':'已登录'" --tab <tab>
```
未登录时暂停，提示用户登录。

**会话恢复**：如果浏览器已有 tab，先 `bb-browser tab` 检查，关闭所有残留的 `manage/batch` tab。

---

## 第1步：检索

```bash
bb-browser eval "(async function(){var i=document.querySelector('input.search-input');i.value='KEYWORDS';i.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('input.search-btn').click();await new Promise(r=>setTimeout(r,4000));return document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1];})()" --tab <tab>
```

高级检索参见 cnki-advanced-search skill。

---

## 第2步：获取结果 + 用户确认

```bash
bb-browser eval "(function(){var rows=document.querySelectorAll('.result-table-list tbody tr');return Array.from(rows).slice(0,10).map((r,i)=>({n:i+1,title:r.querySelector('td.name a.fz14')?.innerText?.trim()?.substring(0,60),author:r.querySelector('td.author a')?.innerText?.trim()||'',journal:r.querySelector('td.source a')?.innerText?.trim()||'',date:r.querySelector('td.date')?.innerText?.trim()||'',cites:r.querySelector('td.quote')?.innerText?.trim()||''}));})()" --tab <tab>
```

展示结果，确认下载范围和排序方式。

> 如果结果列表为空或页面弹出验证码（`#tcaptcha_transform_dy` 可见），暂停并提示用户完成验证码。

---

## 第3步：清除（验证！）+ 排序 + 重新勾选

**清除不依赖页面上的"清除"按钮**（新/旧版知网页面DOM不同，XPath不可靠）。
直接通过 JS 强制取消所有 checked，再纯文本匹配兜底：

```bash
# ① 强制清除（纯 JS，不依赖页面DOM按钮）
bb-browser eval "(function(){var cbs=document.querySelectorAll('.result-table-list tbody input.cbItem:checked');for(var i=cbs.length-1;i>=0;i--){cbs[i].click();}var n=0;document.querySelectorAll('.result-table-list tbody input.cbItem').forEach(function(c){if(c.checked)n++;});if(n>0){var all=document.querySelectorAll('.result-table-list tbody input.cbItem');all.forEach(function(c){if(c.checked)c.click();});var m=0;all.forEach(function(c){if(c.checked)m++;});return'retry:'+m;}return 0;})()" --tab <tab>
# 必须返回 0，否则再执行一次

# ② 排序（可选）
bb-browser eval "document.evaluate(\"//*[text()='被引']\",document,null,9,null).singleNodeValue.click()" --tab <tab>
sleep 3  # DOM 全作废

# ③ 重新查询 + 勾选
bb-browser eval "(function(){var cbs=document.querySelectorAll('.result-table-list tbody input.cbItem');var indices=[0,1,2];indices.forEach(function(i){cbs[i].click();});return{ok:[cbs[0].checked,cbs[1].checked,cbs[2].checked],titles:[document.querySelectorAll('.result-table-list tbody tr')[0]?.querySelector('td.name a.fz14')?.innerText?.substring(0,30)]};})()" --tab <tab>
# 确认 ok=[true,true,true]
```

**关键：清除不靠"清除"按钮，直接走 JS uncheck。** 这在新版和旧版知网页面都有效。

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
bb-browser click @<ref> --tab <batch>
sleep 3

# 确认 es6 已落地
ls -lt /d/下载/ | head -1
```

---

## 第6步：打开 es6 + 研学导入

> **此步执行期间，用户手不要碰鼠标。** 模拟点击会被物理鼠标操作打断。

### ① 打开最新 es6（跨平台）

```bash
# Windows
python3 -c "import os; d=r'D:\\下载'; f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); os.startfile(os.path.join(d,f))"

# Mac
python3 -c "import os,subprocess; d=os.path.expanduser('~/Downloads'); f=max([x for x in os.listdir(d) if x.startswith('CNKI-')],key=lambda x:os.path.getmtime(os.path.join(d,x))); subprocess.run(['open',os.path.join(d,f)])"

sleep 4
```

### ② 点击"导入并获取全文"

**Windows**（pywinauto + ctypes）：

```bash
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

## 第7步：等待 + 验证

提示用户：
> 已触发导入，正在后台下载。约30秒后告诉我"继续"。

用户确认后验证：

```bash
python3 -c "
import os, time; from datetime import datetime
base = r'D:\\E-StudyData\\15760463670\\Literature'
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
