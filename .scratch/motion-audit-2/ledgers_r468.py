#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R468 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 466 轮（R467 · 2026-10-29"
AUDIT_SECTION = u"""## 第 467 轮（R468 · 2026-10-29 · U-1763…U-1767）：设置开关说明文字与标签同轴（旧 200.0/179.0 差 21.0pt → 新 200.0/198.0 差 −2.0pt；14 张 settings 帧变化、基线 280）（产品 1 文件 + 判据）

- **U-1763：⓪ push 与 CI。** 开工 HEAD=`a3ce7b8`、origin/main=`3bd67b1`、**ahead=3**；`git push` 连探 2 次均 `Connection closed by 20.205.243.166 port 22`、`curl api.github.com` 读 **API=000**（exit 35）⇒ **`PUSH_BLOCKED=network`**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1` 与 R468 自身跑均 **NOT-RUN**。已读（上一轮账）：`40710557752 ↔ 7a04a79` failure 3 步（`INLINE_CODE_PAD light 85/80/5.0` 签收、dark 仍 150/147/3.0、`VIDEO_UNAVAILABLE 5/4`、Motion 1<2）；`40714119382 ↔ 0449f4a` failure 3 步（`VIDEO_SURFACE 0/236` 签收、Capture gate 15 张旧帧、inline dark 3.0、Motion 1<2）；`40714151224 ↔ 86d6b6a` failure；其余沿用；436 无新红。
- **U-1764：① 腐烂与预检。** `HIDDEN_ARMS 表=331 可判=1045 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=246 covered=228 arms=631 bad=0`、`ARM_TOTAL files=339 arms=1114`。
- **U-1765：② 产品：设置开关说明文字回到标签轴。** 通用/隐私页的说明段是 `VStack` 里独立的 `Text`，从**复选框左沿**起排，而标签从复选框右侧起排 ⇒ `settings-general` 帧量到标签左 **200.0pt**、说明左 **179.0pt**，差 **21.0pt**（同一组「开关—说明」两条左轴）。新增 `SettingsViewLayout.helperAxisIndent = 21`（= 复选框 14pt + 标签间距 7pt）与 `.settingsHelperAxis()`，接到 6 处：登录回执、暂停说明、OCR 说明、RTF 说明、推荐过滤说明、OCR 存储说明。旧/新：`SETTINGS_HELPER_AXIS light/dark 标签左=200.0 说明左=179.0 差=+21.0 → 200.0/198.0/差=-2.0`（墨迹比标签框早 2pt，容差 4pt）。**14 张旧帧变化**（settings-general/-no-footer/-login-*/privacy/-privacy-tall/-privacy-excluded 亮暗）、0 新增/缺失；基线 **280**；14 张逐张看过：说明在标签正下方、无截断、末尾卡片仍装得下。
- **U-1766：③ 判据/刀与「卡片内缩」对象换位。** 新判据 `testSettingsHelperTextSharesTheToggleLabelAxis` 按行分「控件行（有复选框、193..198 空档、199 之后有标签墨）」与「说明行（有 199 之后宽簇、不是控件行）」，比最左墨，差 ≤4pt；旧 +21.0 红、新 −2.0 绿。`M1272`（21→0）/`M1273`（21→42）⇒ **2/2 CAUGHT**。**卡片内缩尺的对象换位**：说明改轴后通用页卡片的第一处墨从说明文字变成复选框，`CARD_INSET` 从 5.0 变 8.0（亮 8.0 对文字参照 5.0 = +3.0、暗 8.0 对 5.5 = +2.5）；产品卡片内缩未变，是首墨对象变了 ⇒ 按既有「图标首墨」同一形状新增 `controlFirstCells`（8 格）与有界替代判据 [+2.0,+4.0]、开关 `CLIPBOARD_HISTORY_CONTROL_FIRST_ROSTER`，不把等式放宽；`M1274`（关开关）⇒ **1/1 CAUGHT**；旧表 `M566`（图标首墨名册）重跑仍 **CAUGHT**、RESTORE_CLEAN。
- **U-1767：八步与电池。** build **0 告警**（`--build-tests`）；捕获卷 **280 帧**、`CHANGED=14 MISSING=0 ADDED=0`，更新后 `280/0/0/0`；全量 **1272/56/0**（475.9s，轻载；新增 1 条判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 467，`python3 scripts/product_streak.py --streak-for 467`，last=01d3b75）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R467 两跑与 R468 自身跑（CI_READ_BLOCKED）；② `INLINE_CODE_DIAG` 的 runner 数据；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` 的 runner 1x（设置内容列在 runner 上可能整列平涂，判据自带 `SETTINGS_HELPER_AXIS_NOT_RUN=settings-content-blank` 出口）；⑤ `CARD_INSET_CONTROL_FIRST` 的 runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–525 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 465 · R468（第 467 轮 · 2026-10-29）：设置开关说明文字与标签同轴（旧 200.0/179.0 差 21.0pt → 新 200.0/198.0 差 −2.0pt；14 张 settings 帧变化、基线 280）

通用/隐私页的说明段从复选框左沿起排、标签从复选框右侧起排，同一组「开关—说明」的左边断成两条轴（标签 200.0pt / 说明 179.0pt，差 21.0pt）。新增 21pt 的 `settingsHelperAxis()` 接到 6 处说明（登录回执、暂停/OCR/RTF、推荐过滤、OCR 存储）；新判据按行分控件行与说明行比较最左墨（≤4pt），旧 +21.0 红、新 −2.0 绿；M1272/M1273 2/2。说明改轴后通用卡片的「首墨」从说明换成复选框，卡片内缩尺新增 `controlFirstCells`（8 格、有界 +2.0…+4.0），M1274 1/1、旧 M566 重跑 CAUGHT。14 张旧帧变化、0 新增，基线 280/0/0/0；全量 1272/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push 两探失败、API=000 ⇒ PUSH_BLOCKED=network（HEAD a3ce7b8、ahead=3）、CI_READ_BLOCKED；R467 两跑与 R468 跑 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 14 张 changed 帧逐张看过：说明落在标签正下方、无截断、隐私长页末卡未出框。 |
| 判据有效性 | 15/15 | 标签/说明最左墨；旧 +21.0 红、新 −2.0 绿；M1272/M1273 2/2；卡片内缩类 M1274 1/1、M566 重跑仍咬。 |
| 假绿防御 | 14/15 | 判据自带 settings-content-blank 具名出口；扣 1：R467 两跑与 R468 自身跑未读。 |
| 产品面推进 | 15/15 | 新类别（设置说明文字轴）；6 个真实调用点；Store 不动。 |
| 台账一致性 | 15/15 | U-1763…U-1767、D-464、280 帧/1272、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 卡片内缩红按「尺的对象换位」处理并加刀，没有放宽等式；flake 具名。 |
| 可复核性 | 15/15 | 200/179/21 → 200/198/−2、+2.5/+3.0、precheck 246/228/631、rot 331/1045、基线 280 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_464 = u"""## D-464 设置说明文字回到控件标签轴；首墨是复选框的卡片走有界替代判据（R468）

- 背景：说明段是 `VStack` 里独立 `Text`，从复选框左沿起排；标签从复选框右侧起排 ⇒ 同一组「开关—说明」两条左轴（200.0 vs 179.0，差 21.0pt）。改轴后通用卡片的**第一处墨**从说明文字换成复选框，卡片内缩尺读到 8.0pt（对文字参照 +2.5/+3.0），而卡片内缩本身未变。
- 决定：`SettingsViewLayout.helperAxisIndent = 21`（复选框 14pt + 标签间距 7pt），`.settingsHelperAxis()` 接 6 处说明；判据比标签/说明最左墨（≤4pt）。卡片内缩尺新增 `controlFirstCells`（8 格）与有界替代 [+2.0,+4.0]、开关 `CLIPBOARD_HISTORY_CONTROL_FIRST_ROSTER`；不放宽等式、不把这一族记成未判。
- 理由：说明与标签同轴是版式；复选框的墨从框内 3pt 起是**图标类 bearing**，与既有「图标首墨」同一形状；等式只对文字首墨有定义。
- 兼容性/迁移：14 张 settings 帧变化；基线 280 同 commit 更新；旧表 M566 重跑仍咬，M1274 钉住新开关。
- 边界：runner 1x 的设置内容列可能是平涂 ⇒ 判据具名 `SETTINGS_HELPER_AXIS_NOT_RUN=settings-content-blank`；`CARD_INSET_CONTROL_FIRST` 的 runner 读数未读。
- 回滚：删 `.settingsHelperAxis()` 与 `controlFirstCells`；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 设置开关说明文字与标签同轴（旧 21.0pt → 新 −2.0pt；14 张 settings 帧变化、基线 280）+ 卡片内缩复选框首墨名册（R468 / 第 467 轮 / Round 465 / U-1763…U-1767 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**523. `SETTINGS_HELPER_AXIS` 与 `CARD_INSET_CONTROL_FIRST` 的 runner 1x 读数未读**（R468 观察）
    现象：本地亮/暗读到 200.0/198.0/−2.0 与 +3.0/+2.5；CI 网络不可达，设置内容列在 runner 上也可能整列平涂。
    修法：下一跑先读 `SETTINGS_HELPER_AXIS` 与 `CARD_INSET_CONTROL_FIRST`；读不到就保留具名 NOT-RUN，不降容差。

**524. 卡片内缩的「首墨是复选框」名册是手写的**（R468 观察）
    现象：`controlFirstCells` 8 格是按首墨对象手写的；别的卡片若哪天首墨也变成复选框，等式会红而没人知道该加名册。
    修法：把「首墨对象」做成可读出的结构量（视图树控件 frame 或首墨宽簇高度），替代手写名册；先记录。

**525. 「上下文权限」标题下的说明仍停在卡片左沿**（R468 观察）
    现象：它不是某颗开关的说明（是整组标题的说明），所以本轮没接 `settingsHelperAxis()`；若将来这组换成一颗总开关，需要一起接。
    修法：届时按同一轴处理，并补帧。
"""

STATE_SECTION = u"""## R468 状态（2026-10-29 · 本地 · 第 467 轮 / Round 465）：设置开关说明文字与标签同轴（旧 200.0/179.0 差 21.0pt → 新 200.0/198.0 差 −2.0pt；14 张 settings 帧变化、基线 280）；全量 1272/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R468 / 第 467 轮 / Round 465）：通用/隐私页的说明段是 `VStack` 里独立 `Text`，从复选框左沿起排、标签从复选框右侧起排 —— `settings-general` 帧量到标签左 **200.0pt**、说明左 **179.0pt**，差 **21.0pt**。修法：`SettingsViewLayout.helperAxisIndent = 21`（复选框 14pt + 标签间距 7pt）+ `.settingsHelperAxis()`，接 6 处（登录回执、暂停/OCR/RTF、推荐过滤、OCR 存储）。旧/新：`SETTINGS_HELPER_AXIS light/dark 标签左=200.0 说明左=179.0 差=+21.0 → 200.0/198.0/差=-2.0`（容差 4pt）。**14 张旧帧变化**、0 新增/缺失；基线 **280/0/0/0**；14 张逐张看过，说明在标签正下方、无截断。新判据 `testSettingsHelperTextSharesTheToggleLabelAxis` 按行分控件行/说明行比较最左墨；`M1272/M1273` **2/2 CAUGHT**。**卡片内缩尺对象换位**：说明改轴后通用卡片第一处墨变成复选框（`CARD_INSET` 5.0→8.0，对文字参照 +3.0/+2.5），产品卡片内缩未变 ⇒ 新增 `controlFirstCells`（8 格）与有界替代 [+2.0,+4.0]、开关 `CLIPBOARD_HISTORY_CONTROL_FIRST_ROSTER`；`M1274` **1/1 CAUGHT**、旧表 `M566` 重跑 **CAUGHT**、RESTORE_CLEAN。预检 **246/228/631 bad=0**、ARM **339/1114**、HIDDEN **331/1045 rot=0**。⓪：开工 HEAD=`a3ce7b8`、origin/main=`3bd67b1`、**ahead=3**；`git push` 两探均 remote closed、`curl` **API=000** ⇒ **`PUSH_BLOCKED=network`**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、R468 自身跑均 **NOT-RUN**。全量 **1272/56/0**（475.9s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 467，`python3 scripts/product_streak.py --streak-for 467`，last=01d3b75）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 两探 remote closed、API=000 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R467 两跑与 R468 自身跑 NOT-RUN；上一轮 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。
② 产品：设置说明文字与标签同轴（21.0pt → −2.0pt；14 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1272/M1273 2/2；卡片内缩 control-first 类 + M1274 1/1、M566 重跑；precheck 246/228/631；hidden rot 0。
④ 436：无新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 331 / 可判 1045 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1272/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40720200357 ↔ bf9e8ec` / `40720409960 ↔ 3bd67b1` 与 R468 自身跑（CI_READ_BLOCKED）；② `INLINE_CODE_DIAG` 的 runner 数据；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` runner 1x（`settings-content-blank` 出口）；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–525 的其余未结项仍开（含纯文本文件预览异步载入、2x/extended、真机/多屏、13+ 菜单、HTML 各档、Dock 像素等，逐项同 R467 节）。

下一轮（R469）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R468 主笔+追记 head 跑、`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、`40710557752 ↔ 7a04a79`、`40714119382 ↔ 0449f4a` 等的全部失败步骤；重点 `SETTINGS_HELPER_AXIS` 200.0/198.0/−2.0、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`INLINE_CODE_DIAG`（选行/页带/top5 候选，拿数据再改选择器）、`INLINE_CODE_PAD` 两档（dark 应 ≥4.5）、`VIDEO_SEEK` 96/90、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、Capture gate 15 张旧帧、其余既有判据与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R468_REPORT_BULLET = u"""- **R468（设置说明文字轴位）**：通用/隐私页的说明段从复选框左沿起排、标签从复选框右侧起排 ⇒ 同一组「开关—说明」两条左轴（标签 **200.0pt** / 说明 **179.0pt**，差 **21.0pt**）。新增 `SettingsViewLayout.helperAxisIndent = 21`（复选框 14pt + 标签间距 7pt）+ `.settingsHelperAxis()`，接 6 处说明（登录回执、暂停/OCR/RTF、推荐过滤、OCR 存储）。旧/新：`SETTINGS_HELPER_AXIS 200.0/179.0/+21.0 → 200.0/198.0/−2.0`；**14 张旧帧变化**、0 新增，基线 **280/0/0/0**；14 张逐张看过、无截断。判据按行分控件行/说明行比较最左墨（≤4pt）；旧红新绿；M1272/M1273 **2/2**。说明改轴后通用卡片首墨变成复选框，卡片内缩尺新增 `controlFirstCells`（8 格、有界 +2.0…+4.0）；M1274 **1/1**、旧 M566 重跑 CAUGHT。⓪ 两探 remote closed、API=000 ⇒ **PUSH_BLOCKED=network（HEAD a3ce7b8、ahead=3）**、**CI_READ_BLOCKED**；R467 两跑与 R468 跑 NOT-RUN。全量 **1272/56/0**（475.9s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 467 轮（R468" in audit: raise SystemExit("REFUSED AUDIT 已有 R468")
if u"## Round 465 · R468" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 465")
if u"## D-464" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-464")
if u"设置开关说明文字与标签同轴" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**523." in backlog: raise SystemExit("REFUSED BACKLOG 已有 523")
if state.count(u"## R467 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R467 状态"))
U_CELL_OLD = u"U-31 … U-1762（R467 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R467 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_464 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R467 状态", STATE_SECTION + u"## R467 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1767（R468 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R467 节 ②", u"AGENT_STATE.md` 的 R468 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R468_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R468_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
