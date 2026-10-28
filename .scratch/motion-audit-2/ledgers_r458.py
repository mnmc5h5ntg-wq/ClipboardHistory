#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R458 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


AUDIT_TITLE = u"## 第 456 轮（R457 · 2026-10-28"
AUDIT_SECTION = u"""## 第 457 轮（R458 · 2026-10-28 · U-1713…U-1717）：Markdown 五/六级标题不小于正文（旧 14/13/12、正文 14 → 新 15/14.5/14；2 张新帧、基线 266→268）+ R455 底色带判据的 1x 透明页修复（产品 2 文件，标题字阶位）

- **U-1713：⓪ push 与两跑失败步骤。** 开工一次快进 push **`ca40810..dd11f0f` success**（四笔：4380a32/d77acdd/ed26bc9/dd11f0f），HEAD=origin/main=`dd11f0f`、**ahead=0**；`40675730252 ↔ dd11f0f` 读时 **queued ⇒ NOT-RUN**。**`40664012233 ↔ d2a1e80` failure，失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）：唯一测试红＝`testInlineCodeBackgroundHasPadding` light/dark「找不到行内代码的短底色带」；**`40664181811 ↔ ca40810` failure，失败步骤 3 个**（同上 + `Motion coverage floor`）：同一行内码红 + `testMarkdownModeLabelChangeIsAVisibleProcess` 1 帧<2（已知采样红，不改门槛）。两跑另有 checkout 的 `You're on a case-insensitive filesystem` 报错行（步骤继续跑完，不计测试红）。已读未变：`40653092761 ↔ d48bb05` success（`DEEMPHASIS_CONTRAST 99/236/5.09、177/50/5.98`；`TASK_DIM 147.4/114.7 +32.7、136.6/166.4 −29.8`；`STRIKE_DIM 128.1/108.0 +20.1、152.2/174.6 −22.3、隙 3/3`；`HISTORY_ROW_SOURCE 139.0/74.0`、dark NOT-RUN；`WEIGHT_CENTER_TICK_NOT_RUN=flat 轨=1`；`LIST_HANG_STYLE 16/16/0`；Motion `judged=5/5 not-run=-`）；`40645430259 ↔ 5c925a9` success；`40645469967 ↔ c041c8d` failure 仅 receipt 1<2；`40640660665`/`40642482086`/`40636558557` success；`40634880705 ↔ 9743379` 滚动会话采样红。**runner 上 `HISTORY_ROW_MATCH light 来源查询 0/300、正文查询 528/0、无查询 0/0`（≥40 地板）、dark 行带 1 ⇒ 具名 NOT-RUN**。436：`40664181811` 的 Motion floor `judged=5/5 not-run=-`，但 markdown 模式标签采样红把该步拉红 ⇒ **`RUNNER_MARKDOWN_LABEL_SAMPLE_RED=1<2`**，不重猜 `must_judge`。
- **U-1714：① 腐烂与预检。** `HIDDEN_ARMS 表=323 可判=1029 rot=0`；`NEEDLE_PRECHECK tables=236 covered=218 arms=612 bad=0`、`ARM_TOTAL files=329 arms=1095`。
- **U-1715：② 五/六级标题字号下限。** 缺陷形状：`headingFontSize` 的阶梯是 20/17/15.5/14/13/12，而正文是 14 ⇒ 五/六级标题（13/12）比正文还小，作者写下的层级在屏幕上反过来；源码注释「六到一级的标题都至少不比正文小」与实现相反。修法：h4=15、h5=14.5、h6=14（六级与正文同号，靠 semibold 与 0.5–1pt 阶梯区分；每级仍严格递减、每级 ≥ 正文）。旧/新：`HEADING_LADDER 20/17/15.5/14/13/12（正文 14）→ 20/17/15.5/15/14.5/14`、light/dark 同形。新增夹具 `detail-headings`（h1..h6 + 正文 + 列表项保证走渲染），**2 张新帧**、0 旧帧变化/缺失；基线 **266→268**；已逐张看亮/暗：六级不再像小字注释。Store 未动（1108/52/66）。
- **U-1716：R455 判据的 1x 透明页修复与判据/刀。** runner 的 `detail-markdown-rendered` 帧 **76.4%/76.0% 透明**：R455 的尺直接读预乘 RGB、忽略 alpha，两侧都读不到带（这是 40664012233/40664181811 的红）。修法（阈值未动）：先按页面底合成 alpha，再取该行**第二众数**（相对页面底 4…48）为带色，允许字形打断 ≤3pt；旧/新读数 `INLINE_CODE_PAD light 97.5/92.5/5.0、dark 98.0/92.5/5.5`（地板仍 4.5/12）。新帧判据 `testHeadingLevelsAreNeverSmallerThanBody` 从产品渲染出的 NSTextView 读六级与正文的 `.font`；旧形态红在 h5/h6，新形态全绿；`M1254`（h5→13）/`M1255`（h6→12）⇒ **2/2 CAUGHT**、RESTORE_CLEAN=yes。R455 的 `M1246/M1247` 仍在预检名册且 needle 命中。
- **U-1717：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **268 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `268/0/0/0`；全量 **1262/56/0**（387s；本轮轻载无挂起、5 条本地滚动红未复现，`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 457，`python3 scripts/product_streak.py --streak-for 457`，last=4380a32）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40675730252 ↔ dd11f0f`（queued）；② R455 判据在 runner 的复验（随下一跑）；③ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；④ 五/六级同级后再往下的层级（h7+ 不存在，无对象）；⑤ 纯文本预览制表符（490）；⑥ 表格单元格制表符（491）；⑦ 8 空格制表位（492）；⑧ 命中高亮截断外/OCR（487）；⑨ 多文件第 2/3 个文件名（488）；⑩ 选中底高亮对比（489）；⑪ 弱化色选中态（485）；⑫ 行内码两侧标点（486）；⑬ HTML 的 `<del>`（484）；⑭ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑮ 设置内容列 1x 平涂；⑯ 设置脚注带 1x；⑰ 主窗口 content 帧 1x；⑱ 高夹具 1x；⑲ 13+ 菜单像素/标题；⑳ 真实拖拽；㉑ Dock 像素；㉒ 源图标最小窗文字 1x；㉓ 2x/extended；㉔ 固定块揭示偏移（455）；㉕ 跨年时间（456）；㉖ 主列表暗档文字盲区（457）；㉗ 真机/多屏（447）；㉘ 真菜单栏、12 实时腿；㉙ `table-lazy-rows`；㉚ HTML 六档字号（460）；㉛ 清除 × 命中区（461）；㉜ 分隔线令牌（462）；㉝ 展开态已加载内容无帧（463）；㉞ 其它自绘控件帮助文本（464）；㉟ HTML 引用块无导引线（465）；㊱ HTML 表格表头无同档（466）；㊲ 100+ 行行号（467）；㊳ HTML 代码块行号（468）；㊴ 行号选中/滚动两态（469）；㊵ 关于页 1x 盲（470）；㊶ M613 机器前提（472）；㊷ 真机 vibrant 暗档（473）；㊸ 长来源截断（474）；㊹ bundle ID 未搜（475）；㊺ 长首行标签省略无帧（476）；㊻ HTML 代码块无语言标签（477）；㊼ HTML `<hr>` 无通栏线（478）；㊽ HTML 表格体行无同一条线（479）；㊾ QuickPick 键盘提示 1x（480）；㊿ HTML 任务列表无弱化（481）；[51] HTML 列表缩进（482）；[52] 中心刻度端点标签（483）；[53] HTML 的 `<del>`（484）；[54] 弱化色选中态（485）；[55] 行内码两侧标点（486）；[56] 437–495 的未结项仍开。

"""

ITER_SECTION = u"""## Round 455 · R458（第 457 轮 · 2026-10-28）：Markdown 五/六级标题不小于正文（旧 14/13/12、正文 14 → 新 15/14.5/14；2 张新帧、基线 266→268）+ R455 判据 1x 透明页修复

`headingFontSize` 阶梯 20/17/15.5/14/13/12 低于正文 14，五/六级像小字注释，源码注释与实现相反。改为 h4=15、h5=14.5、h6=14（六级与正文同号、靠 semibold 区分；每级严格递减且 ≥ 正文）。旧/新：`HEADING_LADDER 20/17/15.5/14/13/12 → 20/17/15.5/15/14.5/14`、light/dark 同形；新增 `detail-headings` 2 帧、0 变化，基线 266→268/0/0/0；逐张看过。另修 R455 判据：runner 详情帧 76% 透明，旧尺读预乘 RGB 忽略 alpha ⇒ 改为按页面底合成 + 第二众数带色（阈值未动），旧/新 `INLINE_CODE_PAD light 97.5/92.5/5.0、dark 98.0/92.5/5.5`。判据 `testHeadingLevelsAreNeverSmallerThanBody` 旧红 h5/h6、新绿；M1254/M1255 2/2；precheck 236/218/612、rot 323/1029=0。⓪ push `ca40810..dd11f0f` success、ahead=0；R456 两跑 failure 的唯一新红就是上述行内码判据，另有 Motion 模式标签 1<2 采样红；新跑 40675730252 queued。全量 **1262/56/0**（387s，轻载）；build 0 告警；换装 ok/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-headings` 逐张看过：h4–h6 不再小于正文、六级仍靠字重立住。 |
| 判据有效性 | 15/15 | 从产品渲染出的 NSTextView 读六级与正文 `.font`；旧 13/12 红、新 15/14.5/14 绿。 |
| 假绿防御 | 14/15 | 旧形态先红留下旧读数；两把刀全 CAUGHT；扣 1：R455 判据的 runner 复验还要等下一跑。 |
| 产品面推进 | 15/15 | 六级标题第一次都不小于正文；标题阶梯仍严格递减；Store 不动。 |
| 台账一致性 | 15/15 | U-1713…U-1717、D-454、268 帧/1262、streak 1、两跑失败步骤都来自命令与测试。 |
| 交付诚实性 | 15/15 | R456 两跑的失败步骤、Motion 采样红、queued 新跑、R455 判据修复全部具名。 |
| 可复核性 | 15/15 | 20/17/15.5/15/14.5/14、旧 13/12、97.5/92.5/5.0、刀号与 precheck 236/218/612、rot 323/1029、基线 268 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_454 = u"""## D-454 Markdown 四到六级标题不小于正文（R458）

- 背景：`headingFontSize` 的 20/17/15.5/14/13/12 让五/六级（13/12）比正文 14 还小；源码注释却写着「六到一级的标题都至少不比正文小」。
- 决定：h4=15、h5=14.5、h6=14；六级与正文同号，靠 semibold 与 0.5–1pt 阶梯区分；每级严格递减且 ≥ 正文。
- 理由：标题是层级，不该在字号上反向；层级可以靠字重与微差表达，但不能靠「像小字注释」。
- 兼容性/迁移：新增 `detail-headings` 亮/暗 2 张帧；旧帧 0 变化；基线 266→268 同 commit 更新。
- 边界：h6 与正文同号，仅靠字重区分；阅读器若改了字重会退化（用判据钉住字号下界）。
- 回滚：恢复 `headingFontSize` 的 14/13/12；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### Markdown 五/六级标题不小于正文（旧 14/13/12、正文 14 → 新 15/14.5/14；2 张新帧、基线 266→268）（R458 / 第 457 轮 / Round 455 / U-1713…U-1717 · 产品 2 文件，标题字阶位）

"""

BACKLOG_SECTION = u"""**493. R455 行内码判据的 1x 透明页修复还需 runner 复验**（R458 观察）
    现象：本地已按 alpha 合成 + 第二众数带色修好（97.5/92.5/5.0、98.0/92.5/5.5），但 runner 上还没读到 `INLINE_CODE_PAD`。
    修法：下一跑读该行；若仍红，先查 runner 的页面底/带色是否落在第二众数阈值之外，别改 4.5 地板。

**494. 六级标题与正文同号，只靠字重区分**（R458 观察）
    现象：h6=14 与正文同号；若字体没有 semibold 或用户换了字体，六级会读成正文。
    修法：在标题层级里保留一个 ≥0.5pt 的下限差，或给 h6 一个小型大写/颜色区分；先补帧再定。

**495. 其它像素判据可能同样忽略 alpha**（R458 观察）
    现象：R455 的尺踩了「透明页 + 预乘 RGB」；其它详情帧判据（代码块底、行内墨带等）如果也在 runner 的透明页上取色，会重演。
    修法：把「按页面底合成 alpha」做成共享读法，逐条检查详情帧判据；先只记录，不批量改。
"""

STATE_SECTION = u"""## R458 状态（2026-10-28 · 本地 · 第 457 轮 / Round 455）：Markdown 五/六级标题不小于正文（旧 14/13/12、正文 14 → 新 15/14.5/14；2 张新帧、基线 266→268）+ R455 判据 1x 透明页修复（97.5/92.5/5.0、98.0/92.5/5.5）；全量 1262/56/0（产品 2 文件，标题字阶位）

最后更新：2026-10-28（本地 · R458 / 第 457 轮 / Round 455）：`headingFontSize` 的阶梯是 20/17/15.5/14/13/12，而正文是 14 ⇒ 五/六级标题（13/12）比正文还小，作者写下的层级在屏幕上反过来；源码注释「六到一级的标题都至少不比正文小」与实现相反。修法：h4=15、h5=14.5、h6=14（六级与正文同号，靠 semibold 与 0.5–1pt 阶梯区分；每级仍严格递减、每级 ≥ 正文）。旧/新：`HEADING_LADDER 20/17/15.5/14/13/12（正文 14）→ 20/17/15.5/15/14.5/14`、light/dark 同形。新增夹具 `detail-headings`（h1..h6 + 正文 + 列表项保证走渲染），**2 张新帧**、0 旧帧变化/缺失；基线 **266→268**；已逐张看亮/暗：六级不再像小字注释。**R455 判据修复**：runner 的 `detail-markdown-rendered` 帧 76.4%/76.0% 透明，旧尺读预乘 RGB、忽略 alpha，两侧都读不到带（`40664012233`/`40664181811` 的红）；改为按页面底合成 alpha、取该行第二众数为带色，允许字形打断 ≤3pt（阈值未动），旧/新 `INLINE_CODE_PAD light 97.5/92.5/5.0、dark 98.0/92.5/5.5`。新帧判据 `testHeadingLevelsAreNeverSmallerThanBody` 从产品渲染出的 NSTextView 读六级与正文的 `.font`；旧形态红在 h5/h6，新形态全绿；`M1254/M1255` **2/2 CAUGHT**、RESTORE_CLEAN=yes。预检 **236/218/612 bad=0**、ARM **329/1095**、HIDDEN **323/1029 rot=0**。⓪：一次快进 push **`ca40810..dd11f0f` success**（四笔）、HEAD=origin/main=`dd11f0f`、**ahead=0**；`40675730252 ↔ dd11f0f` queued ⇒ NOT-RUN；**`40664012233 ↔ d2a1e80` failure（2 步）与 `40664181811 ↔ ca40810` failure（3 步）**，两跑唯一新红＝上述行内码判据，另一红＝`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2（已知采样红）；`40653092761 ↔ d48bb05` success、`40645430259` success、`40645469967` 仅 receipt 1<2、`40640660665`/`40642482086`/`40636558557` success、`40634880705` 滚动会话采样红。全量 **1262/56/0**（387s，轻载无挂起）；捕获卷 **268 帧**；基线 **268/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 457，`python3 scripts/product_streak.py --streak-for 457`，last=4380a32）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push ca40810..dd11f0f success、ahead=0；读两跑 2/3 个失败步骤，定位行内码判据 + Motion 采样红；新跑 queued。
② 产品：五/六级标题不小于正文（14/13/12 → 15/14.5/14；2 张新帧、基线 268）。
③ 判据：旧红 h5/h6；M1254/M1255 2/2；R455 尺按 alpha 合成后本地绿；precheck 236/218/612；hidden rot 0。
④ 436：Motion floor judged=5/5；markdown 标签 1<2 采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 323 / 可判 1029 / rot 0。
⑥ 捕获 268 帧；基线 268/0/0/0；build 0 告警；换装 ok/383=383；全量 1262/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40675730252 ↔ dd11f0f`（queued）；② R455 判据的 runner 复验（下一跑）；③ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；④ 纯文本预览制表符（490）；⑤ 表格单元格制表符（491）；⑥ 8 空格制表位（492）；⑦ 命中高亮截断外/OCR（487）；⑧ 多文件第 2/3 个文件名（488）；⑨ 选中底高亮对比（489）；⑩ 弱化色选中态（485）；⑪ 行内码两侧标点（486）；⑫ HTML 的 `<del>`（484）；⑬ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑭ 设置内容列 1x 平涂；⑮ 设置脚注带 1x；⑯ 主窗口 content 帧 1x；⑰ 高夹具 1x；⑱ 13+ 菜单像素/标题；⑲ 真实拖拽；⑳ Dock 像素；㉑ 源图标最小窗文字 1x；㉒ 2x/extended；㉓ 固定块揭示偏移（455）；㉔ 跨年时间（456）；㉕ 主列表暗档文字盲区（457）；㉖ 真机/多屏（447）；㉗ 真菜单栏、12 实时腿；㉘ `table-lazy-rows`；㉙ HTML 六档字号（460）；㉚ 清除 × 命中区（461）；㉛ 分隔线令牌（462）；㉜ 展开态已加载内容无帧（463）；㉝ 其它自绘控件帮助文本（464）；㉞ HTML 引用块无导引线（465）；㉟ HTML 表格表头无同档（466）；㊱ 100+ 行行号（467）；㊲ HTML 代码块行号（468）；㊳ 行号选中/滚动两态（469）；㊴ 关于页 1x 盲（470）；㊵ M613 机器前提（472）；㊶ 真机 vibrant 暗档（473）；㊷ 长来源截断（474）；㊸ bundle ID 未搜（475）；㊹ 长首行标签省略无帧（476）；㊺ HTML 代码块无语言标签（477）；㊻ HTML `<hr>` 无通栏线（478）；㊼ HTML 表格体行无同一条线（479）；㊽ QuickPick 键盘提示 1x（480）；㊾ HTML 任务列表无弱化（481）；㊿ HTML 列表缩进（482）；[51] 中心刻度端点标签（483）；[52] HTML 的 `<del>`（484）；[53] 弱化色选中态（485）；[54] 行内码两侧标点（486）；[55] 437–495 的未结项仍开。

下一轮（R459）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R458 主笔+追记 head 跑、`40675730252 ↔ dd11f0f`（R457/R458 链）、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit），重点看 `HEADING_LADDER` 两档 20/17/15.5/15/14.5/14 与正文 14、`INLINE_CODE_PAD` 两档 97.5/92.5/5.0 与 98.0/92.5/5.5（runner 复验）、`HISTORY_ROW_MATCH` 300/528、`CODE_TAB_STOP` 32.14/32.14、64.29/64.29、间隔 32.14、`DEEMPHASIS_CONTRAST` 5.09/5.98、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE` 16/16/0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R458_REPORT_BULLET = u"""- **R458（标题字阶位 + R455 判据修复）**：`headingFontSize` 的阶梯 20/17/15.5/14/13/12 低于正文 14，五/六级像小字注释（源码注释与实现相反）。改为 h4=15、h5=14.5、h6=14（六级与正文同号、靠 semibold 区分；每级严格递减且 ≥ 正文）。旧/新：`HEADING_LADDER 20/17/15.5/14/13/12 → 20/17/15.5/15/14.5/14`、light/dark 同形；新增 `detail-headings` **2 张新帧**、0 旧帧变化，基线 **266→268/0/0/0**；逐张看过。另修 R455 判据：runner 详情帧 76% 透明、旧尺读预乘 RGB 忽略 alpha ⇒ 按页面底合成 + 第二众数带色（阈值未动），旧/新 `INLINE_CODE_PAD light 97.5/92.5/5.0、dark 98.0/92.5/5.5`。判据 `testHeadingLevelsAreNeverSmallerThanBody` 旧红 h5/h6、新绿；`M1254/M1255` **2/2**；precheck 236/218/612 bad=0、ARM 329/1095、HIDDEN 323/1029 rot=0。⓪：push **`ca40810..dd11f0f` success**、ahead=0；`40664012233`/`40664181811` 两跑 failure 的唯一新红就是上述行内码判据，另一红 Motion 标签 1<2（已知采样红）；新跑 `40675730252` queued ⇒ NOT-RUN。全量 **1262/56/0**（387s，轻载）；捕获 268 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 457 轮（R458" in audit: raise SystemExit("REFUSED AUDIT 已有 R458")
if u"## Round 455 · R458" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 455")
if u"## D-454" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-454")
if u"Markdown 五/六级标题不小于正文" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**493." in backlog: raise SystemExit("REFUSED BACKLOG 已有 493")
if state.count(u"## R457 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R457 状态"))
U_CELL_OLD = u"U-31 … U-1712（R457 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R457 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_454 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R457 状态", STATE_SECTION + u"## R457 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1717（R458 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R457 节 ②", u"AGENT_STATE.md` 的 R458 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R458_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R458_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
