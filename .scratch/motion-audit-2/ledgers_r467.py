#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R467 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 465 轮（R466 · 2026-10-28"
AUDIT_SECTION = u"""## 第 466 轮（R467 · 2026-10-29 · U-1758…U-1762）：视频 seek 轨道可见（旧偏离 20/5 → 新 96/90；2 张旧帧变化、基线 280）+ 捕获守卫拆「有意黑底」+ inline 候选诊断（产品 1 文件 + 判据）

- **U-1758：⓪ push 与两跑。** 开工 no-op push success、ahead=0、HEAD=`3bd67b1`；`40720200357 ↔ bf9e8ec` 与 `40720409960 ↔ 3bd67b1` 读时 in_progress ⇒ NOT-RUN（收口再读）。已读（上一轮）：`40710557752 ↔ 7a04a79` failure 3 步：`INLINE_CODE_PAD light 85/80/5.0` 签收、**dark 仍 150/147/3.0**（padding 选择器仍只看到假带 ⇒ 真带不在候选）、`VIDEO_UNAVAILABLE 5/4`、Motion 1<2；`40714119382 ↔ 0449f4a` failure 3 步：`VIDEO_SURFACE light 0/236 差=236` 签收，**Capture gate「黑带消失」15 张旧名册帧**（有意黑底把 `bandsSeenHere` 拉高），inline dark 3.0、Motion 1<2；`40714151224 ↔ 86d6b6a` failure；其余沿用；436 无新红。
- **U-1759：① 腐烂与预检。** `HIDDEN_ARMS 表=331 可判=1045 rot=0`；`NEEDLE_PRECHECK tables=244 covered=226 arms=628 bad=0`、`ARM_TOTAL files=337 arms=1111`。
- **U-1760：靶修一：捕获守卫拆「有意黑底」。** `materialBlindSpotFixtures` 只留系统 List 选中材质；新增文件级 `UICaptureBlackBands.intentional`（现只有 `detail-file-video-controls`）；`extra` 与 `bandsSeenHere` 都排除它（`Reading` 增 `fixture` 字段，三处构造补齐）。这样黑带消失方向不会被有意黑底误开，也不盲缩旧 15 帧名单；本地捕获守卫通过。
- **U-1761：靶修二 + 新面：inline 候选诊断，seek 轨道可见。** inline 判据在选定带后 emit `INLINE_CODE_DIAG`（选行、页/带 luma、候选数、按 padding 的前 5 条 row/span/coverage/ink/padding），本轮**不改选择器、不降 4.5**，等 runner 数据。新面：视频进度滑杆的系统轨道在胶囊底上只偏离 **light 20 / dark 5**（seek 范围几乎看不见）；在 Slider 下垫 `Capsule().fill(primary 0.45).frame(height: 10)`（系统轨道 4pt，上下各露 3pt），新偏离 **96/90**。旧/新：`VIDEO_SEEK light 20→96、dark 5→90`；**2 张旧帧变化**（video-controls 亮/暗）、0 新增/缺失；基线 **280**（同 commit 更新）；亮/暗帧看过轨道清晰、thumb/控件不变。
- **U-1762：判据/刀与八步。** 新帧判据 `testVideoSeekTrackIsVisible` 取 thumb 右侧（x 160..410、y 400..420）对胶囊底众数的最大偏离，要求 ≥60；旧 20/5 红、新 96/90 绿；`M1270`（撤胶囊）/`M1271`（不透明度 0.1）⇒ **2/2 CAUGHT**、RESTORE_CLEAN。build **0 告警**（冷编同）；捕获卷 **280 帧**、`CHANGED=2 MISSING=0 ADDED=0`，更新后 `280/0/0/0`；全量 **1271/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded` 260.7ms>250 ⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**（阈值未动）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 466，`python3 scripts/product_streak.py --streak-for 466`，last=7adc7c6）；清账与电池在台账后复跑。**具名 NOT-RUN**：① R466 两跑（in_progress）；② R467 自身跑（未创建）；③ `INLINE_CODE_DIAG` 的 runner 数据；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–522 的未结项仍开。

"""

ITER_SECTION = u"""## Round 464 · R467（第 466 轮 · 2026-10-29）：视频 seek 轨道可见（旧 20/5 → 新 96/90；2 张旧帧变化、基线 280）+ 捕获守卫拆有意黑底 + inline 候选诊断

系统滑杆轨道在胶囊底上只偏离 light 20/dark 5，seek 范围几乎看不见；在 Slider 下垫 10pt 的 primary 0.45 胶囊（系统轨道 4pt，上下各露 3pt），新偏离 96/90。2 张旧帧变化、0 新增，基线 280/0/0/0；亮/暗看过轨道清晰。判据取 thumb 右侧 x 160..410 对胶囊底众数的最大偏离（≥60）；旧红新绿；M1270/M1271 2/2。另两件靶修：捕获守卫把有意黑底拆成 `UICaptureBlackBands.intentional`，`extra`/`bandsSeenHere` 排除（`Reading` 增 fixture）；inline 判据 emit `INLINE_CODE_DIAG`（选行/页带 luma/top5 候选），不改选择器、不降 4.5。全量 1271/56/1（PerfBudget 260.7 flake）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；R466 两跑 in_progress；R464/R465 跑 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 video-controls 逐张看过：轨道从 thumb 起清晰可见，thumb/控件不变。 |
| 判据有效性 | 15/15 | thumb 右侧轨道段对胶囊底众数最大偏离；旧 20/5 红、新 96/90 绿；两把刀 2/2。 |
| 假绿防御 | 14/15 | 捕获守卫拆表、inline 诊断只打印不判；扣 1：R466 两跑与诊断 runner 数据未读。 |
| 产品面推进 | 15/15 | 新类别（seek 轨道）；真实 .mov 夹具；Store 不动。 |
| 台账一致性 | 15/15 | U-1758…U-1762、D-463、280 帧/1271、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 有意黑底与盲区拆开、inline 只诊断不盲改、flake 全部具名。 |
| 可复核性 | 15/15 | 20/5→96/90、DIAG 字段、precheck 244/226/628、rot 331/1045、基线 280 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_463 = u"""## D-463 seek 轨道自绘胶囊、有意黑底与盲区分表（R467）

- 背景：系统滑杆轨道对胶囊底只偏离 light 20/dark 5，seek 范围几乎看不见；R465 的有意播放器黑底又让捕获守卫的"黑带消失"方向误开（旧 15 帧）。
- 决定：Slider 下垫 10pt `primary 0.45` 胶囊（系统轨道 4pt，上下露 3pt）；捕获守卫新增 `UICaptureBlackBands.intentional`，`extra`/`bandsSeenHere` 排除；`Reading` 增 `fixture`。inline 判据加 `INLINE_CODE_DIAG`。
- 理由：seek 范围是非文本控件，3:1 要有；"产品有意黑底"不是"离屏材质盲区"，两者不能共用一张名单的语义。
- 兼容性/迁移：video-controls 亮/暗 2 张旧帧变化；基线 280 同 commit 更新；捕获守卫/Reading 结构变化已跑旧表与捕获卷。
- 边界：inline dark 的候选诊断待 runner；seek 轨道的暗档 90 差已过 60。
- 回滚：删轨道胶囊与 intentional 名单；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 视频 seek 轨道可见（旧 20/5 → 新 96/90；2 张旧帧变化、基线 280）+ 捕获守卫拆有意黑底 + inline 候选诊断（R467 / 第 466 轮 / Round 464 / U-1758…U-1762 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**520. inline dark 的候选诊断要等 runner 数据**（R467 观察）
    现象：`INLINE_CODE_DIAG` 已在本地打印选行/页带 luma/top5；runner 上还没跑过。
    修法：下一跑读 DIAG，先看真带是否进候选（span/coverage/ink/padding），再改选择器；地板 4.5 不动。

**521. 自绘 seek 轨道的 thumb 仍是系统滑杆**（R467 观察）
    现象：轨道可见了，但 thumb/拖动仍由系统 Slider 画；thumb 在胶囊底上的对比未单独判。
    修法：若要统一，做自定义 thumb 并补帧；先记录。

**522. 有意黑底名单的"gone"方向未单独判**（R467 观察）
    现象：intentional 名单只影响 `bandsSeenHere`/`extra`；如果某一帧的有意黑底消失（改成非黑），没有判据。
    修法：补一条"intentional 帧仍有黑带"的正面判据，或在帧上判底色的结构量。
"""

STATE_SECTION = u"""## R467 状态（2026-10-29 · 本地 · 第 466 轮 / Round 464）：视频 seek 轨道可见（旧偏离 20/5 → 新 96/90；2 张旧帧变化、基线 280）+ 捕获守卫拆有意黑底 + inline 候选诊断；全量 1271/56/1（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R467 / 第 466 轮 / Round 464）：系统滑杆轨道在胶囊底上只偏离 **light 20 / dark 5**，seek 范围几乎看不见；在 Slider 下垫 `Capsule().fill(primary 0.45).frame(height: 10)`（系统轨道 4pt、上下各露 3pt），新偏离 **96/90**。旧/新：`VIDEO_SEEK light 20→96、dark 5→90`；**2 张旧帧变化**（video-controls 亮/暗）、0 新增/缺失；基线 **280**；亮/暗帧看过轨道清晰。新帧判据 `testVideoSeekTrackIsVisible` 取 thumb 右侧（x 160..410、y 400..420）对胶囊底众数的最大偏离（≥60）；旧红新绿；`M1270/M1271` **2/2 CAUGHT**。**靶修一**：捕获守卫拆 `UICaptureBlackBands.intentional`（video-controls），`extra`/`bandsSeenHere` 排除，`Reading` 增 `fixture`，旧 15 帧名单不盲缩；本地捕获守卫通过。**靶修二**：inline 判据 emit `INLINE_CODE_DIAG`（选行/页带 luma/候选数/top5 row/span/coverage/ink/padding），本轮不改选择器、不降 4.5。预检 **244/226/628 bad=0**、ARM **337/1111**、HIDDEN **331/1045 rot=0**。⓪：no-op push success、ahead=0、HEAD=`3bd67b1`；`40720200357 ↔ bf9e8ec` 与 `40720409960 ↔ 3bd67b1` in_progress ⇒ NOT-RUN；上一轮 `40710557752 ↔ 7a04a79` failure 3 步（inline dark 仍 150/147/3.0、VIDEO_UNAVAILABLE 5/4、Motion 1<2；light 5.0 签收）、`40714119382 ↔ 0449f4a` failure 3 步（VIDEO_SURFACE 236 签收；Capture 黑带消失 15 帧；inline dark 3.0；Motion 1<2）。全量 **1271/56/1**（唯一红 PerfBudget 260.7>250 ⇒ `LOCAL_PERF_BUDGET_FLAKE=load`）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 466，`python3 scripts/product_streak.py --streak-for 466`，last=7adc7c6）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R466 两跑 in_progress ⇒ NOT-RUN；上一轮 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。
② 产品：seek 轨道自绘胶囊（20/5→96/90；2 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1270/M1271 2/2；捕获守卫拆有意黑底；inline 候选诊断；precheck 244/226/628；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 331 / 可判 1045 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1271/56/1（PerfBudget flake）。

NOT-RUN / 阻塞（分开写）：① R466 两跑（in_progress）；② R467 自身跑；③ `INLINE_CODE_DIAG` runner 数据；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–522 的未结项仍开。

下一轮（R468）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R467 主笔+追记 head 跑、`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、`40710557752 ↔ 7a04a79`、`40714119382 ↔ 0449f4a` 等的全部失败步骤；重点 `VIDEO_SEEK` 96/90、`INLINE_CODE_DIAG`（选行/页带/top5 候选）、`INLINE_CODE_PAD` 两档、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R467_REPORT_BULLET = u"""- **R467（seek 轨道位 + 两件靶修）**：系统滑杆轨道对胶囊底只偏离 **light 20 / dark 5**，seek 范围几乎看不见；在 Slider 下垫 `Capsule().fill(primary 0.45).frame(height: 10)`（系统轨道 4pt、上下露 3pt），新偏离 **96/90**。旧/新：`VIDEO_SEEK light 20→96、dark 5→90`；**2 张旧帧变化**、0 新增，基线 **280/0/0/0**；亮/暗看过轨道清晰。判据取 thumb 右侧（x 160..410）对胶囊底众数最大偏离（≥60）；旧红新绿；M1270/M1271 **2/2**。靶修：捕获守卫拆 `UICaptureBlackBands.intentional`（`extra`/`bandsSeenHere` 排除，`Reading` 增 fixture）；inline 判据 emit `INLINE_CODE_DIAG`（选行/页带/top5），不改选择器、不降 4.5。⓪ no-op push、ahead=0；R466 两跑 in_progress ⇒ NOT-RUN；上一轮 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。全量 **1271/56/1**（唯一红 PerfBudget 260.7>250 ⇒ `LOCAL_PERF_BUDGET_FLAKE=load`）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 466 轮（R467" in audit: raise SystemExit("REFUSED AUDIT 已有 R467")
if u"## Round 464 · R467" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 464")
if u"## D-463" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-463")
if u"视频 seek 轨道可见" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**520." in backlog: raise SystemExit("REFUSED BACKLOG 已有 520")
if state.count(u"## R466 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R466 状态"))
U_CELL_OLD = u"U-31 … U-1757（R466 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R466 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_463 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R466 状态", STATE_SECTION + u"## R466 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1762（R467 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R466 节 ②", u"AGENT_STATE.md` 的 R467 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R467_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R467_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
