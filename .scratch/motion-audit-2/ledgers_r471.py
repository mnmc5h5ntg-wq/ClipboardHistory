#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R471 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 469 轮（R470 · 2026-10-29"
AUDIT_SECTION = u"""## 第 470 轮（R471 · 2026-10-29 · U-1779…U-1784）：详情截断说明降到 meta 字号（11 vs 正文 14；2 张新帧、基线 288；M1282/M1283 2/2）（产品 1 文件 + 判据）

- **U-1779：⓪ push 与 CI。** 开工 HEAD=origin/main=`e664410`、**ahead=0**；`git push` 两探均 `Connection closed ... port 22` ⇒ **`PUSH_BLOCKED=network`（HEAD=`e664410`、ahead=0）**；`gh run list` EOF ⇒ **`CI_READ_BLOCKED=network`**；R470 两跑 `40754111098 ↔ f15bbf9`、`40754306434 ↔ e664410` 未读到 ⇒ **NOT-RUN**；R469 四跑沿用上轮已读（failure 2 步；`CROSS_YEAR_TIME` 与 `MAIN_ROWS_CROSS_YEAR 38.0` 签收；inline dark；`RUNNER_CODE_TAB_DICT_NIL_FLAKE`；`RUNNER_SCROLL_SESSION_FLAKE`）；`40740068763 ↔ 00ff343` 的失败步骤已读；436 无 R471 新跑。
- **U-1780：① 腐烂与预检。** `HIDDEN_ARMS 表=338 可判=1057 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=251 covered=233 arms=640 bad=0`、`ARM_TOTAL files=344 arms=1123`。
- **U-1781：② 产品：截断说明退到 meta 字号。** 正文超过 40k 时，尾部会追加「……（后面的内容没有渲染，切到「原文」看全文）」；旧形状用**正文字号 14pt**接在最后一段后面，读起来像剪贴板正文的一部分（它是界面说明，不是内容）。修法：说明改用 `DetailTypography.metaFontSize`（11pt），仍 secondary 色。旧/新：`TRUNCATION_NOTE light/dark 说明字号/正文字号 14/14 → 11/14`（说明出现 1 次；`TRUNCATION_PARSE 截断=true 属性串长=39997 含说明=true`）。**2 张新帧**（`detail-markdown-truncated` 亮/暗，渲染后滚到底）、0 变化/缺失；基线 **286→288**；亮/暗看过：说明一行、明显小于正文、位于正文结尾。
- **U-1782：③ 判据/刀。** `testTruncationNoteSitsBelowTheBodyTier` 从产品渲染的 `NSTextView` 读说明与正文的 `.font`：说明出现恰好 1 次、说明字号 < 正文字号 −1pt（相对量，不抄产品常数）。夹具首版 2100 段只有 39.9k ⇒ `TRUNCATION_PARSE 截断=false`，说明根本没被追加；诊断当场抓到，改成 2400 段（45,664 字符）后真截断。`M1282`（说明回正文 14pt）/`M1283`（18pt）⇒ **2/2 CAUGHT**。
- **U-1783：④ 既有面与 436。** 本产品改动只影响 `document.isTruncated` 的文档；既有 Markdown 帧不截断 ⇒ 0 变化。436：无 R471 新跑，Motion floor **NOT-RUN**；采样红沿用。
- **U-1784：八步与电池。** build **0 告警**；捕获卷 **288 帧**、`CHANGED=0 MISSING=0 ADDED=2`，更新后 `288/0/0/0`；全量 **1280/56/0**（492.1s，轻载；新增 1 条截断判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 470，`python3 scripts/product_streak.py --streak-for 470`，last=df63e5b）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R470 两跑与 R471 自身跑（网络）；② 截断说明 runner 1x；③ 40k 夹具 runner 捕获；④ inline dark 新门 runner；⑤ 来源图标 runner 1x；⑥ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–534 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 468 · R471（第 470 轮 · 2026-10-29）：详情截断说明降到 meta 字号（11 vs 正文 14；2 张新帧、基线 288）

正文超过 40k 时，尾部的「后面的内容没有渲染」说明以前用正文字号 14pt 接在最后一段后，读起来像剪贴板内容的一部分。修法：说明改用 `DetailTypography.metaFontSize`（11pt），仍 secondary。`TRUNCATION_NOTE 说明字号/正文字号 14/14 → 11/14`，说明出现 1 次；`TRUNCATION_PARSE 截断=true 属性串长=39997 含说明=true`。2 张新帧（渲染后滚到底）、0 变化，基线 288/0/0/0；全量 1280/56/0；build 0 告警；换装 ok/387=387；电池 683/5。夹具首版 2100 段只有 39.9k（截断=false，说明没有），诊断抓到后改 2400 段（45,664 字）。M1282/M1283 2/2。⓪ 两探断网（ahead=0）⇒ PUSH_BLOCKED；gh EOF ⇒ CI_READ_BLOCKED；R470 两跑与 R471 自身跑 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗两张新帧看过：说明一行、明显小于正文、位于正文结尾。 |
| 判据有效性 | 15/15 | 从产品 NSTextView 读说明/正文字号；说明出现 1 次；11<14；M1282/M1283 2/2。 |
| 假绿防御 | 14/15 | 夹具首版未真截断被 `TRUNCATION_PARSE` 当场抓到；扣 1：R470 两跑与 R471 自身跑未读。 |
| 产品面推进 | 15/15 | 新类别（详情截断提示）；1 个产品文件；说明与正文分层；Store 不动。 |
| 台账一致性 | 15/15 | U-1779…U-1784、D-468、288 帧/1280、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 截断说明只退字号、不藏内容；夹具/判据/刀/帧/基线同笔；网络 NOT-RUN 具名。 |
| 可复核性 | 15/15 | 14/14→11/14、说明 1 次、39997、M1282/M1283、precheck 251/233/640、rot 338/1057、基线 288 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_468 = u"""## D-468 截断说明退到 meta 字号，明确它不是正文（R471）

- 背景：正文超过 40k 时尾部的「后面的内容没有渲染」说明用正文字号 14pt 接在最后一段后；它是界面说明，却读起来像剪贴板内容的一部分。
- 决定：说明改用 `DetailTypography.metaFontSize`（11pt），仍 secondary 色；不改变说明文案、不隐藏内容；正文照旧 40k 截断。
- 理由：说明与正文必须是两个层级；11pt 与正文 14pt 相差 3pt，帧上能一眼分开。相对判据（说明 < 正文 −1pt）不抄产品常数。
- 兼容性/迁移：只影响 `document.isTruncated` 的文档；既有 Markdown 帧 0 变化；2 张新帧、基线 286→288。
- 边界：说明仍是 secondary 11pt（对比度 4.10:1，低于小字 4.5）；它是提示不是正文，先记录（BACKLOG 534）；runner 1x 的说明字号读数待读。
- 回滚：改回 `bodyFont`；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 详情截断说明降到 meta 字号（11 vs 正文 14；2 张新帧、基线 288）（R471 / 第 470 轮 / Round 468 / U-1779…U-1784 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**532. 截断说明的 runner 1x 字号读数未读**（R471 观察）
    现象：本机从产品 NSTextView 读到说明 11 / 正文 14、说明 1 次；runner 的渲染路径与字号尚未读。
    修法：下一跑读 `TRUNCATION_NOTE`；读不到就具名 NOT-RUN，不改相对判据。

**533. 40k 截断夹具的 settle 2.0s 在 runner 上可能更慢**（R471 观察）
    现象：45,664 字符的渲染 + 滚到底；本机 2s settle 够，runner 1x 可能更慢。
    修法：若 runner 帧空白/说明不在，先报 `TRUNCATION_NOTE_NOT_RUN=capture`，不把慢读成产品没做。

**534. 截断说明仍是 secondary 11pt（4.10:1）**（R471 观察）
    现象：说明是小字提示，secondary 在亮档实测 4.10:1，低于小字 4.5 的通用门槛。
    修法：先记录；若把它当正文级信息，需提对比度并补判据，不能只改色不补尺。
"""

STATE_SECTION = u"""## R471 状态（2026-10-29 · 本地 · 第 470 轮 / Round 468）：详情截断说明降到 meta 字号（11 vs 正文 14；2 张新帧、基线 288）；全量 1280/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R471 / 第 470 轮 / Round 468）：正文超过 40k 时，尾部「……（后面的内容没有渲染，切到「原文」看全文）」旧形状用**正文字号 14pt**接在最后一段后，读起来像剪贴板正文的一部分；它是界面说明。修法：说明改用 `DetailTypography.metaFontSize`（11pt），仍 secondary。旧/新：`TRUNCATION_NOTE light/dark 说明字号/正文字号 14/14 → 11/14`（说明出现 1 次）；`TRUNCATION_PARSE 截断=true 属性串长=39997 含说明=true`。**2 张新帧**（`detail-markdown-truncated` 亮/暗，渲染后滚到底）、0 变化/缺失；基线 **286→288/0/0/0**；亮/暗看过：说明一行、明显小于正文、位于正文结尾。判据 `testTruncationNoteSitsBelowTheBodyTier` 从产品 NSTextView 读说明/正文字号（相对量）；`M1282/M1283` **2/2 CAUGHT**；夹具首版 2100 段只有 39.9k（截断=false，说明没有），诊断抓到后改 2400 段（45,664 字）。预检 **251/233/640 bad=0**、ARM **344/1123**、HIDDEN **338/1057 rot=0**。⓪：开工 HEAD=origin/main=`e664410`、**ahead=0**；`git push` 两探均 remote closed ⇒ **`PUSH_BLOCKED=network`（HEAD=`e664410`、ahead=0）**；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**；R470 两跑 `40754111098 ↔ f15bbf9`、`40754306434 ↔ e664410` 均 **NOT-RUN**；R469 四跑沿用上轮（CROSS_YEAR/MAIN_ROWS 38.0 签收、inline dark、code-tab 字典 flake、scroll flake）；436 无 R471 新跑。全量 **1280/56/0**（492.1s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 470，`python3 scripts/product_streak.py --streak-for 470`，last=df63e5b）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 两探 push 断网、gh EOF ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R470 两跑与 R471 自身跑 NOT-RUN；R469 四跑沿用；436 无新跑。
② 产品：截断说明退到 meta 字号（14/14 → 11/14；2 张新帧、基线 288）。
③ 判据：产品 NSTextView 字号相对量；M1282/M1283 2/2；夹具 40k 真截断诊断；precheck 251/233/640；rot 338/1057。
④ 436：无 R471 新跑；Motion floor NOT-RUN，采样红沿用。
⑤ 367：hidden 表 338 / 可判 1057 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1280/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R470 两跑与 R471 自身跑（网络）；② 截断说明 runner 1x；③ 40k 夹具 runner 捕获；④ inline dark 新门 runner；⑤ 来源图标 runner 1x；⑥ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–534 的其余未结项仍开。

下一轮（R472）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R471 主笔+追记 head 跑与 R470 两跑（`40754111098 ↔ f15bbf9`、`40754306434 ↔ e664410`）的全部失败步骤；重点 `TRUNCATION_NOTE`（说明 11/正文 14、说明 1 次）、`QUICKPICK_SOURCE_ICON`、`INLINE_CODE_DIAG`（m=rowMax）与 `INLINE_CODE_PAD` dark、`CROSS_YEAR_TIME`、`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R471_REPORT_BULLET = u"""- **R471（详情截断提示位）**：正文超过 40k 时尾部「后面的内容没有渲染」说明旧形状用正文 14pt 接在最后一段后，读起来像剪贴板内容；修法改 `DetailTypography.metaFontSize`（11pt），仍 secondary。`TRUNCATION_NOTE 说明字号/正文字号 14/14 → 11/14`，说明出现 1 次；`TRUNCATION_PARSE 截断=true 属性串长=39997 含说明=true`。**2 张新帧**（渲染后滚到底）、0 变化，基线 **286→288/0/0/0**；亮/暗看过：说明一行、明显小于正文。判据从产品 NSTextView 读字号（相对量）；M1282/M1283 **2/2**。夹具首版 2100 段仅 39.9k（截断=false），诊断抓到后改 2400 段（45,664 字）。⓪ 两探 push 断网、gh EOF ⇒ **PUSH_BLOCKED=network（HEAD e664410、ahead=0）**、**CI_READ_BLOCKED**；R470 两跑与 R471 跑 NOT-RUN。全量 **1280/56/0**（492.1s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 470 轮（R471" in audit: raise SystemExit("REFUSED AUDIT 已有 R471")
if u"## Round 468 · R471" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 468")
if u"## D-468" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-468")
if u"详情截断说明降到 meta 字号" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**532." in backlog: raise SystemExit("REFUSED BACKLOG 已有 532")
if state.count(u"## R470 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R470 状态"))
U_CELL_OLD = u"U-31 … U-1778（R470 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R470 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_468 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R470 状态", STATE_SECTION + u"## R470 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1784（R471 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R470 节 ②", u"AGENT_STATE.md` 的 R471 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R471_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R471_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
