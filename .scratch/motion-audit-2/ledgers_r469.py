#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R469 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 467 轮（R468 · 2026-10-29"
AUDIT_SECTION = u"""## 第 468 轮（R469 · 2026-10-29 · U-1768…U-1772）：跨年时间标注（旧两条「6月15日 12:00」→ 旧行「2025年6月15日 12:00」；主列表行宽差 +41.0pt；4 张新帧、基线 284）（产品 4 文件 + 判据）

- **U-1768：⓪ push 与 CI。** 开工 HEAD=`00ff343`、origin/main=`0774453`、ahead=2；一次快进 push **`0774453..00ff343` success**、HEAD=origin/main=`00ff343`、**ahead=0**。`40736447466 ↔ 0774453` **job cancelled**（被新 push 顶掉，失败步骤 0）⇒ **NOT-RUN**（不许读成绿）；`40740068763 ↔ 00ff343` **failure 2 步**（Swift tests / Capture gate）：唯一测试红仍是 `INLINE_CODE_PAD dark 150/147/3.0`；Capture gate 的 15 帧黑带方向变成 **`MATERIAL_BLIND_NOT_RUN`**（runner 102 帧一处黑带都没有，名单 15 处 ⇒ 这一方向无从判起；R467 的 intentional 拆分生效），`SETTINGS_HELPER_AXIS_NOT_RUN=settings-content-blank` 亮/暗具名；已读签收：`VIDEO_SEEK 98/106`、`VIDEO_ALIGN 13.0`、`VIDEO_SURFACE 0/157` 与 `0/33`、`VIDEO_UNAVAILABLE 5/4`；`INLINE_CODE_DIAG` 首份数据：light 选行=143 页=236 带=212 候选=326（top s21/p21），dark 选行=319 页=68 带=76 候选=444（top r319 s320/p320，r310 s20/p20）⇒ 真带在候选里但被 320pt 全宽带压过、ink 读 0，选择器留到下一轮按此数据改。R469 自身跑随本轮提交创建，收口读/下一轮读。
- **U-1769：① 腐烂与预检。** `HIDDEN_ARMS 表=334 可判=1050 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=247 covered=229 arms=633 bad=0`、`ARM_TOTAL files=340 arms=1116`。**旧表重钉**：本轮改 QuickPick/行来源的时间调用 ⇒ `mutate_r430_quickpick_time_column` 的 M1174/M1177 与 `mutate_r444_row_source` 的 M1220 针腐烂（预检 bad=3），按源码重钉后 r430 **5/5 CAUGHT**、r444 **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1770：② 产品：跨年时间标注。** 主列表与浮层都用 `ClipboardDateFormatters.sidebarTime` 的 `M月d日 HH:mm`，2025 与 2026 的同月同日看起来一模一样。新增 `TimestampYearPolicy.showsYear(for:relativeTo:)`：参照是**当前列表/候选里最新的一条**（不是挂钟），不同年才加 `yyyy年`。接线：`ClipboardDateFormatters.sidebarTime(for:reference:)`、QuickPick `rowTime(for:reference:)`、`HistoryRowView` 的 `timeReference`、`HistorySidebarView` 传 `filteredEntries` 最新时间。旧/新：`quickpick-cross-year` 两条都「6月15日 12:00」→ 旧行「2025年6月15日 12:00」、新行保持「6月15日 12:00」；`rows-cross-year` 主列表行宽 **新行右 234.5 / 旧行右 275.5 / 差 +41.0pt**。**4 张新帧**（quickpick/rows 各亮暗）、0 变化/缺失；基线 **280→284**；4 张逐张看过：年份只在旧行、无截断。
- **U-1771：③ 判据/刀。** `testCrossYearTimesCarryTheYear` 从产品浮层的 `quickPickTime` 读真字符串（亮暗各两条：带年 2025年 / 紧凑 6月15日）；`testMainRowsCrossYearTimeLineWidens` 量两行组件栈最后两行组的最右墨（+41.0pt ≥20）。纯策略 4 格（同年/跨年/无参照/formatter）。`M1275`（策略恒假）/`M1276`（恒真）⇒ **2/2 CAUGHT**；**首跑 M1275 逃了** —— 测试把「去重后只剩 1 个字符串」当 NOT-RUN，而策略恒假时两行串恰好相同 ⇒ 假绿；改成按**时间格数=2**断言后重跑 2/2。预检 247/229/633 bad=0。
- **U-1772：八步与电池。** build **0 告警**（`--build-tests`）；捕获卷 **284 帧**、`CHANGED=0 MISSING=0 ADDED=4`，更新后 `284/0/0/0`；全量 **1278/56/0**（468.2s，轻载；新增 6 条判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 468，`python3 scripts/product_streak.py --streak-for 468`，last=869e7de）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① `40736447466 ↔ 0774453`（cancelled）与 R469 自身跑（收口视网络）；② `INLINE_CODE_DIAG` 的选择器修复（数据已拿到，下一轮改）；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` runner 1x（settings-content-blank）；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–528 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 466 · R469（第 468 轮 · 2026-10-29）：跨年时间标注（旧两条「6月15日 12:00」→ 旧行「2025年6月15日 12:00」；主列表行宽差 +41.0pt；4 张新帧、基线 284）

主列表与浮层都用 `M月d日 HH:mm`，2025 与 2026 的同月同日分不清。新增 `TimestampYearPolicy`（参照=当前列表/候选最新一条，不同年才加 `yyyy年`），接 4 个产品文件；浮层两条只差一年的记录旧行读「2025年6月15日 12:00」、新行保持紧凑；主列表两行组件的最右墨差 +41.0pt。4 张新帧、0 变化，基线 284/0/0/0；全量 1278/56/0；build 0 告警；换装 ok/387=387；电池 683/5。旧表 M1174/M1177/M1220 因共享调用改行重钉，r430 5/5、r444 2/2；M1275/M1276 2/2（M1275 首跑被测试的去重闸门吞成 NOT-RUN，改成按时间格数断言后重跑）。⓪ push `0774453..00ff343` success、ahead=0；`40736447466` cancelled ⇒ NOT-RUN；`40740068763` failure 2 步仅 inline dark 3.0，Capture 15 帧变 MATERIAL_BLIND_NOT_RUN，设置轴 runner 具名 NOT-RUN；`INLINE_CODE_DIAG` 首份数据已拿到。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张新帧逐张看过：年份只在旧行、新行紧凑、无截断。 |
| 判据有效性 | 15/15 | 浮层真字符串 + 主列表行宽 +41.0pt；旧形状两边都紧凑；M1275/M1276 2/2。 |
| 假绿防御 | 14/15 | M1275 首跑被去重闸门吞成 NOT-RUN，已改成按时间格数断言；扣 1：R469 自身跑未读。 |
| 产品面推进 | 15/15 | 新类别（跨年时间标注）；4 个真实产品文件；Store 不动。 |
| 台账一致性 | 15/15 | U-1768…U-1772、D-465、284 帧/1278、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | cancelled 不读成绿；inline 数据只记账不改选择器；旧表重钉并复跑。 |
| 可复核性 | 15/15 | 字符串两条、+41.0pt、precheck 247/229/633、rot 334/1050、基线 284 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_465 = u"""## D-465 跨年时间以「当前列表最新一条」为参照，不按挂钟（R469）

- 背景：主列表/浮层都用 `M月d日 HH:mm`，2025 与 2026 的同月同日看起来一样；挂钟参照会让所有旧记录一起变宽（夹具 2025 记录在 2026 全带年份），而"同一份历史里最早那条是哪一年"才是扫读时会混的地方。
- 决定：新增 `TimestampYearPolicy.showsYear(for:relativeTo:)`，参照=当前列表/候选里最新的一条；不同年才用 `yyyy年M月d日 HH:mm`。接 `ClipboardDateFormatters`、QuickPick、`HistoryRowView`、`HistorySidebarView` 四处。
- 理由：同一年的历史保持紧凑；跨年边界唯一需要年份。参照按过滤后的集合走，搜索到只剩同一年时不继续跟看不见的记录。
- 兼容性/迁移：4 张新帧（quickpick/rows 亮暗）、0 变化；基线 280→284；旧表 M1174/M1177/M1220 重钉复跑。
- 边界：runner 的 1x 设置内容列仍平涂（与时间无关）；主列表整页的选中黑带使"两行都可见"的整页帧不可得 ⇒ 用两行组件栈作像素证人。
- 回滚：删 `TimestampYearPolicy` 与三处接线；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 跨年时间标注（旧两条「6月15日 12:00」→ 旧行「2025年6月15日 12:00」；主列表行宽差 +41.0pt；4 张新帧、基线 284）（R469 / 第 468 轮 / Round 466 / U-1768…U-1772 · 产品 4 文件 + 判据）

"""

BACKLOG_SECTION = u"""**526. `INLINE_CODE_DIAG` 首份数据：真带在候选里但被 320pt 全宽带压过、ink 读 0**（R469 读 `40740068763`）
    现象：light 选行=143 页=236 带=212 候选=326（top s21/p21），dark 选行=319 页=68 带=76 候选=444（top r319 s320/p320，r310 s20/p20）；dark 仍读 150/147/3.0。
    修法：下一轮按这份数据改选择器/ink 尺（先排除全宽 code-block 带，再解释真带 ink=0）；地板 4.5 不动。

**527. 跨年参照按过滤结果走**（R469 观察）
    现象：搜索到只剩同一年时，年份会从旧行消失；如果用户期望"整份历史"的年份，参照应取全量而不是过滤集。
    修法：先记录；要改就做成产品决定并补帧。

**528. 主列表整页跨年帧被选中黑带挡住**（R469 观察）
    现象：`HistorySidebarView` 的 List 选中行在离屏通道是黑带，整页两行不能同时可见；像素证人改用两行组件栈。
    修法：若要做整页证人，需要 capture seam 让选中底可关；先记录。
"""

STATE_SECTION = u"""## R469 状态（2026-10-29 · 本地 · 第 468 轮 / Round 466）：跨年时间标注（旧两条「6月15日 12:00」→ 旧行「2025年6月15日 12:00」；主列表行宽差 +41.0pt；4 张新帧、基线 284）；全量 1278/56/0（产品 4 文件 + 判据）

最后更新：2026-10-29（本地 · R469 / 第 468 轮 / Round 466）：主列表与浮层都用 `M月d日 HH:mm`，2025 与 2026 的同月同日分不清。新增 `TimestampYearPolicy.showsYear(for:relativeTo:)`：参照=当前列表/候选里最新一条（不是挂钟），不同年才加 `yyyy年`；接 4 个产品文件（`ClipboardDateFormatters`、`QuickPickController`、`HistoryRowViews`、`HistorySidebarView`）。旧/新：`quickpick-cross-year` 两条都「6月15日 12:00」→ 旧行「2025年6月15日 12:00」、新行紧凑；`rows-cross-year` 主列表行宽 **234.5 / 275.5 / +41.0pt**。**4 张新帧**（quickpick/rows 亮暗）、0 变化/缺失；基线 **284/0/0/0**；4 张逐张看过无截断。判据：`testCrossYearTimesCarryTheYear`（浮层真字符串）+ `testMainRowsCrossYearTimeLineWidens`（行宽 +41.0）+ 纯策略 4 格；`M1275/M1276` **2/2 CAUGHT**（M1275 首跑被测试的去重闸门吞成 NOT-RUN，改成按时间格数断言后重跑）。**旧表重钉**：M1174/M1177（r430 时间列）与 M1220（r444 行来源）因共享调用改行腐烂，重钉后 r430 **5/5**、r444 **2/2**、RESTORE_CLEAN。预检 **247/229/633 bad=0**、ARM **340/1116**、HIDDEN **334/1050 rot=0**。⓪：开工 HEAD=`00ff343`、origin/main=`0774453`、ahead=2；一次快进 push **`0774453..00ff343` success**、HEAD=origin/main=`00ff343`、**ahead=0**；`40736447466 ↔ 0774453` **job cancelled**（失败步骤 0）⇒ NOT-RUN；`40740068763 ↔ 00ff343` **failure 2 步**（唯一测试红 inline dark 3.0；Capture 15 帧变 `MATERIAL_BLIND_NOT_RUN`、设置轴 runner 具名 NOT-RUN）；已读 `VIDEO_SEEK 98/106`、`VIDEO_ALIGN 13.0`、`VIDEO_SURFACE 0/157` 与 `0/33`、`VIDEO_UNAVAILABLE 5/4`；`INLINE_CODE_DIAG` 首份数据 light 选行=143/页236/带212/候选326（top s21/p21）、dark 选行=319/页68/带76/候选444（top r319 s320/p320、r310 s20/p20）。全量 **1278/56/0**（468.2s，轻载）；捕获卷 **284 帧**；基线 **284/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 468，`python3 scripts/product_streak.py --streak-for 468`，last=869e7de）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `0774453..00ff343` success、ahead=0；R468 跑 cancelled ⇒ NOT-RUN；00ff343 跑 failure 2 步仅 inline dark 3.0，Capture 15 帧变 MATERIAL_BLIND_NOT_RUN，设置轴具名 NOT-RUN；INLINE_CODE_DIAG 首份数据已拿到。
② 产品：跨年时间标注（浮层/主列表；4 个产品文件；4 张新帧、基线 284）。
③ 判据：浮层真字符串 + 主列表行宽 +41.0；M1275/M1276 2/2；旧表 M1174/M1177/M1220 重钉并复跑；precheck 247/229/633；rot 334/1050。
④ 436：无 R469 新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 334 / 可判 1050 / rot 0。
⑥ 捕获 284 帧；基线 284/0/0/0；build 0 告警；换装 ok/387=387；全量 1278/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40736447466 ↔ 0774453`（cancelled）与 R469 自身跑（收口视网络）；② `INLINE_CODE_DIAG` 的选择器修复（数据已拿到，下一轮改）；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` runner 1x（settings-content-blank）；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–528 的其余未结项仍开。

下一轮（R470）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R469 主笔+追记 head 跑的全部失败步骤，重点 `CROSS_YEAR_TIME`（浮层两条）、`MAIN_ROWS_CROSS_YEAR`（+41.0）、`SETTINGS_HELPER_AXIS` 200/198/−2、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`INLINE_CODE_DIAG` 的选择器修复（真带 r310 s20/p20 vs 全宽 r319 s320/p320、ink=0；地板 4.5 不动）、`INLINE_CODE_PAD` 两档、`VIDEO_SEEK` 98/106、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE`、`VIDEO_UNAVAILABLE`、Capture gate 的 MATERIAL_BLIND_NOT_RUN、其余既有判据与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R469_REPORT_BULLET = u"""- **R469（跨年时间标注位）**：主列表与浮层都用 `M月d日 HH:mm`，2025 与 2026 的同月同日分不清。新增 `TimestampYearPolicy.showsYear(for:relativeTo:)`（参照=当前列表/候选最新一条，不是挂钟），接 `ClipboardDateFormatters`/QuickPick/`HistoryRowViews`/`HistorySidebarView` 4 个产品文件。旧/新：`quickpick-cross-year` 两条都「6月15日 12:00」→ 旧行「2025年6月15日 12:00」、新行紧凑；`rows-cross-year` 主列表行宽 **234.5 / 275.5 / +41.0pt**。**4 张新帧**（quickpick/rows 亮暗）、0 变化，基线 **280→284/0/0/0**；4 张逐张看过、无截断。判据：浮层真字符串 + 主列表行宽 + 纯策略 4 格；M1275/M1276 **2/2**（M1275 首跑被去重闸门吞成 NOT-RUN，改成按时间格数断言后重跑）。旧表 M1174/M1177/M1220 重钉，r430 **5/5**、r444 **2/2**。⓪ push `0774453..00ff343` success、ahead=0；`40736447466` cancelled ⇒ NOT-RUN；`40740068763` failure 2 步仅 inline dark 3.0，Capture 15 帧变 `MATERIAL_BLIND_NOT_RUN`，设置轴 runner 具名 NOT-RUN；`INLINE_CODE_DIAG` 首份数据已拿到。全量 **1278/56/0**（468.2s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 468 轮（R469" in audit: raise SystemExit("REFUSED AUDIT 已有 R469")
if u"## Round 466 · R469" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 466")
if u"## D-465" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-465")
if u"跨年时间标注" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**526." in backlog: raise SystemExit("REFUSED BACKLOG 已有 526")
if state.count(u"## R468 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R468 状态"))
U_CELL_OLD = u"U-31 … U-1767（R468 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R468 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_465 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R468 状态", STATE_SECTION + u"## R468 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1772（R469 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R468 节 ②", u"AGENT_STATE.md` 的 R469 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R469_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R469_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
