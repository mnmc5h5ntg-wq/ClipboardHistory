#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R444 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 442 轮（R443 · 2026-10-28"
AUDIT_SECTION = u"""## 第 443 轮（R444 · 2026-10-28 · U-1643…U-1647）：主列表行的时间行补「· 来自 <来源 App>」（时间在前、来源在后；nil 只显示时间；来源行 140.5pt vs 无来源 73.5pt、差 67.0、左沿 96.5/96.5 同轴；57 张行/侧栏/content 帧变化 + 2 张负臂新帧，基线 246→248）（产品 2 文件 + 1 新策略，主列表行来源位）

- **U-1643：⓪ 网络与 R442 跑。** 开工 `api=000` / apple=200、`git ls-remote`/push 被拒（2 探）⇒ 先记 **`PUSH_BLOCKED=network`（ahead=3，HEAD `ed715f1`，origin/main `bdb4737`）** 与 **`CI_READ_BLOCKED=network`**，本地开轮。收口前 api 短暂恢复 200 ⇒ 补读 **`40605228813 ↔ bdb4737`（R442 自身 head）**：**completed / failure、失败步骤 2 个**：① `testProbesDoNotSitOnVibrantColumns`：`judged=22 != mustJudge=20`（不可判的控件探针被 `checked - notRun` 算成判过）；② `testSettingsSidebarShowsTheAboutCategoryRow`：light 分区标签带 **0 != 7**（R442 的判据用了本地固定 y 60..285，而 R118 量过 runner 的设置侧栏整列下移 **282pt**）。两红都是**我们新判据的仪器病**，不是产品红；R444 当场修：侧栏判据改成从**视图树行带**（`sidebarTextBands`）数、vibrant 判据把不可判的控件从 `judged` 扣掉；阈值/产品未动。R442 跑的其余读数：`CODE_LINE_NUMBERS` 两档 `代码带=54.0pt 行号带=3 正文左=21.0pt 带覆盖=100%`、`TABLE_HEADER 1.10/1.11`、`CAPTION_JUDGED 6/18`（`settings-about` 说明段按名 `CAPTION_NOT_RUN`）。R443 自身跑未创建（三笔未推）；R444 自身跑待 push。436：R442 跑的 Motion floor 行不在失败步骤日志里（整份日志被网络 EOF 挡住）⇒ 具名 NOT-RUN，不重猜。
- **U-1644：① 腐烂与预检。** `HIDDEN_ARMS 表=309 可判=999 rot=0`；`NEEDLE_PRECHECK tables=222 covered=204 arms=582 bad=0`、`ARM_TOTAL files=315 arms=1065 dupes=0 repeats=0`。新表 `mutate_r444_row_source` 已登记。
- **U-1645：② 主列表行时间行补来源 App 名。** 缺陷形状：剪贴板历史里"这条从哪个 App 来"是核心信息，但主列表以前只显示时间 —— 来源只在详情头部（R425 图标 + 文案）。修法：新 `HistoryRowSourceLine`（`时间 · 来自 <来源>`；来源 nil/空白只显示时间；时间在前、来源在后，行宽不够先截断来源）；`RowTextColumn` 的时间行接它，`lineLimit(1)` + tail。旧/新：`HISTORY_ROW_SOURCE light/dark 来源行宽=140.5pt 无来源行宽=73.5pt 差=67.0pt 左沿=96.5/96.5pt`（来源行多出的就是「· 来自 Safari」那一段；时间不挪位）。负臂夹具 `sidebar-no-source`（同一段正文/时间、来源 nil；走存档载入，`add` 会被上下文采集器补成 loginwindow；**清空选中**，否则单条 store 默认选中、黑块盖住整行）。帧：**57 张**行/侧栏/content 帧随来源行进每行变化 + **2 张**负臂新帧，基线 **246→248 / 0/0/0**；已看 `sidebar-history`（四行「时间 · 来自 Safari/预览/访达」）与 `sidebar-no-source`（只剩时间）。
- **U-1646：判据与刀。** 新单测 `HistoryRowSourceLineTests` 3 条（时间在前、nil/空白、长来源不先截）；新帧判据 `testHistoryRowsShowTheirSourceAppName`（`sidebar-history` 第一行 vs `sidebar-no-source` 第一行：时间行墨宽差 ≥25pt、左沿差 ≤1pt；1x 侧栏行可画，整列无墨才具名 NOT-RUN）。`M1220`（行退回纯时间）⇒ 帧判据 **CAUGHT**；`M1221`（策略丢时间、只写「来自 X」）⇒ 单测 **3 条 + 帧判据** 全红 ⇒ **2/2 CAUGHT**、RESTORE_CLEAN=yes。R442 的两条仪器红已按 U-1643 修并本地复跑绿（`PROBE_DOMAIN 问了 44 条、判成 44 条`；`SETTINGS_ABOUT_ROW light/dark 7`）。
- **U-1647：八步与具名 NOT-RUN。** build **0 告警**（冷编 0）；捕获卷全绿 **248 帧**；帧基线 `COMPARED=248 CHANGED=0 MISSING=0 ADDED=0`；全量 **1206/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` 后 **4/4**（`OFFSET 0/221.5/1438`、`TIME 18/9/54.0/1438`、`CHANNEL 0→82.0→600 变化 30442/105600 重抓=no`）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 443，现读 `python3 scripts/product_streak.py --streak-for 443`，last=258fc8e）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① `PUSH_BLOCKED=network`（ahead=3 + 本轮提交；R443 三笔与 R444 本地提交待推）；② `CI_READ_BLOCKED=network`（R442 整份日志、R443 自身跑未创建）；③ R442 跑的 Motion floor 行；④ 长来源截断没有帧（只有单测，474）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 437–474 仍开。

"""

ITER_SECTION = u"""## Round 441 · R444（第 443 轮 · 2026-10-28）：主列表行的时间行补「· 来自 <来源 App>」（时间在前、来源在后；nil 只显示时间；来源行 140.5pt vs 无来源 73.5pt、差 67.0、左沿 96.5/96.5 同轴；57 张行/侧栏/content 帧变化 + 2 张负臂新帧，基线 246→248）

主列表此前只显示时间，来源只在详情头部。新 `HistoryRowSourceLine`：时间在前、` · 来自 <来源>` 在后，nil/空白只显示时间；行宽不够先截断来源。读：来源行 140.5pt vs 无来源 73.5pt（差 67.0）、左沿 96.5/96.5；负臂 `sidebar-no-source`（同一段正文/时间、来源 nil、清空选中避免黑块盖行）。57 张行帧 + 2 张负臂，基线 248/0/0/0。M1220/M1221 2/2。⓪：开工 api=000 两探断 ⇒ PUSH_BLOCKED（ahead=3、HEAD ed715f1、origin/main bdb4737）；收口前 api 短暂恢复 ⇒ 补读 R442 跑 40605228813 failure 2 步：vibrant 判据 judged 22≠20（不可判控件被算成判过）与设置关于行判据 light 0≠7（固定 y vs runner 282pt 下移）—— 都是我们新判据的仪器病，当场改成视图树行带 + 扣掉不可判控件，阈值/产品未动；R442 跑的 CODE/TABLE/CAPTION 读数已取（54/3/21/100、1.10/1.11、6/18）。全量 1206/57/5；捕获 248 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `sidebar-history`（四行「时间 · 来自 Safari/预览/访达」）与 `sidebar-no-source`（只剩时间）逐张看过；两臂同帧读数差 67.0pt、左沿同轴。 |
| 判据有效性 | 15/15 | 来源/无来源两臂 + 时间左沿不变量；M1220/M1221 2/2；R442 的两条仪器红按 runner 原文定位并修（views 树行带、judged 扣不可判控件）。 |
| 假绿防御 | 15/15 | 负臂来源 nil 走存档载入（不被采集器补成 loginwindow）、清空选中（不被黑块盖行）；1x 整列无墨才 NOT-RUN。 |
| 产品面推进 | 14/15 | 真落主列表来源 App 名（剪贴板历史的核心元信息，此前只有详情头部）；扣 1：搜索仍不匹配来源名（437）、长来源截断只有单测（474）。 |
| 台账一致性 | 15/15 | U-1643…U-1647、D-440、R442 跑两步红的原文与修法、248 帧/1206 都从命令与日志解析。 |
| 交付诚实性 | 15/15 | 开工断网/2 探、R442 整份日志 EOF、Motion floor 未读都具名；两条 CI 红照实记为自己的仪器病并写修法。 |
| 可复核性 | 15/15 | 140.5/73.5/67.0、左沿 96.5、负臂夹具、刀号与 precheck/rot、基线 248、换装/清账都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_440 = u"""## D-440 主列表行时间行补来源 App 名（R444）

- 背景：剪贴板历史里"这条从哪个 App 来"是核心信息，但主列表以前只有时间；来源只在详情头部（R425 图标 + 文案）。
- 决定：新 `HistoryRowSourceLine` —— `时间 · 来自 <来源>`，时间在前、来源在后；来源 nil/空白只显示时间；行宽不够先截断来源（`lineLimit(1)` + tail）。
- 理由：时间回答"新旧"、来源回答"从哪来"，前者是扫读第一层；策略纯函数可单测；行帧在 1x 可画，来源/无来源两臂同帧可量。
- 兼容性/迁移：来源行让所有行帧的时间行变宽（57 张帧变化）+ 2 张负臂新帧，基线 246→248；负臂必须走存档载入并清空选中。
- 边界：长来源的截断没有帧（474）；搜索仍不匹配来源名（437）。
- 回滚：时间行回退到 `ClipboardDateFormatters.sidebarTime` 即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 主列表行时间行补「· 来自 <来源 App>」（时间在前；nil 只显示时间；来源行 140.5pt vs 无来源 73.5pt、差 67.0；57 张行帧变化 + 2 张负臂、基线 248）（R444 / 第 443 轮 / Round 441 / U-1643…U-1647 · 产品 2 文件，主列表行来源位）

"""

BACKLOG_SECTION = u"""437 追记（R444 · 仍开）：主列表行现在**显示**来源 App 名，但搜索仍不匹配 `sourceAppName`。

449 追记（R444 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/221.5/1438；TIME 18/9/54/1438；CHANNEL 30442/105600）。

451 追记（R444 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R444 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R444 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R444 · 仍开）：菜单具名标记仍未发射。

455 追记（R444 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R444 · 仍开）：跨年记录仍无年份。

457 追记（R444 · 仍开）：主列表暗档文字仍是另一处（设置侧栏已在 R443 修掉）。

458 追记（R444 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R444 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R444 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R444 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R444 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R444 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R444 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R444 · 仍开）：HTML 引用块没有导引线。

466 追记（R444 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R444 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R444 · 仍开）：HTML 代码块没有行号。

469 追记（R444 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R444 · 仍开）：关于页正文在 runner 1x 是平涂。

471 结案（R443）：设置暗侧栏标签盲区已修（文字显式动态色）。

472 追记（R444 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R444 · 仍开）：设置侧栏文字的真机 vibrant 暗档外观没有同屏对照。

**474. 长来源 App 名的截断没有帧：只有纯函数单测**（R444 观察）
    现象：`HistoryRowSourceLine` 不做长度截断（靠行 `lineLimit(1)` + tail），单测只验"来源留在字符串里、时间在最前"；没有一张较长来源名的行帧证明截断点落在来源上、时间仍完整。
    修法：加一个长来源（如 12 字）的侧栏行帧（2 张），断言时间段的墨宽与短来源帧一致、来源段被截断。
"""

STATE_SECTION = u"""## R444 状态（2026-10-28 · 本地 · 第 443 轮 / Round 441）：主列表行的时间行补「· 来自 <来源 App>」（时间在前、来源在后；nil 只显示时间；来源行 140.5pt vs 无来源 73.5pt、差 67.0、左沿 96.5/96.5 同轴；57 张行/侧栏/content 帧变化 + 2 张负臂新帧，基线 246→248）；R442 跑 failure 2 步（vibrant 判据 22≠20、设置关于行 light 0≠7）⇒ 都是新判据仪器病，已按视图树行带/扣不可判控件修（阈值未动）（产品 2 文件，主列表行来源位）

最后更新：2026-10-28（本地 · R444 / 第 443 轮 / Round 441）：主列表此前只显示时间，来源只在详情头部。新 `HistoryRowSourceLine`：`时间 · 来自 <来源>`（时间在前；来源 nil/空白只显示时间；行宽不够先截断来源），`RowTextColumn` 接它 + `lineLimit(1)`。旧/新：`HISTORY_ROW_SOURCE light/dark 来源行宽=140.5pt 无来源行宽=73.5pt 差=67.0pt 左沿=96.5/96.5pt`；负臂 `sidebar-no-source`（同正文/时间、来源 nil；存档载入 + 清空选中，避免黑块盖行）只剩时间。帧 **57 张行/侧栏/content 变化 + 2 张负臂**，基线 **246→248 / 0/0/0**；`sidebar-history` 四行「时间 · 来自 Safari/预览/访达」已看。`M1220/M1221` **2/2 CAUGHT**；新单测 3 条 + 帧判据 1 条；预检 **222/204/582 bad=0**、ARM **315/1065**、HIDDEN **309/999 rot=0**。⓪：开工 `api=000`、两探断 ⇒ **`PUSH_BLOCKED=network`（ahead=3，HEAD `ed715f1`，origin/main `bdb4737`）** 与 **`CI_READ_BLOCKED=network`**；收口前 api 短暂恢复 ⇒ 补读 R442 自身跑 **`40605228813 ↔ bdb4737` failure、失败步骤 2 个**：vibrant 判据 `judged=22 != mustJudge=20`（不可判控件被算成判过）、设置关于行判据 light `0 != 7`（R118 的 282pt 机器差）—— 两条都是 R442 新判据的仪器病，本轮改成**视图树行带** + 把不可判控件从 judged 扣掉，阈值/产品未动，本地复跑绿（`PROBE_DOMAIN 44/44`、`SETTINGS_ABOUT_ROW light/dark 7`）；R442 跑的 `CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10/1.11`、`CAPTION_JUDGED 6/18` 已取；Motion floor 行不在这份失败步骤日志里 ⇒ NOT-RUN。R443 三笔未推、R444 自身跑待 push。本地全量 **1206/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/221.5/1438；TIME 18/9/54.0/1438；CHANNEL 0→82.0→600 变化 30442/105600 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **248 帧**；基线 **248/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 443，现读 `python3 scripts/product_streak.py --streak-for 443`，last=258fc8e）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 开工两探断 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；收口前补读 R442 跑 failure 2 步（vibrant 22≠20、关于行 0≠7）⇒ 修仪器（视图树行带/扣不可判控件），阈值未动；CODE/TABLE/CAPTION 读数已取。
② 产品：主列表行时间行补「· 来自 <来源 App>」（来源行 140.5 vs 73.5、差 67.0；57 张帧 + 2 张负臂，基线 248）。
③ 判据：M1220/M1221 2/2；新单测 3 条 + 帧判据；负臂清空选中；precheck 222/204/582；hidden rot 0。
④ 436：R442 跑的 Motion floor 行被网络 EOF 挡住，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 309 / 可判 999 / rot 0。
⑥ 捕获 248 帧；换装 ok；清账 162/63/0；帧基线 248/0/0/0；本地全量 1206/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① `PUSH_BLOCKED=network`（ahead=3 + 本轮提交；R443 三笔与 R444 本地提交待推）；② `CI_READ_BLOCKED=network`（R442 整份日志、R443 自身跑未创建、R444 自身跑待 push）；③ R442 跑的 Motion floor 行；④ 长来源截断无帧（474）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 437–474 仍开。

下一轮（R445）的靶：⓪ 先 `git push origin main`（禁 amend/force；**当前 `PUSH_BLOCKED=network`、ahead=3 + 本轮提交**，恢复后先只读 `git ls-remote` 验 remote 仍为 `bdb4737`，再一次快进 push 全部待推提交）并复核 ahead=0；读 R444 主笔+追记 head 跑、R443 三笔所在 head 跑与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看新判据 `HISTORY_ROW_SOURCE` 两档 140.5/73.5、`SETTINGS_ABOUT_ROW` 亮/暗 7（修后）、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主列表来源行/设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R444_REPORT_BULLET = u"""- **R444（主列表行来源位）**：剪贴板历史里"这条从哪个 App 来"是核心信息，但主列表以前只显示时间（来源只在详情头部）。新 `HistoryRowSourceLine`：`时间 · 来自 <来源>`（时间在前、来源在后；nil/空白只显示时间；行宽不够先截断来源），`RowTextColumn` 接它 + `lineLimit(1)`。旧/新：`HISTORY_ROW_SOURCE light/dark 来源行宽=140.5pt 无来源行宽=73.5pt 差=67.0pt 左沿=96.5/96.5pt`；负臂 `sidebar-no-source`（同正文/时间、来源 nil；存档载入 + 清空选中）只剩时间。帧 **57 张行/侧栏/content 变化 + 2 张负臂**，基线 **246→248 / 0/0/0**；`sidebar-history` 四行「时间 · 来自 Safari/预览/访达」已看。`M1220/M1221` **2/2**；新单测 3 条 + 帧判据；预检 222/204/582 bad=0、ARM 315/1065、HIDDEN 309/999 rot=0。⓪：开工 `api=000` 两探断 ⇒ `PUSH_BLOCKED=network`（ahead=3、HEAD `ed715f1`、origin/main `bdb4737`）与 `CI_READ_BLOCKED`；收口前 api 短暂恢复 ⇒ 补读 R442 跑 `40605228813 ↔ bdb4737` **failure 2 步**（vibrant 判据 judged 22≠20、设置关于行 light 0≠7）——都是新判据仪器病，改成视图树行带/扣不可判控件，阈值未动；R442 跑 `CODE 54/3/21/100%`、`TABLE 1.10/1.11`、`CAPTION_JUDGED 6/18` 已取；Motion floor 行未读 ⇒ NOT-RUN。本地全量 **1206/57/5**（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（OFFSET 0/221.5/1438；TIME 18/9/54/1438；CHANNEL 30442/105600）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 248 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
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
if u"第 443 轮（R444" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R444 节")
if u"## Round 441 · R444" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 441")
if u"## D-440" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-440")
if u"主列表行时间行补来源" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**474." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 474")
if state.count(u"## R443 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R443 状态"))
U_CELL_OLD = u"U-31 … U-1642（R443 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R443 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R443 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_440 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R443 状态", STATE_SECTION + u"## R443 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1647（R444 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R443 节 ②",
                                u"AGENT_STATE.md` 的 R444 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R444_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R444_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
