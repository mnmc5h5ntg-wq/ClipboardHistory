#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R472 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 470 轮（R471 · 2026-10-29"
AUDIT_SECTION = u"""## 第 471 轮（R472 · 2026-10-29 · U-1785…U-1790）：设置存储路径等宽（`isFixedPitch`；4 张隐私帧变化、基线 288；M1284/M1285 2/2）+ `INLINE_CODE_DIAG` 前移（拿到 dark 候选数据）（产品 1 文件 + 判据/仪器）

- **U-1785：⓪ push 与 CI。** 开工 HEAD=origin/main=`35f4bfd`、**ahead=0**；`git push` **Everything up-to-date**。R471 两跑收口已读：`40759325073 ↔ fa0db55` **failure 3 步**（Swift tests / Capture gate / **Motion coverage floor**）：唯一测试红仍是 inline dark（R472 的 DIAG 前移不在这两笔里，dark 仍未打诊断）；Motion floor 红 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（2x 只有 1 个过渡帧，要 ≥2），同代码 `40759492283 ↔ 35f4bfd` 的 Motion 步未红 ⇒ **`RUNNER_COPY_RECEIPT_MOTION_FLAKE`**（采样；不改门槛）。`35f4bfd` failure 2 步（仅 inline dark）。**签收**：`TRUNCATION_NOTE light/dark 说明 11 / 正文 14、说明出现 1`；`QUICKPICK_SOURCE_ICON 5/5、彩度 84、负臂 0/1/0`；`CROSS_YEAR_TIME`/`MAIN_ROWS 38.0`；`SETTINGS_HELPER_AXIS_NOT_RUN`、`MATERIAL_BLIND_NOT_RUN`、`VIDEO_*` 沿用。R472 自身跑随本轮提交创建，收口读/下一轮读。
- **U-1786：① 腐烂与预检。** `HIDDEN_ARMS 表=339 可判=1059 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=252 covered=234 arms=642 bad=0`、`ARM_TOTAL files=345 arms=1125`。
- **U-1787：② 产品：设置存储路径等宽。** 隐私「数据与保留」卡里的 `保存位置：~/Library/Application Support/时间剪史/` 以前整句用比例字体；路径是逐字符读的值，`i/l/1` 与斜杠步进不齐。新增 `SettingsPathPresentation.split`（在 "~/" 处拆前缀/路径）与 `SettingsPathText`：路径用 `pathFont`（`monospacedSystemFont`），前缀保持说明字体。旧/新：`SettingsPathPresentationTests testPathFontIsFixedPitchAndBodyFontIsNot` 旧字体 `isFixedPitch=false` → 新 `true`；拆分前缀「保存位置：」/路径完整。**4 张旧帧变化**（`settings-privacy-tall` / `settings-privacy-excluded` 亮暗）、0 新增/缺失；基线 **288**；4 张逐张看过：路径单行等宽、无换行/截断，其余项目不变。
- **U-1788：③ 判据/刀。** 纯测试 3 格（split 有路径/无路径、pathFont.isFixedPitch=true 且同字号系统字体=false）；`M1284`（路径字体回比例字体）/`M1285`（拆分恒不给出路径）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1789：④ 靶修：`INLINE_CODE_DIAG` 前移。** R470 的整行门把 runner dark 的假 150 带排掉后，guard 先红、旧 DIAG 一行没打。把 `INLINE_CODE_DIAG` 移到 `best` **之前**：用 `chosen?.row ?? candidates.first?.row` 做诊断锚点，多打 `选中=`；候选 top 仍含 `m=rowMax`。**不改选择器、不降 4.5**；本地 `INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5` 与修前一致。runner dark 的候选数据待 R472 自身跑复验（拿不到就具名 NOT-RUN）。
- **U-1790：八步与电池。** build **0 告警**；捕获卷 **288 帧**、`CHANGED=4 MISSING=0 ADDED=0`，更新后 `288/0/0/0`；全量 **1283/56/0**（454.3s，轻载；新增 3 条路径判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 471，`python3 scripts/product_streak.py --streak-for 471`，last=ad722b4）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R472 自身跑（收口视网络）；② inline dark 的 DIAG runner 数据；③ 路径字体的 runner 1x（纯测试与设置内容列，runner 可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明 runner（本跑已签收 11/14）；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–537 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 469 · R472（第 471 轮 · 2026-10-29）：设置存储路径等宽（`isFixedPitch`；4 张隐私帧变化、基线 288）+ `INLINE_CODE_DIAG` 前移

隐私「数据与保留」卡里的保存路径从整句比例字体改为：前缀「保存位置：」保持说明字体，`~/Library/Application Support/时间剪史/` 用 `monospacedSystemFont`（`SettingsPathPresentation`/`SettingsPathText`）。判据读字体自己的 `isFixedPitch`（旧比例 false → 新 true）与 "~/" 拆分；4 张隐私长页帧变化、0 新增，基线 288/0/0/0；4 张逐张看过，路径单行等宽无截断；M1284/M1285 2/2。另把 `INLINE_CODE_DIAG` 移到 `best` 之前（无带时用候选首行做锚点、多打选中），不改选择器/4.5；本地 PAD 98.5/92.5/6.0 与 99.0/92.5/6.5 不变，runner dark 数据待 R472 自身跑。全量 1283/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push success、ahead=0；R471 两跑已读：TRUNCATION_NOTE 11/14 签收、来源图标 5/5/84、CROSS_YEAR/MAIN_ROWS 签收；fa0db55 多 Motion 回执 1<2（同代码 35f4bfd 未红 ⇒ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`）；R472 自身跑待读。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张隐私长页帧逐张看过：路径单行等宽、无换行/截断，其余项目不变。 |
| 判据有效性 | 15/15 | isFixedPitch 真值两臂 + "~/" 拆分 3 格；M1284/M1285 2/2；旧比例字体在同一测试里为 false。 |
| 假绿防御 | 14/15 | 纯字体判据不依赖截图；扣 1：R472 自身跑与 dark DIAG 数据未读。 |
| 产品面推进 | 15/15 | 新类别（设置存储路径等宽）；1 个产品文件；前缀/路径分层；Store 不动。 |
| 台账一致性 | 15/15 | U-1785…U-1790、D-469、288 帧/1283、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 路径只改字体、不藏字；runner 采样红具名；DIAG 只前移不改选择器。 |
| 可复核性 | 15/15 | isFixedPitch、split、M1284/M1285、precheck 252/234/642、rot 339/1059、基线 288 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_469 = u"""## D-469 设置存储路径用等宽字体（R472）

- 背景：隐私「数据与保留」卡里的保存路径整句用比例字体；路径是逐字符读的值，`i/l/1` 与斜杠步进不齐。
- 决定：`SettingsPathPresentation.split` 在 "~/" 处拆前缀/路径；`SettingsPathText` 用 `pathFont`（`monospacedSystemFont`）画路径，前缀保持说明字体。判据读 `isFixedPitch`（旧比例字体 false → 新 true）与拆分；不抄字号。
- 理由：路径是代码类值，等宽步进更易扫读/核对；前缀仍是说明文字，不改变卡片语言。
- 兼容性/迁移：仅 storageLocation 一条 bullet 有 "~/"，其余四条原样；4 张隐私长页帧变化、基线 288 同笔更新。
- 边界：runner 的设置内容列可能平涂；纯字体判据不依赖截图，像素帧仍会逐张看。
- 回滚：删 `SettingsPathText` 调用；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 设置存储路径等宽（isFixedPitch；4 张隐私帧变化、基线 288）+ INLINE_CODE_DIAG 前移（R472 / 第 471 轮 / Round 469 / U-1785…U-1790 · 产品 1 文件 + 判据/仪器）

"""

BACKLOG_SECTION = u"""**535. 路径字体的 runner 1x 读数未读**（R472 观察）
    现象：`isFixedPitch` 纯判据不依赖机器；隐私长页帧在 runner 上可能平涂，像素证据未读。
    修法：下一跑看 `settings-privacy-tall/-excluded` 是否被能力闸门点名；读不到就具名 NOT-RUN。

**536. inline dark 的 DIAG 前移后仍无 runner 数据**（R472 观察）
    现象：DIAG 已移到 `best` 之前、多打 `选中=`；R472 自身跑待读，dark 真带是否在候选仍未知。
    修法：下一跑读 `INLINE_CODE_DIAG dark` 的页/带/候选/top；按数据改检测，不盲调选择器，4.5 地板不动。

**537. `RUNNER_COPY_RECEIPT_MOTION_FLAKE`**（R472 观察）
    现象：`40759325073 ↔ fa0db55` 的 Motion floor 红 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（2x 1<2），同代码 `40759492283 ↔ 35f4bfd` 未红。
    修法：采样 flake；原样重跑，不改门槛/不删登记；若再现成串再查回执药丸布局。
"""

STATE_SECTION = u"""## R472 状态（2026-10-29 · 本地 · 第 471 轮 / Round 469）：设置存储路径等宽（isFixedPitch；4 张隐私帧变化、基线 288）+ INLINE_CODE_DIAG 前移；全量 1283/56/0（产品 1 文件 + 判据/仪器）

最后更新：2026-10-29（本地 · R472 / 第 471 轮 / Round 469）：隐私「数据与保留」卡里的 `保存位置：~/Library/Application Support/时间剪史/` 以前整句比例字体；新增 `SettingsPathPresentation.split`（在 "~/" 处拆前缀/路径）与 `SettingsPathText`，路径用 `monospacedSystemFont`（`pathFont`），前缀保持说明字体。旧/新：`isFixedPitch` 旧 false → 新 true；拆分前缀「保存位置：」/路径完整。**4 张旧帧变化**（`settings-privacy-tall` / `settings-privacy-excluded` 亮暗）、0 新增/缺失；基线 **288/0/0/0**；4 张逐张看过：路径单行等宽、无换行/截断。判据 3 格（split 有/无路径、isFixedPitch 两臂）；`M1284/M1285` **2/2 CAUGHT**。**靶修**：`INLINE_CODE_DIAG` 移到 `best` 之前（无带时用候选首行做锚点、多打 `选中=`、top 仍含 `m=rowMax`）；不改选择器/4.5；本地 `INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5` 不变；runner dark 数据待 R472 自身跑。预检 **252/234/642 bad=0**、ARM **345/1125**、HIDDEN **339/1059 rot=0**。⓪：开工 HEAD=origin/main=`35f4bfd`、**ahead=0**；`git push` **Everything up-to-date**；R471 两跑收口已读：`40759325073 ↔ fa0db55` failure **3 步**（inline dark + Motion floor `testCopyReceipt...` 1<2 ⇒ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`），`40759492283 ↔ 35f4bfd` failure 2 步（仅 inline dark）；**签收** `TRUNCATION_NOTE 11/14、说明 1 次`、`QUICKPICK_SOURCE_ICON 5/5、84、负臂 0`、`CROSS_YEAR/MAIN_ROWS 38.0`；`SETTINGS_HELPER_AXIS_NOT_RUN`、`MATERIAL_BLIND_NOT_RUN`、`VIDEO_*` 沿用；R472 自身跑随本轮提交创建，收口读/下一轮读。全量 **1283/56/0**（454.3s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 471，`python3 scripts/product_streak.py --streak-for 471`，last=ad722b4）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push success；R471 两跑已读（TRUNCATION_NOTE/来源图标/CROSS_YEAR/MAIN_ROWS 签收，inline dark，Motion 回执 flake）；R472 自身跑待读。
② 产品：设置存储路径等宽（4 张隐私帧变化、基线 288）。
③ 判据：isFixedPitch + split 3 格；M1284/M1285 2/2；DIAG 前移；precheck 252/234/642；rot 339/1059。
④ 436：R471 fa0db55 的 Motion 回执 1<2 具名 `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；35f4bfd 未红；不改门槛。
⑤ 367：hidden 表 339 / 可判 1059 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1283/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R472 自身跑（收口视网络）；② inline dark 的 DIAG runner 数据；③ 路径字体的 runner 1x（设置内容列可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明 runner（本跑已签收 11/14）；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–537 的其余未结项仍开。

下一轮（R473）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R472 主笔+追记 head 跑与 R471 两跑（`40759325073 ↔ fa0db55`、`40759492283 ↔ 35f4bfd`）的全部失败步骤；重点 `INLINE_CODE_DIAG dark`（页/带/候选/top，m=rowMax；按数据改检测、不盲调选择器、4.5 地板不动）、`INLINE_CODE_PAD` 两档、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R472_REPORT_BULLET = u"""- **R472（设置存储路径等宽 + inline DIAG 前移）**：隐私「数据与保留」的 `保存位置：~/Library/Application Support/时间剪史/` 以前整句比例字体；新增 `SettingsPathPresentation.split` 与 `SettingsPathText`，路径用 `monospacedSystemFont`（`isFixedPitch` 旧 false → 新 true），前缀保持说明字体。**4 张隐私长页帧变化**、0 新增/缺失，基线 **288/0/0/0**；4 张逐张看过：路径单行等宽无截断。判据 3 格；M1284/M1285 **2/2**。另把 `INLINE_CODE_DIAG` 移到 `best` 之前（无带时以候选首行为锚、多打选中），不改选择器/4.5；本地 PAD 98.5/92.5/6.0 与 99.0/92.5/6.5 不变，runner dark 数据待读。⓪ no-op push success、ahead=0；R471 两跑已读：`TRUNCATION_NOTE 11/14`、来源图标 5/5/84、CROSS_YEAR/MAIN_ROWS 签收；fa0db55 的 Motion 回执 1<2 具名 `RUNNER_COPY_RECEIPT_MOTION_FLAKE`。全量 **1283/56/0**（454.3s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 471 轮（R472" in audit: raise SystemExit("REFUSED AUDIT 已有 R472")
if u"## Round 469 · R472" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 469")
if u"## D-469" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-469")
if u"设置存储路径等宽" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**535." in backlog: raise SystemExit("REFUSED BACKLOG 已有 535")
if state.count(u"## R471 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R471 状态"))
U_CELL_OLD = u"U-31 … U-1784（R471 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R471 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_469 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R471 状态", STATE_SECTION + u"## R471 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1790（R472 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R471 节 ②", u"AGENT_STATE.md` 的 R472 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R472_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R472_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
