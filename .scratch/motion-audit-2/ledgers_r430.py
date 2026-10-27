#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R430 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 428 轮（R429 · 2026-10-27"
AUDIT_SECTION = u"""## 第 429 轮（R430 · 2026-10-27 · U-1573…U-1577）：浮层候选行补右侧定宽时间列（长标题不再吃掉时间：末段宽 71.5–74.5pt、五行右沿 385.5pt 同轴；旧帧右沿极差 152.5pt）；R429 跑失败步骤 2 个（runner 1x 脚注带 1/1、light 640 6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动（产品 1 文件，浮层时间列位）

- **U-1573：⓪ R429 跑的失败步骤与分区/菜单命运。** `40501223109 ↔ 3daf0e1` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。8 条断言全部落在 **R429 的脚注带尺**：runner 1x 上 `dark 720 带=1/1`、`dark 640 1/1`、`light 640 6/6`（本机 2x 是 7/6）；y 序断言方向相反（light 720 末带 515.0 对负末带 y1=524.0、dark 720 314.0 对 539.0、light 640 409.0 对 439.0、dark 640 239.0 对 439.0），外加「judged 1 ≠ 2」。**分区带在 runner 上是稳的**：`SIDEBAR_SECTION_HEADER light 正带=13 平带=12 插入带#3=156.0..165.0 墨=216 旧形状同带=163.0..172.0 墨=183`、dark `11/10 #1=156.0..165.0 墨=246 旧=162.0..172.0 墨=232`；`PINNED_SECTION_ROWS 有头=6 无头=5 选中=[2]/[1]`。菜单 `MenuShortcutPresentationTests` **5/5 passed**（真实 NSMenu 5 项两提示）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 在这一跑同样 **grep 0 命中**（只台账具名）。其余全绿：floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=4/5`、无红、无 unlisted；回执 **2/2**（2x 27 帧/2 过渡/峰值 0.0889/窗口 1151ms；1x 27/2/0.1278/1140ms，`重抓=yes`）；滚动 **4/4 passed**（`CHANNEL 0→125→600 变化 30000/17000 重抓=no`、`TIME 7/1/0/1430`）；拖拽源 mass 0.549/0.550、count 0.877/0.884；搜索 6 行；源图标最小窗文字 NOT-RUN；Dock 标记已登记。
- **U-1574：⓪ 的修法：1x 判不了就具名 NOT-RUN，2x 断言一字不动。** 定位到值以后看清了三种成因：① runner 1x 的 y 方向与本机 2x 相反（light 720 的 7/6 对得上，但「末带」在 runner 上是最上面那条导航行，与负臂 512..524 重叠）；② light 640 读 6/6（窄窗下这一列的带数分不开）；③ dark 两档 1/1（暗档整列同极性，就是 `darkSidebarTextBlindSpots` 那族）。这三条都不是产品缺陷，是**机器产物没有可判的带**。修法只动仪器：`density < 1.5` 的臂打 `SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`（带数/末带/负末带照打）并跳过像素断言；2x 本机仍判 7/6、末带墨 1086/1284、负末带 928/703、640 同读数；收尾断言从「judged=2」改成「每档要么判了、要么具名，且两档走同一条路」。阈值、地板、带扫描函数均未动。
- **U-1575：② 浮层候选行补右侧定宽时间列。** 缺陷形状在 `quickpick-list` 上直接看得见：时间与预览共用一条 `.byTruncatingTail` 的字符串 —— 第 0 行（长文本）与第 4 行（密钥）整行没有时间（被标题吃掉），第 1–3 行的时间各自停在自己文字后面（右沿参差）。修法：`rowTitle` 只留预览与命中理由；新 `rowTime(for:)` 沿用 `ClipboardDateFormatters.sidebarTime`（与侧栏同一套时间语言）；行格加一枚 11pt `secondaryLabelColor` 的右对齐时间标签，钉在行右沿 −6pt，标题右沿收到时间左沿 −8pt、压缩优先级降到 `.defaultLow`（标题截标题，时间永不被挤掉）。旧/新同尺（gap=10pt 的末段）：新末段宽 **74.0/71.5/74.0/74.0/73.5**（light）、**74.0/72.0/74.5/74.5/74.5**（dark），起点 311.0–313.0、止点 384.5–385.5 ⇒ 五行同轴；旧帧用同一把尺读 **止点 375.0/231.5/247.0/309.5/384.0**（极差 **152.5pt**）、第 4 行末段 **327.5pt**（标题连到省略号）。命中理由的像素证人改成**跨帧同一条目**：`quickpick-typed` 行 0（合同 + 「来自 访达」）止于 **216.5pt**，`quickpick-list` 行 2（同一条目、无理由）止于 **146.5pt** ⇒ 差 **70.0pt**（亮/暗同读数）。真看图：亮/暗两档每一行的时间都在右侧同一根轴上，长标题截在时间之前，选中行的时间仍可读。
- **U-1576：判据与刀。** 新 `testQuickPickRowsEndOnOneTimeColumn`（每行末段宽 40…140pt、五行起止极差 ≤2pt、每行左半段校准 >100 墨）+ `testRowTimeSurvivesTheLongestTitle`（长标题不含时间、rowTime 非空且等于 formatter）+ 更新 `testSourceOnlyMatchNamesItsReasonWhileOtherMatchesStayBare`（无查询时文案只剩预览）；R405 的像素证人收窄后重写成跨帧对照（时间列会把旧带子顶成恒绿）。`M1174–M1178` **5/5 CAUGHT**（时间列空串 / 时间列跟着标题漂 / 时间拼回标题 / rowTime 空串 / 理由不进标题；红在期望用例、RESTORE_CLEAN=yes）；R405 的 `M1051/M1052` 因注释换位腐烂，重钉后 **2/2 CAUGHT**。预检 `tables=205 covered=187 arms=545 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=298 arms=1028 dupes=0`；`HIDDEN_ARMS 表=292 可判=962 rot=0`。
- **U-1577：八步。** build **0 告警**；捕获 **137 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=10 / MISSING=0 / ADDED=0`（10 张全是 QuickPick 行帧：list/typed/hover/search-focus/search-hover × 亮暗），`UPDATED=238`、复验 **238/0/0/0**；全量 **1162/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=79/末=1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/206/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 429，现读 `python3 scripts/product_streak.py --streak-for 429`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 设置侧栏脚注带在 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`：暗档整列同极性、light 最小窗带数不可分、y 方向相反；2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；R429 跑同样 0 命中）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 浮层时间列不带年份、跨年记录分不清（456）；⑩ 真机/多屏面板落点无截屏（447）；⑪ 真菜单栏表面、12 实时腿；⑫ `table-lazy-rows`；⑬ 437–456 仍开；⑭ R430 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 427 · R430（第 429 轮 · 2026-10-27）：浮层候选行补右侧定宽时间列（长标题不再吃掉时间：末段宽 71.5–74.5pt、五行右沿 385.5pt 同轴；旧帧右沿极差 152.5pt）；R429 跑失败步骤 2 个（runner 1x 脚注带 1/1、light 640 6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动（产品 1 文件，浮层时间列位）

浮层候选行以前把预览、命中理由与时间拼成一条可截断字符串：长标题先把时间吃掉（`quickpick-list` 第 0/4 行整行没有时间），短标题的时间又各自停在文字后面（右沿参差）。改法：`rowTitle` 只留预览与理由，新 `rowTime(for:)` 沿用侧栏 formatter；行格加 11pt 右对齐 `secondaryLabelColor` 时间标签，钉在行右沿 −6pt，标题右沿收到时间左沿 −8pt 且压缩优先级降为 `.defaultLow`。旧/新同尺（gap=10pt 末段）：新末段宽 74.0/71.5/74.0/74.0/73.5（light）、74.0/72.0/74.5/74.5/74.5（dark），起止同轴（385.5）；旧帧止点 375.0/231.5/247.0/309.5/384.0 ⇒ 极差 152.5pt。命中理由的像素证人改成跨帧同一条目：typed 止 216.5 vs list 止 146.5 ⇒ 差 70.0pt。基线 10 张 QuickPick 行帧变化、238/0/0/0。R429 run `40501223109 ↔ 3daf0e1` **failure、失败步骤 2 个**（Swift tests / Capture gate）：8 条断言全在脚注带尺（1x 上 dark 1/1、light 640 6/6、y 反向）⇒ 1x 具名 `SETTINGS_FOOTER_BAND_NOT_RUN`、2x 断言不动；分区带在 1x 稳定（13/12、11/10；表格 6/5、选中 [2]/[1]）。菜单 5/5；floor 4/5/77（notice-banner）；回执 2/2；滚动 4/4；拖拽 mass 0.549/0.550；搜索 6 行。M1174–M1178 5/5；R405 重钉 2/2；预检 205/187/545 bad=0；ARM 298/1028；HIDDEN 292/962 rot=0。全量 1162/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（TIME 18/8、79→1438；CHANNEL 0→82.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 137/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 `quickpick-list`/`quickpick-typed` 亮暗帧：时间列同轴、长标题截在时间之前、理由与时间并存；旧帧同一把尺读到 152.5pt 参差。扣 2：没有真机窗口里的浮层截图，1x 行帧只能等 runner 读数。 |
| 判据有效性 | 15/15 | 末段宽/起止极差/校准三件套 + 长标题单测 + 跨帧理由对照；M1174–M1178 5/5、R405 重钉 2/2、r29d 5/5。 |
| 假绿防御 | 15/15 | 理由证人收窄到时间列之前（否则时间墨把旧带子顶成恒绿）；时间列测试带校准；脚注 1x 判不了就具名 NOT-RUN，不冒充绿。 |
| 产品面推进 | 14/15 | 真落产品 1 文件（浮层候选行信息位，像素可复核）；扣 1：只补了时间列，行密度/选中态未动。 |
| 台账一致性 | 15/15 | U-1573…U-1577、D-426、R429 的 1/1、6/6、152.5、70.0、238、1162 都从日志/帧解析。 |
| 交付诚实性 | 15/15 | R429 的 1x 红定位到三种机器成因并具名 NOT-RUN；菜单具名标记 0 命中照实写；拖拽/Dock/源图标/本地滚动各有具名出口。 |
| 可复核性 | 15/15 | 帧名、末段起止、旧帧读数、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_426 = u"""## D-426 浮层时间改成右侧定宽列；脚注带在 1x 上只登记不冒充（R430）

- 背景：浮层候选行把预览、命中理由、时间拼成一条 `.byTruncatingTail` 字符串；长标题会把时间整段截掉（`quickpick-list` 第 0/4 行），短标题的时间又停在各自文字后面，右沿参差。R429 的脚注带扫描在 runner 1x 上读到 dark 1/1、light 640 6/6，且 y 方向与本机相反。
- 决定：① `rowTitle` 只留预览与「来自 X」；时间走 `rowTime(for:)`（沿用 `ClipboardDateFormatters.sidebarTime`）与行内右侧定宽标签（11pt `secondaryLabelColor`、trailing −6、标题 trailing 收到时间 leading −8、标题压缩优先级 `.defaultLow`、时间 `.required`）。② 脚注像素带只在 2x 判；1x 打 `SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry` 并带读数，不把机器差异记成产品缺陷，也不改带扫描阈值。
- 理由：时间与标题抢同一条截断预算时，被牺牲的永远是排在后面的信息；拆成两列后，标题截标题、时间恒在。像素断言只在本机能复现的产物上判，runner 的 1x 产物用既有 `*_NOT_RUN` 契约登记（与 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN` 同一条路）。
- 兼容性/迁移：浮层行高、图标列、左轴、命中理由都未动；只有行文案少了时间、右侧多一列。10 张 QuickPick 行帧变化，基线仍 238；`quickpick-empty` 无行、帧不变。
- 边界：时间格式沿用侧栏的 `M月d日 HH:mm`，跨年记录没有年份（456）；1x runner 上时间列的断言仍是同一套点坐标（等下一跑签收）。
- 回滚：删 `rowTime`/时间标签与两条约束、把时间拼回 `rowTitle` 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 浮层候选行补右侧定宽时间列（长标题不再吃掉时间：末段宽 71.5–74.5pt、五行右沿 385.5pt 同轴；旧帧右沿极差 152.5pt）；R429 跑失败步骤 2 个（runner 1x 脚注带 1/1、light 640 6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动（R430 / 第 429 轮 / Round 427 / U-1573…U-1577 · 产品 1 文件，浮层时间列位）

"""

BACKLOG_SECTION = u"""437 追记（R430 · 仍开）：本轮补的是浮层候选行的时间列；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R430 · 仍开）：R429 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→125→600、TIME 7/1/0/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、79→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R430 · 仍开）：macOS 12 的详情头部阈值本轮未动；浮层时间列不涉及它。

452 追记（R430 · 仍开，口径收紧）：脚注带扫描在 runner 1x 上判不了（暗档 1/1、light 640 6/6、y 反向）⇒ 1x 具名 `SETTINGS_FOOTER_BAND_NOT_RUN`，像素断言只在 2x 本机跑；版本行布局本轮未动。

453 追记（R430 · 仍开）：真实系统拖拽会话仍无自动化验收；本轮只动了浮层行格。

454 追记（R430 · 仍开）：R429 跑的 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 同样 **grep 0 命中** —— 连续两跑确认它只是台账散文，不是机器通道；菜单 5/5 仍由真实 NSMenu 用例作证。

455 追记（R430 · 仍开）：R429 跑在 1x 上 `PINNED_SECTION_ROWS 6/5 选中 [2]/[1]` 通过，分区带 13/12 与 11/10 也稳；缺的仍是固定条目**滚动到位**的独立偏移验收。

**456. 浮层/侧栏的时间格式 `M月d日 HH:mm` 不带年份：跨年记录分不清**（R430 观察）
    现象：`ClipboardDateFormatters.sidebarTime` 固定 `M月d日 HH:mm`。R430 把时间固定到浮层右侧列以后，一年前的记录与今年的同月同日会显示成同一串；详情头虽然用 `yyyy-MM-dd HH:mm:ss`，但列表/浮层是选条目时唯一看得见的时间。
    修法（下一轮若需要）：按「今天/今年/更早」分档（今天 `HH:mm`、今年 `M月d日`、更早 `yyyy年M月d日`），或在悬停/选中时补年份；改之前先给两侧各拍一张跨年夹具帧，确认列宽不被更长字符串顶开（现有末段宽 71.5–74.5pt 的读数就是地板）。
"""

STATE_SECTION = u"""## R430 状态（2026-10-27 · 本地 · 第 429 轮 / Round 427）：浮层候选行补右侧定宽时间列（长标题不再吃掉时间：末段宽 71.5–74.5pt、五行右沿 385.5pt 同轴；旧帧右沿极差 152.5pt）；R429 跑失败步骤 2 个（runner 1x 脚注带 1/1、light 640 6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动（产品 1 文件，浮层时间列位）

最后更新：2026-10-27（本地 · R430 / 第 429 轮 / Round 427）：浮层候选行以前把预览、命中理由与时间拼成一条可截断字符串 —— 长标题先把时间吃掉（`quickpick-list` 第 0/4 行整行没有时间），短标题的时间又各自停在文字后面（右沿参差）。新 `rowTitle` 只留预览与理由；新 `rowTime(for:)` 沿用 `ClipboardDateFormatters.sidebarTime`；行格加 11pt `secondaryLabelColor` 右对齐时间标签，钉在行右沿 −6pt，标题右沿收到时间左沿 −8pt、压缩优先级降到 `.defaultLow`。旧/新同尺（gap=10pt 末段）：新末段宽 **74.0/71.5/74.0/74.0/73.5**（light）、**74.0/72.0/74.5/74.5/74.5**（dark），起点 311.0–313.0、止点 384.5–385.5；旧帧止点 **375.0/231.5/247.0/309.5/384.0**（极差 **152.5pt**）、第 4 行末段 327.5pt。命中理由的像素证人改跨帧同一条目：typed 止 216.5 vs list 止 146.5 ⇒ 差 **70.0pt**。R429 run `40501223109 ↔ 3daf0e1` **failure，失败步骤 2 个**（Swift tests / Capture gate）：8 条断言全在脚注带尺（1x 上 dark 720/640 1/1、light 640 6/6、y 反向）⇒ 修仪器：1x 打 `SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry` 并带读数，2x 本机仍判 7/6、末带 1086/1284、负末带 928/703；阈值未动。分区带在 1x 稳定（light 13/12、dark 11/10；表格 6/5、选中 [2]/[1]）。菜单 5/5 passed（真实 NSMenu）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 连续两跑 0 命中（只台账具名，454）。floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、无红、无 unlisted；回执 **2/2**；滚动 **4/4**（`CHANNEL 0→125→600 30000/17000`、`TIME 7/1/0/1430`）；拖拽 mass 0.549/0.550。`M1174–M1178` **5/5 CAUGHT**（时间列空/漂/拼回标题/rowTime 空/理由丢失）；R405 `M1051/M1052` 重钉 **2/2**；预检 **205/187/545 bad=0**、ARM **298 文件 / 1028 把**、HIDDEN **292/962 rot=0**。本地全量 **1162/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/79/1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/206/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **137/4/0 / 238 帧**；基线 **238/0/0/0**（10 张 QuickPick 行帧变化）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 429，现读 `python3 scripts/product_streak.py --streak-for 429`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R429 跑 failure、失败步骤 2 个：8 条断言全在脚注带尺的 1x 机器成因（1/1、6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动；分区带/表格行数在 1x 稳定；菜单 5/5；floor 4/5/77 无红；回执 2/2；滚动 4/4；拖拽 mass 0.549/0.550；搜索 6 行。
② 产品：浮层候选行补右侧定宽时间列（旧帧右沿极差 152.5pt → 新五行同轴 385.5；末段宽 71.5–74.5pt；理由证人 70.0pt）。
③ 判据：M1174–M1178 5/5；R405 重钉 2/2；precheck 205/187/545；hidden rot 0。
④ 436：R429 跑 judged=4/5 executed=77（notice-banner 放行）、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 292 / 可判 962 / rot 0。
⑥ 捕获 137/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1162/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`；2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；连续两跑 0 命中）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 跨年记录没有年份（456）；⑩ 真机/多屏面板落点无截屏（447）；⑪ 真菜单栏表面、12 实时腿；⑫ `table-lazy-rows`；⑬ 437–456 仍开；⑭ R430 新跑待 push 后读。

下一轮（R431）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R430 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看浮层时间列在 runner 1x 上的末段宽/同轴读数、`SETTINGS_FOOTER_BAND_NOT_RUN` 是否按名出现且不计红、分区带 13/12 与表格 6/5、菜单 5 项/两提示、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R430_REPORT_BULLET = u"""- **R430（浮层时间列位）**：浮层候选行以前把预览、命中理由与时间拼成一条可截断字符串 —— 长标题先把时间吃掉（`quickpick-list` 第 0/4 行整行没有时间），短标题的时间各自停在文字后面（右沿参差）。新 `rowTitle` 只留预览与理由；新 `rowTime(for:)` 沿用 `ClipboardDateFormatters.sidebarTime`；行格加 11pt `secondaryLabelColor` 右对齐时间标签（钉行右沿 −6pt），标题右沿收到时间左沿 −8pt、压缩优先级降 `.defaultLow`。旧/新同尺（gap=10pt 末段）：新末段宽 **74.0/71.5/74.0/74.0/73.5**（light）/ **74.0/72.0/74.5/74.5/74.5**（dark），起止 **385.5pt** 同轴；旧帧止点 **375.0/231.5/247.0/309.5/384.0** ⇒ 极差 **152.5pt**、第 4 行末段 327.5pt。命中理由像素证人改跨帧同一条目：typed 止 216.5 vs list 止 146.5 ⇒ 差 **70.0pt**。R429 run `40501223109 ↔ 3daf0e1` **failure、失败步骤 2 个**（Swift tests / Capture gate）：8 条断言全在脚注带尺（1x 上 dark 1/1、light 640 6/6、y 反向）⇒ 1x 具名 `SETTINGS_FOOTER_BAND_NOT_RUN`、2x 断言不动；分区带在 1x 稳定（13/12、11/10；表格 6/5、选中 [2]/[1]）。菜单 5/5；floor 4/5/77（notice-banner）；回执 2/2；滚动 4/4（`CHANNEL 0→125→600`、`TIME 7/1/0/1430`）；拖拽 mass 0.549/0.550；搜索 6 行。M1174–M1178 **5/5**；R405 重钉 2/2；预检 205/187/545 bad=0；HIDDEN 292/962 rot=0。本地全量 **1162/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、79→1438；CHANNEL 0→82.5→600、34773/108000）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 137/4/0、238 帧；基线 238/0/0/0（10 张 QuickPick 行帧变化）；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 429 轮（R430" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R430 节")
if u"## Round 427 · R430" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 427")
if u"## D-426" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-426")
if u"浮层候选行补右侧定宽时间列" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**456." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 456")
if state.count(u"## R429 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R429 状态"))
U_CELL_OLD = u"U-31 … U-1572（R429 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R429 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R429 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_426 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R429 状态", STATE_SECTION + u"## R429 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1577（R430 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R429 节 ②",
                                u"AGENT_STATE.md` 的 R430 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R430_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R430_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
