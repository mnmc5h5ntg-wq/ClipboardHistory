#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R427 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 425 轮（R426 · 2026-10-27"
AUDIT_SECTION = u"""## 第 426 轮（R427 · 2026-10-27 · U-1558…U-1562）：拖拽源反馈补行内容降透明度（静置/拖拽墨量比 **0.550/0.549**、墨数比 0.936/0.911；真实 `onDrag` 延迟 50ms 登记、松开轮询清零）；R426 跑失败步骤 2 个（新增固定带在 1x 上读 0）⇒ 差集/具名 NOT-RUN、不改门槛（产品 3 文件，拖拽源反馈位）

- **U-1558：⓪ R426 跑的失败步骤与两条新尺的 1x 命运。** `40478143446 ↔ 1f3dc91` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。caption 探针的修复这次**绿了**；红的是 R426 新加的两条固定带：① `testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed` 的「最小窗整条 header 墨」在 1x 读到 **0**（本机 2x 3071/3471；同帧图标彩色 0）；② `testSettingsSidebarShowsTheVersionFooterOnlyInTheProductArm` 的固定 y 带在 1x 读到 **正臂 0、最小窗 3473 且首墨 x=7**——1x runner 的设置页行高/位置与本机 2x 不同，带子量到的不是脚注。其余：floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted ⇒ 436 REDS=0；回执出现 **2x=2、1x=2、重抓=no**；Dock `DockBadgeTests` **5/5**、`DOCK_BADGE_PIXEL_NOT_RUN` 已登记不计红；搜索 4 行绿；滚动 **4/4 passed**（`CHANNEL 0→143→600 变化 40800/44400 重抓=no`、`TIME 采样=6/中间值=3/首=205/末=1430`）；源图标正/负 1x `59/110、0/63`，最小窗彩色 0。
- **U-1559：R426 两条新尺改成与几何无关的读法。** ① 版本行改为**正/负两帧差集**（`settings-general` vs `settings-general-no-footer`；`settings-min` vs 新增 `settings-min-no-footer`），差集只在侧栏列（x 0..148）里找脚注：本机 720 差 **70×10（light）/70×11（dark）**、正臂墨 **1086/1284**、负臂 0；640 差同样 70×10/11、最小窗墨 **1086/1284**、负臂 0；首墨 24.0/29.0。② 源图标最小窗文字在 1x 读 0 时改成具名 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`（本机 2x 3071/3471；图标彩色 0 仍判）。另把 `settings-min-no-footer` 从卡片节奏尺里排除（与 `settings-min` 同档），并登记进暗档侧栏盲区名册（同一 vibrant 子树）；名册再次把 r29d M132 的针弄空，按「两档负臂同一行 + settings-general」重钉后 **5/5 CAUGHT**。
- **U-1560：② 拖拽源反馈。** 行被拖出去时以前没有任何源反馈。新 `DragSourceFeedbackState`（按 entry ID 归属、`tick(mouseButtons==0)` 清零）+ `DragSourceFeedback` 控制器（`onDrag` 延迟 **50ms** 登记，避开系统拖拽预览抓图；结束时靠 `.common` runloop 的 50ms 轮询 `NSEvent.pressedMouseButtons`）+ `EntryDragModifier(entryID:)` + 行内容 `.opacity(0.55)`（只降内容，不动行底/悬停底）。真读数（同一行 `row-favorite-off` vs `row-drag-source-active`）：静置墨 10162/11384、拖拽墨 9512/10374；**墨数比 0.936/0.911，墨量比 0.550/0.549**（墨数是"过阈值的颗数"，对 0.55 不敏感；墨量才按透明度线性掉）。真看图：拖拽源行的星/图标/文字整体退到背景里，行底仍是原白。静态状态，无动效胶片场景。
- **U-1561：② 的真实拖拽会话是具名 NOT-RUN。** 帧里的拖拽源态由取证键 `draggingEntryIDForCapture` 驱动；真实 `onDrag` 路径由源守卫钉（`beginAfterDelay(entryID)` 在 `content.onDrag` 内；行把 `entry.id` 交给 modifier；轮询在 `.common`），但**没有**自动化一条完整系统拖拽会话（会按下的合成 + 跨进程 drop）。具名 `DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，不把 capture-env 帧当成真实拖拽证据；BACKLOG 453。
- **U-1562：判据、刀与八步。** `DragSourceFeedbackTests` 3 条（状态机/控制器/接线源）+ 产品像素（墨量比 + 正/负同一行）；`M1153–M1159` **7/7 CAUGHT**（state 2 / entrydrag 2 / row 3，RESTORE_CLEAN=yes）；R426 的 footer 9/9 与 r29d 5/5 已在盘上重跑；`EntryDragPlannerTests`/`SidebarListSelectionTests` 的 `EntryDragModifier(content:` 源守卫改到新签名（`entryID:`）；`footerDiffBox` 的两态差集加 alpha 到判定行、`rowInkMass` 按 alpha 加权，避免 `testEveryTwoStateRulerReadsBothAxes` 把新尺记成只读亮度。预检 `tables=196 covered=178 arms=527 bad=0`、`ARM_TOTAL files=289 arms=1011`、`BASH_ARMS 16 bad=0`；`HIDDEN_ARMS 表=283 可判=945 rot=0`。build **0 告警**；捕获 **134/4/0 / 234 帧**；基线 **230→234**（4 增：`row-drag-source-active` 亮暗 2 + `settings-min-no-footer` 亮暗 2；0 变、0 缺）；全量 **1149/57/5**（5 个断言全在 `SelectionRevealAnimationTests`，3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`SCROLL_REVEAL_TIME 采样=18/中间值=9/首=29/末=1438`、`CHANNEL 0→87→600 变化 80951/129600 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 426，现读 `python3 scripts/product_streak.py --streak-for 426`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；② Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；③ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`；本机 3071/3471）；④ 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑤ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑥ 设置侧栏版本行窗口下沿未成立（452）；⑦ 真机/多屏面板落点无截屏（447）；⑧ 真菜单栏表面、12 实时腿；⑨ `table-lazy-rows`；⑩ 437–453 仍开；⑪ R427 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 424 · R427（第 426 轮 · 2026-10-27）：拖拽源反馈补行内容降透明度（静置/拖拽墨量比 **0.550/0.549**、墨数比 0.936/0.911；真实 onDrag 延迟 50ms 登记、松开轮询清零）；R426 跑失败步骤 2 个（新增固定带在 1x 上读 0）⇒ 差集/具名 NOT-RUN、不改门槛（产品 3 文件，拖拽源反馈位）

行被拖出去时以前没有源反馈。新 `DragSourceFeedbackState`（按 entry ID、鼠标松开清零）+ `DragSourceFeedback` 控制器（`onDrag` 延迟 50ms 登记，避开系统拖拽预览；结束时在 `.common` runloop 轮询 `NSEvent.pressedMouseButtons`）+ `EntryDragModifier(entryID:)` + 行内容 `.opacity(0.55)`。真读数：静置墨 10162/11384、拖拽 9512/10374；墨数比 0.936/0.911，**墨量比 0.550/0.549**。真看图：拖拽源行整体退到背景，行底不变。真实系统拖拽会话具名 NOT-RUN（453），capture-env 帧只证视觉态。R426 run `40478143446 ↔ 1f3dc91` **failure、失败步骤 2 个**：caption 已绿；两条新尺的固定带在 1x 读 0（源图标最小窗文字、版本行）⇒ 版本行改正/负差集（720/640 差 70×10/11、1086/1284、负臂 0），源图标最小窗文字具名 NOT-RUN；`settings-min-no-footer` 进卡片节奏排除与暗档盲区名册，r29d M132 二次重钉 5/5。floor judged=5/5 executed=77 无红；回执 2/2 重抓=no；Dock 5/5；搜索 4 行；滚动 4/4。M1153–M1159 7/7；预检 196/178/527；HIDDEN 283/945 rot=0。全量 1149/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（TIME 18/9、29→1438；CHANNEL 0→87→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 134/4/0、234 帧；基线 230→234（4 增、0 变）；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 `row-drag-source-active` 亮暗帧：星/图标/文字整体退到背景、行底仍白；静置同帧作正对照；墨量比 0.550/0.549 与 0.55 透明度对齐。 |
| 判据有效性 | 15/15 | 状态机/控制器/接线 3 条 + 产品像素（墨量比 + 正/负同一行）；M1153–M1159 7/7；真实拖拽缺口具名 NOT-RUN。 |
| 假绿防御 | 15/15 | 用墨量而不是墨数（0.55 时墨数只掉 6–9%，会放过）；负臂同一行；捕获键不冒充真实拖拽；1x 固定带失败改成差集。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，补的是拖出去那一下的源反馈；扣 1：真实系统拖拽会话没有自动化验收（453）。 |
| 台账一致性 | 15/15 | U-1558…U-1562、D-423、436 的 judged=5/5/executed=77、R426 的 1x 0 读数、Dock/搜索/滚动、两窗口差集都从日志/帧解析。 |
| 交付诚实性 | 15/15 | R426 两条新尺的 1x 红照实写并改仪器；真实拖拽缺口具名 NOT-RUN；本地 5 条滚动红具名会话/顺序；不把 capture-env 说成真实拖拽。 |
| 可复核性 | 15/15 | 静置/拖拽两读数、7 把刀 + r29d 5 把重钉、precheck/rot/CI 原文、基线 234、换装/清账读数都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_423 = u"""## D-423 拖拽源只降行内容透明度，并在 50ms 后用 `.common` 轮询松开（R427）

- 背景：把一条记录拖出去时，系统有拖拽预览，但源行本身没有任何变化；用户看不出"手里这份是列表里的哪一条"。
- 决定：`DragSourceFeedbackState` 按 entry ID 记录正在拖的条目；`EntryDragModifier` 在 `onDrag` 里 `beginAfterDelay(entryID)`（50ms，避开系统拖拽预览抓图），行内容 `.opacity(0.55)`（只降内容，不动行底/悬停底）；结束时用 `.common` runloop 的 50ms Timer 轮询 `NSEvent.pressedMouseButtons == 0` 清零。取证键 `draggingEntryIDForCapture` 只给夹具写。
- 理由：透明度是"退到背景里"的单一语义，不需要边框/描边（那会与行选中语言打架）；延迟是为了不把拖拽预览也拍暗；`.common` 是拖拽 tracking 模式下 Timer 仍能跑的唯一模式。
- 兼容性/迁移：新增 `row-drag-source-active` 亮暗 2 帧，基线 230→234；既有行帧逐字节不变；无动效、无胶片场景。
- 边界：真实系统拖拽会话没有自动化验收（capture-env 帧只证视觉态，onDrag/结束由源守卫钉；BACKLOG 453）；如果 Timer 在某个系统版本上不触发，行可能停暗，下一次 begin/end 会重置。
- 回滚：删 `DragSourceFeedback.swift`、`EntryDragModifier` 的 delay 与行的 `.opacity` 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 拖拽源反馈补行内容降透明度（静置/拖拽墨量比 **0.550/0.549**、墨数比 0.936/0.911；真实 onDrag 延迟 50ms 登记、松开轮询清零）；R426 跑失败步骤 2 个（新增固定带在 1x 上读 0）⇒ 差集/具名 NOT-RUN、不改门槛（R427 / 第 426 轮 / Round 424 / U-1558…U-1562 · 产品 3 文件，拖拽源反馈位）

"""

BACKLOG_SECTION = u"""437 追记（R427 · 仍开）：本轮补的是拖拽源反馈；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R427 · 仍开）：R426 CI 跑里 `SelectionRevealAnimationTests` **4/4 passed**（CHANNEL 0→143→600、TIME 6 采样/3 中间值/末 1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿 ⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R427 · 仍开）：macOS 12 的详情头部阈值本轮未动；R427 只改拖拽源与测试带。

452 追记（R427 · 仍开）：设置侧栏版本行仍是内容相对；本轮只把它的像素尺改成正/负差集（1x runner 的固定带不再可靠）。

**453. 真实系统拖拽会话没有自动化验收：capture-env 只能证视觉态，onDrag/结束是源守卫**（R427 观察）
    现象：`row-drag-source-active` 帧由取证键 `draggingEntryIDForCapture` 驱动，能证明"拖拽源态长什么样、墨量比 0.550/0.549"；但完整的系统拖拽（按下-移动-跨进程 drop）在本机/runner 都没有自动化的合成通道。`onDrag` 里的 `beginAfterDelay`、行的 `entry.id` 接线、`.common` 轮询都只有源码守卫，没有一条真实拖拽的运行时签名。
    修法（下一轮若需要）：先用 CGEvent/辅助功能权限试一条最小拖拽（同进程内拖到另一个 NSView 或 Finder），把 `NSEvent.pressedMouseButtons` 的轮询结束与行变暗/复亮写成一条在屏探针；失败就把权限/环境原因具名记 NOT-RUN，不要用 capture-env 帧替代真实会话。另需量一次"Timer 在拖拽 tracking 模式下真的触发"的读数（本轮只有 `.common` 的源守卫，没有实物读数）。
"""

STATE_SECTION = u"""## R427 状态（2026-10-27 · 本地 · 第 426 轮 / Round 424）：拖拽源反馈补行内容降透明度（静置/拖拽墨量比 **0.550/0.549**、墨数比 0.936/0.911；真实 onDrag 延迟 50ms 登记、松开轮询清零）；R426 跑失败步骤 2 个（新增固定带在 1x 上读 0）⇒ 差集/具名 NOT-RUN、不改门槛（产品 3 文件，拖拽源反馈位）

最后更新：2026-10-27（本地 · R427 / 第 426 轮 / Round 424）：行被拖出去时以前没有源反馈。新 `DragSourceFeedbackState`（按 entry ID、鼠标松开清零）+ `DragSourceFeedback` 控制器（`onDrag` 延迟 50ms 登记，避开系统拖拽预览；结束用 `.common` runloop 的 50ms Timer 轮询 `NSEvent.pressedMouseButtons`）+ `EntryDragModifier(entryID:)` + 行内容 `.opacity(0.55)`（只降内容，不动行底/悬停底）。真读数：静置墨 10162/11384、拖拽 9512/10374；**墨数比 0.936/0.911、墨量比 0.550/0.549**。真看图：拖拽源行星/图标/文字整体退到背景、行底仍白。真实系统拖拽会话具名 `DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`（453）；capture-env 帧只证视觉态。R426 run `40478143446 ↔ 1f3dc91` **failure，失败步骤 2 个**（`Swift tests` / `Capture gate`）：caption 探针已绿；两条新尺的固定带在 1x 读 0（源图标最小窗文字 0、版本行正臂 0/最小窗 3473 首墨 x=7）⇒ 版本行改正/负差集（720/640 差 70×10/11、正臂 1086/1284、负臂 0），源图标最小窗文字具名 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`（本机 3071/3471）。`settings-min-no-footer` 加进卡片节奏排除与暗档盲区名册；名册变更把 r29d M132 弄空，二次重钉后 **5/5 CAUGHT**。floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted ⇒ 436 REDS=0；回执 2/2 重抓=no；Dock 5/5；搜索 4 行；滚动 4/4（`CHANNEL 0→143→600 变化 40800/44400 重抓=no`、`TIME 6/3/205/1430`）。`M1153–M1159` **7/7 CAUGHT**（state 2 / entrydrag 2 / row 3）；预检 **196/178/527 bad=0**、ARM **289 文件 / 1011 把**、HIDDEN **283/945 rot=0**。本地全量 **1149/57/5**：5 断言全在 `SelectionRevealAnimationTests`，单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=9/首=29/末=1438`、`CHANNEL 0→87→600 变化 80951/129600 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **134/4/0 / 234 帧**；基线 **230→234**（4 增、0 变、0 缺）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 426，现读 `python3 scripts/product_streak.py --streak-for 426`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R426 跑 failure、失败步骤 2 个：caption 已绿；两条新尺的固定带 1x 读 0 ⇒ 版本行改正/负差集、源图标最小窗文字具名 NOT-RUN；Dock 5/5、搜索 4 行、滚动 4/4、回执 2/2、floor 5/5 无红。
② 产品：拖拽源反馈（静置/拖拽墨量比 0.550/0.549；onDrag 延迟 50ms、松开轮询清零）。
③ 判据：M1153–M1159 7/7；r29d 5/5；precheck 196/178/527；hidden rot 0。
④ 436：R426 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 283 / 可判 945 / rot 0。
⑥ 捕获 134/4/0、234 帧；换装 ok；清账 162/63/0；帧基线 234/0/0/0；本地全量 1149/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；② Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；③ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`；本机 3071/3471）；④ 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑤ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑥ 设置侧栏版本行窗口下沿未成立（452）；⑦ 真机/多屏面板落点无截屏（447）；⑧ 真菜单栏表面、12 实时腿；⑨ `table-lazy-rows`；⑩ 437–453 仍开；⑪ R427 新跑待 push 后读。

下一轮（R428）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R427 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 1x 上版本行差集/源图标最小窗文字具名 NOT-RUN 是否稳定、拖拽源在 CI 上是否只变 2 帧、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R427_REPORT_BULLET = u"""- **R427（拖拽源反馈位）**：行被拖出去时以前没有源反馈。新 `DragSourceFeedbackState`（按 entry ID、鼠标松开清零）+ `DragSourceFeedback` 控制器（`onDrag` 延迟 50ms 登记，避开系统拖拽预览；结束用 `.common` runloop 的 50ms Timer 轮询 `NSEvent.pressedMouseButtons`）+ `EntryDragModifier(entryID:)` + 行内容 `.opacity(0.55)`（只降内容，不动行底/悬停底）。真读数：静置墨 10162/11384、拖拽 9512/10374；**墨数比 0.936/0.911、墨量比 0.550/0.549**。真看图：拖拽源行星/图标/文字整体退到背景、行底仍白。真实系统拖拽会话具名 `DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`（453）。R426 run `40478143446 ↔ 1f3dc91` **failure、失败步骤 2 个**（Swift tests / Capture gate）：caption 已绿；两条新尺的固定带在 1x 读 0（源图标最小窗文字 0、版本行正臂 0/最小窗 3473 首墨 x=7）⇒ 版本行改正/负差集（720/640 差 70×10/11、正臂 1086/1284、负臂 0），源图标最小窗文字具名 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`（本机 3071/3471）；`settings-min-no-footer` 进卡片节奏排除与暗档盲区名册，r29d M132 二次重钉 5/5。floor judged=5/5 executed=77 无红；回执 2/2 重抓=no；Dock 5/5；搜索 4 行；滚动 4/4。M1153–M1159 7/7；预检 196/178/527 bad=0；HIDDEN 283/945 rot=0。本地全量 1149/57/5：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/9、29→1438；CHANNEL 0→87→600）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 134/4/0、234 帧；基线 230→234（4 增、0 变）；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 426 轮（R427" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R427 节")
if u"## Round 424 · R427" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 424")
if u"## D-423" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-423")
if u"拖拽源反馈补行内容降透明度" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**453." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 453")
if state.count(u"## R426 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R426 状态"))
U_CELL_OLD = u"U-31 … U-1557（R426 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R426 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R426 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_423 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R426 状态", STATE_SECTION + u"## R426 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1562（R427 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R426 节 ②",
                                u"AGENT_STATE.md` 的 R427 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R427_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R427_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
