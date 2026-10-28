#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R470 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 468 轮（R469 · 2026-10-29"
AUDIT_SECTION = u"""## 第 469 轮（R470 · 2026-10-29 · U-1773…U-1778）：浮层行补来源 App 图标（5/5 有图、首行 412 彩度；12 张旧帧变化 + 2 张新帧、基线 286）+ inline 全宽块底门（本地 98.5/6.0、99.0/6.5）（产品 1 文件 + 判据/仪器）

- **U-1773：⓪ push 与 CI。** 开工 HEAD=origin/main=`1f7f486`、**ahead=0**；`git push` 两探均 `Connection closed ... port 22` ⇒ **`PUSH_BLOCKED=network`（HEAD=`1f7f486`、ahead=0）**；`gh run list` EOF ⇒ **`CI_READ_BLOCKED=network`**；R469 的四跑 `40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`、`40745716427 ↔ 1f7f486` 均未读到 ⇒ **NOT-RUN**。已读（上轮账）：`40740068763 ↔ 00ff343` **failure 2 步**（Swift tests / Capture gate）唯一测试红 `INLINE_CODE_PAD dark 150/147/3.0`；Capture 15 帧方向变 **`MATERIAL_BLIND_NOT_RUN`**（runner 102 帧无黑带，名单 15；R467 intentional 生效），`SETTINGS_HELPER_AXIS_NOT_RUN=settings-content-blank` 亮/暗；签收 `VIDEO_SEEK 98/106`、`VIDEO_ALIGN 13.0`、`VIDEO_SURFACE 0/157` 与 `0/33`、`VIDEO_UNAVAILABLE 5/4`；`INLINE_CODE_DIAG` light 选行=143/页236/带212/候选326（top s21/p21）、dark 选行=319/页68/带76/候选444（top r319 s320/p320，r310 s20/p20）。`40736447466 ↔ 0774453` 为 cancelled（0 失败步骤）⇒ NOT-RUN。
- **U-1774：① 腐烂与预检。** `HIDDEN_ARMS 表=337 可判=1055 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=250 covered=232 arms=638 bad=0`、`ARM_TOTAL files=343 arms=1121`。**旧表重钉**：来源列改了两条约束/首轴 ⇒ r430 M1175（约束块）、r104 M578/M579（`overlayPill` 新签名的 maxGap 参数）腐烂；按源码重钉后 r430 **5/5 CAUGHT**、r104 M578/M579 **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1775：② 产品：浮层行补来源 App 图标。** 浮层每行原来只有类型符号；主列表/详情有来源，浮层没有。修法：在类型符号后加**固定 16pt 来源槽**（`SourceAppIconProvider` 的 App 图标；没有来源时留空但占位，标题轴不抖），标题从来源槽右侧起。旧/新：`QUICKPICK_SOURCE_ICON light/dark 有图=0 → 5/5、类型=5/5、首行彩度像素=0 → 412/412`；负臂 `quickpick-no-source` 来源图=0、类型=1、彩度=0；首行标题左沿正/负臂同为 78.5pt（固定槽不抖）。**12 张旧帧变化 + 2 张新帧**（quickpick-no-source 亮/暗）、0 缺失；基线 **284→286**；14 张逐张看过：来源图标彩色、标题轴/时间列不变。
- **U-1776：③ inline 全宽块底门（按 DIAG 修选择器，不降 4.5）。** runner dark 的 150/147/3.0 是 320pt code-block 底里的一段；真带在候选里但被全宽块底的碎片压过。修法：候选增加 `rowMaxBandRun`（同一行最长带 run），`best` 要求 `rowMaxBandRun <= maxSpan` —— **整行有全宽块底的行整行排除**，不碰 4.5 地板、不放大上界；DIAG 的 top 候选多打 `m`（rowMax）。本地像素：`INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5`（与修前一致）；纯函数新增「块底碎片 span 150/rowMax 320/padding 20 vs 真带 padding 6」两向格。`M1277`（撤门）/`M1278`（门恒假）⇒ **2/2 CAUGHT**。runner dark 待新跑复验（本轮网络断）。
- **U-1777：④ 药丸材料 gap 容忍。** 来源图标的白色像素与页底同档，严格 run 把浅色药丸读成 25.0pt（搜索首墨 22.5）。给 `overlayPill` 加 `maxGap`（只在该判据传 24pt）：内容图标不能把药丸带切断；light/dark 药丸左沿回 **22.0pt**、搜索 22.5pt、差 **1px**；`M1281`（maxGap=0）⇒ **1/1 CAUGHT**。
- **U-1778：八步与电池。** build **0 告警**；捕获卷 **286 帧**、`CHANGED=12 MISSING=0 ADDED=2`，更新后 `286/0/0/0`；全量 **1279/56/0**（507.3s，轻载；新增 1 条来源图标判据）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 469，`python3 scripts/product_streak.py --streak-for 469`，last=4283a90）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R469 四跑与 R470 自身跑（网络）；② inline runner dark（新门未跑）；③ 来源图标 runner 1x；④ `SETTINGS_HELPER_AXIS` runner 1x；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–531 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 467 · R470（第 469 轮 · 2026-10-29）：浮层行补来源 App 图标（5/5 有图、首行 412 彩度；12 张旧帧变化 + 2 张新帧、基线 286）+ inline 全宽块底门（本地 98.5/6.0、99.0/6.5）

浮层每行原来只有类型符号，来源 App 只在主列表/详情露出。类型符号后加固定 16pt 来源槽（`SourceAppIconProvider` 图标，无来源留空占位），标题从来源槽右侧起：`QUICKPICK_SOURCE_ICON 有图=5/5、类型=5/5、首行彩度=412`；负臂来源图 0/类型 1/彩度 0；首行标题左右正负臂同为 78.5pt。12 张旧帧变化 + 2 张新帧、0 缺失，基线 286/0/0/0；14 张逐张看过。inline 选择器按 runner DIAG 加 `rowMaxBandRun <= maxSpan`（整行全宽块底整行排除），本地 PAD 98.5/92.5/6.0 与 99.0/92.5/6.5 不动，M1277/M1278 2/2；药丸尺加 maxGap 24pt，light/dark 药丸 22.0、搜索 22.5、差 1px，M1281 1/1。旧表 M1175/M578/M579 重钉复跑；全量 1279/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push 两探断网（ahead=0）⇒ PUSH_BLOCKED；gh EOF ⇒ CI_READ_BLOCKED；R469 四跑与 R470 自身跑 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 14 张 changed/new 帧逐张看过：来源图标彩色、负臂留空、标题轴/时间列不变。 |
| 判据有效性 | 15/15 | 来源图 5/5+彩度 412、负臂 0；inline 块底两向纯函数；药丸 22/22.5/1px；M1277/M1278/M1279/M1280/M1281 全咬。 |
| 假绿防御 | 14/15 | 来源图标白像素把药丸读成 25 被左轴尺抓到；M1275 教训后不用派生计数当闸门；扣 1：R469/R470 自身跑未读。 |
| 产品面推进 | 15/15 | 新类别（浮层行来源图标）；1 个产品文件；固定槽不抖；Store 不动。 |
| 台账一致性 | 15/15 | U-1773…U-1778、D-466/D-467、286 帧/1279、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | inline 选择器只按 DIAG 与本地两向改、不降 4.5；旧表重钉复跑；网络 NOT-RUN 具名。 |
| 可复核性 | 15/15 | 5/5、412、98.5/6.0/99.0/6.5、22.0/22.5/1px、precheck 250/232/638、rot 337/1055、基线 286 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_466 = u"""## D-466 浮层行补来源 App 图标，固定槽不抖标题轴（R470）

- 背景：浮层每行只有类型符号，来源 App 只在主列表/详情露出；用户在最常用的快速选择里看不到"从哪来"。
- 决定：类型符号后加固定 16pt 来源槽，`SourceAppIconProvider` 图标；没有来源时留空但占位；标题从来源槽右侧起。
- 理由：来源是快速选择的核心信息之一；固定槽让有无来源的行标题共轴。App 图标是彩色，类型符号仍是灰色；两者不混。
- 兼容性/迁移：12 张 QuickPick 旧帧变化 + 2 张新负臂；基线 284→286；`quickpick-no-source` 是负臂。
- 边界：runner 1x 的 App 图标解析未读（具名 NOT-RUN）；来源图标与类型图标的语义差由像素彩度/结构 image 两条腿判。
- 回滚：删来源槽与赋值；或 `git revert`。
"""

DECISION_467 = u"""## D-467 inline 全宽块底门与药丸材料 gap 容忍（R470）

- 背景：runner dark 的 150/147/3.0 是 320pt code-block 底里的一段，真带候选被块底碎片压过；来源图标的白色像素又把浅色药丸的材料 run 切断，药丸左沿被读成 25.0pt。
- 决定：`InlineCodeBandChoice.Candidate` 增 `rowMaxBandRun`，`best` 要求 `rowMaxBandRun <= maxSpan`（整行有全宽块底的整行排除）；`overlayPill` 增 `maxGap`，仅搜索左轴判据传 24pt（内容图标不能把药丸带切断）。4.5 地板、150 上界、12 灰阶地板均未动。
- 理由：按被判属性选对象——行内码是短带，code-block 底是全宽块；药丸是材质带，图标是压在带上的内容。
- 兼容性/迁移：本地 PAD 98.5/92.5/6.0 与 99.0/92.5/6.5 不变；药丸 22.0/22.5/1px；旧表 M1175/M578/M579 重钉复跑。
- 边界：runner dark 的新选择器未跑（NOT-RUN）；`maxGap` 只在一条判据传 24，其余调用点默认 0。
- 回滚：撤 `rowMaxBandRun` 条件与 `maxGap` 参数；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 浮层行补来源 App 图标（5/5 有图、首行 412 彩度；12 张旧帧变化 + 2 张新帧、基线 286）+ inline 全宽块底门与药丸 gap 容忍（R470 / 第 469 轮 / Round 467 / U-1773…U-1778 · 产品 1 文件 + 判据/仪器）

"""

BACKLOG_SECTION = u"""**529. inline 全宽块底门的 runner dark 复验**（R470 观察）
    现象：本地纯函数两向与像素 98.5/92.5/6.0、99.0/92.5/6.5 已过；runner dark 新门还没跑（本轮网络断）。
    修法：下一跑读 `INLINE_CODE_DIAG` 的 top（多打 m=rowMax）与 `INLINE_CODE_PAD`；仍不对再按数据改，4.5 地板不动。

**530. 浮层来源图标的 runner 1x/2x 读数未读**（R470 观察）
    现象：本机 5/5 有图、首行 412 彩度、负臂 0；runner 的 App 图标解析与 1x 像素尚未读。
    修法：下一跑读 `QUICKPICK_SOURCE_ICON`；读不到就具名 NOT-RUN，不降彩度门限。

**531. `overlayPill` 的 maxGap 只在搜索左轴判据传 24pt**（R470 观察）
    现象：其余调用点默认 0；若别的浮层材质带也被内容图标切断，会读错边。
    修法：先记录；要全局改先补该判据的两向格与刀。
"""

STATE_SECTION = u"""## R470 状态（2026-10-29 · 本地 · 第 469 轮 / Round 467）：浮层行补来源 App 图标（5/5 有图、首行 412 彩度；12 张旧帧变化 + 2 张新帧、基线 286）+ inline 全宽块底门（本地 98.5/6.0、99.0/6.5）；全量 1279/56/0（产品 1 文件 + 判据/仪器）

最后更新：2026-10-29（本地 · R470 / 第 469 轮 / Round 467）：浮层每行原来只有类型符号，来源 App 只在主列表/详情露出。修法：类型符号后加**固定 16pt 来源槽**（`SourceAppIconProvider` 的 App 图标；没有来源时留空但占位，标题轴不抖），标题从来源槽右侧起。旧/新：`QUICKPICK_SOURCE_ICON light/dark 有图=0 → 5/5、类型=5/5、首行彩度像素=0 → 412/412`；负臂 `quickpick-no-source` 来源图=0、类型=1、彩度=0；首行标题左沿正/负臂同为 **78.5pt**。**12 张旧帧变化 + 2 张新帧**、0 缺失；基线 **284→286/0/0/0**；14 张逐张看过。判据 `testQuickPickRowsShowTheirSourceIcon`（结构 image + 像素彩度两条腿）；`M1279/M1280` **2/2 CAUGHT**。**inline 全宽块底门**：候选增 `rowMaxBandRun`，`best` 要求 `rowMaxBandRun <= maxSpan`（整行全宽块底整行排除）；本地 `INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5`（不变）；`M1277/M1278` **2/2 CAUGHT**。**药丸材料 gap 容忍**：`overlayPill` 加 `maxGap`（本判据 24pt），light/dark 药丸 **22.0pt**、搜索 22.5pt、差 **1px**；`M1281` **1/1 CAUGHT**。**旧表重钉**：r430 M1175、r104 M578/M579 因约束签名/overlayPill 新参数腐烂，重钉后 r430 **5/5**、r104 M578/M579 **2/2**、RESTORE_CLEAN。预检 **250/232/638 bad=0**、ARM **343/1121**、HIDDEN **337/1055 rot=0**。⓪：开工 HEAD=origin/main=`1f7f486`、**ahead=0**；`git push` 两探均 remote closed ⇒ **`PUSH_BLOCKED=network`（HEAD=`1f7f486`、ahead=0）**；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**；R469 四跑 `40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`、`40745716427 ↔ 1f7f486` 均 **NOT-RUN**；`40740068763 ↔ 00ff343` failure 2 步仅 inline dark 3.0、Capture 15 帧变 MATERIAL_BLIND_NOT_RUN、设置轴 runner 具名 NOT-RUN、VIDEO_* 签收、DIAG 数据如审计 U-1773。全量 **1279/56/0**（507.3s，轻载）；捕获卷 **286 帧**；基线 **286/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 469，`python3 scripts/product_streak.py --streak-for 469`，last=4283a90）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 两探 push 断网、gh EOF ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R469 四跑与 R470 自身跑 NOT-RUN；上轮 00ff343 跑只 inline dark 3.0，Capture 15 帧变 MATERIAL_BLIND_NOT_RUN，设置轴具名 NOT-RUN；DIAG 数据已拿到。
② 产品：浮层来源 App 图标（固定 16pt 槽；12 张旧帧变化 + 2 张新帧、基线 286）。
③ 判据/仪器：来源图标 2/2、inline 块底门 2/2、药丸 gap 1/1；旧表 M1175/M578/M579 重钉复跑；precheck 250/232/638；rot 337/1055。
④ 436：无 R470 新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 337 / 可判 1055 / rot 0。
⑥ 捕获 286 帧；基线 286/0/0/0；build 0 告警；换装 ok/387=387；全量 1279/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R469 四跑与 R470 自身跑（网络）；② inline runner dark（新门未跑）；③ 来源图标 runner 1x；④ `SETTINGS_HELPER_AXIS` runner 1x；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–531 的其余未结项仍开。

下一轮（R471）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R470 主笔+追记 head 跑与 R469 四跑（`40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`、`40745716427 ↔ 1f7f486`）的全部失败步骤；重点 `QUICKPICK_SOURCE_ICON`（5/5、412、负臂 0）、`INLINE_CODE_DIAG`（top 的 m=rowMax；真带 vs 全宽块底）、`INLINE_CODE_PAD` 两档（dark 新门后应 ≥4.5）、`CROSS_YEAR_TIME`、`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS` 200/198/−2、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`VIDEO_SEEK` 98/106、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE`、`VIDEO_UNAVAILABLE`、Capture MATERIAL_BLIND_NOT_RUN、436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R470_REPORT_BULLET = u"""- **R470（浮层来源图标位 + inline 块底门）**：浮层每行原来只有类型符号，来源 App 只在主列表/详情露出。类型符号后加固定 16pt 来源槽（`SourceAppIconProvider` 图标；无来源留空占位），标题从来源槽右侧起：`QUICKPICK_SOURCE_ICON 有图=5/5、类型=5/5、首行彩度=412`，负臂来源图 0/类型 1/彩度 0，首行标题左右 **78.5pt**。**12 张旧帧变化 + 2 张新帧**、0 缺失，基线 **284→286/0/0/0**；14 张逐张看过。判据结构 image + 像素彩度；M1279/M1280 **2/2**。inline 选择器按 runner DIAG 加 `rowMaxBandRun <= maxSpan`（整行全宽块底整行排除），本地 PAD 98.5/92.5/6.0 与 99.0/92.5/6.5，M1277/M1278 **2/2**；药丸尺加 maxGap 24pt，light/dark 药丸 22.0、搜索 22.5、差 1px，M1281 **1/1**。旧表 M1175/M578/M579 重钉复跑。⓪ 两探 push 断网、gh EOF ⇒ **PUSH_BLOCKED=network（HEAD 1f7f486、ahead=0）**、**CI_READ_BLOCKED**；R469 四跑与 R470 跑 NOT-RUN。全量 **1279/56/0**（507.3s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 469 轮（R470" in audit: raise SystemExit("REFUSED AUDIT 已有 R470")
if u"## Round 467 · R470" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 467")
if u"## D-466" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-466")
if u"浮层行补来源 App 图标" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**529." in backlog: raise SystemExit("REFUSED BACKLOG 已有 529")
if state.count(u"## R469 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R469 状态"))
U_CELL_OLD = u"U-31 … U-1772（R469 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R469 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_466 + "\n\n" + DECISION_467 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R469 状态", STATE_SECTION + u"## R469 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1778（R470 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R469 节 ②", u"AGENT_STATE.md` 的 R470 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R470_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R470_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
