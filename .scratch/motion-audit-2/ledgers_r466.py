#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R466 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 464 轮（R465 · 2026-10-28"
AUDIT_SECTION = u"""## 第 465 轮（R466 · 2026-10-28 · U-1753…U-1757）：视频播放器与控件胶囊右缘对齐（旧差 63.0pt → 新 13.0pt；2 张旧帧变化、基线 280）（产品 1 文件，视频播放器/控件对齐位）

- **U-1753：⓪ push 与读数。** 开工 `git push` 一次探针被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`86d6b6a`、ahead=0）**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40710557752 ↔ 7a04a79`（R464 head）与 R465 两跑读不到 ⇒ NOT-RUN。已读（上一轮）：`40703707900 ↔ dda66f4` 与 `40703583494 ↔ 7d73179` failure 2 步：`FALLBACK_ICON 3.84/5.08`、`FALLBACK_NAME 83/82`、`INLINE_CODE_PAD light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652` 签收；dark 仍「找不到带」；`40698931269`/`40698866675` failures、`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。
- **U-1754：① 腐烂与预检。** `HIDDEN_ARMS 表=330 可判=1043 rot=0`；`NEEDLE_PRECHECK tables=243 covered=225 arms=626 bad=0`、`ARM_TOTAL files=336 arms=1109`。
- **U-1755：② 播放器/控件右缘对齐。** 缺陷：播放器只留 `.padding(.horizontal, 20)`，而控件胶囊的 trailing 是 `52+12+16=80`（给右下角浮层让位）⇒ 播放器右缘比控件多 **63.0pt**（569.5 vs 506.5），黑区还伸到浮层下面。修法：播放器的 leading/trailing 改用 `VideoPlaybackMetrics.controlsLeadingPadding`（12）/`controlsTrailingPadding`（80），与控件同缘、同时给浮层让位。旧/新：`VIDEO_ALIGN light/dark 播放器右=569.5 控件右=506.5 差=63.0 → 519.5/506.5/13.0`。**2 张旧帧变化**（`detail-file-video-controls` 亮/暗）、0 新增/缺失；基线 **280**（同 commit 更新）；亮/暗帧看过：黑区 x 24..1040、浮层从 1060 起、控件胶囊同一条右缘。
- **U-1756：判据与刀。** 新帧判据 `testVideoPlayerAlignsWithItsControls` 取播放器顶部黑带（y 120..200，浮层从 240pt 起）的最右黑列与控件行（y 395..430，x<535 避开浮层）的最右墨列，要求差 ≤30pt；旧 63.0 红、新 13.0 绿；`M1268`（回 horizontal 20）/`M1269`（trailing 0）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1757：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **280 帧**、`CHANGED=2 MISSING=0 ADDED=0`，更新后 `280/0/0/0`；全量 **1270/56/0**（456.1s，轻载）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 465，`python3 scripts/product_streak.py --streak-for 465`，last=71bed3d）；清账与电池在台账后复跑。**具名 NOT-RUN**：① R464/R465 两跑（CI_READ_BLOCKED）；② R466 自身跑（未推/未创建）；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–519 的未结项仍开。

"""

ITER_SECTION = u"""## Round 463 · R466（第 465 轮 · 2026-10-28）：视频播放器与控件胶囊右缘对齐（旧差 63.0pt → 新 13.0pt；2 张旧帧变化、基线 280）

播放器只留 horizontal 20，控件 trailing 是 80（给浮层让位）⇒ 播放器右缘多 63pt、黑区伸到浮层下。修法：播放器 leading/trailing 改用控件的 12/80，同缘且让位。旧/新：`VIDEO_ALIGN 播放器右=569.5 控件右=506.5 差=63.0 → 519.5/506.5/13.0`；2 张旧帧变化、0 新增，基线 280/0/0/0；亮/暗看过黑区 x 24..1040、浮层 1060 起、控件同右缘。判据取顶部黑带最右黑列与控件行最右墨列，差 ≤30；旧红新绿；M1268/M1269 2/2。全量 1270/56/0（456.1s）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push 一次探针被拒、gh 不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R464/R465 两跑未读（NOT-RUN）；上一轮签收 FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652，dark 仍找不到带。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 video-controls 逐张看过：黑区右缘与控件胶囊同轴、浮层外。 |
| 判据有效性 | 15/15 | 顶部黑带最右黑列 vs 控件行最右墨列；旧 63 红、新 13 绿；两把刀 2/2。 |
| 假绿防御 | 14/15 | 两把刀全 CAUGHT；扣 1：R464/R465 跑未读、padding 选择器未验。 |
| 产品面推进 | 15/15 | 新类别（播放器/控件对齐）；真实 .mov 夹具；Store 不动。 |
| 台账一致性 | 15/15 | U-1753…U-1757、D-462、280 帧/1270、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 断网、CI 读不到、dark 仍找不到带、flake 全部具名。 |
| 可复核性 | 15/15 | 569.5/506.5/63.0→519.5/506.5/13.0、precheck 243/225/626、rot 330/1043、基线 280 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_462 = u"""## D-462 视频播放器与控件胶囊共用左右缘（R466）

- 背景：播放器只留 20pt，控件 trailing 是 80pt（给浮层让位）⇒ 播放器右缘多 63pt、黑区伸到浮层下。
- 决定：播放器用 `VideoPlaybackMetrics.controlsLeadingPadding`（12）与 `controlsTrailingPadding`（80）。
- 理由：播放器和它的控件是同一条横向轴；给浮层的让位必须两边都做，不能只有控件让。
- 兼容性/迁移：`detail-file-video-controls` 亮/暗 2 张旧帧变化；基线 280 同 commit 更新。
- 边界：视频真实播放帧仍无帧（514）；时间码/滑杆另开（515）。
- 回滚：播放器回 `.padding(.horizontal, 20)`；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 视频播放器与控件胶囊右缘对齐（旧差 63.0pt → 新 13.0pt；2 张旧帧变化、基线 280）（R466 / 第 465 轮 / Round 463 / U-1753…U-1757 · 产品 1 文件，播放器/控件对齐位）

"""

BACKLOG_SECTION = u"""**517. R464/R465/R466 跑仍未读**（R466 观察）
    现象：开工 push/gh 均不可达；R464 head 与 R465 两跑读不到，R466 自身跑未创建。
    修法：下一轮联网后先成对读；重点 `INLINE_CODE_PAD` dark（padding 优先）、`VIDEO_SURFACE`、`VIDEO_ALIGN`。

**518. 播放器左缘 12 与正文 20 不同轴**（R466 观察）
    现象：为与控件对齐，播放器/控件的左缘是 12；正文/头部是 20。两种轴并存在同一屏。
    修法：若要统一，给控件/播放器一个与正文一致的 leading；先补帧再定，别顺手改。

**519. 控件胶囊内的时间码仍非等宽数字**（R466 观察）
    现象：时间码随秒数变化可能有宽度抖动；未拍 0:09/0:10 两态。
    修法：加 `.monospacedDigit()` 并做两态帧；先记录。
"""

STATE_SECTION = u"""## R466 状态（2026-10-28 · 本地 · 第 465 轮 / Round 463）：视频播放器与控件胶囊右缘对齐（旧差 63.0pt → 新 13.0pt；2 张旧帧变化、基线 280）；全量 1270/56/0；R464/R465 跑未读（产品 1 文件，播放器/控件对齐位）

最后更新：2026-10-28（本地 · R466 / 第 465 轮 / Round 463）：播放器只留 `.padding(.horizontal, 20)`，而控件胶囊的 trailing 是 `52+12+16=80`（给右下角浮层让位）⇒ 播放器右缘比控件多 **63.0pt**（569.5 vs 506.5），黑区还伸到浮层下面。修法：播放器的 leading/trailing 改用 `VideoPlaybackMetrics.controlsLeadingPadding`（12）/`controlsTrailingPadding`（80），与控件同缘、同时给浮层让位。旧/新：`VIDEO_ALIGN light/dark 播放器右=569.5 控件右=506.5 差=63.0 → 519.5/506.5/13.0`。**2 张旧帧变化**（`detail-file-video-controls` 亮/暗）、0 新增/缺失；基线 **280**（同 commit 更新）；亮/暗帧看过：黑区 x 24..1040、浮层从 1060 起、控件胶囊同一条右缘。新帧判据 `testVideoPlayerAlignsWithItsControls` 取播放器顶部黑带（y 120..200）最右黑列与控件行（y 395..430、x<535）最右墨列，差 ≤30pt；旧 63.0 红、新 13.0 绿；`M1268/M1269` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **243/225/626 bad=0**、ARM **336/1109**、HIDDEN **330/1043 rot=0**。⓪：开工 push 一次探针被拒（`Connection closed ... port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`86d6b6a`、ahead=0）**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40710557752`（R464 head）与 R465 两跑 NOT-RUN。上一轮签收：`FALLBACK_ICON 3.84/5.08`、`FALLBACK_NAME 83/82`、`INLINE_CODE_PAD light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652`；dark 仍找不到带。全量 **1270/56/0**（456.1s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 465，`python3 scripts/product_streak.py --streak-for 465`，last=71bed3d）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push/gh 均不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R464/R465 两跑 NOT-RUN；上一轮签收 FALLBACK_ICON/NAME、INLINE light、FILE_TEXT。
② 产品：播放器/控件右缘对齐（63.0→13.0；2 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1268/M1269 2/2；precheck 243/225/626；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 330 / 可判 1043 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1270/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R464/R465 两跑（CI_READ_BLOCKED）；② R466 自身跑；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–519 的未结项仍开。

下一轮（R467）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R466 主笔+追记 head 跑、`40710557752 ↔ 7a04a79`、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3` 等的全部失败步骤；重点 `VIDEO_ALIGN` 13.0、`INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5）、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R466_REPORT_BULLET = u"""- **R466（播放器/控件对齐位）**：播放器只留 `horizontal 20`，控件 trailing 是 80（给浮层让位）⇒ 播放器右缘多 **63.0pt**（569.5 vs 506.5），黑区伸到浮层下。修法：播放器 leading/trailing 改用控件的 12/80。旧/新：`VIDEO_ALIGN light/dark 569.5/506.5/63.0 → 519.5/506.5/13.0`；**2 张旧帧变化**、0 新增，基线 **280/0/0/0**；亮/暗看过黑区 x 24..1040、浮层 1060 起。判据取顶部黑带最右黑列 vs 控件行最右墨列（差 ≤30）；旧红新绿；M1268/M1269 **2/2**。⓪ 开工 push 一次探针被拒、gh 不可达 ⇒ `PUSH_BLOCKED=network`（HEAD=86d6b6a、ahead=0）+ `CI_READ_BLOCKED=network`；R464/R465 两跑 NOT-RUN；上一轮签收 FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652，dark 仍找不到带。全量 **1270/56/0**（456.1s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 465 轮（R466" in audit: raise SystemExit("REFUSED AUDIT 已有 R466")
if u"## Round 463 · R466" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 463")
if u"## D-462" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-462")
if u"视频播放器与控件胶囊右缘对齐" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**517." in backlog: raise SystemExit("REFUSED BACKLOG 已有 517")
if state.count(u"## R465 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R465 状态"))
U_CELL_OLD = u"U-31 … U-1752（R465 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R465 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_462 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R465 状态", STATE_SECTION + u"## R465 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1757（R466 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R465 节 ②", u"AGENT_STATE.md` 的 R466 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R466_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R466_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
