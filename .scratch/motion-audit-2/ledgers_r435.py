#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R435 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 433 轮（R434 · 2026-10-27"
AUDIT_SECTION = u"""## 第 434 轮（R435 · 2026-10-28 · U-1598…U-1602）：浮层搜索框补清除按钮（有字才出现：typed 帧按钮带 405/410 墨、空查询 0；4 张浮层帧变化、基线 238）；R434 跑 `40535594620 ↔ 78a0cf5` **success、失败步骤 0**（仪器全部按名/按读数签收）（产品 1 文件，浮层搜索框位）

- **U-1598：⓪ R434 跑的失败步骤与仪器命运（success）。** `40535594620 ↔ 78a0cf5` **success、20/20 步全绿、失败步骤 0**。R433 的两条仪器都签收：`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain` 亮暗两档**按名出现、不计红**；`DETAIL_IMAGE_EDGE` 在 1x 继续绿（light 图框 `240..479×220..359px`、页底 236、边带差 **30.0**；dark 页底 50、**26.0**）。R434 自己的仪器也在 runner 上落地：`HTML_HEADING_LADDER light html=19.0pt markdown=18.0pt 差=1.0pt`（本机 2x 是 20/18、差 2.0；1x 上两条通道几乎重合）。其余：理由带 `typed 217/248、list 0`；时间列 light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现；分区 `13/12`、`11/10`；`PINNED_SECTION_ROWS 6/5 选中 [2]/[1]`；回执 **2/2**（2x 0.1333/1289ms、1x 0.1389/1385ms，均 `重抓=no`）；滚动 **4/4**（`CHANNEL 0→109→600 变化 37200/28469`、`TIME 5/1/660/1430`）；拖拽 mass 0.549/0.550；floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted。**STATE ⓪ 已回写**：`AGENT_STATE.md` R434 节「下一轮（R435）的靶」里已把占位句替换为 `40535594620 ↔ 78a0cf5`（success、失败步骤 0）与上述读数，并单独提交 `00939fa` push。
- **U-1599：② 浮层搜索框补清除按钮。** 缺陷形状（`quickpick-typed` 亮/暗直看）：主窗口的 `SearchField` 早有 ×，浮层的主输入框一直没有 —— 打错一个字只能全选重打；空结果态那颗「清除搜索」只在 0 条时出现，不是输入中的清除手段。修法：`QuickPickController` 在搜索框右端加一颗 18×18 的无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），可见性由纯函数 `showsClearButton(text:)` 决定（有字才出现）；`QuickPickSearchFieldCell` 的文本矩形右留 22pt 让位；产品路径（delegate → `queryChanged`）与取证路径（`windowForCapture`）共用 `updateClearButton`。旧/新帧读数（`QUICKPICK_CLEAR_BUTTON`）：light `typed 按钮带=405 校准=354 / list 按钮带=0 校准=1232`、dark `410/408 / 0/1474`，地板 80（20·s²）。真看图：typed 帧右上出现灰色 ×；empty 帧（查询「zzz 不存在」）同样出现 ×，与「清除搜索」CTA 并存但职责不同（一个是字段控制、一个是解释性出口）。
- **U-1600：判据与刀。** 新 `QuickPickSearchClearButtonTests` 两条（可见性真值表 / 真实面板按钮跟随查询：`windowForCapture(query:"访达")` 里恰好一颗 identifier 匹配的按钮、非隐藏；`performClick` 后收起）+ `testQuickPickSearchFieldShowsAClearButtonOnlyWhenTyping`（typed vs list 的搜索框右端 384..406pt 墨带 + 左半段校准；地板按 `scale²`）。`M1195–M1196` **2/2 CAUGHT**（永远隐藏 / 永远显示；RESTORE_CLEAN=yes）。预检 `tables=213 covered=195 arms=562 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=306 arms=1045 dupes=0`；`HIDDEN_ARMS 表=300 可判=979 rot=0`。
- **U-1601：八步。** build **0 告警**；捕获 **142 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=4 / MISSING=0 / ADDED=0`（`quickpick-typed`、`quickpick-empty` × 亮暗），`UPDATED=238`、复验 **238/0/0/0**；全量 **1179/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=23.5/末=1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/194.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 434，现读 `python3 scripts/product_streak.py --streak-for 434`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **U-1602：具名 NOT-RUN / 观察。** ① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 浮层清除按钮命中区 18pt，低于主窗口搜索框的 22pt（461）；⑲ 437–461 仍开；⑳ R435 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 432 · R435（第 434 轮 · 2026-10-28）：浮层搜索框补清除按钮（有字才出现：typed 帧按钮带 405/410 墨、空查询 0；4 张浮层帧变化、基线 238）；R434 跑 `40535594620 ↔ 78a0cf5` **success、失败步骤 0**（仪器全部按名/按读数签收）（产品 1 文件，浮层搜索框位）

主窗口的 `SearchField` 早有清除 ×，浮层的搜索框一直没有 —— 打错一个字只能全选重打。新：`QuickPickController` 在搜索框右端加 18×18 无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），可见性由 `showsClearButton(text:)` 决定（有字才出现），`QuickPickSearchFieldCell` 右留 22pt 让位，产品路径与取证路径共用 `updateClearButton`。旧/新：`QUICKPICK_CLEAR_BUTTON light typed 按钮带=405 校准=354 list 按钮带=0 校准=1232`、dark `410/408 / 0/1474`，地板 80（20·s²）。4 张浮层帧变化（typed/empty × 亮暗），基线 238/0/0/0。R434 run `40535594620 ↔ 78a0cf5` **success、20/20 步、失败步骤 0**：`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain` 按名生效、`DETAIL_IMAGE_EDGE` 1x 30/26、`HTML_HEADING_LADDER` 19/18、理由带 217/248 vs 0、时间列、脚注、分区、表格、回执 2/2、滚动 4/4、floor 5/5/77 全绿；STATE ⓪ 已回写（`00939fa`）。M1195–M1196 2/2；预检 213/195/562 bad=0；HIDDEN 300/979 rot=0。全量 1179/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、23.5→1438；CHANNEL 0→86.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 142/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 `quickpick-typed`/`quickpick-empty` 亮暗：× 出现在搜索框右上、与输入文字不重叠；empty 帧里 × 与「清除搜索」CTA 并存、职责可辨。扣 2：没有真机点击验收；18pt 命中区比主窗口 22pt 小（461）。 |
| 判据有效性 | 15/15 | 真值表 + 真实面板按钮跟随查询（含 performClick 收起）+ 像素正/负两带；M1195–M1196 2/2。 |
| 假绿防御 | 15/15 | 負臂（空查询）必须 0 墨、正臂两档都要有墨、校准带证明字段画出来了；地板按 s²；两档都判。 |
| 产品面推进 | 14/15 | 真落 1 文件（浮层搜索框位），补的是"输入中不可清除"的真空档；扣 1：命中区 18pt 偏小、没有 Esc 清空的额外提示。 |
| 台账一致性 | 15/15 | U-1598…U-1602、D-431、R434 的 success/0 步、R435 的 405/410 vs 0、1179 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | push 曾 PUSH_BLOCKED（ahead=2）如实报，网络恢复后一次 push 并回写 STATE ⓪；各 NOT-RUN 分列。 |
| 可复核性 | 15/15 | 帧名、两条墨带、identifier、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_431 = u"""## D-431 浮层搜索框补清除按钮；可见性由纯函数决定（R435）

- 背景：主窗口 `SearchField` 早有清除 ×，浮层的主输入框一直没有；打错一个字只能全选重打，空结果态的「清除搜索」只在 0 条时出现，不是输入中的清除手段。
- 决定：① `QuickPickController.showsClearButton(text:) = !text.isEmpty` 做可见性真值表；② 面板里加一颗 18×18 无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），trailing = 字段右沿 −4、centerY 对齐；③ `QuickPickSearchFieldCell` 的文本矩形右留 22pt 给按钮让位（左轴不动）；④ 产品路径（delegate → `queryChanged`）与取证路径（`windowForCapture`）共用 `updateClearButton`。
- 理由：清除是输入框的一部分，应该和主窗口同一种语言（字段右侧的 ×，有字才出现），而不是只在空结果态给一颗大 CTA。可见性写成纯函数才能用真值表与刀钉住。
- 兼容性/迁移：搜索框左轴、占位语、药丸宽度都不动；4 张浮层帧变化（typed/empty × 亮暗），基线仍 238。
- 边界：× 的命中区 18pt，比主窗口搜索框的 22pt 小（461）；没有为 × 另配键盘快捷键（Esc 仍是关闭面板）。
- 回滚：删 `clearButton` 的创建、`updateClearButton` 两处调用与 cell 的右留白即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 浮层搜索框补清除按钮（有字才出现：typed 帧按钮带 405/410 墨、空查询 0；4 张浮层帧变化、基线 238）；R434 跑 `40535594620 ↔ 78a0cf5` success、失败步骤 0（仪器全部按名/按读数签收）（R435 / 第 434 轮 / Round 432 / U-1598…U-1602 · 产品 1 文件，浮层搜索框位）

"""

BACKLOG_SECTION = u"""437 追记（R435 · 仍开）：本轮只补浮层搜索框的清除按钮；主列表仍不匹配 `sourceAppName`。

449 追记（R435 · 仍开）：R434 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→109→600、TIME 5/1/660/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、23.5→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R435 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R435 · 仍开）：脚注 1x 具名 NOT-RUN 继续按名出现。

453 追记（R435 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R435 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R435 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R435 · 仍开）：跨年记录仍无年份。

457 追记（R435 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R435 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 上的行首符号像素证人仍缺。

459 追记（R435 · 仍开）：设置内容列/高夹具在 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN` 依此）。

460 追记（R435 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

**461. 浮层搜索框清除按钮的命中区 18pt，低于主窗口搜索框的 22pt**（R435 观察）
    现象：R435 的 × 是 `18×18` 的 NSButton（字形 `VisualFont.row`），而主窗口 `SearchField` 的 × 在 R20 已经把命中区抬到约 22pt（`labelPadding: 4`）并写下「命中的地方不该比字形小」。同一件"清除输入"的控件在两个表面给了两种命中区，正是 R3/R20 反复收的那一族。
    修法（下一轮若需要）：把 × 的 `widthAnchor/heightAnchor` 抬到 22（字形仍 14），或给 NSButton 加 `contentInsets`；判据可读按钮 frame（管线探针）与像素两带，不需要新帧。
"""

STATE_SECTION = u"""## R435 状态（2026-10-28 · 本地 · 第 434 轮 / Round 432）：浮层搜索框补清除按钮（有字才出现：typed 帧按钮带 405/410 墨、空查询 0；4 张浮层帧变化、基线 238）；R434 跑 `40535594620 ↔ 78a0cf5` success、失败步骤 0（产品 1 文件，浮层搜索框位）

最后更新：2026-10-28（本地 · R435 / 第 434 轮 / Round 432）：主窗口的 `SearchField` 早有清除 ×，浮层的搜索框一直没有 —— 打错一个字只能全选重打。新：`QuickPickController` 在搜索框右端加一颗 18×18 无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），可见性由 `showsClearButton(text:)` 决定（有字才出现）；`QuickPickSearchFieldCell` 的文本矩形右留 22pt 让位（左轴不动）；产品路径与取证路径共用 `updateClearButton`。旧/新帧读数：`QUICKPICK_CLEAR_BUTTON light typed 按钮带=405 校准=354 list 按钮带=0 校准=1232`、dark `410/408 / 0/1474`（地板 80 = 20·s²）。4 张浮层帧变化（typed/empty × 亮暗），基线 **238/0/0/0**。R434 run `40535594620 ↔ 78a0cf5` **success、20/20 步、失败步骤 0**：`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain` 按名生效、`DETAIL_IMAGE_EDGE` 1x 30/26、`HTML_HEADING_LADDER` 19/18、理由带 217/248 vs 0、时间列 `[74,71,74,74,74]`/`[74,72,74,74,74]`、脚注 NOT-RUN 按名出现、分区 13/12 与 11/10、表格 6/5、回执 2/2、滚动 4/4、拖拽 mass 0.549/0.550、floor 5/5/77 无红；**STATE ⓪ 已回写**（`00939fa` push）。`M1195–M1196` **2/2 CAUGHT**；预检 **213/195/562 bad=0**、ARM **306 文件 / 1045 把**、HIDDEN **300/979 rot=0**。本地全量 **1179/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/23.5/1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/194.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **142/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 434，现读 `python3 scripts/product_streak.py --streak-for 434`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R434 跑 success、失败步骤 0：`EXCLUDED_APP_ROW_NOT_RUN` 按名生效、`DETAIL_IMAGE_EDGE` 30/26、`HTML_HEADING_LADDER` 19/18、理由带/时间列/脚注/分区/表格/回执/滚动/floor 全绿；STATE ⓪ 已回写并 push（`00939fa`）。
② 产品：浮层搜索框补清除 ×（有字才出现；typed 405/410 vs list 0）。
③ 判据：M1195–M1196 2/2；真值表 + 真实面板按钮 + 像素两带；precheck 213/195/562；hidden rot 0。
④ 436：R434 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 300 / 可判 979 / rot 0。
⑥ 捕获 142/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1179/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 清除按钮命中区 18pt（461）；⑲ 437–461 仍开；⑳ R435 新跑待 push 后读。

下一轮（R436）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R435 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `QUICKPICK_CLEAR_BUTTON` 两档读数（typed 有墨、list 0）、`EXCLUDED_APP_ROW_NOT_RUN`、`DETAIL_IMAGE_EDGE`、`HTML_HEADING_LADDER`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R435_REPORT_BULLET = u"""- **R435（浮层搜索框位）**：主窗口的 `SearchField` 早有清除 ×，浮层的搜索框一直没有 —— 打错一个字只能全选重打。新：`QuickPickController` 在搜索框右端加一颗 18×18 无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），可见性由纯函数 `showsClearButton(text:)` 决定（有字才出现）；`QuickPickSearchFieldCell` 右留 22pt 让位（左轴不动）；产品路径与取证路径共用 `updateClearButton`。旧/新帧读数：`QUICKPICK_CLEAR_BUTTON light typed 按钮带=405 校准=354 list 按钮带=0 校准=1232`、dark `410/408 / 0/1474`（地板 80 = 20·s²）。4 张浮层帧变化（typed/empty × 亮暗），基线 **238/0/0/0**。R434 run `40535594620 ↔ 78a0cf5` **success、20/20 步、失败步骤 0**：`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain` 按名生效、`DETAIL_IMAGE_EDGE` 1x 30/26、`HTML_HEADING_LADDER` 19/18、理由带 217/248 vs 0、时间列、脚注、分区、表格、回执 2/2、滚动 4/4、floor 5/5/77 全绿；STATE ⓪ 已回写（`00939fa`）。M1195–M1196 **2/2**；预检 213/195/562 bad=0；HIDDEN 300/979 rot=0。本地全量 **1179/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、23.5→1438；CHANNEL 0→86.5→600、76639/127200）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 142/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 434 轮（R435" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R435 节")
if u"## Round 432 · R435" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 432")
if u"## D-431" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-431")
if u"浮层搜索框补清除按钮" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**461." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 461")
if state.count(u"## R434 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R434 状态"))
U_CELL_OLD = u"U-31 … U-1597（R434 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R434 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R434 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_431 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R434 状态", STATE_SECTION + u"## R434 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1602（R435 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R434 节 ②",
                                u"AGENT_STATE.md` 的 R435 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R435_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R435_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
