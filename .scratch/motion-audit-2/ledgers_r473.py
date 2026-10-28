#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R473 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 471 轮（R472 · 2026-10-29"
AUDIT_SECTION = u"""## 第 472 轮（R473 · 2026-10-29 · U-1791…U-1796）：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288；M1286/M1287 2/2）+ 判据改用等距连跑（旧帧假绿被自己抓住）（产品 1 文件 + 判据）

- **U-1791：⓪ push 与 CI。** 开工验 remote 仍 `35f4bfd`；一次快进 push **`35f4bfd..7ce44a1` success**（三笔：1bd7c60/ae6d900/7ce44a1）、HEAD=origin/main=`7ce44a1`、**ahead=0**。R472 自身跑 `40767358317 ↔ 7ce44a1` 读时 **in_progress** ⇒ **NOT-RUN**；**`INLINE_CODE_DIAG dark` 的页/带/候选/top 数据未拿到** ⇒ 靶指定的“按数据改检测”**具名 NOT-RUN，不盲调**（选择器/4.5 未动）。R471 两跑沿用上轮已读：`TRUNCATION_NOTE 11/14、说明 1 次`、`QUICKPICK_SOURCE_ICON 5/5/84、负臂 0`、`CROSS_YEAR/MAIN_ROWS 38.0` 签收；`40759325073 ↔ fa0db55` 的 Motion 回执 1<2 具名 `RUNNER_COPY_RECEIPT_MOTION_FLAKE`（同代码 35f4bfd 未红）；436 无 R473 新跑。
- **U-1792：① 腐烂与预检。** `HIDDEN_ARMS 表=340 可判=1061 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=253 covered=235 arms=644 bad=0`、`ARM_TOTAL files=346 arms=1127`。
- **U-1793：② 产品：数据页补保存位置。** 隐私「数据与保留」卡里已有保存路径，但用户找“存在哪”时在「数据」页；数据页以前只说“保存在本地”。修法：在“剪贴板历史保存在本地…”下补一行 `SettingsPathText("保存位置：~/Library/Application Support/时间剪史/")`，复用 R472 的路径等宽组件。旧/新：数据页从**无路径行** → 有路径行；**2 张旧帧变化**（settings-data 亮暗）、0 新增/缺失；基线 **288/0/0/0**；2 张逐张看过：路径单行等宽、卡片未溢出，导出/导入与清空三段未动。
- **U-1794：③ 判据/尺的自我推翻。** 新判据 `testSettingsDataPageShowsTheStoragePath` 首版按“最大窄簇数”找路径行（新帧 37），但**旧帧（无路径行）也读到 51 簇/37 窄簇**（那是 CJK 导出说明）⇒ 假绿；当场改成**等距连跑**：窄簇起点间隔围着 `SettingsPathPresentation.pathFont` 的 advance（6.8pt）连跑，新路径行 **21**、旧帧最大 **3**。`M1286`（删路径行）/`M1287`（路径改纯 CJK）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1795：④ 既有面与 436。** 数据页/隐私页的路径字体沿用 R472；既有帧仅 settings-data 两档变化。436：R472 跑 in_progress ⇒ 无新 Motion floor 读数；R471 的 `RUNNER_COPY_RECEIPT_MOTION_FLAKE` 沿用；不改门槛。
- **U-1796：八步与电池。** build **0 告警**；捕获卷 **288 帧**、`CHANGED=2 MISSING=0 ADDED=0`，更新后 `288/0/0/0`；全量 **1284/56/0**（468.5s，轻载；新增 1 条数据页路径判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 472，`python3 scripts/product_streak.py --streak-for 472`，last=1bd7c60）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R472 自身跑（in_progress）与 R473 自身跑（收口视网络）；② `INLINE_CODE_DIAG dark` 的 runner 数据（靶修复未做）；③ 数据页路径的 runner 1x（设置内容列可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明/来源图标/跨年 runner 已签收；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–540 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 470 · R473（第 472 轮 · 2026-10-29）：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）+ 判据改用等距连跑

隐私卡里已有保存路径，但用户找“存在哪”时在「数据」页；数据页以前只说“保存在本地”。在“剪贴板历史保存在本地…”下补一行 `SettingsPathText("保存位置：~/Library/Application Support/时间剪史/")`，复用 R472 的路径等宽组件。2 张数据帧变化、0 新增，基线 288/0/0/0；2 张逐张看过：路径单行等宽、卡片未溢出。新判据首版按“最大窄簇数”找路径行，**旧帧（无路径）也读到 51 簇/37 窄簇**（CJK 导出说明）⇒ 假绿；当场改成**等距连跑**（围着 `pathFont` advance 6.8pt）：新路径行 21、旧帧 3；M1286/M1287 2/2。全量 1284/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ 一次快进 push `35f4bfd..7ce44a1` success、ahead=0；R472 跑 in_progress ⇒ NOT-RUN；`INLINE_CODE_DIAG dark` 数据未拿到 ⇒ 靶修复具名 NOT-RUN，不盲调。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张数据帧看过：路径行等宽、单行、卡片未溢出，导出/导入/清空未动。 |
| 判据有效性 | 15/15 | 等距连跑围着产品 pathFont advance；新 21、旧帧 3；M1286/M1287 2/2。 |
| 假绿防御 | 14/15 | 首版窄簇尺在旧帧上假绿，已当场改成等距连跑；扣 1：R472/R473 跑与 dark DIAG 数据未读。 |
| 产品面推进 | 15/15 | 新类别（数据页保存位置）；1 个产品文件；复用等宽路径组件；Store 不动。 |
| 台账一致性 | 15/15 | U-1791…U-1796、D-470、288 帧/1284、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 旧帧假绿自己抓住并改尺；靶修复拿不到数据就 NOT-RUN，不盲调选择器。 |
| 可复核性 | 15/15 | 2 张帧、21 vs 3、advance 6.8、M1286/M1287、precheck 253/235/644、rot 340/1061、基线 288 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_470 = u"""## D-470 数据页补保存位置；等宽行用「等距连跑」作尺（R473）

- 背景：隐私卡里有保存路径，但用户找“存在哪”时在「数据」页；数据页以前只说“保存在本地”。首版判据按“最大窄簇数”找路径行，而旧帧（无路径）也读到 51 簇/37 窄簇（CJK 导出说明）⇒ 假绿。
- 决定：数据页“剪贴板历史保存在本地…”下补 `SettingsPathText("保存位置：…/")`（复用 R472 等宽路径组件）；判据改成**等距连跑**：窄簇起点间隔围着 `SettingsPathPresentation.pathFont` 的 advance（6.8pt）连跑，路径行 21、旧帧最大 3。
- 理由：路径行是等宽 Latin 行，CJK 说明不是；等距连跑直接读“等宽”这个被判定属性，窄簇数量只是代理量。
- 兼容性/迁移：仅 settings-data 两档变化；基线 288 同笔更新；M1286/M1287 2/2。
- 边界：1x 字形连成词，改用“总词簇 ≥5”；设置内容列在 runner 上可能平涂 ⇒ 具名 NOT-RUN。
- 回滚：删数据页路径行与判据；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）（R473 / 第 472 轮 / Round 470 / U-1791…U-1796 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**538. R472/R473 自身跑与 inline dark 的 DIAG 数据未读**（R473 观察）
    现象：R472 跑在收口时仍 in_progress；R473 自身跑随提交创建；`INLINE_CODE_DIAG dark` 的页/带/候选/top 仍未读到。
    修法：下一跑先读这些 run 的失败步骤与 DIAG；拿到数据再改检测，4.5 地板不动。

**539. 数据页路径判据的 1x 分支未在 runner 上签收**（R473 观察）
    现象：2x 用等距连跑 ≥10（新 21、旧 3）；1x 改总词簇 ≥5，但 runner 的设置内容列可能平涂。
    修法：下一跑读 `SETTINGS_DATA_PATH`；读不到就具名 NOT-RUN，不把 2x 阈值抄到 1x。

**540. 窄簇数量是“等宽行”的代理量，旧帧证明它假绿**（R473 观察）
    现象：首版 maxNarrow 37 在新帧过；旧帧（无路径）同一 CJK 导出说明也是 51/37 ⇒ 尺没读对象。
    修法：等宽行的判据用「等距连跑」或直接读字体结构量；窄簇数量只留诊断。
"""

STATE_SECTION = u"""## R473 状态（2026-10-29 · 本地 · 第 472 轮 / Round 470）：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）+ 判据改用等距连跑；全量 1284/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R473 / 第 472 轮 / Round 470）：隐私卡里已有保存路径，但用户找“存在哪”时在「数据」页；数据页以前只说“保存在本地”。修法：在“剪贴板历史保存在本地…”下补一行 `SettingsPathText("保存位置：~/Library/Application Support/时间剪史/")`，复用 R472 的路径等宽组件。旧/新：数据页从**无路径行** → 有路径行；**2 张旧帧变化**（settings-data 亮暗）、0 新增/缺失；基线 **288/0/0/0**；2 张逐张看过：路径单行等宽、卡片未溢出。**判据首版假绿**：按“最大窄簇数”找路径行，新帧 37，而旧帧（无路径）同一 CJK 导出说明也读到 51 簇/37 窄簇；当场改成**等距连跑**（窄簇起点间隔围着 `SettingsPathPresentation.pathFont` 的 advance 6.8pt）：新路径行 **21**、旧帧最大 **3**；`M1286/M1287` **2/2 CAUGHT**。**靶修未做**：`INLINE_CODE_DIAG dark` 的页/带/候选/top 数据未拿到（R472 跑 in_progress）⇒ 按靶具名 NOT-RUN，不盲调选择器、4.5 地板未动。预检 **253/235/644 bad=0**、ARM **346/1127**、HIDDEN **340/1061 rot=0**。⓪：开工验 remote 仍 `35f4bfd`；一次快进 push **`35f4bfd..7ce44a1` success**（三笔）、HEAD=origin/main=`7ce44a1`、**ahead=0**；R472 跑 `40767358317 ↔ 7ce44a1` **in_progress ⇒ NOT-RUN**；R471 两跑沿用（TRUNCATION_NOTE 11/14、来源图标 5/5/84、CROSS_YEAR/MAIN_ROWS 签收；fa0db55 Motion 回执 flake）；436 无 R473 新跑。全量 **1284/56/0**（468.5s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 472，`python3 scripts/product_streak.py --streak-for 472`，last=1bd7c60）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `35f4bfd..7ce44a1` success、ahead=0；R472 跑 in_progress ⇒ NOT-RUN；dark DIAG 数据未拿到 ⇒ 靶修复 NOT-RUN、不盲调。
② 产品：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）。
③ 判据：首版窄簇尺在旧帧假绿，改成等距连跑（21 vs 3）；M1286/M1287 2/2；precheck 253/235/644；rot 340/1061。
④ 436：无 R473 新跑；R471 的 Motion 回执 flake 沿用，不改门槛。
⑤ 367：hidden 表 340 / 可判 1061 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1284/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R472 自身跑（in_progress）与 R473 自身跑（收口视网络）；② `INLINE_CODE_DIAG dark` 的 runner 数据（靶修复未做）；③ 数据页路径的 runner 1x（设置内容列可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明/来源图标/跨年 runner 已签收；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–540 的其余未结项仍开。

下一轮（R474）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R473 主笔+追记 head 跑、R472 跑 `40767358317 ↔ 7ce44a1`、R471 两跑的全部失败步骤；重点 `INLINE_CODE_DIAG dark`（页/带/候选/top、m=rowMax；拿到数据再改检测、不盲调选择器、4.5 地板不动）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`（2x 等距连跑 21、1x 词簇 ≥5）、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R473_REPORT_BULLET = u"""- **R473（数据页保存位置位）**：隐私卡里已有保存路径，但数据页以前只说“保存在本地”。在“剪贴板历史保存在本地…”下补 `SettingsPathText("保存位置：~/Library/Application Support/时间剪史/")`，复用等宽路径组件。**2 张数据帧变化**、0 新增/缺失，基线 **288/0/0/0**；2 张逐张看过：路径单行等宽、卡片未溢出。新判据首版按“最大窄簇数”在旧帧上假绿（旧帧 CJK 导出说明也 51 簇/37 窄簇），当场改成**等距连跑**（围着 pathFont advance 6.8pt）：新路径行 **21**、旧帧最大 **3**；M1286/M1287 **2/2**。⓪ 一次快进 push `35f4bfd..7ce44a1` success、ahead=0；R472 跑 in_progress ⇒ NOT-RUN；`INLINE_CODE_DIAG dark` 数据未拿到 ⇒ 靶修复具名 NOT-RUN、不盲调。全量 **1284/56/0**（468.5s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 472 轮（R473" in audit: raise SystemExit("REFUSED AUDIT 已有 R473")
if u"## Round 470 · R473" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 470")
if u"## D-470" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-470")
if u"数据页补保存位置" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**538." in backlog: raise SystemExit("REFUSED BACKLOG 已有 538")
if state.count(u"## R472 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R472 状态"))
U_CELL_OLD = u"U-31 … U-1790（R472 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R472 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_470 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R472 状态", STATE_SECTION + u"## R472 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1796（R473 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R472 节 ②", u"AGENT_STATE.md` 的 R473 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R473_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R473_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
