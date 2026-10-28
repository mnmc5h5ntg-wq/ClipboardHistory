#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R452 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 450 轮（R451 · 2026-10-28"
AUDIT_SECTION = u"""## 第 451 轮（R452 · 2026-10-28 · U-1683…U-1687）：推荐权重滑块补 100% 中心刻度（9 条滑轨中心各 1×5pt 竖墨、邻列 0.0pt；旧形状只有 1pt 原生小点；8 张推荐面帧变化、基线 260）（产品 1 文件，权重刻度位）

- **U-1683：⓪ push 与六跑。** 开工 remote=`eb04e37`、ahead=3，一次快进 push **`eb04e37..86044bf` success**（三笔：cade8bb/b868327/86044bf），HEAD=origin/main=`86044bf`、**ahead=0**。已读：**`40636558557 ↔ 667d1a2` success**，`TASK_DIM light 勾选=158.0 未勾选=115.1 差=+42.9 墨数=376/426`、`dark 128.4/166.4 差=−38.0 墨数=469/492`（1x 上符号与地板都成立）；同跑 Motion floor `judged=4/5 executed=77 not-run=notice-banner`、红 0。**`40636617018 ↔ eb04e37` success**（R450 预记 head）。**`40634880705 ↔ 9743379` failure**：① `testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ `RUNNER_SCROLL_SESSION_FLAKE`（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R453 重跑复核）；② Motion floor `testMarkdownModeLabelChange` 1<2；同跑 QUICKPICK_HINT 400/519 签收。`40632882239 ↔ 224b8ee` success、`40629867848 ↔ 107f2b3` success、`40629776895 ↔ 0737460` failure 仅 Motion floor、`40623613789 ↔ ecb8e69` failure 仅 Motion floor（receipt 1<2）、`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）。436 只复核 Motion floor：`judged=4/5 executed=77 not-run=notice-banner`、红 0；两个采样红原样重跑，不改门槛、不重猜 `must_judge`。
- **U-1684：① 腐烂与预检。** `HIDDEN_ARMS 表=317 可判=1015 rot=0`；`NEEDLE_PRECHECK tables=230 covered=212 arms=598 bad=0`、`ARM_TOTAL files=323 arms=1081`。本轮改的是 `WeightSliderRow` 的 overlay，没有弄断旧针。
- **U-1685：② 推荐权重滑块的 100% 中心刻度。** 缺陷形状：0–200% 的量程里，默认位（100%）只有一排 1pt 原生小点，滑杆移开后没有"默认在哪"的参照。修法：`Slider` 上叠一条 1×5pt `Capsule`（`Color.secondary.opacity(0.55)`、中心对齐、下移 9pt、`allowsHitTesting(false)`）。旧/新：`WEIGHT_CENTER_TICK light 轨=9 中心最高=5.0pt 邻列最高=0.0pt`、`dark 5.0/0.0`（判据先按长灰条找 9 条滑轨，再在轨道下方 4..14pt 量中心列/±20pt 邻列的最长竖墨；旋钮阴影贴着轨道，不进这一带）。**8 张推荐面帧变化**（weights、weights-adjusted、settings-recommendations、settings-recommendations-tall × 亮/暗）、0 新增/缺失；基线名单仍 **260**（`FRAME_BASELINE_UPDATED=260`，同 commit 更新）；已看亮/暗 9 条滑杆：中心刻度都在旋钮正下方。Store 未动（1108 行/52 方法/最长 66）。
- **U-1686：判据与刀。** 帧判据 `testWeightSlidersMarkTheDefaultCenter`：9 条滑轨，每条中心列竖墨 ≥3.5pt、邻列 ≤2pt（旧形状中心列与邻列一样只有小点/0）。`M1238`（去掉 overlay 整块）⇒ CAUGHT；`M1239`（刻度 5→1pt）⇒ CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes。没有新增纯函数：这是 view-only 的叠层，几何/颜色由判据的 9 条滑轨各自复核。
- **U-1687：八步与具名 NOT-RUN。** build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`）；捕获卷 **260 帧**、`COMPARED=260 CHANGED=0 MISSING=0 ADDED=0`；全量 **1240/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 451，`python3 scripts/product_streak.py --streak-for 451`，last=cade8bb）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40640660665 ↔ 86044bf`（R451 head，读时 in_progress）；② R452 自身跑（提交后创建）；③ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的滚动红；R453 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ `WEIGHT_CENTER_TICK` 的 runner 1x 读数（若设置内容列平涂，判据会具名 NOT_RUN；本轮只读本地 2x 5.0/0.0）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度的端点标签（483）；㊻ 437–483 的未结项仍开。

"""

ITER_SECTION = u"""## Round 449 · R452（第 451 轮 · 2026-10-28）：推荐权重滑块补 100% 中心刻度（9 条滑轨中心各 1×5pt 竖墨、邻列 0.0pt；旧形状只有 1pt 原生小点；8 张推荐面帧变化、基线 260）

0–200% 量程里默认位没有参照。`WeightSliderRow` 在原生 Slider 上叠一条 1×5pt Capsule（secondary 0.55、中心对齐、下移 9pt、不挡点击）。判据在 `weights` 组件帧：先按长灰条找 9 条滑轨（旋钮把轨道截成两段，取首末跨度），再在轨道下方 4..14pt 量中心列/±20pt 邻列最长竖墨；读数 `WEIGHT_CENTER_TICK light 轨=9 中心最高=5.0pt 邻列=0.0pt`、dark 同形。8 张帧变化（weights/weights-adjusted/settings-recommendations/tall × 亮暗）、0 新增，基线 260/0/0/0；已看 9 条滑杆。M1238/M1239 2/2。⓪：push eb04e37..86044bf success、ahead=0；TASK_DIM 1x 签收（亮 158.0/115.1 +42.9、暗 128.4/166.4 −38.0）；9743379 的滚动会话采样红（同代码两跑 success）+ Motion 模式标签 1<2；667d1a2/eb04e37 两跑 success。全量 1240/57/5；捕获 260；换装 ok/SHA_MATCH=1/381=381；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 weights 与 settings-recommendations 逐张看过：9 条滑杆的中心刻度都在旋钮正下方。 |
| 判据有效性 | 15/15 | 9 条滑轨逐条量中心/邻列竖墨（≥3.5pt vs ≤2pt）；轨道被旋钮截断用首末跨度；M1238/M1239 2/2。 |
| 假绿防御 | 15/15 | 量窗下移到轨道下方 4..14pt 排除旋钮阴影；旧形状（无刻度/1pt）由两把刀钉住。 |
| 产品面推进 | 14/15 | 默认位第一次有可见参照；Store 不动；扣 1：0%/200% 端点仍无标签（483）。 |
| 台账一致性 | 15/15 | U-1683…U-1687、D-448、push 86044bf、260 帧/1240、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | TASK_DIM 1x 读数与本地 2x 分开写；9743379 的滚动/Motion 红原文照记；1x 刻度读数未读时具名。 |
| 可复核性 | 15/15 | 9/5.0/0.0、轨道下方 4..14pt、刀号与 precheck 230/212/598、rot 317/1015、基线 260 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_448 = u"""## D-448 权重滑块补 100% 中心刻度（R452）

- 背景：0–200% 量程里默认位（100%）只有一排 1pt 原生小点，滑杆移开后没有"默认在哪"的参照。
- 决定：`WeightSliderRow` 在 Slider 上叠 1×5pt `Capsule`（`Color.secondary.opacity(0.55)`、中心对齐、下移 9pt、不挡点击）。
- 理由：中心是默认位；刻度比原生点更强但不抢眼；view-only，不碰 Store。
- 兼容性/迁移：8 张推荐面帧变化、0 新增；基线 260 同 commit 更新。
- 边界：0%/200% 端点仍无标签（483）；设置内容列 1x 平涂时 runner 读数可能具名 NOT_RUN。
- 回滚：删 overlay 即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 推荐权重滑块补 100% 中心刻度（9 条滑轨中心各 1×5pt 竖墨、邻列 0.0pt；旧形状只有 1pt 原生小点；8 张推荐面帧变化、基线 260）（R452 / 第 451 轮 / Round 449 / U-1683…U-1687 · 产品 1 文件，权重刻度位）

"""

BACKLOG_SECTION = u"""449 追记（R452 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R452 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R452 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R452 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R452 · 仍开）：菜单具名标记仍未发射。

455 追记（R452 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R452 · 仍开）：跨年记录仍无年份。

457 追记（R452 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R452 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R452 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R452 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R452 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R452 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R452 · 仍开）：展开态已加载内容仍无帧。

464 追记（R452 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R452 · 仍开）：HTML 引用块没有导引线。

466 追记（R452 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R452 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R452 · 仍开）：HTML 代码块没有行号。

469 追记（R452 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R452 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R452 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R452 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R452 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R452 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R452 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R452 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R452 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R452 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R452 · 仍开）：QuickPick 键盘提示 1x 已签收；12 帧名单仍只在本地。

481 追记（R452 · 仍开）：HTML 任务列表没有同一条完成态弱化。

482 追记（R452 · 仍开）：HTML 渲染路径的列表没有同一条悬挂制表位。

**483. 权重滑块只有中心刻度，0% / 200% 端点没有标签**（R452 观察）
    现象：R452 在 100% 默认位加了中心刻度；量程两端仍只有原生小点，用户不知道两端就是 0% / 200%（那句说明写在卡片头部，离滑杆较远）。
    修法：在滑杆下方两端加 0% / 200% 小标签（或端点刻度加粗），补一帧与端点墨量判据。
"""

STATE_SECTION = u"""## R452 状态（2026-10-28 · 本地 · 第 451 轮 / Round 449）：推荐权重滑块补 100% 中心刻度（9 条滑轨中心各 1×5pt 竖墨、邻列 0.0pt；旧形状只有 1pt 原生小点；8 张推荐面帧变化、基线 260）；TASK_DIM 1x 签收（亮 158.0/115.1、暗 128.4/166.4）；9743379 跑滚动会话采样红 + Motion 模式标签 1<2（产品 1 文件，权重刻度位）

最后更新：2026-10-28（本地 · R452 / 第 451 轮 / Round 449）：0–200% 量程里默认位只有一排 1pt 原生小点。`WeightSliderRow` 在 Slider 上叠一条 1×5pt `Capsule`（`Color.secondary.opacity(0.55)`、中心对齐、下移 9pt、`allowsHitTesting(false)`）。读数：`WEIGHT_CENTER_TICK light 轨=9 中心最高=5.0pt 邻列最高=0.0pt`、`dark 5.0/0.0`（先按长灰条找 9 条滑轨——旋钮把轨道截成两段，取首末跨度；再在轨道下方 4..14pt 量中心列/±20pt 邻列的最长竖墨；旋钮阴影贴着轨道，不进这一带）。**8 张推荐面帧变化**（weights、weights-adjusted、settings-recommendations、tall × 亮/暗）、0 新增/缺失；基线名单 **260**（同 commit 更新）；已看亮/暗 9 条滑杆的中心刻度。`M1238/M1239` **2/2**（去掉 overlay / 刻度缩成 1pt）。预检 **230/212/598 bad=0**、ARM **323/1081**、HIDDEN **317/1015 rot=0**。⓪：一次快进 push **`eb04e37..86044bf` success**（三笔）、HEAD=origin/main=`86044bf`、**ahead=0**；**`40636558557 ↔ 667d1a2` success**：`TASK_DIM light 勾选=158.0 未勾选=115.1 差=+42.9 墨数=376/426`、`dark 128.4/166.4 差=−38.0 墨数=469/492`，Motion floor `judged=4/5 executed=77 not-run=notice-banner` 红 0；**`40636617018 ↔ eb04e37` success**；**`40634880705 ↔ 9743379` failure**：`testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ `RUNNER_SCROLL_SESSION_FLAKE`（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R453 重跑复核）+ Motion floor `testMarkdownModeLabelChange` 1<2；同跑 QUICKPICK_HINT 400/519 签收；`40629776895`/`40623613789` failure 仅 Motion floor、`40620912699` failure 1 步（dark 行带，已修）；`40640660665 ↔ 86044bf`（R451 head）读时 in_progress ⇒ NOT-RUN。本地全量 **1240/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **260 帧**；基线 **260/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 451，`python3 scripts/product_streak.py --streak-for 451`，last=cade8bb）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push eb04e37..86044bf success、ahead=0；TASK_DIM 1x 签收；9743379 的滚动会话采样红（RUNNER_SCROLL_SESSION_FLAKE）与 Motion 模式标签 1<2 原文已读；667d1a2/eb04e37 两跑 success；R451 head 未读 ⇒ NOT-RUN。
② 产品：权重滑块 100% 中心刻度（9/5.0/0.0；8 帧变化、基线 260）。
③ 判据：M1238/M1239 2/2；帧判据 9 条滑轨逐条量中心/邻列；precheck 230/212/598；hidden rot 0。
④ 436：Motion floor judged=4/5 executed=77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 317 / 可判 1015 / rot 0。
⑥ 捕获 260 帧；基线 260/0/0/0；build 0 告警；换装 ok；本地全量 1240/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40640660665 ↔ 86044bf`（R451 head，in_progress）；② R452 自身跑；③ `RUNNER_SCROLL_SESSION_FLAKE`（R453 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ `WEIGHT_CENTER_TICK` 的 runner 1x 读数（若设置内容列平涂，判据会具名 NOT_RUN）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度端点标签（483）；㊻ 437–483 的未结项仍开。

下一轮（R453）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R452 主笔+追记 head 跑、`40640660665 ↔ 86044bf`（R451 head，含 `LIST_HANG_STYLE`）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40636617018 ↔ eb04e37` 与 `40634880705 ↔ 9743379`（滚动会话采样红原文）、`40632882239 ↔ 224b8ee`（success；QUICKPICK_HINT 400/519）、`40629867848 ↔ 107f2b3`（success）、`40629776895 ↔ 0737460`、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `WEIGHT_CENTER_TICK` 两档 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`TASK_DIM` 158.0/115.1/+42.9 与 128.4/166.4/−38.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R452_REPORT_BULLET = u"""- **R452（权重刻度位）**：0–200% 量程里默认位（100%）只有一排 1pt 原生小点，滑杆移开后没有"默认在哪"的参照。`WeightSliderRow` 在 Slider 上叠 1×5pt `Capsule`（`secondary.opacity(0.55)`、中心对齐、下移 9pt、不挡点击）。判据在 `weights` 组件帧：先按长灰条找 9 条滑轨（旋钮把轨道截成两段，取首末跨度），再在轨道下方 4..14pt 量中心列/±20pt 邻列最长竖墨：`WEIGHT_CENTER_TICK light 轨=9 中心最高=5.0pt 邻列最高=0.0pt`、dark 5.0/0.0（旧形状中心与邻列一样只有小点）。**8 张推荐面帧变化**（weights/weights-adjusted/settings-recommendations/tall × 亮暗）、0 新增，基线 **260/0/0/0**；已看亮/暗 9 条滑杆。`M1238/M1239` **2/2**；预留判据无新纯函数（view-only 叠层，9 条滑轨各自复核）；预检 230/212/598 bad=0、ARM 323/1081、HIDDEN 317/1015 rot=0。⓪：一次快进 push **`eb04e37..86044bf` success**、HEAD=origin/main=`86044bf`、ahead=0；**`40636558557 ↔ 667d1a2` success**（`TASK_DIM light 158.0/115.1 +42.9、dark 128.4/166.4 −38.0`；Motion floor 4/5/77、红 0）、`40636617018 ↔ eb04e37` success；`40634880705 ↔ 9743379` failure：`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE`（同代码 224b8ee/107f2b3 两跑 success）+ Motion `testMarkdownModeLabelChange` 1<2；同跑 QUICKPICK_HINT 400/519；`40640660665 ↔ 86044bf`（R451 head）读时 in_progress ⇒ NOT-RUN。全量 **1240/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 260 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 451 轮（R452" in audit: raise SystemExit("REFUSED AUDIT 已有 R452")
if u"## Round 449 · R452" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 449")
if u"## D-448" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-448")
if u"推荐权重滑块补 100% 中心刻度" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**483." in backlog: raise SystemExit("REFUSED BACKLOG 已有 483")
if state.count(u"## R451 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R451 状态"))
U_CELL_OLD = u"U-31 … U-1682（R451 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R451 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_448 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R451 状态", STATE_SECTION + u"## R451 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1687（R452 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R451 节 ②", u"AGENT_STATE.md` 的 R452 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R452_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R452_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
