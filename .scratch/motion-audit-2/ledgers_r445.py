#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R445 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 443 轮（R444 · 2026-10-28"
AUDIT_SECTION = u"""## 第 444 轮（R445 · 2026-10-28 · U-1648…U-1652）：侧栏搜索补匹配来源 App 名（R437 欠账；只命中来源的查询从 0 行→1 行、无结果态无表=0；新 `HistorySearchPolicy` + Store 收薄到 1108 行/最长 66；2 张新帧、基线 248→250）（产品 3 文件，侧栏搜索来源位）

- **U-1648：⓪ push 与两跑。** 开工按监督者读数一次快进 push **`bdb4737..eeccad0` success**（六笔：R443 三 + R444 三），HEAD = origin/main = `eeccad0`、**ahead=0**。新 head 跑 **`40613782362 ↔ eeccad0`** 开始 in_progress、稍后 `gh` **EOF** ⇒ 具名 **`CI_READ_BLOCKED=network` / NOT-RUN**（R444 的两条仪器修复在 runner 1x 上是否真绿待 R446 ⓪ 补读）。R442 跑 `40605228813 ↔ bdb4737` 已读：failure、失败步骤 2 个（vibrant 判据 judged 22≠20、设置关于行 light 0≠7）= 上一轮的仪器病，R444 已修（视图树行带/扣不可判控件）；其 `CODE_LINE_NUMBERS 54/3/21/100%`、`TABLE_HEADER 1.10/1.11`、`CAPTION_JUDGED 6/18` 已取。收口 `api=000` ⇒ R445 的提交将具名 **`PUSH_BLOCKED=network`**（见预记）。
- **U-1649：① 腐烂与预检。** `HIDDEN_ARMS 表=310 可判=1001 rot=0`；`NEEDLE_PRECHECK tables=223 covered=205 arms=584 bad=0`、`ARM_TOTAL files=316 arms=1067 dupes=0 repeats=0`。新表 `mutate_r445_search_source` 已登记。
- **U-1650：② 侧栏搜索补匹配来源 App 名。** 缺陷形状（R437）：搜索不匹配 `sourceAppName`——而 R444 已把来源显示在每行（`时间 · 来自 <来源>`）：看得见、搜不到。修法：新 `HistorySearchPolicy.matches`（**来源名与内容/OCR/文件并列**，不是替换；空来源/空查询不编匹配）；`HistoryStore.computeFilteredEntries` 收成一行调用，Store 从 1120→**1108 行**、最长方法仍 **66**（薄守卫不升）。旧/新：`HISTORY_SEARCH_SOURCE light/dark 来源查询行数=0→1（行带 3） 无结果查询=无表/0`；夹具 `sidebar-search-source`（查询 "Safari" 不在任何正文里，只在第一行来源）旧口径与 `sidebar-no-results` 同形、新口径 1 行。**2 张新帧、0 张旧帧变化**，基线 **248→250 / 0/0/0**；已看：搜索框 "Safari" + "1 条记录" + 行内「来自 Safari」。
- **U-1651：判据、刀与夹具修正。** 新单测 `HistorySearchPolicyTests` 4 条（来源+内容并列/大小写、nil/空白回退、空查询、**产品入口** store 搜索只命中来源的行）+ 新帧判据 `testSidebarSearchMatchesTheSourceAppName`（来源查询表行数=1、无结果态无表=0、行带 ≥3；1x 行带 0 时具名 `HISTORY_SEARCH_SOURCE_NOT_RUN`）。`M1224`（策略删来源）⇒ 单测 2 条 + 帧判据 CAUGHT；`M1225`（策略丢正文）⇒ 单测 4 条 + 既有 `testPerformUpdatesSearchAndFiltersEntries` 红 ⇒ **2/2**、RESTORE_CLEAN=yes。两处夹具修正：过滤后单行被 List 默认选中（离屏黑块吞字，亮档行带只剩 1）⇒ 清空选中；无结果态**没有 NSTableView** ⇒ 负臂读成"无表=0 行"，不把 -1 当行数。
- **U-1652：八步与具名 NOT-RUN。** build **0 告警**（冷编 0）；捕获卷全绿 **250 帧**；帧基线 `COMPARED=250 CHANGED=0 MISSING=0 ADDED=0`；全量 **1211/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` 后 **4/4**（`OFFSET 0/202.0/1438`、`TIME 18/8/24.5/1438`、`CHANNEL 0→80.0→600 变化 721/96000 重抓=no`；起→中只 721 偏低但 >0，复跑绿）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 444，现读 `python3 scripts/product_streak.py --streak-for 444`，last=50c186d）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① R445 自身跑（提交后创建；收口 `api=000`）；② `40613782362 ↔ eeccad0`（CI_READ_BLOCKED=network，R444 修复的 runner 验证待 R446）；③ 436 的新跑 Motion floor（本跑未读）；④ 搜索匹配 **bundle ID** 未接（475）；⑤ 长来源截断无帧（474）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 437–475 仍开。

"""

ITER_SECTION = u"""## Round 442 · R445（第 444 轮 · 2026-10-28）：侧栏搜索补匹配来源 App 名（R437 欠账；只命中来源的查询从 0 行→1 行、无结果态无表=0；新 `HistorySearchPolicy` + Store 收薄到 1108 行/最长 66；2 张新帧、基线 248→250）

搜索不匹配来源名，而 R444 已把来源显示在行里。新 `HistorySearchPolicy.matches`：来源与内容/OCR/文件并列（不是替换；空来源/空查询不编匹配）；Store 的 `computeFilteredEntries` 收成一行调用（1120→1108 行、最长仍 66）。夹具 `sidebar-search-source`（查询 "Safari" 不在正文、只在来源）旧口径 0 行、新 1 行；无结果态没有 NSTableView（负臂读成无表=0，不把 -1 当行数）；过滤后单行被 List 默认选中（黑块吞字）⇒ 清空选中。2 张新帧、0 变化，基线 250/0/0/0。M1224/M1225 2/2。⓪：push bdb4737..eeccad0 success、ahead=0；新 head 跑 40613782362 读时 in_progress 后 EOF ⇒ CI_READ_BLOCKED；R442 跑 failure 2 步（仪器病，R444 已修）读数已取；收口 api=000 ⇒ R445 提交待推。全量 1211/57/5；捕获 250 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `sidebar-search-source` 逐张看过：搜索框 "Safari"、"1 条记录"、行内「来自 Safari」；旧口径与无结果同形被表行数/行带两轴钉住。 |
| 判据有效性 | 15/15 | 纯策略 4 条 + 产品入口 store 搜索 + 帧判据（行数 1/无表 0/行带 3）；M1224/M1225 2/2。 |
| 假绿防御 | 15/15 | 负对照是"无结果态无表"而不是"-1 行"；过滤单行的选中黑块被识别并清掉；1x 行带 0 才 NOT-RUN。 |
| 产品面推进 | 14/15 | 真把来源名接进搜索（437 欠账闭合，R444 显示→R445 可搜）；Store 只减不加；扣 1：bundle ID 未搜（475）。 |
| 台账一致性 | 15/15 | U-1648…U-1652、D-441、push eeccad0、250 帧/1211、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 新跑 in_progress/EOF 具名；收口断网照实记；R442 的 2 步红与其修复对上轮；CHANNEL 721 偏低也照印。 |
| 可复核性 | 15/15 | 行数 1/无表 0、行带 3、策略 4 条、刀号与 precheck/rot、基线 250、换装/清账都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_441 = u"""## D-441 侧栏搜索匹配来源 App 名（R445）

- 背景：R437 起记着"主列表搜索不匹配 `sourceAppName`"；R444 已把来源显示在每行（`时间 · 来自 <来源>`）——看得见、搜不到。
- 决定：新 `HistorySearchPolicy.matches`：来源名与内容/OCR/文件**并列**（不是替换；空来源/空查询不编匹配）；`HistoryStore.computeFilteredEntries` 收成一行调用（Store 只减不加）。
- 理由：来源是剪贴板历史的核心元信息；策略纯函数可单测；行帧在 1x 可画，来源查询的行数 0→1 是结构量。
- 兼容性/迁移：新夹具 `sidebar-search-source`（2 帧，基线 248→250）；无结果态无 NSTableView（负臂=无表 0 行）；过滤单行会被 List 默认选中（离屏黑块）⇒ 夹具清空选中。
- 边界：bundle ID 未搜（475）；长来源截断无帧（474）；QuickPick 已有来源理由带（R430）。
- 回滚：Store 恢复原 switch 即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 侧栏搜索补匹配来源 App 名（只命中来源的查询 0 行→1 行；新 `HistorySearchPolicy` + Store 收薄到 1108 行/最长 66；2 张新帧、基线 250）（R445 / 第 444 轮 / Round 442 / U-1648…U-1652 · 产品 3 文件，侧栏搜索来源位）

"""

BACKLOG_SECTION = u"""437 结案（R445）：主列表搜索已匹配 `sourceAppName`（R444 显示、R445 可搜）；bundle ID 仍未接（475）。

449 追记（R445 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/202/1438；TIME 18/8/24.5/1438；CHANNEL 721/96000）。

451 追记（R445 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R445 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R445 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R445 · 仍开）：菜单具名标记仍未发射。

455 追记（R445 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R445 · 仍开）：跨年记录仍无年份。

457 追记（R445 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R445 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R445 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R445 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R445 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R445 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R445 · 仍开）：展开态已加载内容仍无帧。

464 追记（R445 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R445 · 仍开）：HTML 引用块没有导引线。

466 追记（R445 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R445 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R445 · 仍开）：HTML 代码块没有行号。

469 追记（R445 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R445 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R445 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R445 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R445 · 仍开）：长来源 App 名的截断没有帧。

**475. 侧栏搜索不匹配来源 App 的 bundle ID**（R445 观察）
    现象：R445 把 `sourceAppName`（显示名）接进搜索；`sourceAppBundleID`（如 `com.apple.Safari`）没有。搜 "com.apple" 仍 0 行，而它是同一条来源信息的机器名。
    修法：把 bundle ID 也并进 `HistorySearchPolicy` 的来源匹配（显示名优先；bundle ID 作为第二段），加单测与一个 `com.apple` 查询帧。
"""

STATE_SECTION = u"""## R445 状态（2026-10-28 · 本地 · 第 444 轮 / Round 442）：侧栏搜索补匹配来源 App 名（只命中来源的查询 0 行→1 行、无结果态无表=0；新 `HistorySearchPolicy`，Store 收薄 1120→1108 行/最长 66；2 张新帧、基线 248→250）；R444 修复的 runner 验证被 EOF 挡住（40613782362 in_progress→EOF）（产品 3 文件，侧栏搜索来源位）

最后更新：2026-10-28（本地 · R445 / 第 444 轮 / Round 442）：搜索不匹配来源名，而 R444 已把来源显示在行里。新 `HistorySearchPolicy.matches`：来源名与内容/OCR/文件并列（不是替换；空来源/空查询不编匹配）；`HistoryStore.computeFilteredEntries` 收成一行调用（1120→**1108 行**、最长仍 **66**）。夹具 `sidebar-search-source`（查询 "Safari" 不在任何正文、只在第一行来源）：旧口径 0 行（与 `sidebar-no-results` 同形）、新 **1 行**；无结果态**没有 NSTableView** ⇒ 负臂读成"无表=0 行"（不是 -1）；过滤后单行被 List 默认选中（离屏黑块吞字）⇒ 夹具清空选中。读数：`HISTORY_SEARCH_SOURCE light/dark 来源查询行数=1（行带 3） 无结果查询=-1（无表）`；**2 张新帧、0 张旧帧变化**，基线 **248→250 / 0/0/0**；已看搜索框 "Safari"、"1 条记录"、行内「来自 Safari」。`M1224/M1225` **2/2 CAUGHT**；新单测 4 条 + 存储入口 + 帧判据；预检 **223/205/584 bad=0**、ARM **316/1067**、HIDDEN **310/1001 rot=0**。⓪：开工一次快进 push **`bdb4737..eeccad0` success**（六笔）、HEAD=origin/main=`eeccad0`、**ahead=0**；新 head 跑 **`40613782362 ↔ eeccad0`** 开始 in_progress、后 EOF ⇒ `CI_READ_BLOCKED=network`/NOT-RUN（R444 的两条仪器修复的 runner 验证待 R446）；R442 跑 `40605228813 ↔ bdb4737` failure 2 步（仪器病，R444 已修）读数已取；收口 `api=000` ⇒ R445 提交 `PUSH_BLOCKED=network`（见预记）。本地全量 **1211/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/202.0/1438；TIME 18/8/24.5/1438；CHANNEL 0→80.0→600 变化 721/96000 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **250 帧**；基线 **250/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 444，现读 `python3 scripts/product_streak.py --streak-for 444`，last=50c186d）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push `bdb4737..eeccad0` success、ahead=0；新 head 跑 40613782362 in_progress→EOF ⇒ CI_READ_BLOCKED；R442 跑 2 步红（仪器病已修）读数已取；收口断网 ⇒ R445 提交待推。
② 产品：侧栏搜索补匹配来源 App 名（0→1 行；Store 收薄 1108/66；2 张新帧、基线 250）。
③ 判据：M1224/M1225 2/2；新单测 4 条 + store 入口 + 帧判据；负臂无表=0；precheck 223/205/584；hidden rot 0。
④ 436：新跑读数被 EOF 挡住，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 310 / 可判 1001 / rot 0。
⑥ 捕获 250 帧；换装 ok；清账 162/63/0；帧基线 250/0/0/0；本地全量 1211/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① R445 自身跑（提交后创建；收口 api=000）；② `40613782362 ↔ eeccad0`（CI_READ_BLOCKED=network，R444 修复的 runner 验证）；③ 436 新跑 Motion floor；④ bundle ID 未搜（475）；⑤ 长来源截断无帧（474）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 437–475 仍开。

下一轮（R446）的靶：⓪ 先 `git push origin main`（禁 amend/force；恢复后先只读 `git ls-remote` 验 remote 未变再一次快进 push）并复核 ahead=0；读 R445 主笔+追记 head 跑、`40613782362 ↔ eeccad0` 与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看 `HISTORY_SEARCH_SOURCE` 两档 0→1/行带 3、`HISTORY_ROW_SOURCE` 140.5/73.5、`SETTINGS_ABOUT_ROW` 亮/暗 7、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R445_REPORT_BULLET = u"""- **R445（侧栏搜索来源位）**：R437 起记着搜索不匹配 `sourceAppName`，而 R444 已把来源显示在行里（看得见、搜不到）。新 `HistorySearchPolicy.matches`：来源名与内容/OCR/文件**并列**（不是替换；空来源/空查询不编匹配）；`HistoryStore.computeFilteredEntries` 收成一行调用，Store **1120→1108 行**、最长仍 **66**。夹具 `sidebar-search-source`（查询 "Safari" 不在正文、只在第一行来源）：旧口径 0 行（与 `sidebar-no-results` 同形）、新 **1 行**；无结果态**没有 NSTableView** ⇒ 负臂"无表=0"（不是 -1）；过滤后单行被 List 默认选中（黑块吞字）⇒ 清空选中。读数：`HISTORY_SEARCH_SOURCE light/dark 来源查询行数=1（行带 3） 无结果=无表`；**2 张新帧、0 旧帧变化**，基线 **248→250 / 0/0/0**；已看搜索框 "Safari"、"1 条记录"、行内「来自 Safari」。`M1224/M1225` **2/2**；新单测 4 条 + store 入口 + 帧判据；预检 223/205/584 bad=0、ARM 316/1067、HIDDEN 310/1001 rot=0。⓪：一次快进 push **`bdb4737..eeccad0` success**、HEAD=origin/main=`eeccad0`、ahead=0；新 head 跑 `40613782362 ↔ eeccad0` in_progress→EOF ⇒ `CI_READ_BLOCKED`/NOT-RUN（R444 仪器修复的 runner 验证待 R446）；R442 跑 failure 2 步（仪器病已修）读数已取；收口 api=000 ⇒ R445 提交待推。本地全量 **1211/57/5**，单跑 4/4（OFFSET 0/202/1438；TIME 18/8/24.5/1438；CHANNEL 721/96000）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 250 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 444 轮（R445" in audit: raise SystemExit("REFUSED AUDIT 已有 R445")
if u"## Round 442 · R445" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 442")
if u"## D-441" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-441")
if u"侧栏搜索补匹配来源 App 名" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**475." in backlog: raise SystemExit("REFUSED BACKLOG 已有 475")
if state.count(u"## R444 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R444 状态"))
U_CELL_OLD = u"U-31 … U-1647（R444 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R444 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_441 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R444 状态", STATE_SECTION + u"## R444 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1652（R445 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R444 节 ②", u"AGENT_STATE.md` 的 R445 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R445_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R445_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
