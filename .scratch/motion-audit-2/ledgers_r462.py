#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R462 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 460 轮（R461 · 2026-10-28"
AUDIT_SECTION = u"""## 第 461 轮（R462 · 2026-10-28 · U-1733…U-1737）：不支持文件 fallback 的长文件名留在窗格内（旧左沿 7.0pt、2 带 → 新 83.0pt、2 带；2 张新帧、基线 272→274）+ dark 假带上限 150→120（产品 1 文件，fallback 文件名位）

- **U-1733：⓪ push 与两跑读数。** 开工 no-op push success、ahead=0、HEAD=`b942e6b`。**`40693473537 ↔ b942e6b` failure，失败步骤 3 个**（Swift tests、Capture gate、Motion coverage floor）：`INLINE_CODE_PAD light 85.0/80.0/5.0`（**R461 修复在 runner 签收**）、`dark 150.0/147.0/3.0`（**150 恰是选择器上限 ⇒ 假带仍在**，R461 的覆盖率门槛没把它排除）；Motion `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1<2（已知采样红）。**`40693357120 ↔ 0b034c4` failure** 同族。`FILE_TEXT_PREVIEW light/dark 637.0/652.0`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 均 runner 签收；`40688652304`/`40688610679` failures（行内码旧读数）、`40681994982`/`40682072865` failures、`40675730252` failure 2 步、`40653092761` success 等沿用。436 无新红。
- **U-1734：① 腐烂与预检。** `HIDDEN_ARMS 表=326 可判=1035 rot=0`；`NEEDLE_PRECHECK tables=239 covered=221 arms=618 bad=0`。
- **U-1735：② 不支持文件 fallback 的文件名。** 缺陷：`DetailPreviewViews.fallbackView` 的 `Text(lastPathComponent)` 没有行数/截断/内边距 —— 一条 8×「很长文件名-」的 `.xyz` 在 600×440 里**单行从窗格左缘 7.0pt 跑到右缘、压在浮层药丸下**。修法：`lineLimit(2)` + 居中 + 中间省略 + 左右 80pt 内边距。旧/新：`FALLBACK_NAME light 左沿=7.0pt 行带=2 → 83.0pt/2`、dark 同形；夹具用**真实 `.xyz` 文件 + 缩略图**走产品 `DetailFileView` 的 `.fallback` 载入。**2 张新帧**（600×440 亮/暗）、0 旧帧变化/缺失；基线 **272→274**；已看亮/暗：名字两行居中、左右留白、避开水印药丸。
- **U-1736：判据、刀与 dark 假带。** 新帧判据 `testFallbackFileNameStaysInsideThePane` 在缩略图左侧窄列（x 0..200pt，缩略图从 236pt、浮层从 540pt 起）读文件名最左墨：旧 7.0 <60 红、新 83.0 绿；`M1260`（撤四修饰）/`M1261`（只撤内边距）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。另修 R461 留下的 dark 假带：真带 ~85..99pt，而假带正卡在 150 上限 ⇒ 选择器上限 **150→120**（紧凑对象界，拒绝整段假 run；**地板 4.5 不动**）；本地 light 98.5/92.5/6.0、dark 99.0/92.5/6.5（≥4.5）；runner dark 复验待下一跑。
- **U-1737：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **274 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `274/0/0/0`；全量 **1265/56/0**（427s，轻载）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 387=387`（前后一致）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 461，`python3 scripts/product_streak.py --streak-for 461`，last=885c8ae）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40693473537 ↔ b942e6b` / `40693357120 ↔ 0b034c4`（completed=failure，见 U-1733）；② R462 自身跑（未创建）；③ dark 假带 120 上限的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（本跑 receipt 1<2）；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–507 的未结项仍开。

"""

ITER_SECTION = u"""## Round 459 · R462（第 461 轮 · 2026-10-28）：不支持文件 fallback 的长文件名留在窗格内（旧左沿 7.0pt、2 带 → 新 83.0pt、2 带；2 张新帧、基线 272→274）+ dark 假带上限 150→120

`DetailPreviewViews.fallbackView` 的文件名没有行数/截断/内边距：一条 8×「很长文件名-」的 `.xyz` 在 600×440 里单行从 7.0pt 跑到右缘、压在浮层药丸下。修法：`lineLimit(2)` + 居中 + 中间省略 + 左右 80pt；夹具用真实 `.xyz` + 缩略图走产品 `.fallback`。旧/新：`FALLBACK_NAME 7.0/2 → 83.0/2`、亮暗同形；2 张新帧、0 变化，基线 272→274/0/0/0；逐张看过两行居中、避开药丸。判据在缩略图左侧窄列读最左墨；旧红新绿；M1260/M1261 2/2。另修 R461 的 dark 假带：真带 85..99、假带卡 150 ⇒ 上限 150→120（地板 4.5 不动），本地 6.0/6.5，runner 待验。全量 1265/56/0（427s）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；R461 两跑 failure：INLINE light 5.0 签收、dark 假带仍红；FILE_TEXT_PREVIEW 637/652、HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收；Motion receipt 1<2 采样红。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-file-fallback-longname` 逐张看过：两行居中、左右留白、避开浮层。 |
| 判据有效性 | 15/15 | 在缩略图左侧窄列读最左墨；旧 7.0 红、新 83.0 绿；两把刀 2/2。 |
| 假绿防御 | 14/15 | dark 假带的上限修复只有 runner 能验；扣 1。 |
| 产品面推进 | 15/15 | 新类别（fallback 文件名）；真实 `.xyz` 文件走产品载入；Store 不动。 |
| 台账一致性 | 15/15 | U-1733…U-1737、D-458、274 帧/1265、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R461 两跑 failure、light 5.0 签收/dark 假带仍红、Motion 采样红都照记。 |
| 可复核性 | 15/15 | 7.0/83.0、2 带、150→120、98.5/92.5/6.0 与 99.0/92.5/6.5、刀号/precheck 239/221/618、rot 326/1035、基线 274 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_458 = u"""## D-458 fallback 文件名限两行并在 80pt 内边距内居中（R462）

- 背景：`DetailPreviewViews.fallbackView` 的文件名无行数/截断/内边距；600×440 里长名从 7.0pt 跑到右缘、压浮层。
- 决定：`lineLimit(2)` + `multilineTextAlignment(.center)` + `truncationMode(.middle)` + `padding(.horizontal, 80)`。
- 理由：文件名的可读性靠两行 + 中间省略；两侧内边距同时避开右下角浮层，不靠"运气没撞上"。
- 兼容性/迁移：新增真实 `.xyz` 夹具 `detail-file-fallback-longname`（600×440）亮/暗 2 张帧；旧帧 0 变化；基线 272→274 同 commit 更新。
- 边界：极长无分隔符的文件名由中间省略处理；缩略图缺失时走 `doc.fill`，本轮未单独拍。
- 回滚：删四个修饰；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 不支持文件 fallback 的长文件名留在窗格内（旧左沿 7.0pt、2 带 → 新 83.0pt、2 带；2 张新帧、基线 272→274）（R462 / 第 461 轮 / Round 459 / U-1733…U-1737 · 产品 1 文件，fallback 文件名位）

"""

BACKLOG_SECTION = u"""**505. dark 假带的 120pt 上限要 runner 复验**（R462 观察）
    现象：真带 85..99pt、假带卡在 150；上限 150→120 后本地 light/dark 6.0/6.5，但 runner 还没跑过。
    修法：下一跑读 `INLINE_CODE_PAD`；若 dark 仍 150/147，先在帧里打印候选 run 的 span/coverage，再查对象身份；地板 4.5 不动。

**506. fallback 无缩略图的 `doc.fill` 分支没有帧**（R462 观察）
    现象：本轮夹具带缩略图；`else` 的 `doc.fill` 只靠系统符号，未单独拍长文件名。
    修法：补一张无缩略图的 fallback 帧，确认同一套两行/内边距规则。

**507. 极长无分隔符文件名只靠中间省略**（R462 观察）
    现象：`.xyz` 名以连字符分隔；无分隔符的 120+ 字符文件名会截成两行中的省略。
    修法：若要更好，按扩展名/词缀分段；先记录边界。
"""

STATE_SECTION = u"""## R462 状态（2026-10-28 · 本地 · 第 461 轮 / Round 459）：不支持文件 fallback 的长文件名留在窗格内（旧左沿 7.0pt、2 带 → 新 83.0pt、2 带；2 张新帧、基线 272→274）+ dark 假带上限 150→120；全量 1265/56/0（产品 1 文件，fallback 文件名位）

最后更新：2026-10-28（本地 · R462 / 第 461 轮 / Round 459）：`DetailPreviewViews.fallbackView` 的 `Text(lastPathComponent)` 没有行数/截断/内边距 —— 一条 8×「很长文件名-」的 `.xyz` 在 600×440 里**单行从窗格左缘 7.0pt 跑到右缘、压在浮层药丸下**。修法：`lineLimit(2)` + 居中 + 中间省略 + 左右 80pt 内边距。旧/新：`FALLBACK_NAME light 左沿=7.0pt 行带=2 → 83.0pt/2`、dark 同形；夹具用**真实 `.xyz` 文件 + 缩略图**走产品 `DetailFileView` 的 `.fallback` 载入。**2 张新帧**（600×440 亮/暗）、0 旧帧变化/缺失；基线 **272→274**；已看亮/暗：名字两行居中、左右留白、避开浮层。新帧判据 `testFallbackFileNameStaysInsideThePane` 在缩略图左侧窄列（x 0..200pt）读文件名最左墨：旧 7.0 <60 红、新 83.0 绿；`M1260/M1261` **2/2 CAUGHT**、RESTORE_CLEAN。**dark 假带修复**：R461 的 3.0 是 150pt 上限饱和；真带 85..99 ⇒ 选择器上限 **150→120**（紧凑对象界；地板 4.5 不动），本地 light 98.5/92.5/6.0、dark 99.0/92.5/6.5。预检 **239/221/618 bad=0**、ARM 332/1101、HIDDEN **326/1035 rot=0**。⓪：no-op push success、ahead=0、HEAD=`b942e6b`；`40693473537 ↔ b942e6b` failure 3 步（Swift tests、Capture gate、Motion floor）：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、dark 150/147/3.0 假带仍红；Motion receipt 1<2 采样红；`40693357120 ↔ 0b034c4` failure；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 签收。全量 **1265/56/0**（427s，轻载）；捕获卷 **274 帧**；基线 **274/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 461，`python3 scripts/product_streak.py --streak-for 461`，last=885c8ae）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R461 两跑 failure（light 5.0 签收、dark 假带仍红、Motion 采样红）；其余面签收。
② 产品：fallback 长文件名两行居中、80pt 内边距（7.0→83.0；2 张新帧、基线 274）。
③ 判据：M1260/M1261 2/2；dark 假带上限 150→120（地板 4.5 不动）；precheck 239/221/618；hidden rot 0。
④ 436：无新红；Motion 采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 326 / 可判 1035 / rot 0。
⑥ 捕获 274 帧；基线 274/0/0/0；build 0 告警；换装 ok/387=387；全量 1265/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40693473537 ↔ b942e6b` / `40693357120 ↔ 0b034c4`（completed=failure）；② R462 自身跑（未创建）；③ dark 假带 120 上限的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（receipt 1<2）；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–507 的未结项仍开。

下一轮（R463）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R462 主笔+追记 head 跑、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4`、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（light 85/80/5.0 签收；dark 修复后应不再 150/147/3.0）、`FALLBACK_NAME` 83.0/2、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R462_REPORT_BULLET = u"""- **R462（fallback 文件名位 + dark 假带）**：`DetailPreviewViews.fallbackView` 的文件名没有行数/截断/内边距 —— 8×「很长文件名-」的 `.xyz` 在 600×440 里单行从 **7.0pt** 跑到右缘、压在浮层药丸下。修法：`lineLimit(2)` + 居中 + 中间省略 + 左右 80pt。旧/新：`FALLBACK_NAME 7.0/2 → 83.0/2`、亮暗同形；真实 `.xyz` 夹具（600×440）**2 张新帧**、0 变化，基线 **272→274/0/0/0**；逐张看过。判据读缩略图左侧窄列最左墨；M1260/M1261 **2/2**。另修 R461 的 dark 假带：真带 85..99、假带卡 150 ⇒ 选择器上限 **150→120**（地板 4.5 不动），本地 light 98.5/92.5/6.0、dark 99.0/92.5/6.5；runner dark 待验。⓪ no-op push、ahead=0；`40693473537 ↔ b942e6b` failure 3 步：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、dark 150/147/3.0 假带仍红、Motion receipt 1<2 采样红；`FILE_TEXT_PREVIEW 637/652`、HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收。全量 **1265/56/0**（427s）；捕获 274 帧；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 461 轮（R462" in audit: raise SystemExit("REFUSED AUDIT 已有 R462")
if u"## Round 459 · R462" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 459")
if u"## D-458" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-458")
if u"不支持文件 fallback 的长文件名留在窗格内" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**505." in backlog: raise SystemExit("REFUSED BACKLOG 已有 505")
if state.count(u"## R461 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R461 状态"))
U_CELL_OLD = u"U-31 … U-1732（R461 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R461 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_458 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R461 状态", STATE_SECTION + u"## R461 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1737（R462 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R461 节 ②", u"AGENT_STATE.md` 的 R462 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R462_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R462_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
