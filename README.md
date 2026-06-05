# CNKI Batch Download Skill

批量下载知网文献并自动导入知网研学。适用于 Claude Code。

## 功能

- 知网关键词检索 / 高级检索（CSSCI、北大核心过滤）
- 按被引量排序，摘要预筛选
- 浏览器自动化勾选 → 批量导出研学
- 桌面自动化点击导入（Windows pywinauto / Mac AppleScript）
- 自动验证 PDF 入库

## 安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/edsion12138/cnki-batch-download.git ~/.claude/skills/cnki-batch-download
```

## 前置条件

1. 安装[知网研学](https://estudy.cnki.net/)桌面端并登录
2. Chrome 浏览器已登录知网（机构登录）
3. 在研学中预先创建目标专题
4. 每日批量下载限额 100 篇（校园网 IP）

### 依赖

**Windows**：`python3`, `bb-browser`, `pywinauto`
**Mac**：`python3`, `bb-browser`, `pyautogui`（可选 `cliclick`）

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
| 导入研学 | pywinauto | osascript |
