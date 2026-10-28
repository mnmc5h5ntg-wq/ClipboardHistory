#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R451 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 449 轮（R450 · 2026-10-28"
AUDIT_SECTION = u"""## 第 450 轮（R451 · 2026-10-28 · U-1678…U-1682）：折行列表项的续行回到首行正文同一竖轴（制表位 16.0 == headIndent 16.0、首行缩进 0.0；旧形状默认制表位 28 vs 续行 16 = 错开 12pt；2 张新帧 + 4 张旧帧变化、基线 258→260）（产品 2 文件，列表悬挂缩进位）

- **U-1678：⓪ push 与跑。** 开工 remote=`eb04e37`、ahead=0，`git push` 为 **no-op**。`gh run list` 读到 `40636558557 ↔ 667d1a2`（R450 head，含 `TASK_DIM`）、`40634880705 ↔ 9743379`（R449 预记 head）、`40636617018 ↔ eb04e37`（R450 预记 head）读时 **in_progress**；稍后 **`40634880705 ↔ 9743379` completed failure**，读原文：① `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` —— `产品时长下没有任何中间 origin（[0.0, 1430.0, 1430.0, 1430.0]）⇒ 这是瞬移，不是过程`；同代码的 `40632882239 ↔ 224b8ee` 与 `40629867848 ↔ 107f2b3` 都是 **success**，故这是**滚动套件的 runner 会话/动画钟采样红**（具名 `RUNNER_SCROLL_SESSION_FLAKE`，不改门槛；R452 ⓪ 重跑复核）；② Motion floor `MOTION_FLOOR_SUITE_RED=1`＝`testMarkdownModeLabelChangeIsAVisibleProcess`（1 帧<2）——与 0737460 同一个采样红，未复现于其他跑。同跑 `QUICKPICK_HINT light 400、dark 519（地板 12）文本/位置全对`；`40629776895 ↔ 0737460` failure 仅 Motion floor（同 markdown 模式标签 1<2）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（receipt 1<2）；`40629867848 ↔ 107f2b3` success（R448 读数已签收）、`40632882239 ↔ 224b8ee` success（QUICKPICK_HINT 400/519、Motion 红 0）。`40636558557/40636617018` 的 `TASK_DIM` 尚未读到 ⇒ NOT-RUN，R452 ⓪ 必读。436 只复核 Motion floor：`judged=5/5 executed=77`；两个采样红原样重跑，不改门槛、不重猜 `must_judge`。
- **U-1679：① 腐烂与预检。** `HIDDEN_ARMS 表=316 可判=1013 rot=0`；`NEEDLE_PRECHECK tables=229 covered=211 arms=596 bad=0`、`ARM_TOTAL files=322 arms=1079`。本轮改的是 `paragraphStyle` 的制表位，没有弄断旧针。
- **U-1680：② 列表悬挂缩进。** 缺陷形状：`headIndent` 是 `firstLineHeadIndent + 16`，但首行正文的 `\\t` 走**默认制表位 28pt** —— 首行正文 28、续行 16，多行列表项一折行就错开 12pt（现有夹具都是短项，R450 前没暴露）。修法：新 `ListHangingIndent` 纯策略（`max(16, 标记宽 + 2)`）；`MarkdownPresentation.hangingIndent` 用标记字体量宽；列表块的 `paragraphStyle` 设一条显式制表位，位置 == `headIndent`；两三位数编号的正文列跟着标记变宽。旧/新（产品文本视图的 `NSParagraphStyle`）：`LIST_HANG_STYLE light 制表位数=1 制表位=16.0 续行=16.0 首行=0.0pt`、`dark 同形`（旧形状制表位数 0、默认 28 ⇒ 首行正文 28 vs 续行 16）。夹具 `detail-list-wrap`（两条必须折行的列表项）；**2 张新帧、4 张旧帧变化**（`detail-markdown-rendered` 与 `detail-tasks` 的列表文字从 48 移到 36），基线 **258→260 / 0/0/0**；已看亮/暗：两条列表的首行正文与续行都在 36pt 同轴，任务项文字也更贴近标记。Store 未动（1108 行/52 方法/最长 66）。
- **U-1681：判据、刀与一次尺的换代。** 新单测 `ListHangingIndentTests` 4 条（16pt 最小列、宽标记推出、列表制表位==headIndent、段落无悬挂缩进）+ 产品入口判据 `testWrappedListItemsAlignTheirContinuation`（真实 `DetailView` 的文本存储里读该段 `NSParagraphStyle`：tabStops 恰好 1 个且位置==headIndent、headIndent>firstLine）。**尺换代记**：第一版用裸像素读「标记之后正文簇 vs 续行」，但这张帧的 `NSBitmapImageRep` 指针通道读出的带左沿与同文件 PIL 读数不一致（Python 22/36.5 vs Swift 48/44），换成段样式结构量后两者才对上；没有把对不上的像素读数当结论。`M1236`（去掉显式制表位）⇒ 单测+产品判据 CAUGHT；`M1237`（headIndent 退回首行）⇒ 同上 CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes。第一次 0 告警门咬到新测试里 `allSubviews` 的 MainActor 隔离（同 R449 的坑）—— 加 `@MainActor` 后冷编 0/0/0。
- **U-1682：八步与具名 NOT-RUN。** build **0 告警**（第一次 1 warning 已修）；捕获卷 **260 帧**、`COMPARED=260 CHANGED=0 MISSING=0 ADDED=0`；全量 **1239/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 450，`python3 scripts/product_streak.py --streak-for 450`，last=eb836bf）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40636558557 ↔ 667d1a2`（TASK_DIM 未读）；② `40636617018 ↔ eb04e37`（同上）；③ R451 自身跑（提交后创建）；④ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的 `testProductDurationRevealStillMovesOverTime` 无中间 origin；同代码两跑 success，R452 重跑复核）；⑤ 436 的 markdown 模式标签采样红（1<2；与 0737460 同源，未复现于其他跑）；⑥ HTML 列表缩进无同一制表位（482）；⑦ HTML 任务列表无弱化（481）；⑧ HTML 表格体行无同一条线（479）；⑨ 设置内容列 1x 平涂；⑩ 设置脚注带 1x；⑪ 主窗口 content 帧 1x；⑫ 高夹具 1x；⑬ 13+ 菜单像素/标题；⑭ 真实拖拽；⑮ Dock 像素；⑯ 源图标最小窗文字 1x；⑰ 本地全量 5 条滚动红（449）；⑱ 2x/extended；⑲ 固定块揭示偏移（455）；⑳ 跨年时间（456）；㉑ 主列表暗档文字盲区（457）；㉒ 真机/多屏（447）；㉓ 真菜单栏、12 实时腿；㉔ `table-lazy-rows`；㉕ HTML 六档字号（460）；㉖ 清除 × 命中区（461）；㉗ 分隔线令牌（462）；㉘ 展开态已加载内容无帧（463）；㉙ 其它自绘控件帮助文本（464）；㉚ HTML 引用块无导引线（465）；㉛ HTML 表格表头无同档（466）；㉜ 100+ 行行号（467）；㉝ HTML 代码块行号（468）；㉞ 行号选中/滚动两态（469）；㉟ 关于页 1x 盲（470）；㊱ M613 机器前提（472）；㊲ 真机 vibrant 暗档（473）；㊳ 长来源截断（474）；㊴ bundle ID 未搜（475）；㊵ 长首行标签省略无帧（476）；㊶ HTML 代码块无语言标签（477）；㊷ HTML `<hr>` 无通栏线（478）；㊸ HTML 表格体行无同一条线（479）；㊹ QuickPick 键盘提示 1x（480）；㊺ 437–482 的未结项仍开。

"""

ITER_SECTION = u"""## Round 448 · R451（第 450 轮 · 2026-10-28）：折行列表项的续行回到首行正文同一竖轴（制表位 16.0 == headIndent 16.0、首行缩进 0.0；旧形状默认制表位 28 vs 续行 16 = 错开 12pt；2 张新帧 + 4 张旧帧变化、基线 260）

缺陷是首行正文的 `\\t` 走默认制表位 28、续行走 headIndent 16。新 `ListHangingIndent`（max(16, 标记宽+2)）；`hangingIndent` 量标记宽；列表块的段落样式设一条显式制表位，位置==headIndent。读数 `LIST_HANG_STYLE light 制表位数=1 制表位=16.0 续行=16.0 首行=0.0`、dark 同形；旧形状制表位数 0、首行 28 vs 续行 16。夹具 `detail-list-wrap`；2 张新帧 + 4 张旧帧变化（markdown-rendered 与 tasks 的列表文字移到 36），基线 260/0/0/0；已看亮/暗同轴。第一版像素簇读数与同文件 PIL 不一致，换成段样式结构量；M1236/M1237 2/2；第一次 0 告警门咬到 allSubviews 的 MainActor 隔离，修后 0。⓪：开工 no-op push；9743379 跑 failure 读到 `testProductDurationRevealStillMovesOverTime` 无中间 origin（同代码 224b8ee/107f2b3 success ⇒ RUNNER_SCROLL_SESSION_FLAKE）+ Motion floor markdown 模式标签 1<2；QUICKPICK_HINT 400/519 签收；667d1a2/eb04e37 跑 TASK_DIM 未读。全量 1239/57/5；捕获 260；换装 ok/SHA_MATCH=1/381=381；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-list-wrap 逐张看过：两条的首行正文与续行都在 36pt 同轴；任务项也看。 |
| 判据有效性 | 15/15 | 产品文本视图的段落样式：tabStops 恰 1 且位置==headIndent、headIndent>firstLine；M1236/M1237 2/2。 |
| 假绿防御 | 15/15 | 像素簇尺与 PIL 不一致时没有采信，换结构量并写明；旧形状（无显式制表位）由刀钉住；0 告警红照记。 |
| 产品面推进 | 14/15 | 修的是所有折行列表项的续行对齐 + 宽编号列；Store 不动；扣 1：HTML 列表未覆盖（482）。 |
| 台账一致性 | 15/15 | U-1678…U-1682、D-447、no-op push/ahead=0、260 帧/1239、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 9743379 的滚动红与 Motion 红原文照记并对照同代码 success；像素尺换代写明；两新跑未读具名。 |
| 可复核性 | 15/15 | 16.0/16.0/0.0、首行 28 vs 续行 16、刀号与 precheck 229/211/596、rot 316/1013、基线 260 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_447 = u"""## D-447 列表项的显式制表位与 headIndent 同值（R451）

- 背景：`headIndent` 是 16，但首行正文的 `\\t` 走默认制表位 28 —— 折行列表项首行正文 28、续行 16，错开 12pt；现有夹具都是短项。
- 决定：新 `ListHangingIndent`（max(16, 标记宽+2)）；`hangingIndent` 用标记字体量宽；列表块的 `paragraphStyle` 设一条显式制表位，位置 == headIndent；两三位数编号的列跟着变宽。
- 理由：首行正文与续行必须同轴；宽度跟标记走，不靠默认 28；纯策略不碰 Store（1108/66）。
- 兼容性/迁移：新夹具 `detail-list-wrap`；`detail-markdown-rendered`/`detail-tasks` 的列表文字从 48 移到 36；基线 258→260。
- 边界：HTML 列表未接（482）；裸像素簇尺在这张 rep 上不可靠，判据读产品段落样式。
- 回滚：删 `tabStops` 与 `hangingIndent` 的使用、恢复 `headIndent = firstLine + 16`；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 折行列表项的续行回到首行正文同一竖轴（制表位 16.0 == headIndent、首行缩进 0.0；旧形状默认制表位 28 vs 续行 16；2 张新帧 + 4 张旧帧变化、基线 260）（R451 / 第 450 轮 / Round 448 / U-1678…U-1682 · 产品 2 文件，列表悬挂缩进位）

"""

BACKLOG_SECTION = u"""449 追记（R451 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R451 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R451 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R451 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R451 · 仍开）：菜单具名标记仍未发射。

455 追记（R451 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R451 · 仍开）：跨年记录仍无年份。

457 追记（R451 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R451 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R451 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R451 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R451 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R451 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R451 · 仍开）：展开态已加载内容仍无帧。

464 追记（R451 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R451 · 仍开）：HTML 引用块没有导引线。

466 追记（R451 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R451 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R451 · 仍开）：HTML 代码块没有行号。

469 追记（R451 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R451 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R451 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R451 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R451 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R451 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R451 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R451 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R451 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R451 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R451 · 仍开）：QuickPick 键盘提示的 runner 1x 像素读数已签收（400/519）；12 帧名单仍只在本地。

481 追记（R451 · 仍开）：HTML 任务列表没有同一条完成态弱化。

**482. HTML 渲染路径的列表没有同一条悬挂制表位**（R451 观察）
    现象：R451 只修了 Markdown 渲染路径的列表制表位；HTML 预览走 `NSAttributedString` 的 HTML 导入，`<li>` 的续行缩进是另一条路径，没有 `tabStops` == `headIndent` 的契约，也没有折行帧。
    修法：给 HTML 预览拍一张折行列表帧，量首行正文与续行；若导入器不保留制表位，用同一 `ListHangingIndent` 在 HTML 路径补。
"""

STATE_SECTION = u"""## R451 状态（2026-10-28 · 本地 · 第 450 轮 / Round 448）：折行列表项的续行回到首行正文同一竖轴（制表位 16.0 == headIndent 16.0、首行缩进 0.0；旧形状默认制表位 28 vs 续行 16 = 错开 12pt；2 张新帧 + 4 张旧帧变化、基线 258→260）；9743379 跑读到滚动会话采样红 + Motion 模式标签采样红（同代码两跑 success）（产品 2 文件，列表悬挂缩进位）

最后更新：2026-10-28（本地 · R451 / 第 450 轮 / Round 448）：`headIndent` 是 `firstLineHeadIndent + 16`，但首行正文的 `\\t` 走默认制表位 28 —— 首行正文 28、续行 16，折行列表项错开 12pt。新 `ListHangingIndent` 纯策略（`max(16, 标记宽 + 2)`）；`MarkdownPresentation.hangingIndent` 用标记字体量宽；列表块的 `paragraphStyle` 设一条显式制表位，位置 == `headIndent`。读数：`LIST_HANG_STYLE light 制表位数=1 制表位=16.0 续行=16.0 首行=0.0pt`、`dark 同形`（旧形状制表位数 0、默认 28 ⇒ 28 vs 16）。夹具 `detail-list-wrap`；**2 张新帧、4 张旧帧变化**（`detail-markdown-rendered`/`detail-tasks` 的列表文字从 48 移到 36），基线 **258→260 / 0/0/0**；已看亮/暗同轴。**尺换代记**：第一版裸像素簇读数与同文件 PIL 不一致（Python 22/36.5 vs Swift 48/44），换成产品文本视图的段落样式结构量；没有把对不上的像素当结论。`M1236/M1237` **2/2**；新单测 4 条 + 产品入口判据；第一次 0 告警门咬到新测试 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0。预检 **229/211/596 bad=0**、ARM **322/1079**、HIDDEN **316/1013 rot=0**。⓪：开工 remote=`eb04e37`、ahead=0，`git push` 为 **no-op**；`40634880705 ↔ 9743379` 读时 in_progress、稍后 **failure**：`SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ 具名 **`RUNNER_SCROLL_SESSION_FLAKE`**（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R452 重跑复核）+ Motion floor `testMarkdownModeLabelChange` 1<2（与 0737460 同源）；同跑 `QUICKPICK_HINT 400/519` 签收；`40636558557 ↔ 667d1a2`（TASK_DIM）与 `40636617018 ↔ eb04e37` 尚未读到 ⇒ NOT-RUN；`40629867848 ↔ 107f2b3`/`40632882239 ↔ 224b8ee` success；`0737460` failure 仅 Motion floor；`36284e1` failure 1 步（dark 行带，已修）、`fe956e3` 2、`eeccad0` 1。本地全量 **1239/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **260 帧**；基线 **260/0/0/0**；build **0 告警**（第一次 1 warning 已修）；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 450，`python3 scripts/product_streak.py --streak-for 450`，last=eb836bf）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push（remote eb04e37、ahead=0）；9743379 跑读到滚动会话采样红（RUNNER_SCROLL_SESSION_FLAKE）与 Motion 模式标签 1<2；QUICKPICK_HINT 400/519 签收；667d1a2/eb04e37 的 TASK_DIM 未读 ⇒ NOT-RUN。
② 产品：折行列表项续行回到首行正文同轴（制表位 16/续行 16/首行 0；2 新帧 + 4 旧帧变化、基线 260）。
③ 判据：M1236/M1237 2/2；新单测 4 条 + 产品入口段样式判据；像素簇尺与 PIL 不一致时换代记；第一次 0 告警门 1 条 MainActor 隔离，修后 0；precheck 229/211/596；hidden rot 0。
④ 436：Motion floor 5/5/77；markdown 模式标签采样红与 0737460 同源，未复现于其他跑；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 316 / 可判 1013 / rot 0。
⑥ 捕获 260 帧；基线 260/0/0/0；build 0 告警；换装 ok；本地全量 1239/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40636558557 ↔ 667d1a2`（TASK_DIM 未读）；② `40636617018 ↔ eb04e37`（同上）；③ R451 自身跑；④ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的 testProductDurationRevealStillMovesOverTime；R452 重跑复核）；⑤ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑥ HTML 列表缩进无同一制表位（482）；⑦ HTML 任务列表无弱化（481）；⑧ HTML 表格体行无同一条线（479）；⑨ 设置内容列 1x 平涂；⑩ 设置脚注带 1x；⑪ 主窗口 content 帧 1x；⑫ 高夹具 1x；⑬ 13+ 菜单像素/标题；⑭ 真实拖拽；⑮ Dock 像素；⑯ 源图标最小窗文字 1x；⑰ 本地全量 5 条滚动红（449）；⑱ 2x/extended；⑲ 固定块揭示偏移（455）；⑳ 跨年时间（456）；㉑ 主列表暗档文字盲区（457）；㉒ 真机/多屏（447）；㉓ 真菜单栏、12 实时腿；㉔ `table-lazy-rows`；㉕ HTML 六档字号（460）；㉖ 清除 × 命中区（461）；㉗ 分隔线令牌（462）；㉘ 展开态已加载内容无帧（463）；㉙ 其它自绘控件帮助文本（464）；㉚ HTML 引用块无导引线（465）；㉛ HTML 表格表头无同档（466）；㉜ 100+ 行行号（467）；㉝ HTML 代码块行号（468）；㉞ 行号选中/滚动两态（469）；㉟ 关于页 1x 盲（470）；㊱ M613 机器前提（472）；㊲ 真机 vibrant 暗档（473）；㊳ 长来源截断（474）；㊴ bundle ID 未搜（475）；㊵ 长首行标签省略无帧（476）；㊶ HTML 代码块无语言标签（477）；㊷ HTML `<hr>` 无通栏线（478）；㊸ HTML 表格体行无同一条线（479）；㊹ QuickPick 键盘提示 1x（480）；㊺ 437–482 的未结项仍开。

下一轮（R452）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R451 主笔+追记 head 跑、`40636558557 ↔ 667d1a2`（TASK_DIM）、`40636617018 ↔ eb04e37` 与 `40634880705 ↔ 9743379`（滚动会话采样红原文）、`40632882239 ↔ 224b8ee`（success；QUICKPICK_HINT 400/519）、`40629867848 ↔ 107f2b3`（success）、`40629776895 ↔ 0737460`、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `LIST_HANG_STYLE` 两档 16.0/16.0/0.0 与 `detail-list-wrap` 帧、`TASK_DIM` 两档 148.3/85.1/+63.2 与 136.0/184.7/−48.7、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R451_REPORT_BULLET = u"""- **R451（列表悬挂缩进位）**：`headIndent` 是 `firstLineHeadIndent + 16`，但首行正文的 `\\t` 走默认制表位 28 —— 首行正文 28、续行 16，折行列表项错开 12pt（现有夹具都是短项）。新 `ListHangingIndent`（max(16, 标记宽+2)）；`hangingIndent` 量标记宽；列表块的 `paragraphStyle` 设一条显式制表位，位置==`headIndent`。读数：`LIST_HANG_STYLE light 制表位数=1 制表位=16.0 续行=16.0 首行=0.0pt`、dark 同形（旧形状制表位数 0、默认 28 ⇒ 28 vs 16）。夹具 `detail-list-wrap`；**2 张新帧 + 4 张旧帧变化**（`detail-markdown-rendered`/`detail-tasks` 的列表文字从 48 移到 36），基线 **258→260 / 0/0/0**；已看亮/暗同轴。**尺换代记**：第一版裸像素簇读数与同文件 PIL 不一致（Python 22/36.5 vs Swift 48/44），换成产品文本视图的段落样式结构量；没有把对不上的像素当结论。`M1236/M1237` **2/2**；新单测 4 条 + 产品入口判据；第一次 0 告警门咬到 `allSubviews` 的 MainActor 隔离，修后冷编 0；预检 229/211/596 bad=0、ARM 322/1079、HIDDEN 316/1013 rot=0。⓪：开工 no-op push、ahead=0；**`40634880705 ↔ 9743379` failure** 读到 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ 具名 `RUNNER_SCROLL_SESSION_FLAKE`（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R452 重跑）+ Motion floor `testMarkdownModeLabelChange` 1<2；同跑 `QUICKPICK_HINT 400/519` 签收；`40636558557 ↔ 667d1a2`（TASK_DIM）与 `40636617018 ↔ eb04e37` 未读 ⇒ NOT-RUN；`107f2b3`/`224b8ee` success；`0737460` failure 仅 Motion floor。全量 **1239/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 260 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 450 轮（R451" in audit: raise SystemExit("REFUSED AUDIT 已有 R451")
if u"## Round 448 · R451" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 448")
if u"## D-447" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-447")
if u"折行列表项的续行回到首行正文同一竖轴" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**482." in backlog: raise SystemExit("REFUSED BACKLOG 已有 482")
if state.count(u"## R450 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R450 状态"))
U_CELL_OLD = u"U-31 … U-1677（R450 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R450 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_447 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R450 状态", STATE_SECTION + u"## R450 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1682（R451 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R450 节 ②", u"AGENT_STATE.md` 的 R451 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R451_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R451_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
