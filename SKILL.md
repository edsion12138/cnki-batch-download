---
name: cnki-batch-download
description: 批量检索知网文献、选择结果、导出知网研学 es6 文件，并通过知网研学获取全文。支持关键词或高级检索、CSSCI/北大核心筛选、按被引排序、视觉或 DOM 操作策略，以及手动或自动导入；不用于绕过登录、验证码、机构权限或下载额度。
---

# CNKI 批量下载并导入研学

核心流程：策略选择 → 检索 → 清除旧选择 → 排序 → 重新选择 → 导出研学 → 下载 es6 → 导入 → 验证入库。

## 前置条件

1. 安装并登录知网研学。
2. 在“设置 → 知网获取全文设置 → 其他设置”中勾选“默认优先获取PDF格式文献”，否则可能得到 CAJ 文件。
3. 浏览器已登录 CNKI，并具有机构文献下载权限。
4. 知网研学中已创建目标专题；导入会进入最近使用的专题。
5. 确认当前机构和 IP 的下载额度。出现限额提示时停止，不重复重试。

## 参数与策略

从请求中识别检索词、筛选条件、下载数量，以及两个可选参数：

- `--strategy vision|dom`：未指定时截图自测；能实际读取页面图像则用 `vision`，否则用 `dom`。
- `--import manual|auto`：默认 `manual`。只有用户明确选择自动导入且研学已放在主屏时，才运行 `scripts/click_import.py`。

确定策略后必须读取对应文件：

- 视觉模式：[references/vision.md](references/vision.md)
- DOM 模式：[references/dom.md](references/dom.md)

## 浏览器会话

使用 `agent-browser`。首次执行：

```powershell
agent-browser skills get core
agent-browser doctor --offline --quick
agent-browser --session cnki-batch --headed --auto-connect open "https://kns.cnki.net/kns8s/search"
agent-browser --session cnki-batch snapshot -i -u
```

自动连接不可用时使用持久化 `--profile`。不要读取、输出或保存用户凭据。函数模板必须包成 `(<函数>)()`，再编码为 Base64 传给 `agent-browser eval -b`。页面跳转、排序、弹窗或切换标签后，旧 `@eN` 引用立即失效，必须重新快照。

视觉能力自测：

```powershell
agent-browser --session cnki-batch screenshot "<绝对临时路径>"
```

用图像查看工具打开截图。能辨认按钮、文字与结果表格才进入视觉模式；看不到实际画面时进入 DOM 模式。

## 通用步骤

### 1. 检索与预览

普通检索使用 `input.search-input` 和 `input.search-btn`；高级检索调用 `cnki-advanced-search`。提取前 10 条，让用户确认下载范围和排序。验证码仅在 `#tcaptcha_transform_dy` 可见时成立；出现时保持浏览器打开，请用户人工完成。

### 2. 清除、排序与选择

1. 勾选前调用 `#selectCount` 附近的 `filenameClear()`，回首页，并确认 CNKI 的已选计数为 0。
2. 排序后等待结果刷新，重新查询 DOM，不能复用旧元素。
3. 选择时触发完整事件链：`checked=false → dispatchEvent(click) → cb.onclick()`。
4. 以 `#selectCount` 为准确认选中数量，不能只看 checkbox 的 `.checked`。
5. 批量页显示的“批量下载已选 N 篇”必须与用户确认数量一致。

### 3. 导出与下载 es6

1. 用 `agent-browser --session cnki-batch tab` 找到并关闭残留的 `manage/batch` 标签。
2. 回检索页重新快照，点击“批量操作”与“下载到研学”。普通点击不生效时，再用页面已有 jQuery 触发菜单项。
3. 切换到新的 `manage/batch` 标签，重新快照并核对 N。
4. 使用 `agent-browser --session cnki-batch download <按钮ref> <绝对es6路径>`；按钮选择器为 `#btn-download-all`。
5. 用 `scripts/wait_es6.sh` 或等价的本机文件轮询确认生成了新的 es6，不能靠固定睡眠猜测。

### 4. 导入研学

Windows 优先显式调用研学程序打开 es6：

```powershell
& "C:\ProgramData\CNKI\CNKI E-Study\知网研学.exe" -o "<es6绝对路径>"
```

- `manual`：提示用户点击“导入并获取全文”，完成后继续。
- `auto`：确认研学在主屏后运行 `python scripts/click_import.py`。首次使用、DPI 或窗口布局变化时重新校准 RELX/RELY。

多屏环境下使用 `scripts/grab_window.py` 获取研学窗口区域和物理坐标；跨屏点击使用脚本中的 ctypes 物理坐标方式，不假设主屏坐标范围。

### 5. 验证入库

在点击导入前记录 epoch 秒数，运行：

```powershell
python scripts/wait_papers.py <开始时间> <预期篇数> 120
```

从研学设置获取文献库根目录，不硬编码用户 ID。至少报告请求数量、es6 数量、最终入库数量、PDF/CAJ 数量、缺失题名，以及登录、验证码或额度状态。

## 边界与停止条件

- 不绕过 CNKI 登录、验证码、机构授权或下载限额。
- 不在用户未确认范围时批量下载。
- 不删除已有 es6、PDF、CAJ 或研学库文件。
- 页面显示 0 篇、数量不一致或连续两次操作无效时停止该步骤并诊断，不盲目重试。
