# CNKI Batch Download Skill

批量检索知网文献、导出知网研学 es6，并通过研学获取全文。支持 Codex 和 Claude Code。

## 功能

- 关键词或高级检索，支持 CSSCI、北大核心筛选和被引排序
- 浏览器自动选择、导出与 es6 下载
- 视觉与 DOM 两种运行策略
- 手动导入，或在校准后自动操作知网研学
- 轮询验证 PDF 入库

## 安装

Codex：

```bash
git clone https://github.com/edsion12138/cnki-batch-download.git ~/.agents/skills/cnki-batch-download
```

Claude Code：

```bash
git clone https://github.com/edsion12138/cnki-batch-download.git ~/.claude/skills/cnki-batch-download
```

## 前置条件

1. 安装并登录[知网研学](https://estudy.cnki.net/)。
2. 在研学设置中启用“默认优先获取PDF格式文献”。
3. Chrome 已登录 CNKI，并具有机构下载权限。
4. 研学中已创建目标专题。
5. 安装 Python 3、`agent-browser`；视觉或自动导入模式按需安装 Pillow、pyautogui、pywinauto。

## 策略

| | 视觉模式 | DOM 模式 |
|---|---|---|
| 状态判断 | 截图确认 | JavaScript 与页面文本 |
| 浏览器点击 | 快照 ref | 快照 ref |
| 研学导入 | 手动或校准脚本 | 手动或校准脚本 |

浏览器统一使用 `agent-browser`；验证码由用户人工完成。策略细节见 `references/vision.md` 与 `references/dom.md`。

## 示例

```text
下载职业教育高质量发展的5篇CSSCI文献
按被引排序下载职业本科前3篇 --strategy vision --import manual
```
