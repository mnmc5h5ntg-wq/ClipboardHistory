#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R429 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 427 轮（R428 · 2026-10-27"
AUDIT_SECTION = u"""## 第 428 轮（R429 · 2026-10-27 · U-1568…U-1572）：侧栏固定块补「已固定」分区头（旧形状无头 5 行 → 新 6 行、插入带墨 742/784、选中揭示行号 +1；基线 238）；R428 跑失败步骤 2 个（runner 上找不到品红标记）⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动（产品 4 文件，侧栏分区位）

- **U-1568：⓪ R428 跑的失败步骤与菜单 / marker 命运。** `40493617687 ↔ ab3e656` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。唯一红是 R428 的脚注**品红标记**在 runner 上找不到：`light：正臂里找不到脚注的品红标记 ⇒ 版本行没画出来`、`dark` 同句，外加 `XCTAssertEqual failed: ("0") is not equal to ("2") - 两档里有一档没量到对象`；同跑 `SETTINGS_FOOTER` 通道**没有一行**（先判：尺没走到 / 打印被改名，不许把无行读成绿）。菜单命运：`MenuShortcutPresentationTests` **5/5 passed**（真实 NSMenu 带两枚提示 + 快速选择、配置热键映射、自定义键在 populate 跟随、标题只追加非空提示、两个表面同源），`AppCommandTests` 3/3、`MenuBarPopulationTests` 全绿；但 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu` 在 runner 日志里 **grep 0 命中** ⇒ 它只是台账散文中具名，不是机器发射的通道（照实记账，见 454 追记）。其余全绿：floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted（`SUITE_NOT_SEEN=2`、`LOOP_NOT_JUDGED` 2 个具名）；源图标最小窗文字 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`（59/110、0/63、0/0；dark 59/139、0/57、0/0）；拖拽源 `墨数比=0.877/0.884、墨量比=0.549/0.550`；搜索 4 行；滚动 **4/4 passed**（`CHANNEL 0→41→600 变化 25200/6561 重抓=no`、`TIME 4 采样/1 中间值/首=1330/末=1430`、`OFFSET 0/398/1430`）；Dock `DOCK_BADGE_PIXEL_NOT_RUN` 已登记；`MOTION_COPY_RECEIPT` **2/2**（2x 27 帧/2 过渡/峰值 0.1333/窗口 1321ms；1x 27/2/0.1278/1303ms，`重抓=yes`）⇒ 不再是 NOT-RUN。
- **U-1569：R429 把 marker 退役，改成同帧带扫描 + 真实表格行数。** 原因：品红标记依赖 runner 上的 vibrant 合成路径，R428 跑里亮暗两档都找不到（不是阈值问题）。新尺不再找颜色标记：① 脚注用 `sidebarInkBands` 数**同帧墨带**——`settings-general` 7 带 vs `settings-general-no-footer` 6 带，末带 **262.5..272.0 墨=1086**（light）/ **262.0..272.0 墨=1284**（dark），负臂末带只是最后一行导航（230.5..242.5 墨=928 / 231.0..242.5 墨=703），640×440 最小窗同为 7/6 带、末带 1086/1284；② 分区头用同一把带尺：`sidebar-pinned-section` 13 带 vs flat 12 带，插入带 #3 **158.0..168.0 墨=742**（light）/ **157.5..167.5 墨=784**（dark），旧形状同带 164.0..175.0 墨 831/931（整块下移一行）；③ 行数用**真实 `NSTableView`**：有头 **6 行**、无头 **5 行**，选中行 **[2]/[1]**（`PINNED_SECTION_ROWS`）。帧集合：4 张 marker 帧撤掉、4 张分区帧新增；基线复验 `CHANGED=0 / MISSING=4（marker）/ ADDED=4（section）`，同一笔 `UPDATED=238`，复验 **238/0/0/0**。阈值与地板一律未动。
- **U-1570：② 侧栏固定块补「已固定」分区头。** 以前固定条目与普通条目完全同形，只有星标区分。新 `SidebarSectionPlan`（`pinnedTitle=已固定`、`hasPinnedHeader = pinnedCount > 0`、`displayRowIndex(forFilteredIndex:)` 头部存在时 +1）+ `SidebarSectionHeader`（11pt `VisualFont.meta` semibold、`secondaryLabelColor`、左沿 22pt、上下 4pt、`.isHeader` 无障碍特征）+ `HistorySidebarView` 在固定块上方放一个 `Section`（无固定条目或无头时仍走原单个 `ForEach`，老帧不变）；`SelectedRowRevealer` 的行号经 `sectionPlanForDrawing` 换算。旧/新真读数（300×520 离屏帧）：无头 12 带 / 有头 13 带，插入带墨 742（light）/ 784（dark）；选中揭示行号 +1 由真实表格行数 6/5 与选中 [2]/[1] 作证。真看图：亮/暗两档「已固定」在固定块上方、固定行整块下移一行、行内容与星标不变。静态取证帧把选区显式清空（`setSelection([])`），免得选中行的材料带被暗档盲区守卫读成黑带（R428 的教训）。
- **U-1571：判据与刀。** 新 `SidebarSectionHeaderTests`（plan 恒等/+1、标题、`Section/header/reveal rowIndex/header view` 四段源守卫）+ `UICaptureHarness` 三条管线级判据（脚注带差 7/6、分区带差 13/12、真实表格行数 6/5+选中 [2]/[1]）+ `UIInteractionProbeTests` 的 `sectionRow` 映射（r61 的落点带/矩形/表格集合都按 `table.rowHeight` 与 `SidebarSectionPlan` 换算）。`M1167–M1173` **7/7 CAUGHT**（plan 2 / header 2 / wiring 3，红在期望用例、RESTORE_CLEAN=yes）；r29d M132–M136 **5/5 CAUGHT**（名册去 marker 行后第三次重钉）；r61 的 M314 因旧异步块被 R413 边界动画替换而退役、M316 重钉到新 `.map { sectionPlanForDrawing.displayRowIndex… }` 块。预检 `tables=204 covered=186 arms=540 bad=0`、`BASH_ARMS tables=6 arms=16 bad=0`、`ARM_TOTAL files=297 arms=1023 dupes=0`；`HIDDEN_ARMS 表=291 可判=957 rot=0`。
- **U-1572：八步。** build **0 告警**；捕获 **136 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `UPDATED=238`、复验 `238/0/0/0`；全量 **1160/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=9/首=52.5/末=1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/204.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 428，现读 `python3 scripts/product_streak.py --streak-for 428`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 13+ MenuBarExtra 系统菜单的像素/标题通道（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；本轮 grep 0 命中 ⇒ 只在台账具名、不进已登记标记表）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑥ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑦ 设置侧栏版本行窗口下沿未成立（452）；⑧ 固定块揭示行号在真实滚动里的像素/偏移没有独立验收（455）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–455 仍开；⑬ R429 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 426 · R429（第 428 轮 · 2026-10-27）：侧栏固定块补「已固定」分区头（旧形状无头 5 行 → 新 6 行、插入带墨 742/784、选中揭示行号 +1；基线 238）；R428 跑失败步骤 2 个（runner 上找不到品红标记）⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动（产品 4 文件，侧栏分区位）

侧栏里固定条目以前与普通条目完全同形。新 `SidebarSectionPlan`（标题「已固定」、有固定条目才显示头、揭示行号 +1）+ `SidebarSectionHeader`（11pt semibold、secondaryLabelColor、左沿 22pt、`.isHeader`）+ `HistorySidebarView` 在固定块上方放一个 Section；`SelectedRowRevealer` 的行号走 plan 换算；无固定条目仍走原单个 ForEach。旧/新真读数：无头 12 带 / 有头 13 带，插入带墨 742（light）/ 784（dark）；真实 NSTableView 行数 6/5、选中 [2]/[1]。R428 run `40493617687 ↔ ab3e656` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是品红标记在 runner 亮暗两档都找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役，脚注/分区改用同帧墨带扫描（7/6、13/12），行数用真实表格；4 张 marker 帧撤、4 张分区帧增，基线 238/0/0/0，阈值未动。菜单 5/5 passed（真实 NSMenu）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 在 runner 日志 0 命中（只台账具名）。floor 5/5/77 无红；回执 2/2；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550；搜索 4 行；滚动 4/4。M1167–M1173 7/7；r29d 5/5；r61 M314 退役、M316 重钉；预检 204/186/540；HIDDEN 291/957 rot=0。全量 1160/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（TIME 18/9、52.5→1438；CHANNEL 0→81→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 136/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 4 张分区帧（亮/暗 正/负）与设置暗帧：「已固定」在固定块上方、整块下移一行、行内容不变；带扫描 13/12 与行数 6/5 同源。扣 2：没有真机窗口里固定块滚动的截图，1x 分区头只在离屏帧上验。 |
| 判据有效性 | 15/15 | 组件 plan 两条 + 视图源守卫 + 管线级三条（脚注带差、分区带差、真实表格行数与选中）+ r61 落点映射；M1167–M1173 7/7、r29d 5/5、r61 重钉后重跑。 |
| 假绿防御 | 15/15 | 静态帧显式清选区，避免选中行材料被盲区守卫读成黑带；负臂同名册对账；表格行数读真实 NSTableView；marker 退役不把无行读成绿；菜单具名 NOT-RUN 未发射照实写。 |
| 产品面推进 | 14/15 | 真落 Sources（侧栏新分区类别，像素可复核）；扣 1：分区头只有一行文字，未做折叠/计数（最小改动，视觉增量有限）。 |
| 台账一致性 | 15/15 | U-1568…U-1572、D-425、436 的 judged=5/5/executed=77、R428 的 0/2 与无行、R429 的 742/784、6/5、238 都从日志/帧/表格解析。 |
| 交付诚实性 | 15/15 | runner 上 marker 找不到照实写并退役仪器；`MENU_ITEM_SHORTCUT` 未发射照实写；源图标/拖拽/Dock/本地滚动各有具名 NOT-RUN。 |
| 可复核性 | 15/15 | 帧名、带区间与墨量、行数/选中、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账读数都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_425 = u"""## D-425 固定块分区头只加一行、行号偏移集中在一个纯函数；取证 marker 退役改同帧带扫描（R429）

- 背景：侧栏固定条目与普通条目同形；R428 的脚注品红标记在 runner 上亮暗两档都找不到（`SETTINGS_FOOTER` 无行），差集/标记两条路都不稳。
- 决定：① `SidebarSectionPlan` 承载「有固定条目才显示头」与 `displayRowIndex` 的 +1，`HistorySidebarView` 只留薄接线；`SelectedRowRevealer` 的行号必须经 plan。② 取证不再依赖颜色标记：脚注与分区头都用 `sidebarInkBands` 在同一帧里数墨带（7/6、13/12），行数用真实 `NSTableView`（6/5、选中 [2]/[1]）；静态分区帧显式清空选区。
- 理由：分区头只加一行、不拆分组，能保持列表选择/揭示/拖拽的既有语义；把偏移放在纯函数里才能用变异刀钉住。颜色标记依赖合成路径（runner vibrant 重映射），带扫描只依赖墨与几何，档位无关。
- 兼容性/迁移：无固定条目时仍是原来的单个 ForEach（老帧不变）；4 张 marker 帧删除、4 张分区帧新增，基线仍 238；`settings-general-no-footer`/`settings-min-no-footer` 继续作脚注负臂。
- 边界：固定块的揭示行号在真实滚动里的像素/偏移还没有独立验收（455）；分区头不做折叠/计数。
- 回滚：删 `SidebarSectionPlan.swift`、`SidebarSectionHeader.swift` 与 `HistorySidebarView` 的 Section 分支即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 侧栏固定块补「已固定」分区头（旧形状无头 5 行 → 新 6 行、插入带墨 742/784、选中揭示行号 +1；基线 238）；R428 跑失败步骤 2 个（runner 上找不到品红标记）⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动（R429 / 第 428 轮 / Round 426 / U-1568…U-1572 · 产品 4 文件，侧栏分区位）

"""

BACKLOG_SECTION = u"""437 追记（R429 · 仍开）：本轮补的是侧栏固定块的分区头；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R429 · 仍开）：R428 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→41→600、TIME 4/1/1330/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/9、52.5→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R429 · 仍开）：macOS 12 的详情头部阈值本轮未动；侧栏分区不涉及它。

452 追记（R429 · 仍开）：设置侧栏版本行仍是内容相对；本轮把它的像素尺从 marker 改成同帧带扫描（7/6、墨 1086/1284），布局未动。

453 追记（R429 · 仍开）：真实系统拖拽会话仍无自动化验收；本轮没动拖拽源。

454 追记（R429 · 仍开，且口径收紧）：R428 的 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu` 只写在台账里，R429 现读 runner 日志 **grep 0 命中** ⇒ 它既不是通道读数，也不进 Motion gate 的已登记标记表。下一轮要么在测试里显式打印它并登记通道，要么把这句从「具名通道」降级为账本观察，不许拿它当「已具名所以没问题」的证据。

**455. 固定块分区头把揭示行号 +1：真实滚动里的偏移只有源守卫与表格行数作证，缺一条像素/偏移验收**（R429 观察）
    现象：`SidebarSectionPlan.displayRowIndex` 在头部存在时 +1，`SelectedRowRevealer` 经它换算；本机 `testPinnedSectionHeaderAddsExactlyOneTableRow` 只证表格行数 6/5 与选中 [2]/[1]，`M1173` 只证源接线。选中一条固定条目后**滚动到位**的视口偏移没有独立判据（现有滚动三臂用的是无头夹具）。
    修法（下一轮若需要）：加一条带固定条目的 reveal 用例，在同一进程里读 `NSScrollView` 的 `contentView.bounds.origin` 与目标行 `rect(ofRow:)`，判落点贴边；或把现有 `SelectionRevealAnimationTests` 的夹具扩出一组固定条目，保持 reduce=true 的确定性路径。
"""

STATE_SECTION = u"""## R429 状态（2026-10-27 · 本地 · 第 428 轮 / Round 426）：侧栏固定块补「已固定」分区头（旧形状无头 5 行 → 新 6 行、插入带墨 742/784、选中揭示行号 +1；基线 238）；R428 跑失败步骤 2 个（runner 上找不到品红标记）⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动（产品 4 文件，侧栏分区位）

最后更新：2026-10-27（本地 · R429 / 第 428 轮 / Round 426）：侧栏里固定条目以前与普通条目同形。新 `SidebarSectionPlan`（`pinnedTitle=已固定`、`hasPinnedHeader = pinnedCount > 0`、`displayRowIndex` 头部存在时 +1）+ `SidebarSectionHeader`（11pt `VisualFont.meta` semibold、`secondaryLabelColor`、左沿 22pt、上下 4pt、`.isHeader`）+ `HistorySidebarView` 在固定块上方放一个 `Section`（无固定条目仍走原单个 `ForEach`，老帧不变）；`SelectedRowRevealer` 的行号经 plan 换算。真读数：无头 12 带 / 有头 13 带，插入带 #3 **158.0..168.0 墨=742**（light）/ **157.5..167.5 墨=784**（dark）；真实表格 **6 行 / 5 行**、选中 **[2]/[1]**。脚注 marker 退役：`settings-general` 7 带 vs 负臂 6 带，末带 **262.5..272.0 墨=1086** / **262.0..272.0 墨=1284**，负臂末带只是最后一行（928/703），640×440 同为 7/6、末带 1086/1284。R428 run `40493617687 ↔ ab3e656` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是品红标记在 runner 亮暗两档都找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役、改正/平带扫描 + 真实表格行数，阈值未动；4 张 marker 帧撤、4 张分区帧增，基线 **238/0/0/0**。菜单 `MenuShortcutPresentationTests` **5/5 passed**（真实 NSMenu 5 项两提示）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 在 runner 日志 **0 命中**（只台账具名，454 追记）。floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted；回执 **2/2**；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550、count 0.877/0.884；搜索 4 行；滚动 **4/4 passed**（`CHANNEL 0→41→600 变化 25200/6561 重抓=no`、`TIME 4/1/1330/1430`）。`M1167–M1173` **7/7 CAUGHT**（plan 2 / header 2 / wiring 3）；r29d **5/5**；r61 M314 退役、M316 重钉；预检 **204/186/540 bad=0**、ARM **297 文件 / 1023 把**、HIDDEN **291/957 rot=0**。本地全量 **1160/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=9/首=52.5/末=1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/204.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **136/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 428，现读 `python3 scripts/product_streak.py --streak-for 428`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R428 跑 failure、失败步骤 2 个：唯一红是品红标记在 runner 找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役；菜单 5/5 passed（真实 NSMenu）；floor 5/5 无红；回执 2/2；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550；搜索 4 行、滚动 4/4。
② 产品：侧栏固定块补「已固定」分区头（12→13 带、墨 742/784、表格 6/5、选中行号 +1）。
③ 判据：M1167–M1173 7/7；r29d 5/5；r61 M314 退役/M316 重钉；precheck 204/186/540；hidden rot 0。
④ 436：R428 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 291 / 可判 957 / rot 0。
⑥ 捕获 136/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1160/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；runner 日志 0 命中 ⇒ 只在台账具名）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑥ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑦ 设置侧栏版本行窗口下沿未成立（452）；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–455 仍开；⑬ R429 新跑待 push 后读。

下一轮（R430）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R429 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看脚注带扫描 7/6 与 1086/1284 在 runner 1x 上是否稳定、分区带 13/12 与表格 6/5 是否同读数、菜单 5 项/两提示是否仍绿、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R429_REPORT_BULLET = u"""- **R429（侧栏分区位）**：侧栏里固定条目以前与普通条目同形。新 `SidebarSectionPlan`（`pinnedTitle=已固定`、`hasPinnedHeader = pinnedCount > 0`、`displayRowIndex` 头部存在时 +1）+ `SidebarSectionHeader`（11pt semibold、secondaryLabelColor、左沿 22pt、`.isHeader`）+ `HistorySidebarView` 在固定块上方放一个 `Section`（无固定条目仍走原单个 `ForEach`）；`SelectedRowRevealer` 行号经 plan 换算。真读数：无头 12 带 / 有头 13 带，插入带墨 **742/784**；真实 NSTableView **6/5 行**、选中 **[2]/[1]**；脚注 7/6 带、末带 **1086/1284**，负臂末带 928/703（640×440 同 7/6、1086/1284）。R428 run `40493617687 ↔ ab3e656` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是品红标记在 runner 亮暗两档都找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动；4 张 marker 帧撤、4 张分区帧增，基线 **238/0/0/0**。菜单 `MenuShortcutPresentationTests` **5/5 passed**（真实 NSMenu 5 项两提示）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 在 runner 日志 **0 命中**（只台账具名，454 追记）。floor judged=5/5 executed=77 无红；回执 **2/2**；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550；搜索 4 行；滚动 4/4（`CHANNEL 0→41→600 变化 25200/6561`、`TIME 4/1/1330/1430`）。M1167–M1173 **7/7**；r29d 5/5；r61 M314 退役/M316 重钉；预检 204/186/540 bad=0；HIDDEN 291/957 rot=0。本地全量 **1160/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/9、52.5→1438；CHANNEL 0→81→600、18453/100800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 136/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 428 轮（R429" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R429 节")
if u"## Round 426 · R429" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 426")
if u"## D-425" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-425")
if u"侧栏固定块补「已固定」分区头" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**455." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 455")
if state.count(u"## R428 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R428 状态"))
U_CELL_OLD = u"U-31 … U-1567（R428 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R428 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R428 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_425 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R428 状态", STATE_SECTION + u"## R428 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1572（R429 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R428 节 ②",
                                u"AGENT_STATE.md` 的 R429 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R429_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R429_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
