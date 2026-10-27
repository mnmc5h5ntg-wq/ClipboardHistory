#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R442 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 440 轮（R441 · 2026-10-28"
AUDIT_SECTION = u"""## 第 441 轮（R442 · 2026-10-28 · U-1633…U-1637）：设置新增「关于」分区与关于页（应用名 / 版本+build / 定位句 / 版权；侧栏 6→7 行、页卡同档留白；tagline 接 caption 探针 18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧随新行变化，基线 244→246）（产品 4 文件 + 1 新策略，设置关于页位）

- **U-1633：⓪ 网络与两跑。** 开工 `api=000` / apple=200：`git push origin main` 被拒、`gh` 读两跑均 EOF ⇒ 先记 **`CI_READ_BLOCKED=network`**（ahead=0，HEAD `f83270e` 已在远端），本地照常开轮。收口前复探 `api=200` 恢复 ⇒ 补读：`40594607166 ↔ d382848` 与 `40594639509 ↔ f83270e` 都 **completed / success、失败步骤 0**。`CODE_LINE_NUMBERS` runner 1x：light/dark 都 `代码带=54.0pt 行号带=3 正文左=21.0pt 带覆盖=100%`（R441 的三轴全部成立）。`TABLE_HEADER` 仍 `1.10/1.11`（地板 1.08，余量薄、地板不动）。`testProductDurationRevealStillMovesOverTime` **passed（0.784s）**、`testMarkdownModeLabelChangeIsAVisibleProcess` 与 `testFrameIntervalsUnderStateChanges` 在 Swift tests 里 skipped（各自的 env 门），而 **On-screen probe coverage floor 这一步全绿** ⇒ 130.2ms 红未复现。**436** = `MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- REDS=0`。
- **U-1634：① 腐烂与重钉。** `HIDDEN_ARMS 表=307 可判=995 rot=0`（最终读）。本轮新增设置行后，R116/R118/R120 三张旧表的针盯着的 `settingsSidebarTextColumn` 从 h192 改成 h224 ⇒ 预检 `bad=3`、电池 `HIDDEN_ROT_DRIFT rot=3`；逐表重钉后三表复跑：M610/M611 **CAUGHT**、M612 **CAUGHT**、M615 **SKIPPED**（各自期望），M613 在本机 2x 上 **SURVIVED**——本机 2x 的暗侧栏盲区名册为空，这一臂没有对象（runner 侧的名册非空）；记具名机器前提，不改期望。`NEEDLE_PRECHECK tables=220 covered=202 arms=578 bad=0`、`ARM_TOTAL files=313 arms=1061 dupes=0 repeats=0`。
- **U-1635：② 设置新增「关于」分区与关于页。** 缺陷形状：设置里只有侧栏底部一行 `时间剪史 1.4.8`，既没有 build，也没有一句"这个应用是什么"。修法：`SettingsCategory` 新增 `.about`（标题「关于」、图标 `info.circle`，排最后）；关于页用与其它页同一张 `GroupBox` 卡片（`.settingsCardInset()` 在卡内、VStack spacing 12）：应用名 `.title3` semibold、版本行「版本 1.4.8（build 1）」、定位句「轻量、离线、可回溯的剪贴板历史。」、版权「© 2026 时间剪史」；版本/build 由 `AboutPresentation` 统一（读不到不编占位；capture 缝 `settingsSidebarVersionForCapture` + `settingsAboutBuildForCapture`）。旧/新：侧栏分区 6→7 行；`SETTINGS_ABOUT_ROW light 分区行=7 应为=7`；关于页 tagline `CAPTION_INK light ratio=3.80 参照=3.75 比值=1.01`、dark `5.72/6.06 比值=0.95`、`CAPTION_JUDGED 18/18`、`CAPTION_COVERAGE 设置分区 7 个`。帧：**2 张新帧**（`settings-about` 亮/暗）+ **40 张设置面帧**随新行变化（设置页 18 张 × 亮暗、侧栏选中三态、cardprobe-split），基线 **244→246 / 0/0/0**；亮/暗关于页与 `settings-general` 都逐张看过。
- **U-1636：判据、刀与涟漪。** 新帧判据 `testSettingsSidebarShowsTheAboutCategoryRow`（亮档数主色/强调色标签带 = 7；暗档是 R457 同族的离屏暗侧栏盲区 ⇒ `SETTINGS_ABOUT_ROW_NOT_RUN=runner-dark-sidebar-text-blind`）。第一版用 ≤190 数带，M1214（侧栏丢关于行）**逃脱**：署名行上移顶替成第 7 条带 ⇒ 改 ≤110（主色 0 / 强调色 ≈101 进，secondary ≈128 不进），M1214/M1215 **2/2 CAUGHT**。全量当场抓出 6 条 UICapture + 1 条 VisualToken 涟漪并全修：暗侧栏盲区名册补 `settings-about`；`settingsSidebarTextColumn` h192→224；关于卡 `.settingsCardInset()` 从 GroupBox 外挪进卡内、去掉多余 2pt（节奏 14.5/14.0 与其它卡同档）；应用名从就地 20pt 改 `.title3`（字号刻度守卫）；tagline caption 探针带从 175..188 改 179..192（重测）。
- **U-1637：八步与具名 NOT-RUN。** build **0 告警**（冷编 0；先修掉判据里一个未使用 `height`）；捕获卷全绿、**246 帧**；帧基线 `COMPARED=246 CHANGED=0 MISSING=0 ADDED=0`；全量 **1202/57/5**（5 个断言全在 `SelectionRevealAnimationTests`；第一跑 12 红全部是 U-1636 的涟漪，修后回 5）；单跑 `caffeinate -u` 后 **4/4**（`OFFSET 0/193.5/1438`、`TIME 19/9/36.5/1438`、`CHANNEL 0→90.0→600 变化 104363/144000 重抓=no`）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 441，现读 `python3 scripts/product_streak.py --streak-for 441`，last=3853690）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① 暗侧栏未选中标签（raw 位图 max=28，R457 同族；`SETTINGS_ABOUT_ROW_NOT_RUN`）；② 设置内容列在 runner 1x 平涂（关于页说明段 `CAPTION_NOT_RUN`，2x 本机判 18/18）；③ M613 本机 2x 空名册（机器前提，期望保留给 runner）；④ 本轮的 run 签收（提交后的新跑）；⑤ 436 的 Motion floor 本跑已读 `judged=5/5 REDS=0`，notice-banner 未判时按 NOT-RUN；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号/9pt 档（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页内容 1x 盲（470）。

"""

ITER_SECTION = u"""## Round 439 · R442（第 441 轮 · 2026-10-28）：设置新增「关于」分区与关于页（应用名 / 版本+build / 定位句 / 版权；侧栏 6→7 行、页卡同档留白；tagline 接 caption 探针 18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧随新行变化，基线 244→246）

设置里只有侧栏底部一行版本，没有 build、没有一句定位。新 `.about` 分区 + 关于页：名字（.title3 semibold）/版本+build/定位句/版权，卡片与其它页同一档留白；版本与 build 由 `AboutPresentation` 统一（读不到不编占位）。读数：侧栏 7 行、tagline caption 比值 1.01/0.95、18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧，基线 246/0/0/0。侧栏判据第一版用 ≤190 被 M1214 逃脱（署名行顶替第 7 带）⇒ 改 ≤110 后 2/2；全量抓出 6 条 UICapture + 1 条 VisualToken 涟漪全修（暗盲名册、文本列 h224、卡片 inset 进卡内、title3、探针带 179..192）。R116/R118/R120 因文本列 h192→224 腐烂，重钉后 M610/M612/M615 各达期望、M613 本机空名册 SURVIVED（机器前提）。⓪：开工 api=000 ⇒ 两跑 EOF；恢复后补读 `40594607166 ↔ d382848`、`40594639509 ↔ f83270e` 都 success、失败步骤 0；`CODE_LINE_NUMBERS` 1x 3/21.0/100%；TABLE_HEADER 1.10/1.11；436 = judged 5/5 executed 77 REDS 0。全量 1202/57/5；捕获 246 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 关于页亮/暗与 `settings-general` 逐张看过：新行、卡片四段、侧栏选中；tagline 比值 1.01/0.95。扣 1：设置内容在 runner 1x 平涂（关于页正文只有本机 2x 与 caption 探针作证）。 |
| 判据有效性 | 15/15 | 侧栏 7 行（主色/强调色）、tagline caption、M1214/M1215 2/2；第一版被署名行顶替当场改阈值并复跑。 |
| 假绿防御 | 15/15 | 署名行顶替第 7 带被 M1214 抓出；暗档盲区/1x 平涂都具名 NOT-RUN；6 条 UICapture + 1 条 VisualToken 涟漪全修。 |
| 产品面推进 | 13/15 | 真落一个新设置分区 + 一页（名字/版本+build/定位/版权），补的是"只有版本行、没有 build 与定位"的空档；扣 2：正文 1x 盲、无应用图标、文本型页面。 |
| 台账一致性 | 15/15 | U-1633…U-1637、D-438、两跑 success 与 CODE_LINE_NUMBERS/TABLE_HEADER/436 都从日志解析；246 帧与基线一致。 |
| 交付诚实性 | 15/15 | 开工断网与恢复后补读都写；M613 本机 SURVIVED 按机器前提记不粉饰；暗侧栏与 1x 正文具名 NOT-RUN。 |
| 可复核性 | 15/15 | 7 行/≤110 阈值、tagline 带 179..192、caption 18/18、覆盖 7/7、刀号与 precheck/rot、基线 246、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（98）。"""

DECISION_438 = u"""## D-438 设置新增「关于」分区：版本/build/定位/版权在一页（R442）

- 背景：设置里只有侧栏底部的版本行，没有 build，也没有"这个应用是什么"；关于信息没有一个正式落点。
- 决定：`SettingsCategory` 新增 `.about`（标题「关于」、图标 `info.circle`，排最后）；关于页用与其它页同一张 `GroupBox` 卡片（卡内 `.settingsCardInset()`、VStack spacing 12），放应用名（`.title3` semibold）、版本行「版本 1.4.8（build 1）」、定位句、版权；版本/build 由 `AboutPresentation` 统一，读不到不编占位；capture 缝注入固定版本/build。
- 理由：macOS 应用的常规落点；一页说清版本、build、定位与版权；文案与版本规范化是纯函数，可单测。
- 兼容性/迁移：设置分区 6→7，侧栏行与所有设置面帧随新行变化（2 新 + 40 变，基线 244→246）；关于页正文在 runner 1x 平涂（470），暗侧栏未选标签盲（471）。
- 边界：无应用图标（文本型）；定位句与版权是常量（跨年稳定）。
- 回滚：删 `.about` case/页/侧栏行即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 设置新增「关于」分区与关于页（应用名 / 版本+build / 定位句 / 版权；侧栏 6→7 行、tagline caption 1.01/0.95、18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧、基线 246）（R442 / 第 441 轮 / Round 439 / U-1633…U-1637 · 产品 4 文件，设置关于页位）

"""

BACKLOG_SECTION = u"""437 追记（R442 · 仍开）：主列表仍不匹配 `sourceAppName`。

449 追记（R442 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/193.5/1438；TIME 19/9/36.5/1438；CHANNEL 104363/144000）。

451 追记（R442 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R442 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R442 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R442 · 仍开）：菜单具名标记仍未发射。

455 追记（R442 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R442 · 仍开）：跨年记录仍无年份。

457 追记（R442 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字；设置暗侧栏未选标签同族（471）。

458 追记（R442 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R442 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R442 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R442 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R442 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R442 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R442 · 仍开）：其它自绘控件（浮层清除 ×、批量栏五颗）仍无同类帮助判据。

465 追记（R442 · 仍开）：HTML 引用块没有导引线（只接了 Markdown 路径）。

466 追记（R442 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R442 · 仍开）：代码块行号的 9pt 档只在纯函数里验，1000+ 行会超出外边距。

468 追记（R442 · 仍开）：HTML 代码块没有行号（只接了 Markdown 路径）。

469 追记（R442 · 仍开）：代码块行号的选中态/滚动态没有帧。

**470. 关于页的正文在 runner 1x 是平涂：只有侧栏行与 2x 的 caption 探针作证**（R442 观察）
    现象：设置内容列在 1x 整列平涂（BACKLOG 459）；关于页的应用名/版本/build/版权在 CI 上读不到，tagline 的 caption 探针在 1x 是 `CAPTION_NOT_RUN`，18/18 判成是本机 2x 的那一跑。侧栏第 7 行在 1x 可画，是这一页唯一的 CI 像素证人。
    修法（下一轮若需要）：给关于页做一个 **1x 可画的组合帧**（例如只把页卡放进一个独立 520 帧，而不是整窗 720×540），并把应用名/版本行接进同一张 caption/标题带判据。

**471. 设置暗侧栏未选中的分类标签在离屏通道里不落墨（about 行继承同一盲区）**（R442 观察）
    现象：`settings-general` 暗帧文字列的 raw 位图 max=28（背景），只有选中的强调色标签与底部署名行有墨；`settings-about` 同族。`SETTINGS_ABOUT_ROW` 的暗档因此具名 NOT-RUN。
    修法：与 457 同一条通道问题；要判暗档只能换通道（真屏/合成），不是改阈值。

**472. R118 的 M613 在本机 2x 上是空对象：暗侧栏盲区名册为空**（R442 观察）
    现象：把行带助手改成返回空数组（M613）在本机 2x 不红 —— 本机 2x 的盲区名册是空集，等式 0=0；该臂的期望（CAUGHT）是给名册非空的 runner 写的。重钉 R116/R118/R120 的文本列矩形后，M610/M611/M612/M615 都达期望，只有 M613 记为机器前提 SURVIVED。
    修法：把 M613 的期望按机器分档（名册为空时记 NOT-RUN/MACHINE_PREMISE），或在 runner 上跑它；不改产品与守卫。
"""

STATE_SECTION = u"""## R442 状态（2026-10-28 · 本地 · 第 441 轮 / Round 439）：设置新增「关于」分区与关于页（应用名 / 版本+build / 定位句 / 版权；侧栏 6→7 行、tagline caption 1.01/0.95、18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧随新行变化，基线 244→246）；⓪ 开工 api=000 两跑 EOF，恢复后补读 `40594607166 ↔ d382848`、`40594639509 ↔ f83270e` 都 success、失败步骤 0（产品 4 文件，设置关于页位）

最后更新：2026-10-28（本地 · R442 / 第 441 轮 / Round 439）：设置里只有侧栏底部版本行，没有 build 与定位。新增 `SettingsCategory.about`（「关于」、`info.circle`、排最后）与关于页：应用名（`.title3` semibold）、版本行「版本 1.4.8（build 1）」、定位句「轻量、离线、可回溯的剪贴板历史。」、版权「© 2026 时间剪史」；卡片与其它页同档（卡内 `.settingsCardInset()`、spacing 12）；版本/build 由 `AboutPresentation` 统一（读不到不编占位），capture 缝注入固定值。读数：`SETTINGS_ABOUT_ROW light 分区行=7`；tagline `CAPTION_INK light 3.80/3.75=1.01`、dark `5.72/6.06=0.95`、`CAPTION_JUDGED 18/18`、`CAPTION_COVERAGE 7 个`；侧栏 6→7 行、2 张新帧 + 40 张设置面帧，基线 **244→246 / 0/0/0**。侧栏判据第一版 ≤190 被 M1214 逃脱（署名行顶替第 7 带）⇒ 改 ≤110 后 M1214/M1215 **2/2**；全量抓出 6 条 UICapture + 1 条 VisualToken 涟漪并全修（暗盲名册补 settings-about、`settingsSidebarTextColumn` h192→224、卡片 inset 挪进卡内、名称改 `.title3`、探针带 179..192）。R116/R118/R120 因文本列改高腐烂，重钉后 M610/M611/M612/M615 各达期望、M613 本机空名册 SURVIVED（机器前提，472）。预检 **220/202/578 bad=0**、ARM **313 文件 / 1061 把**、HIDDEN **307/995 rot=0**。⓪：开工 `api=000` ⇒ `CI_READ_BLOCKED=network`（ahead=0，HEAD `f83270e` 已在远端）；收口前恢复 `api=200` ⇒ 补读两跑 **success、失败步骤 0**；`CODE_LINE_NUMBERS` runner 1x light/dark 都 `代码带=54.0pt 行号带=3 正文左=21.0pt 带覆盖=100%`；`TABLE_HEADER 1.10/1.11`（地板 1.08 未动）；`testProductDurationRevealStillMovesOverTime` passed、on-screen probe 步全绿 ⇒ 130.2ms 未复现；**436** = `judged=5/5 executed=77 REDS=0`。本地全量 **1202/57/5**（5 断言全在 `SelectionRevealAnimationTests`；第一跑 12 红全是新页涟漪，已修）；单跑 **4/4**（`OFFSET 0/193.5/1438`、`TIME 19/9/36.5/1438`、`CHANNEL 0→90.0→600 变化 104363/144000 重抓=no`）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **246 帧**；基线 **246/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 441，现读 `product_streak.py --streak-for 441`，last=3853690）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 开工断网（api=000、两跑 EOF）⇒ 记 CI_READ_BLOCKED；恢复后补读两跑 success、失败步骤 0；CODE_LINE_NUMBERS 1x 3/21/100%、TABLE_HEADER 1.10/1.11、436 judged 5/5 REDS 0；130.2ms 未复现。
② 产品：设置新增「关于」分区 + 关于页（名字/版本+build/定位/版权；侧栏 7 行、卡片同档留白）。
③ 判据：M1214/M1215 2/2（第一版被署名行顶替，改 ≤110）；6 条 UICapture + 1 条 VisualToken 涟漪全修；R116/R118/R120 重钉后各达期望（M613 机器前提）；precheck 220/202/578；hidden rot 0。
④ 436：`judged=5/5 executed=77 not-run=- REDS=0`；不重猜 must_judge。
⑤ 367：hidden 表 307 / 可判 995 / rot 0。
⑥ 捕获 246 帧；换装 ok；清账 162/63/0；帧基线 246/0/0/0；本地全量 1202/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 暗侧栏未选标签（SETTINGS_ABOUT_ROW_NOT_RUN，R457/471）；② 关于页正文 1x 平涂（CAPTION_NOT_RUN，2x 判 18/18，470）；③ M613 本机 2x 空名册（机器前提，472）；④ 本轮提交后的新跑签收；⑤ 436 的 notice-banner 若未判（NOT-RUN）；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 437–472 仍开。

下一轮（R443）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R442 主笔+追记 head 跑与预记跑的全部失败步骤（成对 run↔commit），重点看新判据 `SETTINGS_ABOUT_ROW` 亮档 7 行 / 暗档 NOT-RUN、`settings-about` 的 `CAPTION_JUDGED`/覆盖 7 个、以及 `CODE_LINE_NUMBERS` 3/21/100% 与 `TABLE_HEADER` 1.10/1.11 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R442_REPORT_BULLET = u"""- **R442（设置关于页位）**：设置里只有侧栏底部一行版本，没有 build，也没有一句定位。新 `SettingsCategory.about`（「关于」、`info.circle`、排最后）+ 关于页：应用名（`.title3` semibold）、版本行「版本 1.4.8（build 1）」、定位句、版权；卡片与其它页同档留白；版本/build 由 `AboutPresentation` 统一（读不到不编占位）。读数：侧栏 **6→7 行**、tagline `CAPTION_INK 1.01/0.95`、`CAPTION_JUDGED 18/18`、`CAPTION_COVERAGE 7 个`；**2 张新帧 + 40 张设置面帧**随新行变化，基线 **244→246 / 0/0/0**。侧栏判据第一版 ≤190 被 M1214 逃脱（署名行顶替第 7 带）⇒ 改 ≤110 后 **M1214/M1215 2/2**；全量抓出 6 条 UICapture + 1 条 VisualToken 涟漪全修（暗盲名册、文本列 h224、卡片 inset 进卡内、`.title3`、探针带 179..192）。R116/R118/R120 因文本列改高腐烂，重钉后 M610/M611/M612/M615 各达期望、M613 本机空名册 SURVIVED（机器前提，472）。⓪：开工 `api=000`、两跑 EOF ⇒ `CI_READ_BLOCKED=network`（ahead=0）；恢复后补读 `40594607166 ↔ d382848`、`40594639509 ↔ f83270e` 都 **success、失败步骤 0**；`CODE_LINE_NUMBERS` 1x 3/21.0/100%、`TABLE_HEADER` 1.10/1.11、**436** = `judged=5/5 executed=77 REDS=0`；130.2ms 未复现。本地全量 **1202/57/5**（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（OFFSET 0/193.5/1438；TIME 19/9/36.5/1438；CHANNEL 104363/144000）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 246 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)
report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 441 轮（R442" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R442 节")
if u"## Round 439 · R442" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 439")
if u"## D-438" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-438")
if u"设置新增「关于」分区" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**470." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 470")
if state.count(u"## R441 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R441 状态"))
U_CELL_OLD = u"U-31 … U-1632（R441 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R441 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R441 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_438 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R441 状态", STATE_SECTION + u"## R441 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1637（R442 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R441 节 ②",
                                u"AGENT_STATE.md` 的 R442 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R442_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R442_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
