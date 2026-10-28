#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R465 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 463 轮（R464 · 2026-10-28"
AUDIT_SECTION = u"""## 第 464 轮（R465 · 2026-10-28 · U-1748…U-1752）：视频播放器补实底黑（旧播放器=页底、差 0 → 新 差 255/30；2 张新帧、基线 278→280）（产品 1 文件，视频播放器实底位）

- **U-1748：⓪ push 与两跑。** 开工一次快进 push **`dda66f4..7a04a79` success**（三笔：686737c/707e242/7a04a79），HEAD=origin/main=`7a04a79`、**ahead=0**；`40710557752 ↔ 7a04a79`（R464 head）读时 in_progress ⇒ NOT-RUN（收口再读；仍读不到则具名）。已读：`40703707900 ↔ dda66f4` 与 `40703583494 ↔ 7d73179` **failure，失败步骤 2 个**（Swift tests、Capture gate）：`FALLBACK_ICON light 3.84/dark 5.08`、`FALLBACK_NAME 83/82`、`INLINE_CODE_PAD light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652` 签收；**dark 仍「找不到带」**（120 上限）；`40698931269`/`40698866675` failures、`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。
- **U-1749：① 腐烂与预检。** `HIDDEN_ARMS 表=329 可判=1041 rot=0`；`NEEDLE_PRECHECK tables=242 covered=224 arms=624 bad=0`。
- **U-1750：② 视频播放器实底。** 缺陷：`VideoPreview` 的 `VideoPlayerSurface` 没有底；第一帧未到时播放器区就是**空白页色**（亮 255/暗 30，与页底差 0），看起来像没有视频。修法：给播放器面 `.background(Color.black)`（实底；视频帧覆盖其上）。旧/新：`VIDEO_SURFACE light 播放器=255 页底=255 差=0 → 0/255/255`、`dark 30/30/0 → 0/30/30`。夹具用**真实生成的 .mov**（AVAssetWriter，64×36）走产品 `VideoPreview`，600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **278→280**；亮帧人眼复核（黑底 + 播放/时间/滑杆/静音胶囊）。**捕获守卫**把这张帧的纯黑带当成新盲区 ⇒ 已确认是产品有意的播放器黑底（AVPlayerLayer 离屏不画），登记进 `materialBlindSpotFixtures` 并写明理由，不放宽未绘制阈值。
- **U-1751：判据与刀。** 新帧判据 `testVideoPlayerHasASolidBackingSurface` 比较播放器区（x 100..500、y 120..360）与页底（x 4..16）的平均亮度，要求页底−播放器 ≥20；旧差 0/0 红、新差 255/30 绿；`M1266`（撤黑底）/`M1267`（改白底）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1752：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **280 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `280/0/0/0`（捕获守卫在登记黑带后通过）；全量 **1269/56/0**（445.8s，轻载）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 464，`python3 scripts/product_streak.py --streak-for 464`，last=686737c）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40710557752 ↔ 7a04a79`（in_progress）；② R465 自身跑（未创建）；③ padding 选择器的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–516 的未结项仍开。

"""

ITER_SECTION = u"""## Round 462 · R465（第 464 轮 · 2026-10-28）：视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 278→280）

`VideoPlayerSurface` 没有底：第一帧未到时播放器区就是空白页色（亮 255/暗 30，与页底差 0），像没有视频。给播放器面 `.background(Color.black)`；视频帧覆盖其上。旧/新：`VIDEO_SURFACE light 255/255/0 → 0/255/255`、`dark 30/30/0 → 0/30/30`。夹具用真实生成的 .mov（AVAssetWriter 64×36）走 `VideoPreview`，600×440，2 张新帧、0 变化，基线 278→280/0/0/0；亮帧看过黑底 + 控件胶囊。捕获守卫误报新黑带 ⇒ 确认是**产品有意黑底**（AVPlayerLayer 离屏不画），登记名册并写明理由。判据比播放器区/页底平均亮度（差 ≥20）；旧红新绿；M1266/M1267 2/2。全量 1269/56/0（445.8s）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push dda66f4..7a04a79 success、ahead=0；R463 两跑 failure（FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652 签收；dark 仍找不到带）；R464 head run in_progress。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮帧看：黑底播放器面 + 播放/时间/滑杆/静音胶囊；暗档差 30。 |
| 判据有效性 | 15/15 | 播放器区/页底平均亮度差；旧 0/0 红、新 255/30 绿；两把刀 2/2。 |
| 假绿防御 | 14/15 | 黑带登记有身份与理由；扣 1：padding 选择器与 R464 跑未读。 |
| 产品面推进 | 15/15 | 新类别（视频播放器实底）；真实 .mov 走产品；Store 不动。 |
| 台账一致性 | 15/15 | U-1748…U-1752、D-461、280 帧/1269、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R463 两跑 dark 仍找不到带、R464 run in_progress、flake 全部具名。 |
| 可复核性 | 15/15 | 255/255/0→0/255/255、30/30/0→0/30/30、precheck 242/224/624、rot 329/1041、基线 280 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_461 = u"""## D-461 视频播放器面用实底黑（R465）

- 背景：`VideoPlayerSurface` 无底；第一帧未到时播放器区是空白页色（亮/暗与页底差 0），看起来像没有视频。
- 决定：给播放器面 `.background(Color.black)`；视频帧覆盖其上；黑带登记进 `materialBlindSpotFixtures`（有意的产品黑底，不是材质盲区）。
- 理由：播放器需要自己的表面；AVPlayerLayer 在离屏通道不画时，黑底正好是"第一帧未到"的实底，不再伪装成空白页。
- 兼容性/迁移：新增真实 .mov 夹具 `detail-file-video-controls`（600×440）亮/暗 2 张帧；旧帧 0 变化；基线 278→280 同 commit 更新。
- 边界：真实视频播放（AVPlayerLayer 在屏）仍未拍；播放控件的时间码等宽/滑杆轨道另开（512/513 族）。
- 回滚：删 `.background(Color.black)` 与名册行；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 278→280）（R465 / 第 464 轮 / Round 462 / U-1748…U-1752 · 产品 1 文件，视频播放器实底位）

"""

BACKLOG_SECTION = u"""**514. 真实视频播放帧仍无帧**（R465 观察）
    现象：夹具用 1 帧 64×36 的 .mov；AVPlayerLayer 在离屏通道不画，黑底证明的是"第一帧前的表面"，不是播放中的画面。
    修法：若要判播放帧，先在屏/录制通道确认 AVPlayerLayer 可拍，再选新面；别把黑底当播放证据。

**515. 视频控件的时间码/滑杆轨道未单独判**（R465 观察）
    现象：控件胶囊可见；时间码是否等宽、滑杆轨道对比未量（R464 的 511/512 族）。
    修法：给时间码 `.monospacedDigit()` 并加一条宽度不随秒数变化的判据；滑杆轨道按非文本对比另判。

**516. padding 选择器的 runner 复验仍欠**（R465 观察）
    现象：本地两向通过（真带 6 压过假带 3/子段 1），R464 的 run 还没读。
    修法：下一跑读 `INLINE_CODE_PAD`；若 dark 仍「找不到带」，打印候选三列；地板 4.5 不动。
"""

STATE_SECTION = u"""## R465 状态（2026-10-28 · 本地 · 第 464 轮 / Round 462）：视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 278→280）；全量 1269/56/0；R464 跑未读（产品 1 文件，视频播放器实底位）

最后更新：2026-10-28（本地 · R465 / 第 464 轮 / Round 462）：`VideoPlayerSurface` 没有底；第一帧未到时播放器区就是**空白页色**（亮 255/暗 30，与页底差 0），看起来像没有视频。修法：给播放器面 `.background(Color.black)`（视频帧覆盖其上）。旧/新：`VIDEO_SURFACE light 播放器=255 页底=255 差=0 → 0/255/255`、`dark 30/30/0 → 0/30/30`。夹具用**真实生成的 .mov**（AVAssetWriter，64×36）走产品 `VideoPreview`，600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **278→280**；亮帧人眼复核（黑底 + 播放/时间/滑杆/静音胶囊）。**捕获守卫**把这张帧的纯黑带当成新盲区 ⇒ 确认是产品有意的播放器黑底（AVPlayerLayer 离屏不画），登记进 `materialBlindSpotFixtures` 并写明理由，不放宽未绘制阈值；登记后捕获守卫通过。新帧判据 `testVideoPlayerHasASolidBackingSurface` 比较播放器区（x 100..500、y 120..360）与页底（x 4..16）的平均亮度，要求页底−播放器 ≥20；旧 0/0 红、新 255/30 绿；`M1266/M1267` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **242/224/624 bad=0**、ARM **335/1107**、HIDDEN **329/1041 rot=0**。⓪：一次快进 push **`dda66f4..7a04a79` success**（三笔）、HEAD=origin/main=`7a04a79`、**ahead=0**；`40710557752 ↔ 7a04a79` in_progress ⇒ NOT-RUN；`40703707900 ↔ dda66f4` 与 `40703583494 ↔ 7d73179` failure 2 步（FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652 签收；dark 仍找不到带）；`40698931269`/`40698866675` failures 等沿用。全量 **1269/56/0**（445.8s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 464，`python3 scripts/product_streak.py --streak-for 464`，last=686737c）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push dda66f4..7a04a79 success、ahead=0；R463 两跑 failure（light 5.0、dark 找不到带；FALLBACK_ICON/NAME、FILE_TEXT 签收）；R464 run in_progress。
② 产品：视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 280）。
③ 判据：旧红新绿；M1266/M1267 2/2；黑带名册登记有理由；precheck 242/224/624；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 329 / 可判 1041 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1269/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40710557752 ↔ 7a04a79`（in_progress）；② R465 自身跑（未创建）；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–516 的未结项仍开。

下一轮（R466）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R465 主笔+追记 head 跑、`40710557752 ↔ 7a04a79`、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5、不再「找不到带」）、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R465_REPORT_BULLET = u"""- **R465（视频播放器实底位）**：`VideoPlayerSurface` 没有底，第一帧未到时播放器区就是空白页色（亮 255/暗 30，与页底差 0），像没有视频。给播放器面 `.background(Color.black)`。旧/新：`VIDEO_SURFACE light 255/255/0 → 0/255/255`、`dark 30/30/0 → 0/30/30`；真实生成的 .mov（AVAssetWriter 64×36）走产品 `VideoPreview`，600×440，**2 张新帧**、0 变化，基线 **278→280/0/0/0**；亮帧看过黑底 + 控件胶囊。捕获守卫误报新黑带 ⇒ 确认是**有意的播放器黑底**（AVPlayerLayer 离屏不画），登记 `materialBlindSpotFixtures` 并写理由。判据比播放器区/页底平均亮度（差 ≥20）；旧红新绿；M1266/M1267 **2/2**。⓪ push dda66f4..7a04a79 **success**、ahead=0；R463 两跑 failure（FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652 签收；dark 仍找不到带）；R464 head run in_progress。全量 **1269/56/0**（445.8s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 464 轮（R465" in audit: raise SystemExit("REFUSED AUDIT 已有 R465")
if u"## Round 462 · R465" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 462")
if u"## D-461" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-461")
if u"视频播放器补实底黑" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**514." in backlog: raise SystemExit("REFUSED BACKLOG 已有 514")
if state.count(u"## R464 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R464 状态"))
U_CELL_OLD = u"U-31 … U-1747（R464 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R464 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_461 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R464 状态", STATE_SECTION + u"## R464 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1752（R465 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R464 节 ②", u"AGENT_STATE.md` 的 R465 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R465_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R465_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
