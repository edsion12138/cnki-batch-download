# CNKI Batch Download Skill

批量下载知网文献并自动导入知网研学。适用于 Claude Code。

## 功能

- 知网关键词检索 / 高级检索（CSSCI、北大核心过滤）
- 按被引量排序，摘要预筛选
- 浏览器自动化勾选 → 批量导出研学
- 桌面自动化点击导入（Windows pyautogui/pywinauto / Mac AppleScript）
- 自动验证 PDF 入库
- **按模型视觉能力自动选策略**：多模态走截图视觉策略（看屏确认+精准定位），单模态走 DOM 策略

## 安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/edsion12138/cnki-batch-download.git ~/.claude/skills/cnki-batch-download
```

## 前置条件

1. 安装[知网研学](https://estudy.cnki.net/)桌面端并登录
2. **研学内设置优先 PDF**：设置 → 知网获取全文设置 → 其他设置 → 勾选"默认优先获取PDF格式文献"（否则下载全是 CAJ 文件，后续无法处理）
3. Chrome 浏览器已登录知网（机构登录）
4. 在研学中预先创建目标专题
5. 每日批量下载限额 100 篇（校园网 IP）

### 依赖

**Windows**：`python3`, `bb-browser`, `pywinauto`, `pyautogui`
**Mac**：`python3`, `bb-browser`, `pyautogui`（可选 `cliclick`）

> `pyautogui` 是视觉策略的刚需（桌面截图 + 精准点击）。只走 DOM 策略时可省。

## 两种运行策略

skill 每次运行先做一次运行时自测：截一张浏览器图，模型确认自己能否看清页面内容，据此自动进入对应策略（可用 `--strategy vision|dom` 强制覆盖）。

| | 策略A · 视觉模式（多模态模型） | 策略B · DOM模式（单模态模型） |
|---|---|---|
| 判断状态 | 截图看屏确认 | JS 返回布尔/DOM 文本 |
| 点击 | 浏览器用 ref；原生窗口用全屏截图定位+点击 | 浏览器/原生窗口用 ref + 硬编码坐标 |
| 导入按钮 | 截图定位，免跨机校准 | 硬编码 `(left+533, top+1241)` 需校准 |
| 适用 | 有视觉能力的模型（如 DeepSeek-V4-Flash-Vision-Exp） | 无视觉能力的模型 |

策略细节见 `references/vision.md` 与 `references/dom.md`。

## 使用

在 Claude Code 中说：
```
下载职业教育高质量发展的5篇CSSCI文献
按被引排序下载职业本科前3篇
```

## 平台

| 步骤 | Windows | Mac |
|------|---------|-----|
| 搜索→es6 | bb-browser | bb-browser |
| 导入研学 | 视觉: pyautogui 截图定位 / DOM: pywinauto | osascript / cliclick |
