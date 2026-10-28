#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R464 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 462 轮（R463 · 2026-10-28"
AUDIT_SECTION = u"""## 第 463 轮（R464 · 2026-10-28 · U-1743…U-1747）：视频分辨率不可读态说出文件名（旧 3 条带 → 新 4；2 张新帧、基线 276→278）+ dark 假带改「内边距优先」选择器（本地 98.5/92.5/6.0、99.0/92.5/6.5）（产品 1 文件 + 判据；靶指定修复 + 新类别）

- **U-1743：⓪ push 与两跑。** 开工 no-op push success、ahead=0、HEAD=`dda66f4`；`40703707900 ↔ dda66f4` 读时 in_progress、`40703583494 ↔ 7d73179` queued ⇒ NOT-RUN（收口再读；仍读不到则具名）。已读：`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` failure 3 步（Swift tests、Capture gate、Motion floor）：`FALLBACK_NAME 83/82`、`INLINE light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652` 签收；**dark 变「找不到带」**（120 上限切真带）；Motion 1<2。`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。
- **U-1744：① 腐烂与预检。** `HIDDEN_ARMS 表=328 可判=1039 rot=0`；`NEEDLE_PRECHECK tables=241 covered=223 arms=622 bad=0`。
- **U-1745：靶修 dark 选择器（本地两向验证）。** 先按靶试「覆盖率最高」：本地选中 **78.5pt 的带内子段**（隙 1.0 <4.5）⇒ **真带方向先失败**，不上 runner。改成选**内边距最大**的候选（判据自己的对象：真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛；上限还原 **150**（不降 4.5 地板）。纯函数 `InlineCodeBandChoice` 两向验证：真带（padding 6）压过假文字带（3）与子段（1）；假带单独 + 覆盖率 0.56 被排除；>150 的 run 被排除。像素判据本地回到 `light 98.5/92.5/6.0、dark 99.0/92.5/6.5`；runner 待下一跑（R462 的 120 上限已证明错，R464 不再收上界）。
- **U-1746：② 视频不可读态的文件身份。** 缺陷：`videoInfoUnavailableView` 只有图标/「无法读取这段视频的分辨率信息」/Finder 按钮，**不说出是哪个文件**（头部 meta 可能被截断）。修法：在说明与按钮之间补 `url.lastPathComponent`（11pt secondary、单行、中间省略）。旧/新：`VIDEO_UNAVAILABLE light/dark 状态带=3 → 4`。真实 `clip.mov`（文本字节，走 `.informationUnavailable`）夹具 600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **276→278**；亮帧人眼复核（clip.mov 居中在说明与按钮之间）。
- **U-1747：判据与刀、八步。** 新帧判据 `testVideoUnavailableStateNamesTheFile` 数状态区（x 100..500、y 120..380）的墨带；旧 3 红、新 4 绿；`M1264`（撤行）/`M1265`（置空）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。build **0 告警**（首编有一处未用 `bandRun` 告警，删后冷编 0）；捕获 **278 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `278/0/0/0`；全量 **1268/56/0**（433.9s，轻载）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 463，`python3 scripts/product_streak.py --streak-for 463`，last=3c0d195）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40703707900 ↔ dda66f4` / `40703583494 ↔ 7d73179`（in_progress/queued）；② R464 自身跑（未创建）；③ padding 优先选择器的 runner 复验（dark）；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–513 的未结项仍开。

"""

ITER_SECTION = u"""## Round 461 · R464（第 463 轮 · 2026-10-28）：视频不可读态说出文件名（3→4 条带；2 张新帧、基线 276→278）+ dark 假带改「内边距优先」选择器（本地 98.5/92.5/6.0、99.0/92.5/6.5）

靶修 dark：覆盖率优先本地选中 78.5pt 子段（真带方向失败）；改为选**内边距最大**的候选（真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛，上限还原 150（不降 4.5 地板）；纯函数两向验证后像素判据回 98.5/92.5/6.0 与 99.0/92.5/6.5，runner 待验。新面：视频不可读态补文件名 `clip.mov`（说明与按钮之间），状态带 3→4；真实 `.mov`（信息不可读）夹具 2 张新帧、0 变化，基线 276→278/0/0/0；亮帧人眼复核。判据数状态区墨带；旧红新绿；M1264/M1265 2/2。全量 1268/56/0（433.9s）；build 0 告警（删一处未用变量）；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；R463 两跑 in_progress/queued；R462 两跑 failure（light 5.0、dark 找不到带、Motion 1<2；FALLBACK_NAME 83/82、FILE_TEXT 637/652 签收）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `detail-file-video-unavailable` 亮帧看：clip.mov 在说明与按钮之间；暗档判据 4 带。 |
| 判据有效性 | 15/15 | 状态带 3→4；两把刀 2/2；选择器纯函数两向（真带/假带/子段）。 |
| 假绿防御 | 14/15 | 覆盖率优先本地先失败并当场换掉；扣 1：padding 选择器 runner 未验。 |
| 产品面推进 | 15/15 | 新类别（视频不可读态身份）；真实 `.mov` 走产品载入；Store 不动。 |
| 台账一致性 | 15/15 | U-1743…U-1747、D-460、278 帧/1268、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 覆盖率优先失败、dark 120 切真带、R463 两跑未读全部具名。 |
| 可复核性 | 15/15 | 3→4 带、98.5/92.5/6.0、99.0/92.5/6.5、6/3/1 padding 三臂、precheck 241/223/622、rot 328/1039、基线 278 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_460 = u"""## D-460 行内码带按内边距优先选择，视频不可读态补文件名（R464）

- 背景：R462 的 150→120 上限把真带也切掉（runner dark 变「找不到带」）；R464 试覆盖率优先又选中 78.5pt 子段（本地失败）。
- 决定：候选选择改为**内边距最大**（真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛，上限还原 150；视频不可读态在说明与按钮之间补 `lastPathComponent`。
- 理由：选择器按判据自己的对象（带与字之间的空隙）挑；视频状态要说出是哪个文件，头部 meta 可能被截断。
- 兼容性/迁移：新增 `detail-file-video-unavailable` 亮/暗 2 张帧；旧帧 0 变化；基线 276→278 同 commit 更新；`InlineCodeBandChoice` 纯函数 + 两向单测。
- 边界：padding 选择器在 runner 1x 的复验待下一跑；视频状态只覆盖信息不可读态，播放控件仍无帧（510）。
- 回滚：删文件名行、还原选择器；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 视频不可读态说出文件名（3→4 条带；2 张新帧、基线 276→278）+ dark 假带改内边距优先选择器（本地 98.5/92.5/6.0、99.0/92.5/6.5）（R464 / 第 463 轮 / Round 461 / U-1743…U-1747 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**511. padding 优先选择器的 runner 复验**（R464 观察）
    现象：本地两向已验证（真带 6 压过假带 3/子段 1；假带单独/超宽被排除），runner dark 还没跑过。
    修法：下一跑读 `INLINE_CODE_PAD`；若 dark 仍找不到，先打印候选的 span/coverage/padding 三列，再改选择器；地板 4.5 不动。

**512. 视频播放控件仍无帧**（R464 观察）
    现象：本轮只覆盖信息不可读态；播放/时间/滑杆/静音控件从未捕获（需要真实视频资产）。
    修法：先确认 AVPlayerLayer 离屏可画，再选新面。

**513. 视频不可读态在极长文件名下的两行**（R464 观察）
    现象：文件名行是单行中间省略；极长名在 600 宽下的省略位置未单独拍。
    修法：补一张 120+ 字符的视频名帧；若要两行，和 fallback 用同一规则。
"""

STATE_SECTION = u"""## R464 状态（2026-10-28 · 本地 · 第 463 轮 / Round 461）：视频不可读态说出文件名（旧 3 条带 → 新 4；2 张新帧、基线 276→278）+ dark 假带改「内边距优先」选择器（本地 98.5/92.5/6.0、99.0/92.5/6.5）；全量 1268/56/0（产品 1 文件 + 判据；靶修复 + 新类别）

最后更新：2026-10-28（本地 · R464 / 第 463 轮 / Round 461）：靶修 dark 选择器：先按靶试「覆盖率最高」，本地选中 **78.5pt 带内子段**（隙 1.0）⇒ **真带方向失败**，不上 runner；改为选**内边距最大**的候选（真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛，上限还原 **150**（不降 4.5 地板）；纯函数 `InlineCodeBandChoice` 两向验证（真带压过假带/子段；假带单独 + 覆盖率门槛被排除；>150 被排除）；像素判据本地回到 `light 98.5/92.5/6.0、dark 99.0/92.5/6.5`。**新面**：`videoInfoUnavailableView` 只有图标/说明/Finder 按钮，不说出是哪个文件；在说明与按钮之间补 `url.lastPathComponent`（11pt secondary、单行、中间省略）。旧/新：`VIDEO_UNAVAILABLE light/dark 状态带=3 → 4`。真实 `clip.mov`（信息不可读）夹具 600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **276→278**；亮帧看 clip.mov 居中在说明与按钮之间。判据 `testVideoUnavailableStateNamesTheFile` 数状态区（x 100..500、y 120..380）墨带；旧红新绿；`M1264/M1265` **2/2 CAUGHT**。build **0 告警**（首编一处未用 `bandRun`，删后冷编 0）；捕获 **278 帧**；全量 **1268/56/0**（433.9s，轻载）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 463，`python3 scripts/product_streak.py --streak-for 463`，last=3c0d195）；清账与电池在台账后复跑。⓪：no-op push success、ahead=0、HEAD=`dda66f4`；`40703707900 ↔ dda66f4` in_progress、`40703583494 ↔ 7d73179` queued ⇒ NOT-RUN；`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` failure 3 步（FALLBACK_NAME 83/82、INLINE light 85/80/5.0、FILE_TEXT 637/652 签收；dark「找不到带」；Motion 1<2）。

本轮做了什么：
① ⓪ no-op push、ahead=0；R463 两跑 in_progress/queued；R462 两跑 failure（light 5.0、dark 找不到带、Motion 1<2；FALLBACK_NAME/FILE_TEXT 签收）。
② 产品：视频不可读态补文件名（3→4 带；2 张新帧、基线 278）。
③ 判据：dark 选择器改内边距优先（本地两向；98.5/92.5/6.0 与 99.0/92.5/6.5）；M1264/M1265 2/2；precheck 241/223/622；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 328 / 可判 1039 / rot 0。
⑥ 捕获 278 帧；基线 278/0/0/0；build 0 告警；换装 ok/387=387；全量 1268/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40703707900 ↔ dda66f4` / `40703583494 ↔ 7d73179`（in_progress/queued）；② R464 自身跑（未创建）；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–513 的未结项仍开。

下一轮（R465）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R464 主笔+追记 head 跑、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3`、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5、不再「找不到带」也不是 150/147）、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON` 3.95/5.92、`FALLBACK_NAME` 83/82、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R464_REPORT_BULLET = u"""- **R464（视频不可读态 + dark 选择器）**：视频不可读态只有图标/说明/Finder 按钮，**不说出是哪个文件**；在说明与按钮之间补 `lastPathComponent`（11pt secondary、单行、中间省略）。旧/新：`VIDEO_UNAVAILABLE 3 → 4 条带`；真实 `clip.mov`（信息不可读）夹具 600×440，**2 张新帧**、0 变化，基线 **276→278/0/0/0**；亮帧看过。判据数状态区墨带；M1264/M1265 **2/2**。靶修 dark 选择器：覆盖率优先本地选中 78.5pt 子段（真带方向失败）⇒ 改为**内边距最大**（真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛，上限还原 **150**（不降 4.5 地板）；纯函数两向验证；像素本地 `light 98.5/92.5/6.0、dark 99.0/92.5/6.5`；runner 待验。⓪ no-op push、ahead=0；R463 两跑 in_progress/queued；R462 两跑 failure（light 5.0 签收、dark 找不到带、Motion 1<2；FALLBACK_NAME/FILE_TEXT 签收）。全量 **1268/56/0**（433.9s）；build 0 告警（删一处未用变量）；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 463 轮（R464" in audit: raise SystemExit("REFUSED AUDIT 已有 R464")
if u"## Round 461 · R464" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 461")
if u"## D-460" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-460")
if u"视频不可读态说出文件名" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**511." in backlog: raise SystemExit("REFUSED BACKLOG 已有 511")
if state.count(u"## R463 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R463 状态"))
U_CELL_OLD = u"U-31 … U-1742（R463 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R463 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_460 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R463 状态", STATE_SECTION + u"## R463 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1747（R464 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R463 节 ②", u"AGENT_STATE.md` 的 R464 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R464_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R464_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
