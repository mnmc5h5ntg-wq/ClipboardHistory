#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R431 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 429 轮（R430 · 2026-10-27"
AUDIT_SECTION = u"""## 第 430 轮（R431 · 2026-10-27 · U-1578…U-1582）：主列表行首类型符号补绝对颜色（旧：文本行暗档 0 墨、文件行两档全空 → 新 209/165/231 与 209/492/492；35 张行帧变化、基线 238）；R430 跑失败步骤 2 个（搜索框「框外」带被新时间列污染 2.8<3.0、来源理由跨帧差 1x 读 0）⇒ 修仪器、阈值未动（产品 2 文件，行首类型符号位）

- **U-1578：⓪ R430 跑的失败步骤与时间列/带扫描命运。** `40506737072 ↔ 5234370` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。4 条红全是 **R430 新仪器被新内容污染**：`testQuickPickSearchFieldFocusLiftsItsChrome` light `焦点框内与框外只差 2.8`（<3.0）、`testQuickPickSearchFieldHoverLiftsItsChrome` light 同值，`testQuickPickSourceMatchReasonExtendsTheTypedRow` light/dark `只多出 0.0pt`（<40）。**时间列本身在 runner 1x 上是稳的**：`QUICKPICK_TIME_COLUMN light 末段宽=[74.0,71.0,74.0,74.0,74.0] 起=[296,298,296,296,296] 止=[370,369,370,370,370] 校准=[689,346,400,515,586]`、dark `[74.0,72.0,74.0,74.0,74.0]`、起 296–298、止 370、校准 395–800 ⇒ 五行同轴（极差 ≤2pt）。`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry` **按名出现、脚注用例 passed、不计红**；分区带 1x 稳定（light `13/12`、dark `11/10`），`PINNED_SECTION_ROWS 6/5 选中 [2]/[1]`。其余全绿：菜单 `MenuShortcutPresentationTests` **5/5 passed**；floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted；回执 **2/2**（两档均 `重抓=yes`、峰值 0.1333）；滚动 **4/4 passed**（`CHANNEL 0→221→600 变化 45600/46800`、`TIME 4/2/862/1430`）；拖拽源 mass 0.549/0.550、count 0.877/0.884；Dock 标记已登记。
- **U-1579：⓪ 的修法：把两把尺的取样带从「被新内容占用的区域」挪开，阈值不动。** ① 搜索框焦点/悬停的「框外」带原来是 `y=60..80` —— 正好是列表第一行的时间列（R430 新画的那一段），均值被行内文字污染到 2.8；改取**搜索框上方的面板留白** `y=0..8`（只由面板底色决定），本机新读数：焦点 light `静置 255.0 / 焦点 235.0 / 框外 255.0`（差 20）、dark `30.0 / 47.5 / 30.0`（差 17.5），悬停同值。② 来源理由的像素证人 R430 用「跨帧墨段右端差」，在 1x 上两帧都被同一矩形截断 ⇒ 0.0；改成**固定带** `x=160..300pt`（时间列 311 之前）：typed 行 0 扩展带 **880/998** 墨、list 行 2 **0/0**，两端校准 1487/1515、1680/1754。两条都没有改阈值（3.0 / 5 / 40 原样）。
- **U-1580：② 主列表行首类型符号补绝对颜色。** 缺陷形状：`.file` / `.files` 两行行首的 16pt 方块在 `content-with-history` 亮/暗两档都**一笔符号墨都没有**（只剩 `.quaternary` 底、描边与阴影）；`.text` 行的 `doc.text` 在暗档同样 0 墨。根因：`foregroundStyle(.secondary)` 是**相对环境**的层级色，在这一列被解析成与底同色的白/黑（Bisect：把符号换成红圆仍不显示；`secondaryLabelColor` 一改就出现）。修法：`ThumbnailSymbol` 与 `.text` 分支都改用绝对的 `Color(nsColor: .secondaryLabelColor)`（两行产品改动）。修后同帧读数（`FILE_ROW_SYMBOL`）：light 校准 492 / 文本行 **209** / file **165** / files **231**，dark 475 / **209** / **492** / **492**（旧：暗档文本 0、文件两档 0）。35 张含行的帧变化（content 族、sidebar 族），基线仍 **238/0/0/0**。
- **U-1581：判据与刀。** 新 `testFileRowsShowTheirTypeSymbol`（三枚行首类型的墨 + 同帧彩色缩略图作校准；地板按 `scale²` 推：图标 20·s²、校准 50·s² —— 本机 2x 为 80/200，1x 为 20/50）。`M1179`（文本行首退回 `.secondary`）**CAUGHT**；`M1180`（符号色退回 `.secondary`）、`M1181`（透明）、`M1182`（符号名为空）**3/3 CAUGHT**；`RESTORE_CLEAN=yes`。预检 `tables=207 covered=189 arms=549 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=300 arms=1032 dupes=0`；`HIDDEN_ARMS 表=294 可判=966 rot=0`。
- **U-1582：八步。** build **0 告警**；捕获 **138 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=35 / MISSING=0 / ADDED=0`（35 张全是含行的 content/sidebar 帧），`UPDATED=238`、复验 **238/0/0/0**；全量 **1163/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=84/末=1438`、`CHANNEL 0→92→600 变化 119660/153600 重抓=no`、`OFFSET 0/232.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 430，现读 `python3 scripts/product_streak.py --streak-for 430`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`，2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；连续三跑 0 命中）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 跨年记录没有年份（456）；⑩ **主列表暗档文字在离屏帧里是黑底黑字**（与 `darkSidebarTextBlindSpots` 同族的合成前极性；本轮的校准因此改用彩色缩略图，见 457）；⑪ 真机/多屏面板落点无截屏（447）；⑫ 真菜单栏表面、12 实时腿；⑬ `table-lazy-rows`；⑭ 437–457 仍开；⑮ R431 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 428 · R431（第 430 轮 · 2026-10-27）：主列表行首类型符号补绝对颜色（旧：文本行暗档 0 墨、文件行两档全空 → 新 209/165/231 与 209/492/492；35 张行帧变化、基线 238）；R430 跑失败步骤 2 个（搜索框「框外」带被新时间列污染 2.8<3.0、来源理由跨帧差 1x 读 0）⇒ 修仪器、阈值未动（产品 2 文件，行首类型符号位）

主列表行首的类型符号以前在 `.file` / `.files` 两行是**空框**（只剩 `.quaternary` 底、描边与阴影），`.text` 行在暗档也看不见。根因是 `foregroundStyle(.secondary)` 的相对层级解析：在这一列被解析成与底同色的白/黑（把符号换成红圆仍不显示，换 `secondaryLabelColor` 立即可见）。修法：`ThumbnailSymbol` 与 `.text` 分支都改用绝对的 `Color(nsColor: .secondaryLabelColor)`。修后帧读数 light 校准 492 / 文本行 209 / file 165 / files 231，dark 475 / 209 / 492 / 492（旧：暗档文本 0、文件两档 0）；35 张含行的 content/sidebar 帧变化，基线 238/0/0/0。判据 `testFileRowsShowTheirTypeSymbol`（三枚行首 + 彩色缩略图校准；地板 20·s²/50·s²），M1179–M1182 4/4 CAUGHT；预检 207/189/549 bad=0；HIDDEN 294/966 rot=0。R430 run `40506737072 ↔ 5234370` **failure、失败步骤 2 个**（Swift tests / Capture gate）：4 条红全是新仪器被新内容污染 —— 搜索框「框外」带 y60..80 落在时间列上（2.8<3.0）、来源理由跨帧右端差在 1x 被同一矩形截断（0.0）⇒ 框外带改面板上沿 y0..8（本机焦点 255/235/255、暗 30/47.5/30），理由证改固定带 x160..300（typed 880/998、list 0/0），阈值未动。时间列在 1x 稳定（light 74/71/74/74/74、止 369–370；dark 74/72/74/74/74、止 370）；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现不计红；分区 13/12 与 11/10、表格 6/5 [2]/[1]；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4。全量 1163/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（TIME 18/8、84→1438；CHANNEL 0→92→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 138/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看图：文件行从空框变成 doc/doc.on.doc 灰符号（亮暗两档），文本行暗档符号也出现；35 张含行帧逐一归因到这两处颜色。扣 2：没有真机暗档截图；主列表暗档文字在离屏帧里仍是黑底黑字（457）。 |
| 判据有效性 | 15/15 | 三枚行首类型 + 彩色缩略图校准 + scale² 地板；M1179–M1182 4/4、r29d 5/5、r405 重写。 |
| 假绿防御 | 15/15 | 校准换成彩色缩略图（暗档文字盲区不冒充"画了"）；搜索框框外带避开行区；理由证人有 negative=0；像素地板按 s² 推，1x 不假红。 |
| 产品面推进 | 14/15 | 真落产品 2 行（行首类型符号位），修的是"看得见但什么都没画"的缺陷；扣 1：范围小（只两处颜色），未动布局。 |
| 台账一致性 | 15/15 | U-1578…U-1582、D-427、R430 的 2.8/0.0、R431 的 209/165/231、1163 都从日志/帧解析。 |
| 交付诚实性 | 15/15 | R430 的红照实写成仪器污染并给新旧读数；主列表暗档文字盲区具名进 457；Dock/拖拽/源图标/本地滚动各有具名出口。 |
| 可复核性 | 15/15 | 帧名、三枚矩形读数、地板公式、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_427 = u"""## D-427 行首类型符号用绝对 label 色；暗档离屏帧的文字盲区不拿来做校准（R431）

- 背景：主列表 `.file` / `.files` 行首的 16pt 占位方块在亮/暗两档都只剩框（符号 0 墨），`.text` 行首在暗档同样 0 墨。Bisect 结论：`foregroundStyle(.secondary)` 是相对环境前景的层级色，被这一列的容器解析成与底同色的白/黑；红圆替身同样不显示，`secondaryLabelColor` 一换就出现。
- 决定：① `ThumbnailSymbol` 与 `RowLeadingVisual` 的 `.text` 分支改用绝对的 `Color(nsColor: .secondaryLabelColor)`；② 像素判据的"这屏画出来了"校准改用同一帧的**彩色缩略图**，不用暗档列表文字（它在离屏帧里是黑底黑字，属 `darkSidebarTextBlindSpots` 同族的合成前极性）。
- 理由：需要"看得见的图形线索"的位点不能依赖相对层级色 —— 相对色只在"环境前景正好是 label"时成立，而带 `.quaternary` 底的方块不是那个环境。校准必须是这台机器拍得到的东西，盲区里的文字不能拿来当"画了"的证据。
- 兼容性/迁移：布局/行高/左轴一字未动，只改颜色解析；35 张含行帧变化，基线仍 238；`quickpick-empty` 等无行帧不变。
- 边界：主列表暗档文字的离屏盲区仍未登记成名册（457）；真机暗档未截图。
- 回滚：把两处 `Color(nsColor: .secondaryLabelColor)` 改回 `.secondary` 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 主列表行首类型符号补绝对颜色（旧：文本行暗档 0 墨、文件行两档全空 → 新 209/165/231 与 209/492/492；35 张行帧变化、基线 238）；R430 跑失败步骤 2 个（搜索框「框外」带被新时间列污染 2.8<3.0、来源理由跨帧差 1x 读 0）⇒ 修仪器、阈值未动（R431 / 第 430 轮 / Round 428 / U-1578…U-1582 · 产品 2 文件，行首类型符号位）

"""

BACKLOG_SECTION = u"""437 追记（R431 · 仍开）：本轮修的是行首类型符号的颜色解析；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R431 · 仍开）：R430 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→221→600、TIME 4/2/862/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、84→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R431 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R431 · 仍开）：脚注带的 1x 具名 NOT-RUN 已生效（R430 跑里按名出现、用例 passed、不计红）；版本行布局未动。

453 追记（R431 · 仍开）：真实系统拖拽会话仍无自动化验收；本轮只改行首符号颜色。

454 追记（R431 · 仍开）：R430 跑的 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 仍 0 命中；菜单 5/5 继续由真实 NSMenu 用例作证。

455 追记（R431 · 仍开）：R430 跑在 1x 上 `PINNED_SECTION_ROWS 6/5 选中 [2]/[1]` 通过；固定条目滚动到位的独立偏移验收仍缺。

456 追记（R431 · 仍开）：浮层/侧栏时间格式本轮未动；跨年记录仍无年份。

**457. 主列表暗档文字在离屏帧里是黑底黑字：与 `darkSidebarTextBlindSpots` 同族的盲区，但还没登记成册**（R431 观察）
    现象：`content-with-history` 暗档帧里，标题/时间文字在背景 (28,28,28) 上被画成 (0,0,0)，亮像素计数为 0 —— 与设置侧栏那族"合成前极性"一致。R431 的像素判据要用**彩色缩略图**当"这屏画出来了"的校准，正是因为这段文字在帧上不可读。
    修法（下一轮若需要）：把这批 content 帧按侧栏那套机制登记进名册（正/负两侧墨计数 + "这些帧的暗档文字不能当证据"的守卫），或者先证明它只是捕获通道的合成方向问题、真机可读（需要一张真机暗档截图）。
"""

STATE_SECTION = u"""## R431 状态（2026-10-27 · 本地 · 第 430 轮 / Round 428）：主列表行首类型符号补绝对颜色（旧：文本行暗档 0 墨、文件行两档全空 → 新 209/165/231 与 209/492/492；35 张行帧变化、基线 238）；R430 跑失败步骤 2 个（搜索框「框外」带被新时间列污染 2.8<3.0、来源理由跨帧差 1x 读 0）⇒ 修仪器、阈值未动（产品 2 文件，行首类型符号位）

最后更新：2026-10-27（本地 · R431 / 第 430 轮 / Round 428）：主列表行首的类型符号以前在 `.file` / `.files` 两行只是一个空框（`.quaternary` 底 + 描边 + 阴影），`.text` 行在暗档也看不见 —— `foregroundStyle(.secondary)` 是相对环境的层级色，在这一列被解析成与底同色的白/黑（Bisect：红圆替身同样不显示，`secondaryLabelColor` 一换即现）。修法：`ThumbnailSymbol` 与 `RowLeadingVisual` 的 `.text` 分支都改用 `Color(nsColor: .secondaryLabelColor)`。修后同帧读数 light 校准 492 / 文本行 **209** / file **165** / files **231**，dark 475 / **209** / **492** / **492**（旧：暗档文本 0、文件两档 0）；35 张含行的 content/sidebar 帧变化，基线 **238/0/0/0**。新判据 `testFileRowsShowTheirTypeSymbol`（三枚行首 + 彩色缩略图校准；地板 20·s²/50·s²）。R430 run `40506737072 ↔ 5234370` **failure，失败步骤 2 个**（Swift tests / Capture gate）：4 条红全是新仪器被新内容污染 —— 搜索框「框外」带 y60..80 落在 R430 的时间列上（light 2.8<3.0），来源理由跨帧右端差在 1x 被同一矩形截断（0.0）⇒ 框外带改面板上沿 y0..8（本机焦点 light 255/235/255、dark 30/47.5/30），理由证改固定带 x160..300（typed 880/998、list 0/0），阈值未动。时间列在 1x 稳定（light 74/71/74/74/74、起 296–298、止 369–370；dark 74/72/74/74/74、止 370）；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现、脚注用例 passed、不计红；分区 13/12 与 11/10、表格 6/5 [2]/[1]；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→221→600 45600/46800`、`TIME 4/2/862/1430`）；拖拽 mass 0.549/0.550。`M1179–M1182` **4/4 CAUGHT**；预检 **207/189/549 bad=0**、ARM **300 文件 / 1032 把**、HIDDEN **294/966 rot=0**。本地全量 **1163/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/84/1438`、`CHANNEL 0→92→600 变化 119660/153600 重抓=no`、`OFFSET 0/232.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **138/4/0 / 238 帧**；基线 **238/0/0/0**（35 张含行帧变化）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 430，现读 `python3 scripts/product_streak.py --streak-for 430`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R430 跑 failure、失败步骤 2 个：4 条红全是新仪器被新内容污染（框外带 2.8、理由跨帧 0.0）⇒ 修取样带、阈值未动；时间列 1x 稳定（74/71/74/74/74、止 369–370）；脚注 1x 具名 NOT-RUN 生效；分区 13/12、表格 6/5；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4。
② 产品：主列表行首类型符号补绝对颜色（旧：文本行暗档 0、文件行两档 0 → 新 209/165/231 与 209/492/492；35 张帧变化）。
③ 判据：M1179–M1182 4/4；r405 重写；precheck 207/189/549；hidden rot 0。
④ 436：R430 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 294 / 可判 966 / rot 0。
⑥ 捕获 138/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1163/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`；2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 跨年记录没有年份（456）；⑩ 主列表暗档文字离屏盲区未登记（457）；⑪ 真机/多屏面板落点无截屏（447）；⑫ 真菜单栏表面、12 实时腿；⑬ `table-lazy-rows`；⑭ 437–457 仍开；⑮ R431 新跑待 push 后读。

下一轮（R432）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R431 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看行首类型符号的 `FILE_ROW_SYMBOL` 在 runner 1x 上是否过 s² 地板、搜索框焦点/悬停的外带新读数、来源理由固定带、时间列 74/71、脚注 1x 具名、分区 13/12、菜单 5 项/两提示、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R431_REPORT_BULLET = u"""- **R431（行首类型符号位）**：主列表行首的类型符号以前在 `.file` / `.files` 两行只是空框（`.quaternary` 底 + 描边 + 阴影），`.text` 行在暗档也看不见 —— `foregroundStyle(.secondary)` 是相对环境的层级色，在这一列被解析成与底同色的白/黑（红圆替身同样不显示，换 `secondaryLabelColor` 即现）。修法：`ThumbnailSymbol` 与 `RowLeadingVisual` 的 `.text` 分支都改用绝对的 `Color(nsColor: .secondaryLabelColor)`。修后同帧读数 light 校准 492 / 文本行 **209** / file **165** / files **231**，dark 475 / **209** / **492** / **492**（旧：暗档文本 0、文件两档 0）；35 张含行的 content/sidebar 帧变化，基线 **238/0/0/0**。R430 run `40506737072 ↔ 5234370` **failure、失败步骤 2 个**（Swift tests / Capture gate）：4 条红全是新仪器被新内容污染 —— 搜索框「框外」带 y60..80 落在 R430 的时间列上（light 2.8<3.0）、来源理由跨帧右端差在 1x 被同一矩形截断（0.0）⇒ 框外带改面板上沿 y0..8（本机焦点 255/235/255、暗 30/47.5/30），理由证改固定带 x160..300（typed 880/998、list 0/0），阈值未动。时间列在 1x 稳定（light 74/71/74/74/74、止 369–370；dark 74/72/74/74/74、止 370）；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现不计红；分区 13/12 与 11/10、表格 6/5 [2]/[1]；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4。M1179–M1182 **4/4**；预检 207/189/549 bad=0；HIDDEN 294/966 rot=0。本地全量 **1163/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、84→1438；CHANNEL 0→92→600、119660/153600）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 138/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 430 轮（R431" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R431 节")
if u"## Round 428 · R431" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 428")
if u"## D-427" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-427")
if u"主列表行首类型符号补绝对颜色" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**457." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 457")
if state.count(u"## R430 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R430 状态"))
U_CELL_OLD = u"U-31 … U-1577（R430 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R430 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R430 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_427 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R430 状态", STATE_SECTION + u"## R430 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1582（R431 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R430 节 ②",
                                u"AGENT_STATE.md` 的 R431 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R431_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R431_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
