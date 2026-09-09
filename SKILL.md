---
name: cnki-batch-download
description: 批量下载知网文献并导入知网研学。运行时会根据模型视觉能力自动选策略——多模态模型走截图视觉策略（截图确认状态、精准定位导入按钮），单模态模型走DOM策略。支持关键词检索、高级检索（CSSCI/北大核心）、按被引排序。使用bb-browser操控浏览器 + pywinauto/pyautogui 桌面自动化。
argument-hint: "[检索主题] [筛选条件] [下载数量] [--strategy vision|dom]"
---

# CNKI 批量下载 + 导入研学

## 核心流程

策略选择 → 搜索 → 清除+验证 → 排序 → 重新勾选 → 导出研学 → 下载es6 → 打开→导入→验证入库

## 运行策略选择（每次运行第一件事）

**先确定本会话用哪套策略**。这与当前模型的视觉能力强相关——有视觉能力的模型能通过截图看清屏幕，做事更精准；没有的就只能靠 DOM 判断。

判定方法（运行时自测）：

```bash
# 浏览器已打开且停留在知网搜索页后，截一张当前页
bb-browser screenshot /tmp/capability.png --tab <tab>
```

然后用 Read 工具打开 `/tmp/capability.png`，看自己**是否真的能看到页面内容**：

- **能看到**（按钮、文字、结果表格都清晰）→ 本会话有视觉能力 → 走 **策略A · 视觉模式** → `references/vision.md`
- **只能看到空白 / 尺寸占位 / 完全感知不到画面** → 本会话无视觉能力 → 走 **策略B · DOM模式** → `references/dom.md`

手动覆盖：如果自测有歧义想强制某套，在参数里传 `--strategy vision` 或 `--strategy dom`，跳过自测直接走对应策略。

> 不要凭"我猜这个模型会不会看图"来判断。**真的截一张，真的读进去**，以你实际看到的东西为准。这是整个流程最前面的一步，选错了后面全部白忙。

## 使用前必读

### 前置条件
1. **安装知网研学桌面端**：[官网下载](https://estudy.cnki.net/)，Windows/Mac 均支持。安装后登录机构账号
2. **设置优先下载 PDF**：研学 → 设置 → 知网获取全文设置 → 其他设置 → 勾选"默认优先获取PDF格式文献"。否则下载的可能全是不便后续处理的 CAJ 文件
3. **浏览器已登录知网**：在 Chrome 中提前登录一次（机构登录或 IP 登录）
4. **创建目标专题**：在研学中新建一个专题（如"文献下载"），论文导入时自动进入最近使用的专题

### 每日下载额度
- 知网批量下载每日上限 **100 篇**，与校园网 IP 绑定
- 校外访问（VPN/机构SSO）可能无法使用批量下载功能
- 超出限额或 IP 不符时，批量页会提示下载失败

### 平台兼容性

| 步骤 | Windows | Mac |
|------|---------|-----|
| 搜索→导出→es6落地 | bb-browser（跨平台） | bb-browser（跨平台） |
| 打开es6 | `os.startfile` | `open` 命令 |
| 点击"导入并获取全文" | 视觉: `pyautogui` 全屏截图+定位<br>DOM: `pywinauto`+ctypes | `cliclick` / `osascript` |
| 验证PDF入库 | Python（跨平台） | Python（跨平台） |

**视觉模式** 原生窗口用 `pyautogui`（全屏截图与点击共享坐标系，免 DPI 换算）；**DOM模式** Windows 用 `pywinauto`+ctypes 硬编码坐标。二者互为后备，详见各自 reference。

## 通用步骤（无论哪个策略都要走）

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

## 进入对应策略（第3步起的差异部分）

- **模型有视觉能力** → 读 `references/vision.md` 走 **策略A**（截图确认 + 精准定位导入按钮）
- **模型无视觉能力** → 读 `references/dom.md` 走 **策略B**（DOM 判断 + ref 点击 + 硬编码坐标兜底）

## 关键提示（两类策略共用的易错点）

1. **每次 snap 后逐个确认 ref**：ref 会变，不要复用上次的。找到目标文字后只点那个 ref
2. **JS eval 只用 function 表达式**：禁用箭头函数 + var + return 混用，避免 `SyntaxError`
3. **导出前必须关旧 batch tab**：`bb-browser tab | grep batch` 找出来逐个 close
4. **pywinauto 用预写脚本执行**：不要 inline 写，避免 auto mode 拦截
5. **中途遇到验证码**：暂停提示用户手动完成
6. **第6步执行期间用户手不要碰鼠标**：模拟点击会被物理鼠标操作打断
