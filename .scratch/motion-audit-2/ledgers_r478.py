#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R478 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 476 轮（R477 · 2026-10-29"
AUDIT_SECTION = u"""## 第 477 轮（R478 · 2026-10-29 · U-1833…U-1838）：文件兜底态补父目录路径（4 张旧帧变化、基线 294；M1300/M1301 2/2）+ R462/R463 旧表重锚（M1260 退役为负向证人）（产品 1 文件 + 判据）

- **U-1833：⓪ push 与 CI。** 开工 `git push` **Everything up-to-date**、HEAD=origin/main=`7a79987`、**ahead=0**。R477 跑 `40797827495 ↔ 0fd3ec0` 与补记跑 `40797866181 ↔ 7a79987` 读时 **in_progress（结论空）⇒ NOT-RUN**；R476 跑 `40791382232 ↔ 599ec98` 三步失败（sources 时序、inline light 1.0、幻影 396、冲突平涂）与 R475/R474/R473/R472/R471 的失败步骤沿用已读。R477 跑的 `INLINE_CODE_PAD`/`QUICKPICK_GREY_BAND`/`QUICKPICK_PIN`/`SHORTCUT_CONFLICT` **均未读到** ⇒ 三处修复的 runner 复验仍具名 NOT-RUN。436 无 R478 新跑；最后已知 `MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=0`（R476 跑）。
- **U-1834：① 腐烂与预检。** `HIDDEN_ARMS 表=347 可判=1075 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=260 covered=242 arms=658 bad=0`、`ARM_TOTAL files=353 arms=1141`。R478 把文件名包进 VStack 后两把旧刀需重钉：`M1262/M1263`（占位图标色）原先命中共享的 `.foregroundStyle` 行，现把针改成带 `doc.fill` 与 R463 注释的整段（**2/2 CAUGHT**）；`M1260`（撤文件名四修饰）在新的 VStack padding 下**不再越界** ⇒ 退役为负向证人（期望 ESCAPED、实测 ESCAPED），`M1261`（撤内边距）仍 **CAUGHT**，R462 表 **2/2 符合期望**。
- **U-1835：② 产品：文件兜底态补父目录路径。** 缺陷形状（`detail-file-fallback-nothumb` 直看）：兜底态只重复一遍文件名（详情头部已经有一份），用户看不到文件在哪；视频不可读态至少有 Finder 出口，普通文件兜底态连位置都没有。修法：`DetailFileView.fallbackView` 在文件名下补一行父目录（11pt、secondaryLabelColor、单行中间截断、与文件名同中轴），长文件名不再独占一整块。旧/新：**4 张旧帧变化**（两个兜底夹具 × 亮暗）、0 新增/缺失；基线 **294/0/0/0**；逐张看过：路径是稳定的用户路径 `/Users/tester/Desktop`、中间截断、不压浮层。读数（`FALLBACK_PATH`）：图标带下方最宽一行 **113.0pt**（旧形状里这一行是文件名本身，约 60pt），两档同形。
- **U-1836：③ 判据与刀。** 新判据 `testFallbackFileShowsWhereTheFileLives` 读同一张帧：先找图标带，再在其下找最宽一行，要求 ≥90pt（文件名约 60pt）；它不是数"多了一行"（4pt 间距在 1x 可能粘行）。刀：`M1300`（整段删掉路径）、`M1301`（路径置空串）**2/2 CAUGHT**、RESTORE_CLEAN。**帧稳定性的自伤**：第一版直接用 `preview.url` 的父目录，帧里出现捕获目录 `/var/folders/...` ⇒ 每一跑路径都不同；加捕获缝 `fallbackParentPathForCapture`（产品默认 nil 读真实路径，夹具写稳定用户路径）后重捕，4 帧才可基线化。
- **U-1837：④ 既有面。** R462 表的负向证人 `M1260` 记录的是"VStack padding 已接管窗格边"（旧刀被掩蔽，不硬凑 CAUGHT）；`M1261` 仍钉内边距。R463 的 `M1262/M1263` 因共享色行重锚后 2/2。`detail-file-fallback-nothumb`/`longname` 的路径行与文件名同轴，未影响头部/浮层/分隔线。
- **U-1838：八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **294 帧**、`CHANGED=4 MISSING=0 ADDED=0`，更新后 `294/0/0/0`；全量 **1295/56/0**（453.6s，轻载；新增 1 条兜底路径判据）；换装 `ok / SHA_MATCH=1 / 387=387`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 477，`python3 scripts/product_streak.py --streak-for 477`，last=0fd3ec0）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R477 两跑（in_progress）；② inline padding 池/幻影 8 行/图钉/冲突的 runner 复验（仍未读到）；③ 兜底路径的 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 回执 flake；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–553 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 475 · R478（第 477 轮 · 2026-10-29）：文件兜底态补父目录路径（4 张旧帧变化、基线 294）+ R462/R463 旧表重锚

兜底态只重复一遍文件名（头部已有一份），用户看不到文件在哪。`DetailFileView.fallbackView` 在文件名下补一行父目录（11pt、secondary、单行中间截断、同中轴）；4 张旧帧变化、0 新增，基线 294/0/0/0；`FALLBACK_PATH` 图标下最宽行 113pt（旧形状是文件名约 60pt）。第一版直接用捕获临时路径，帧每跑都不同 ⇒ 加 `fallbackParentPathForCapture` 捕获缝（产品读真实路径、夹具写 `/Users/tester/Desktop`）后重捕。M1300（删）/M1301（置空）2/2；R462 M1260 在新 VStack padding 下不再越界 ⇒ 退役为负向证人，M1261 仍 CAUGHT；R463 M1262/M1263 因共享色行重锚后 2/2。预检 260/242/658、rot 347/1075、ARM 353/1141。全量 1295/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；R477 两跑 in_progress ⇒ NOT-RUN；R477 的 inline/phantom/pin/conflict 复验仍未读到。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张变化帧逐张看过：路径在文件名下、同轴、中间截断、不压浮层；长名帧文件名仍完整。 |
| 判据有效性 | 15/15 | 同一帧读图标下最宽行（113pt vs 文件名 ~60pt），不数行数；M1300/M1301 2/2。 |
| 假绿防御 | 14/15 | 第一版路径用捕获临时目录 ⇒ 帧每跑不同，当场加捕获缝后重捕；扣 1：R477 的 runner 复验仍未读到。 |
| 产品面推进 | 15/15 | 新类别（兜底态所在路径）；1 个产品文件；4 张旧帧变化；Store 不动。 |
| 台账一致性 | 15/15 | U-1833…U-1838、D-475、294 帧/1295、387=387 都来自命令与测试；M1260 退役有读数。 |
| 交付诚实性 | 15/15 | 旧刀不咬就退役为负向证人，不硬凑 CAUGHT；帧里的临时路径自己抓住并改缝。 |
| 可复核性 | 15/15 | 4 张帧、113pt、M1300/M1301、M1260 的 ESCAPED 与 M1261 的 CAUGHT、precheck 260/242/658、rot 347/1075、基线 294 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_475 = u"""## D-475 文件兜底态补父目录；帧里不许出现捕获目录的临时路径；旧刀被新 padding 掩蔽时退役为负向证人（R478）

- 背景：兜底态只重复文件名（头部已有一份），用户看不到文件在哪；第一版直接用 `url` 父目录，帧里出现 `/var/folders/...`，每一跑都不同，无法基线化；R478 把文件名包进 VStack 后，R462 的 M1260（撤四修饰）不再越界。
- 决定：`DetailFileView.fallbackView` 在文件名下补父目录（11pt、secondaryLabelColor、单行中间截断、同中轴）；加捕获缝 `fallbackParentPathForCapture`（产品默认 nil 读真实路径，夹具写 `/Users/tester/Desktop`）；R462 的 M1260 期望改为 ESCAPED 并注明被 VStack padding 掩蔽，M1261 仍 CAUGHT；R463 M1262/M1263 重锚到带图标的整段。
- 理由：位置是兜底态唯一缺的信息；帧基线必须确定（临时路径不可入帧）；刀不咬时不能硬凑 CAUGHT，要么换被测对象，要么诚实退役。
- 兼容性/迁移：4 张旧帧变化、0 新增，基线 294 同笔更新；捕获缝只在夹具写，产品路径不变。
- 边界：兜底路径的 runner 1x/dark 未签收；R477 的 inline/phantom/pin/conflict runner 复验仍未读到。
- 回滚：删路径行、判据与捕获缝；R462 表恢复 M1260 为 CAUGHT 会回到"刀被掩蔽却假装有牙"。
"""

CHANGELOG_SECTION = u"""### 文件兜底态补父目录路径（4 张旧帧变化、基线 294）+ 捕获路径缝 + R462/R463 旧表重锚（R478 / 第 477 轮 / Round 475 / U-1833…U-1838 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**553. R477 跑对 inline padding 池/幻影 8 行/图钉/冲突的复验仍未读到**（R478 观察）
    现象：R477 跑 `40797827495 ↔ 0fd3ec0` 与补记跑 `40797866181 ↔ 7a79987` 读时 in_progress（结论空）；这些修复只有本机读数。
    修法：读 R478 跑（或 R477 收口跑）的 `INLINE_CODE_PAD`/`QUICKPICK_GREY_BAND`/`QUICKPICK_PIN`/`SHORTCUT_CONFLICT(_NOT_RUN)`；仍红按读数继续，4.5 与 150 不动。

**554. 兜底态父目录路径的 runner 1x/dark 未签收**（R478 观察）
    现象：本机两档 `FALLBACK_PATH` 都是 113pt；runner 1x 的 11pt 字与中间截断可能让最宽行低于 90pt。
    修法：读新跑的 `FALLBACK_PATH`；低于地板就按 scale² 重算地板（不是改产品字号），读不到就具名 NOT-RUN。

**555. R462 M1260 已退役为负向证人，M1261 是唯一钉窗格边的刀**（R478 观察）
    现象：R478 的 VStack padding 接管了窗格边，撤文件名四修饰不再越界（ESCAPED）；旧表曾把它当 CAUGHT。
    修法：以后读 R462 表要看期望（M1260=ESCAPED、M1261=CAUGHT）；别把负向证人重新标成刀，除非被测对象又变。
"""

STATE_SECTION = u"""## R478 状态（2026-10-29 · 本地 · 第 477 轮 / Round 475）：文件兜底态补父目录路径（4 张旧帧变化、基线 294）+ 捕获路径缝 + R462/R463 旧表重锚；全量 1295/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R478 / 第 477 轮 / Round 475）：兜底态只重复一遍文件名（详情头部已经有一份），用户看不到文件在哪。修法：`DetailFileView.fallbackView` 在文件名下补一行父目录（11pt、secondaryLabelColor、单行中间截断、与文件名同中轴），长文件名不再独占一整块。旧/新：**4 张旧帧变化**（两个兜底夹具 × 亮暗）、0 新增/缺失；基线 **294/0/0/0**；逐张看过：路径是稳定的用户路径 `/Users/tester/Desktop`、中间截断、不压浮层。读数（`FALLBACK_PATH`）：图标带下方最宽一行 **113.0pt**（旧形状里这一行是文件名本身，约 60pt），两档同形。第一版直接用 `url` 父目录，帧里出现捕获目录 `/var/folders/...` ⇒ 每跑都不同；加捕获缝 `fallbackParentPathForCapture`（产品默认 nil 读真实路径，夹具写稳定用户路径）后重捕，4 帧才可基线化。新判据 `testFallbackFileShowsWhereTheFileLives` 读图标下最宽行（≥90pt），不数行数；`M1300`（删路径）/`M1301`（置空）**2/2**。R478 把文件名包进 VStack 后，R462 的 `M1260`（撤四修饰）不再越界 ⇒ 退役为负向证人（期望 ESCAPED），`M1261`（撤内边距）仍 CAUGHT；R463 `M1262/M1263` 因共享色行重锚后 **2/2**。预检 **260/242/658 bad=0**、ARM **353/1141**、HIDDEN **347/1075 rot=0**。⓪：`git push` **Everything up-to-date**、HEAD=origin/main=`7a79987`、**ahead=0**；R477 跑 `40797827495 ↔ 0fd3ec0` 与补记跑 `40797866181 ↔ 7a79987` 读时 in_progress ⇒ **NOT-RUN**；R476 跑三步失败与四跑沿用已读；`INLINE_CODE_PAD`/`QUICKPICK_GREY_BAND`/`QUICKPICK_PIN`/`SHORTCUT_CONFLICT` 仍未读到 ⇒ 三处修复 runner 复验具名 NOT-RUN；436 无新跑，最后已知 `MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=0`。全量 **1295/56/0**（453.6s，轻载）；捕获卷 **294 帧**；基线 **294/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 477，`python3 scripts/product_streak.py --streak-for 477`，last=0fd3ec0）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R477 两跑 in_progress ⇒ NOT-RUN；R477 修复的 runner 复验未读到；436 无新跑。
② 产品：文件兜底态补父目录路径（4 张旧帧变化、基线 294）；加捕获路径缝让帧稳定。
③ 判据：M1300/M1301 2/2；R462 M1260 退役为负向证人、M1261 CAUGHT；R463 M1262/M1263 重锚 2/2。
④ 预检 260/242/658；rot 347/1075；ARM 353/1141。
⑤ 捕获 294 帧；基线 294/0/0/0；build 0 告警；换装 ok/387=387；全量 1295/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R477 两跑（in_progress）；② inline padding 池/幻影 8 行/图钉/冲突的 runner 复验；③ 兜底路径的 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 回执 flake；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–555 的其余未结项仍开。

下一轮（R479）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R478 自身跑、R477 两跑 `40797827495 ↔ 0fd3ec0`/`40797866181 ↔ 7a79987`、R476 跑 `40791382232 ↔ 599ec98`、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `INLINE_CODE_PAD`（light ≥4.5/真带 85/5.0、dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 块下限 8 行）、`QUICKPICK_PIN`（+104/+105、标题末列不动）、`FALLBACK_PATH`（≥90pt）、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 地板与 150 上限不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R478_REPORT_BULLET = u"""- **R478（兜底态所在路径位）**：兜底态只重复文件名（详情头部已有一份），用户看不到文件在哪。`DetailFileView.fallbackView` 在文件名下补一行父目录（11pt、secondary、单行中间截断、同中轴）。**4 张旧帧变化**、0 新增/缺失，基线 **294/0/0/0**；`FALLBACK_PATH` 图标下最宽行 **113pt**（旧形状是文件名约 60pt）。第一版帧里出现捕获目录 `/var/folders/...` ⇒ 每跑都不同，加 `fallbackParentPathForCapture` 捕获缝后重捕。判据读图标下最宽行（≥90pt）；M1300/M1301 **2/2**。R462 M1260 被新 VStack padding 掩蔽 ⇒ 退役为负向证人（ESCAPED），M1261 仍 CAUGHT；R463 M1262/M1263 重锚 **2/2**。⓪ no-op push、ahead=0；R477 两跑 in_progress ⇒ NOT-RUN；inline/phantom/pin/conflict 的 runner 复验仍未读到。全量 **1295/56/0**（453.6s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 477 轮（R478" in audit: raise SystemExit("REFUSED AUDIT 已有 R478")
if u"## Round 475 · R478" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 475")
if u"## D-475" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-475")
if u"文件兜底态补父目录" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**553." in backlog: raise SystemExit("REFUSED BACKLOG 已有 553")
if state.count(u"## R477 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R477 状态"))
U_CELL_OLD = u"U-31 … U-1832（R477 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R477 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_475 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R477 状态", STATE_SECTION + u"## R477 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1838（R478 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R477 节 ②", u"AGENT_STATE.md` 的 R478 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R478_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R478_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
