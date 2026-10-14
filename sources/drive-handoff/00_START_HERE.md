# 仓颉｜G 指法 Capo 2｜Codex Handoff（2026-10-14）

## 立即开始

请先阅读 `01_CODEX_MASTER_PROMPT.md`，再阅读 `02_ACCEPTANCE_GATE.md` 和 `03_CURRENT_STATE.md`。这是 **给 Codex 的执行交接包**，不是完成验收的曲谱。直接按 Master Prompt 执行，不要要求用户再重述需求。

## 目标（已由用户明确确认）

交付 **一个完整、自包含、离线可运行的 HTML 文件**。打开它即可查看《仓颉》全曲 G 调指法六线谱、试听、变速、循环和跟谱高亮；点击「打印 / 导出 PDF」即打开原生打印窗口，能正常另存为 A4 PDF 或打印纸质谱。

- 标准调弦 E A D G B e（六弦到一弦），**G 调指法、Capo 2**，实际演唱/发声调为 A。
- 原截图从 C 调指法开始，后段升到 D 调指法；目标相应为 **G 指法 → A 指法（都夹 2 品）**，实际音高 A → B。**不得把全曲所有段落强行写成 G 和弦体系。**
- 每个原谱 `×` 是「当前和弦图在这根弦上的按弦音」，不是闷音、打板或休止符。先按原谱和弦图还原每个音，再转调。和弦图上弦外的禁弹标记则不同，需要分清。
- 保留每个实际单音、双音、低音、旋律走向、时值、和弦变化、扫弦方向和尽量准确的歌词对位。不得用统一扫弦模板或随机分解和弦充当原谱。
- 导出 PDF 使用 `window.print()` + `@media print` / `@page`，隐藏控件，排版无截断、重叠和横向溢出。
- 完成全部再交一次。**不要在工作过程中给用户发多个 HTML 半成品，也不要把原截图拼版当作已经转调的正式六线谱。**

## 文件位置

- `SOURCE_SCREENSHOTS/IMG_7041.PNG`～`IMG_7056.PNG`：用户给的 16 张 **原谱连续截图**，其中相邻截图含重叠小节；这是优先级最高的事实来源。
- `SOURCE_SCREENSHOTS/IMG_7027_intro_reference.png`：更早的前奏截图。
- `SOURCE_SCREENSHOTS/user_original_归档.zip`：用户上传的原始压缩包（保留供完整性核对）。
- `CURRENT_WORKING_DRAFT/WORKING_DRAFT_not_verified.html`：ChatGPT 之前做的 67 小节单 HTML 工作稿。能显示和操作，但**严禁视为逐音正确**。
- `CURRENT_WORKING_DRAFT/src/make.py`：临时手工转录、配器与打包脚本（目前有绝对路径 `/mnt/data`，需要修正）。
- `CURRENT_WORKING_DRAFT/src/score.json`：临时结构化谱数据，数据不是逐音权威转写，多个小节是算法生成伴奏。
- `CURRENT_WORKING_DRAFT/src/app.js`、`app.css`：播放器与谱面渲染逻辑。
- `CURRENT_WORKING_DRAFT/src/verify.py`：Playwright 冒烟测试；需要加实质谱面与音高测试。
- `CURRENT_WORKING_DRAFT/qa/`：UI 截图、打印样张和 PDF 测试产物。只作为工作稿回归参考。

## 交付物及优先级

P0. 以截图为准完成全曲谱面与转调，确保能弹、能听、旋律/和声没有被改错。

P1. 单文件 HTML 完整播放器、网页查看与 PDF 打印；小屏和 A4 排版好读。

P2. 提供可复核的 source-to-score 映射、自动测试、手工抽查记录和已知的无法解决的截图问题。原图模糊处禁止猜测，要在交付报告里标注。

工程决策在不影响音乐准确性的前提下由 Codex 自主完成；不需要用户逐步审批。只在原谱不可辨、必然影响完整准确交付时才询问用户。

## 禁止误判

当前工作稿 **67 小节 / 7 段 / 18 行 / 363 个显示音符 / 306 个扫弦符号** 的数量只是代码冒烟测试统计，不是原谱经人工完全复核的准确数量。不得以它证明“完成逐音校对”。
