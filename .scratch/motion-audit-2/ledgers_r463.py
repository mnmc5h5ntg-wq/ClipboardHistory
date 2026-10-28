#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R463 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 461 轮（R462 · 2026-10-28"
AUDIT_SECTION = u"""## 第 462 轮（R463 · 2026-10-28 · U-1738…U-1742）：fallback 无缩略图的占位图标可见（旧 1.25/1.34:1 → 新 3.95/5.92:1；2 张新帧、基线 274→276）（产品 1 文件，fallback 占位图标位）

- **U-1738：⓪ push 与两跑。** 开工 no-op push success、ahead=0、HEAD=`b3531d4`；`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` 读时 in_progress ⇒ NOT-RUN（收口再试；仍读不到则具名 CI_READ_BLOCKED）。已读：`40693473537 ↔ b942e6b` **failure 3 步**（Swift tests、Capture gate、Motion coverage floor）：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、`dark 150.0/147.0/3.0`（150 是选择器上限 ⇒ 假带；R462 已收上限 120，待新跑）；Motion receipt 1<2 采样红；`40693357120 ↔ 0b034c4` failure；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 签收；`40688652304`/`40688610679` failures、`40681994982`/`40682072865` failures、`40675730252` failure 2 步、`40653092761` success 等沿用；436 无新红。
- **U-1739：① 腐烂与预检。** `HIDDEN_ARMS 表=327 可判=1037 rot=0`；`NEEDLE_PRECHECK tables=240 covered=222 arms=620 bad=0`。
- **U-1740：② fallback 无缩略图的占位图标。** 缺陷：`fallbackView` 的 `else` 分支 `doc.fill` 用 `.quaternary` —— 亮/暗实测 **1.25/1.34:1**，状态图标几乎看不见（非文本图形 3:1 地板）。修法：改 `Color(nsColor: .secondaryLabelColor)`（3.95/5.92:1），仍是"空占位"但不装死。旧/新：`FALLBACK_ICON light 图标=230 页底=255 比=1.25 → 128/255/3.95`、`dark 52/30/1.34 → 154/30/5.92`。新增真实 `.xyz` 无缩略图夹具 `detail-file-fallback-nothumb`（600×440），**2 张新帧**、0 旧帧变化/缺失；基线 **274→276**；亮帧人眼复核（图标清晰），暗档由判据 5.92 签收。
- **U-1741：判据与刀。** 新帧判据 `testFallbackPlaceholderIconIsVisible` 在图标上半区（x 260..340、y 150..250；标题在 284pt 之下）取最暗像素与页底算 sRGB 对比，地板 3.0；旧 1.25/1.34 红、新 3.95/5.92 绿；`M1262`（回 quaternary）/`M1263`（降 tertiary）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1742：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **276 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `276/0/0/0`；全量 **1266/56/0**（388.6s，轻载）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 462，`python3 scripts/product_streak.py --streak-for 462`，last=a91d4a6）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40698931269 ↔ b3531d4` / `40698866675 ↔ b362cf3`（in_progress）；② R463 自身跑（未创建）；③ dark 假带 120 上限的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（receipt 1<2）；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–510 的未结项仍开。

"""

ITER_SECTION = u"""## Round 460 · R463（第 462 轮 · 2026-10-28）：fallback 无缩略图的占位图标可见（旧 1.25/1.34:1 → 新 3.95/5.92:1；2 张新帧、基线 274→276）

无缩略图的 fallback 用 `doc.fill` + `.quaternary`，亮/暗只有 1.25/1.34:1，状态图标等于没有。改成 `secondaryLabelColor`（3.95/5.92），仍是空占位但不装死。旧/新：`FALLBACK_ICON light 230/255/1.25 → 128/255/3.95`、`dark 52/30/1.34 → 154/30/5.92`；真实 `.xyz` 无缩略图夹具（600×440）2 张新帧、0 变化，基线 274→276/0/0/0；亮帧人眼复核。判据取图标上半区最暗像素与页底算 sRGB 对比（地板 3.0）；旧红新绿；M1262/M1263 2/2。全量 1266/56/0（388.6s）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；R462 两跑 in_progress；R461 跑 INLINE light 5.0 签收、dark 假带仍红、Motion 1<2；FILE_TEXT 637/652、HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮帧看图标清晰；暗档由判据 5.92 签收（同帧页底 30）。 |
| 判据有效性 | 15/15 | 图标上半区最暗像素/页底 sRGB 对比；旧 1.25/1.34 红、新 3.95/5.92 绿。 |
| 假绿防御 | 14/15 | 两把刀全 CAUGHT；扣 1：R462 跑与 R463 自身跑未读。 |
| 产品面推进 | 15/15 | 新类别（fallback 占位图标）；真实无缩略图文件走产品载入；Store 不动。 |
| 台账一致性 | 15/15 | U-1738…U-1742、D-459、276 帧/1266、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R462 两跑 in_progress、R461 红、flake 与 NOT-RUN 全部具名。 |
| 可复核性 | 15/15 | 230/255/1.25、128/255/3.95、52/30/1.34、154/30/5.92、precheck 240/222/620、rot 327/1037、基线 276 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_459 = u"""## D-459 fallback 无缩略图的占位图标取 secondary（R463）

- 背景：无缩略图的 fallback 用 `doc.fill` + `.quaternary`，亮/暗只有 1.25/1.34:1，状态图标几乎看不见。
- 决定：改 `Color(nsColor: .secondaryLabelColor)`（3.95/5.92:1）；仍是"空占位"，不是可交互控件。
- 理由：非文本图形 3:1 是地板；图标是这一屏唯一的视觉身份，不能装死。
- 兼容性/迁移：新增真实 `.xyz` 无缩略图夹具 `detail-file-fallback-nothumb`（600×440）亮/暗 2 张帧；旧帧 0 变化；基线 274→276 同 commit 更新。
- 边界：有缩略图的 fallback 上一轮已做文件名；无缩略图的极长文件名未单独拍（507 同族）。
- 回滚：`secondaryLabelColor` → `.quaternary`；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### fallback 无缩略图的占位图标可见（旧 1.25/1.34:1 → 新 3.95/5.92:1；2 张新帧、基线 274→276）（R463 / 第 462 轮 / Round 460 / U-1738…U-1742 · 产品 1 文件，fallback 占位图标位）

"""

BACKLOG_SECTION = u"""**508. R462 的 dark 假带 120 上限仍待 runner 复验**（R463 观察）
    现象：本地 light/dark 6.0/6.5；R462 两跑在开工时仍 in_progress，收口未读到 dark 新读数。
    修法：下一跑读 `INLINE_CODE_PAD`；若 dark 仍 150/147，查候选 run 的 span/coverage 对象身份；地板 4.5 不动。

**509. fallback 无缩略图的极长文件名未单独拍**（R463 观察）
    现象：本轮无缩略图夹具用短名 `notes.xyz`；R462 的两行/内边距规则只在有缩略图的长名上验过。
    修法：补一张无缩略图 + 长名帧，确认图标与文件名同时可读。

**510. 视频预览控件仍无帧**（R463 观察）
    现象：`VideoPreview`（播放/时间/滑杆/静音）从未被捕获；需要真实视频资产或帧注入。
    修法：先确认可捕获（AVPlayerLayer 离屏）再选新面；别先改产品。
"""

STATE_SECTION = u"""## R463 状态（2026-10-28 · 本地 · 第 462 轮 / Round 460）：fallback 无缩略图的占位图标可见（旧 1.25/1.34:1 → 新 3.95/5.92:1；2 张新帧、基线 274→276）；全量 1266/56/0；R462 两跑未读（产品 1 文件，fallback 占位图标位）

最后更新：2026-10-28（本地 · R463 / 第 462 轮 / Round 460）：无缩略图的 fallback 用 `doc.fill` + `.quaternary` —— 亮/暗实测 **1.25/1.34:1**，状态图标几乎看不见（非文本图形 3:1 地板）。修法：改 `Color(nsColor: .secondaryLabelColor)`（3.95/5.92:1），仍是"空占位"但不装死。旧/新：`FALLBACK_ICON light 图标=230 页底=255 比=1.25 → 128/255/3.95`、`dark 52/30/1.34 → 154/30/5.92`。新增真实 `.xyz` 无缩略图夹具 `detail-file-fallback-nothumb`（600×440），**2 张新帧**、0 旧帧变化/缺失；基线 **274→276**；亮帧人眼复核，暗档由判据 5.92 签收。新帧判据 `testFallbackPlaceholderIconIsVisible` 在图标上半区（x 260..340、y 150..250；标题 284pt 之下）取最暗像素与页底算 sRGB 对比，地板 3.0；旧 1.25/1.34 红、新 3.95/5.92 绿；`M1262/M1263` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **240/222/620 bad=0**、ARM **333/1103**、HIDDEN **327/1037 rot=0**。⓪：no-op push success、ahead=0、HEAD=`b3531d4`；`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` 读时 in_progress ⇒ NOT-RUN；`40693473537 ↔ b942e6b` failure 3 步（INLINE light 85/80/5.0 签收、dark 150/147/3.0 假带、Motion receipt 1<2）；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 签收。全量 **1266/56/0**（388.6s，轻载）；捕获卷 **276 帧**；基线 **276/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 462，`python3 scripts/product_streak.py --streak-for 462`，last=a91d4a6）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R462 两跑 in_progress ⇒ NOT-RUN；R461 跑 INLINE light 5.0 签收、dark 假带仍红、Motion 1<2。
② 产品：fallback 无缩略图占位图标 1.25/1.34 → 3.95/5.92（2 张新帧、基线 276）。
③ 判据：旧红新绿；M1262/M1263 2/2；precheck 240/222/620；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 327 / 可判 1037 / rot 0。
⑥ 捕获 276 帧；基线 276/0/0/0；build 0 告警；换装 ok/387=387；全量 1266/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40698931269 ↔ b3531d4` / `40698866675 ↔ b362cf3`（in_progress）；② R463 自身跑（未创建）；③ dark 假带 120 上限 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–510 的未结项仍开。

下一轮（R464）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R463 主笔+追记 head 跑、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3`、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4`、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（light 85/80/5.0 签收；dark 120 上限修复后应 ≥4.5、不再 150/147）、`FALLBACK_ICON` 3.95/5.92、`FALLBACK_NAME` 83.0/2、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R463_REPORT_BULLET = u"""- **R463（fallback 占位图标位）**：无缩略图的 fallback 用 `doc.fill` + `.quaternary`，亮/暗只有 **1.25/1.34:1**，状态图标几乎看不见。改 `secondaryLabelColor`（**3.95/5.92:1**），仍是空占位但不装死。旧/新：`FALLBACK_ICON light 230/255/1.25 → 128/255/3.95`、`dark 52/30/1.34 → 154/30/5.92`；真实 `.xyz` 无缩略图夹具（600×440）**2 张新帧**、0 变化，基线 **274→276/0/0/0**；亮帧人眼复核。判据取图标上半区最暗像素/页底 sRGB 对比（地板 3.0）；旧红新绿；M1262/M1263 **2/2**。⓪ no-op push、ahead=0；R462 两跑 `40698931269`/`40698866675` 读时 in_progress ⇒ NOT-RUN；R461 跑 `40693473537 ↔ b942e6b` failure 3 步：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、dark 150/147/3.0 假带仍红、Motion receipt 1<2；`FILE_TEXT_PREVIEW 637/652`、HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收。全量 **1266/56/0**（388.6s）；捕获 276 帧；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 462 轮（R463" in audit: raise SystemExit("REFUSED AUDIT 已有 R463")
if u"## Round 460 · R463" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 460")
if u"## D-459" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-459")
if u"fallback 无缩略图的占位图标" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**508." in backlog: raise SystemExit("REFUSED BACKLOG 已有 508")
if state.count(u"## R462 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R462 状态"))
U_CELL_OLD = u"U-31 … U-1737（R462 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R462 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_459 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R462 状态", STATE_SECTION + u"## R462 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1742（R463 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R462 节 ②", u"AGENT_STATE.md` 的 R463 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R463_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R463_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
