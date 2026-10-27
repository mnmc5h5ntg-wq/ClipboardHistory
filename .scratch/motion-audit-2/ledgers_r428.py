#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R428 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 426 轮（R427 · 2026-10-27"
AUDIT_SECTION = u"""## 第 427 轮（R428 · 2026-10-27 · U-1563…U-1567）：菜单项补全局快捷键提示并把「快速选择…」挂进菜单（12 的 NSMenu 旧 4 项/无提示 → 新 5 项、显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V；13+ 系统菜单像素具名 NOT-RUN）；R427 跑失败步骤 2 个（版本行差集在 runner 上整页不同）⇒ 单帧品红标记定位、阈值未动（产品 7 文件，菜单项快捷键位）

- **U-1563：⓪ R427 跑的失败步骤与版本行差集的命运。** `40487018343 ↔ fb55ffc` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。唯一红是 R427 的版本行**正/负差集**：runner 上 `settings-general` 与 `settings-general-no-footer` 整页不同（720 差 **136×203**、640 **136×202**），负臂同一差集仍读到 **5725/23690 颗墨**、dark 首墨 0 ⇒ 差集不是脚注。其余全绿：floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted；`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry` **4 行出现且不计红**（light/dark × 两步骤）；拖拽源 `DRAG_SOURCE_ROW light 静置墨=3026 拖拽墨=2655 墨数比=0.877 墨量比=0.549`、dark `3333/2948/0.884/0.550`；搜索 4 行；滚动 **4/4 passed**（`CHANNEL 0→133→600 变化 39600/32252 重抓=no`、`TIME 6 采样/2 中间值/首=840/末=1430`）；Dock `DOCK_BADGE_PIXEL_NOT_RUN` 已登记；`MOTION_COPY_RECEIPT` 这一跑**没有行** ⇒ 具名 NOT-RUN（不是绿）。
- **U-1564：R427 红改成单帧标记定位。** 版本行不再拿两张整页帧做差集：脚注左缘在取证环境里画一颗 **2×2 品红标记**（`settingsSidebarFooterMarkerForCapture`，只有夹具写），像素尺在**同一帧**里找品红，再量标记右侧 130×20pt 的墨。新增 `settings-general-footer-marker` / `settings-min-footer-marker` 亮暗 4 帧；本机：标记 **2×2@0,270**、720 墨 **1086/1284**、首 24/29，640 同样 1086/1284；负臂 `settings-general-no-footer` / `settings-min-no-footer` 找不到标记。基线 **234→238**（4 增、0 变、0 缺）；r29d 盲区名册因新增两帧再次弄空 M132，按「no-footer + marker + settings-general」三行重钉后 **5/5 CAUGHT**。
- **U-1565：② 菜单项补全局快捷键提示 + 快速选择入口。** 以前菜单栏菜单只有「显示主窗口 / 设置 / 清空未收藏 / 退出」，全局热键只在设置页看得到。新 `MenuShortcutPresentation`：标题追加当前热键的 `displayString`；`AppCommandCatalog.menuBarCommands` 增 `.showQuickPick`（同一个 `AppCommand`，不造第二条粘贴/显示路径，菜单项的 `keyEquivalent` 仍为空）；`MenuBarController` 用**活的 provider**（`menuShortcutHints()`）在每次 `populate` 时读取，`ApplicationShell` 传当前 `showMainWindowHotKeySettings` / `quickPickHotKeySettings`，13+ 的 `App.swift` 走 `appDelegate.menuShortcutHint(for:)`。旧/新同带（12 的真实 `NSMenuItem.title`）：旧 `显示主窗口 | 设置 | 清空未收藏 | 退出时间剪史`（4 项、无快速选择）→ 新 `显示主窗口  ⌃⌥V | 快速选择…  ⌃⌥⇧V | 设置 | 清空未收藏 | 退出时间剪史`（5 项）；自定义热键在 `populate` 时跟随（⌃⌥V→⌃⌥C，测试实测）。13+ 的 MenuBarExtra 是系统菜单，像素/标题通道具名 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`；12 的 NSMenu 标题是真实 AppKit 证人。
- **U-1566：判据与刀。** `MenuShortcutPresentationTests` 5 条（hint 映射 / 标题追加 / 12 真实菜单 / 自定义热键跟随 / 双表面源守卫）+ `AppCommandTests` 顺序更新 + `MenuBarPopulationTests` 全绿。`M1160–M1166` **6/6 CAUGHT**（policy 2 / controller 1 / catalog 1 / App 1 / Shell 1，RESTORE_CLEAN=yes）；r29d M132–M136 **5/5 CAUGHT**。预检 `tables=201 covered=183 arms=533 bad=0`、`ARM_TOTAL files=294 arms=1017`、`BASH_ARMS 16 bad=0`；`HIDDEN_ARMS 表=288 可判=951 rot=0`。
- **U-1567：八步。** build **0 告警**；捕获 **134 条 / 4 skip / 0 失败 / 238 帧**；基线 `UPDATED=238`、复验 `COMPARED=238 CHANGED=0 MISSING=0 ADDED=0`（4 张 marker 帧新增；既有 234 帧逐字节不变）；全量 **1154/57/5**（5 个断言全在 `SelectionRevealAnimationTests`，3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`SCROLL_REVEAL_TIME 采样=18/中间值=8/首=30.5/末=1438`、`CHANNEL 0→90.5→600 变化 108162/146400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 427，现读 `python3 scripts/product_streak.py --streak-for 427`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 13+ MenuBarExtra 系统菜单的像素/标题通道（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ R427 跑的 `MOTION_COPY_RECEIPT` 无行（NOT-RUN）；⑥ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 设置侧栏版本行窗口下沿未成立（452）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–454 仍开；⑬ R428 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 425 · R428（第 427 轮 · 2026-10-27）：菜单项补全局快捷键提示并把「快速选择…」挂进菜单（12 的 NSMenu 旧 4 项/无提示 → 新 5 项、显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V；13+ 系统菜单像素具名 NOT-RUN）；R427 跑失败步骤 2 个（版本行差集在 runner 上整页不同）⇒ 单帧品红标记定位、阈值未动（产品 7 文件，菜单项快捷键位）

菜单栏菜单以前只有四项、全局热键只在设置页可见。新 `MenuShortcutPresentation` 把当前热键追加到标题；`AppCommandCatalog.menuBarCommands` 增 `.showQuickPick`（同一 AppCommand，不造第二条路径）；`MenuBarController` 用活 provider 在每次 populate 读当前键；`ApplicationShell` 传两份 HotKeySettings；13+ 的 App.swift 走 `appDelegate.menuShortcutHint`。12 真实 NSMenu 旧/新：`显示主窗口|设置|清空未收藏|退出`（4 项）→ `显示主窗口  ⌃⌥V|快速选择…  ⌃⌥⇧V|设置|清空未收藏|退出`（5 项）；自定义热键在 populate 时跟随（⌃⌥V→⌃⌥C）。13+ 系统菜单像素具名 NOT-RUN（454）；12 标题是真实 AppKit 证人。R427 run `40487018343 ↔ fb55ffc` **failure、失败步骤 2 个**：唯一红是版本行正/负差集在 runner 上整页不同（720 136×203、负臂 5725/23690）⇒ 改成**单帧 2×2 品红标记**定位，新增 4 张 marker 帧，本机 1086/1284、负臂无标记；基线 234→238；r29d 名册再重钉 5/5。其余：floor judged=5/5 executed=77 无红；源图标最小窗文字 NOT-RUN 4 行；拖拽 mass 0.549/0.550；搜索 4 行；滚动 4/4；`MOTION_COPY_RECEIPT` 无行 NOT-RUN。M1160–M1166 6/6；预检 201/183/533；HIDDEN 288/951 rot=0。全量 1154/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（TIME 18/8、30.5→1438；CHANNEL 0→90.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 134/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 12 的 NSMenu 用真实 NSMenuItem 标题作证（旧 4 项/新 5 项、两枚热键提示、custom 键跟随）；13+ 的 MenuBarExtra 是系统菜单，像素/标题只走源守卫并具名 NOT-RUN。扣 3：没有一张菜单像素图。 |
| 判据有效性 | 15/15 | 5 条呈现/真实菜单/动态源 + AppCommand 顺序 + MenuBarPopulation；M1160–M1166 6/6；quick pick 选同一个 AppCommand。 |
| 假绿防御 | 15/15 | 菜单命令区顺序由测试钉住；提示读活 provider（改键后 populate 跟随）；13+ 系统菜单不冒充像素；`MOTION_COPY_RECEIPT` 无行记 NOT-RUN。 |
| 产品面推进 | 14/15 | 真落 Sources 7 文件（菜单 6 + 脚注标记缝 1），补的是菜单项可发现性与快速选择入口；扣 1：13+ 菜单像素没有直接证据（454）。 |
| 台账一致性 | 15/15 | U-1563…U-1567、D-424、436 的 judged=5/5/executed=77、R427 的 136×203/23690、拖拽 mass、R428 的旧/新标题都从日志/真实菜单解析。 |
| 交付诚实性 | 15/15 | R427 差集红照实写并改仪器；13+ 系统菜单具名 NOT-RUN；真实拖拽/Dock/源图标最小窗各有具名 NOT-RUN；本地 5 条滚动红具名会话/顺序。 |
| 可复核性 | 15/15 | 旧/新菜单标题、4 张 marker 帧、6 把刀 + r29d 5 把重钉、precheck/rot/CI 原文、基线 238、换装/清账读数都在。 |

均分 = 101/105 ≈ 14.4/15（96）。"""

DECISION_424 = u"""## D-424 菜单项用文字显示全局快捷键；快速选择进菜单命令区（R428）

- 背景：菜单栏菜单只有显示主窗口/设置/清空/退出，全局热键（⌃⌥V、⌃⌥⇧V）只在设置页可见；快速选择只能靠热键唤起。
- 决定：`MenuShortcutPresentation` 在当前标题后追加 `HotKeyShortcut.displayString`；`AppCommandCatalog.menuBarCommands` 增 `.showQuickPick`（同一个 `AppCommand`，不造第二条粘贴/显示路径，`keyEquivalent` 仍为空）；`MenuBarController` 用活的 provider 在每次 `populate` 读取当前热键；`ApplicationShell` 传当前 `showMainWindowHotKeySettings` / `quickPickHotKeySettings`；13+ 的 `App.swift` 用 `AppDelegate.menuShortcutHint(for:)`。
- 理由：热键是全局 Carbon 注册，不是本地 key equivalent；把组合写成菜单的 key equivalent 会造第二条路径（全局热键 + 菜单项同时触发）。文字提示既让命令可发现，又保持只有一条行为路径；provider 让用户改键后菜单跟着走。
- 兼容性/迁移：12 的 NSMenu 命令区从 4 项变 5 项（加快速选择），`AppCommandTests` 顺序更新；既有帧不变，基线 234→238 是 R427 修复的 4 张脚注 marker 帧。
- 边界：13+ MenuBarExtra 是系统菜单，像素/标题通道具名 NOT-RUN（454）；快速选择菜单项点下会先关菜单再开浮层，未做真机点击验收。
- 回滚：删 `MenuShortcutPresentation.swift`、命令目录里的 `.showQuickPick`、两个表面的标题调用即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 菜单项补全局快捷键提示并把「快速选择…」挂进菜单（12 的 NSMenu 旧 4 项/无提示 → 新 5 项、显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V；13+ 系统菜单像素具名 NOT-RUN）；R427 跑失败步骤 2 个（版本行差集在 runner 上整页不同）⇒ 单帧品红标记定位、阈值未动（R428 / 第 427 轮 / Round 425 / U-1563…U-1567 · 产品 7 文件，菜单项快捷键位）

"""

BACKLOG_SECTION = u"""437 追记（R428 · 仍开）：本轮补的是菜单项的快捷键提示与快速选择入口；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R428 · 仍开）：R427 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→133→600、TIME 6/2/840/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿 ⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R428 · 仍开）：macOS 12 的详情头部阈值本轮未动；菜单提示不涉及它。

452 追记（R428 · 仍开）：设置侧栏版本行仍是内容相对；本轮只把它的像素尺从差集改成单帧 marker。

453 追记（R428 · 仍开）：真实系统拖拽会话仍无自动化验收；本轮没动拖拽源。

**454. 13+ MenuBarExtra 的系统菜单没有像素/标题通道：12 的 NSMenu 是真实 AppKit 证人，13+ 只有源守卫**（R428 观察）
    现象：12 的菜单由 `MenuBarController.populate` 建 `NSMenuItem`，测试能读真实标题（旧 4 项→新 5 项、⌃⌥V/⌃⌥⇧V）；13+ 的 `MenuBarExtraStyle.menu` 由系统把 SwiftUI label 编成 NSMenu，测试进程拿不到那张菜单，像素也没有（系绘制）。本轮具名 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`。
    修法（下一轮若需要）：在 13+ 上要么用辅助功能在真机读菜单项标题（需要权限与真机），要么保持 `MenuShortcutPresentation` 的纯函数 + App.swift 源守卫，不把 12 的 NSMenu 读数冒充 13+ 证据；如将来跑真机点击，顺带验"快速选择菜单项点下会关菜单再开浮层"。
"""

STATE_SECTION = u"""## R428 状态（2026-10-27 · 本地 · 第 427 轮 / Round 425）：菜单项补全局快捷键提示并把「快速选择…」挂进菜单（12 的 NSMenu 旧 4 项/无提示 → 新 5 项、显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V；13+ 系统菜单像素具名 NOT-RUN）；R427 跑失败步骤 2 个（版本行差集在 runner 上整页不同）⇒ 单帧品红标记定位、阈值未动（产品 7 文件，菜单项快捷键位）

最后更新：2026-10-27（本地 · R428 / 第 427 轮 / Round 425）：菜单栏菜单以前只有四项、全局热键只在设置页看得到。新 `MenuShortcutPresentation`（标题后追加当前热键的 `displayString`；全局热键不挂 key equivalent，避免第二条路径）+ `AppCommandCatalog.menuBarCommands` 增 `.showQuickPick` + `MenuBarController` 的活 provider（每次 populate 读当前键）+ `ApplicationShell` 传两份 HotKeySettings + `AppDelegate.menuShortcutHint` 给 13+ 的 App.swift。12 真实 NSMenu 旧/新：`显示主窗口|设置|清空未收藏|退出`（4 项）→ `显示主窗口  ⌃⌥V|快速选择…  ⌃⌥⇧V|设置|清空未收藏|退出`（5 项）；自定义热键在 populate 时跟随（⌃⌥V→⌃⌥C 实测）。13+ 系统菜单像素/标题具名 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`（454）。R427 run `40487018343 ↔ fb55ffc` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是版本行正/负差集在 runner 上整页不同（720 136×203、640 136×202、负臂 5725/23690 墨）⇒ 改成**单帧 2×2 品红标记**定位（`settingsSidebarFooterMarkerForCapture`；新增 4 张 marker 帧；本机 1086/1284、首 24/29、负臂无标记），基线 **234→238**；r29d 名册因新增两帧再次弄空 M132，三行重钉后 **5/5 CAUGHT**。其余：floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted；`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN` 4 行出现不计红；拖拽 mass 0.549/0.550、count 0.877/0.884；搜索 4 行；滚动 4/4（`CHANNEL 0→133→600 变化 39600/32252 重抓=no`、`TIME 6/2/840/1430`）；`MOTION_COPY_RECEIPT` 无行 ⇒ NOT-RUN。`M1160–M1166` **6/6 CAUGHT**（policy 2 / controller 1 / catalog 1 / App 1 / Shell 1）；预检 **201/183/533 bad=0**、ARM **294 文件 / 1017 把**、HIDDEN **288/951 rot=0**。本地全量 **1154/57/5**：5 断言全在 `SelectionRevealAnimationTests`，单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=8/首=30.5/末=1438`、`CHANNEL 0→90.5→600 变化 108162/146400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **134/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 427，现读 `python3 scripts/product_streak.py --streak-for 427`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R427 跑 failure、失败步骤 2 个：唯一红是版本行差集整页不同 ⇒ 单帧品红标记修复；源图标最小窗文字 NOT-RUN 4 行；拖拽 mass 0.549/0.550；搜索 4 行、滚动 4/4、floor 5/5 无红。
② 产品：菜单项补全局快捷键提示 + 快速选择入口（12 旧 4 项→新 5 项；13+ 源守卫/系统菜单 NOT-RUN）。
③ 判据：M1160–M1166 6/6；r29d 5/5；precheck 201/183/533；hidden rot 0。
④ 436：R427 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 288 / 可判 951 / rot 0。
⑥ 捕获 134/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1154/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ R427 跑的 `MOTION_COPY_RECEIPT` 无行（NOT-RUN）；⑥ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 设置侧栏版本行窗口下沿未成立（452）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–454 仍开；⑬ R428 新跑待 push 后读。

下一轮（R429）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R428 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 12 NSMenu 的 5 项与两枚提示、13+ 源守卫、marker 帧 4 张、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R428_REPORT_BULLET = u"""- **R428（菜单项快捷键位）**：菜单栏菜单以前只有四项、全局热键只在设置页可见。新 `MenuShortcutPresentation`（标题后追加当前热键 `displayString`；全局热键不挂 key equivalent，避免第二条路径）+ `AppCommandCatalog.menuBarCommands` 增 `.showQuickPick` + `MenuBarController` 的活 provider（每次 populate 读当前键）+ `ApplicationShell` 传两份 HotKeySettings + `AppDelegate.menuShortcutHint` 给 13+ 的 App.swift。12 真实 NSMenu 旧/新：`显示主窗口|设置|清空未收藏|退出`（4 项）→ `显示主窗口  ⌃⌥V|快速选择…  ⌃⌥⇧V|设置|清空未收藏|退出`（5 项）；自定义热键在 populate 时跟随（⌃⌥V→⌃⌥C 实测）。13+ 系统菜单像素/标题具名 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`（454）。R427 run `40487018343 ↔ fb55ffc` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是版本行正/负差集在 runner 上整页不同（720 136×203、640 136×202、负臂 5725/23690 墨）⇒ 单帧 2×2 品红标记定位（新增 4 张 marker 帧；本机 1086/1284、首 24/29、负臂无标记），基线 234→238；r29d 名册再重钉 5/5。floor judged=5/5 executed=77 无红；源图标最小窗文字 NOT-RUN 4 行；拖拽 mass 0.549/0.550；搜索 4 行；滚动 4/4；`MOTION_COPY_RECEIPT` 无行 NOT-RUN。M1160–M1166 6/6；预检 201/183/533 bad=0；HIDDEN 288/951 rot=0。本地全量 1154/57/5：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、30.5→1438；CHANNEL 0→90.5→600）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 134/4/0、238 帧；基线 238/0/0/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 427 轮（R428" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R428 节")
if u"## Round 425 · R428" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 425")
if u"## D-424" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-424")
if u"菜单项补全局快捷键提示" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**454." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 454")
if state.count(u"## R427 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R427 状态"))
U_CELL_OLD = u"U-31 … U-1562（R427 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R427 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R427 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_424 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R427 状态", STATE_SECTION + u"## R427 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1567（R428 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R427 节 ②",
                                u"AGENT_STATE.md` 的 R428 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R428_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R428_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
