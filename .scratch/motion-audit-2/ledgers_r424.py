#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R424 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 422 轮（R423 · 2026-10-27"
AUDIT_SECTION = u"""## 第 423 轮（R424 · 2026-10-27 · U-1543…U-1547）：Dock 图标状态补「未读剪辑」角标（后台新到 3 条 → `dockTile.badgeLabel` 旧 nil/新「3」、激活清零；像素通道由 WindowServer 画 ⇒ 具名 NOT-RUN）；R423 跑 success、20/20 步、失败步骤 0（搜索无结果 4 行 2025→2411/宽 64→134；滚动 4/4 绿）；本地全量 5 条滚动红由 CI 绿证伪为会话/顺序（产品 3 文件，Dock 图标状态）

- **U-1543：⓪ R423 head 跑与搜索/滚动/floor 命运。** `40460495274 ↔ 37f15d8` **success**：20/20 步全部 success，**失败步骤 0 个**（`gh run view --json jobs` 逐条读）。搜索无结果 4 帧在 runner 上成立：`SEARCH_NO_RESULTS light 前墨=2025 后墨=2411 变化=2985 前宽=64 后宽=134`、`dark 前墨=2021 后墨=2416 变化=3023 前宽=64 后宽=134`（runner 1x；本机 2x 7790→8841 墨、128→264 宽，按 scale² 同带）。`SelectionRevealAnimationTests` 在 CI **4/4 passed**：`SCROLL_REVEAL_CHANNEL 起点=0.0 中段=73.0 落点=600.0 起→中变化=21138 中→落变化=32400 重抓=no`、`SCROLL_REVEAL_OFFSET 起点=0.0 中段=251.0 落点=1430.0 目标=1430.0 中段是否严格在两端之间=true`、`SCROLL_REVEAL_TIME 采样=5 中间值=2 首=590.0 末=1430.0 目标=1430.0 时长=0.20`。floor：`MOTION_FLOOR_FACTS judged=5/5 executed=76 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=4`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`、`MOTION_FLOOR_SUITE_CLEAN=0`、无 `MOTION_FLOOR_UNLISTED`。436 只复核，不重猜 `must_judge`。
- **U-1544：② Dock 图标状态补「未读剪辑」角标。** 主窗口关掉/App 不在前台时，新到的剪辑此前在 Dock 上没有任何读数。新 `DockBadgePolicy`（0→nil、1…99→数字、>99→「99+」）+ `DockBadgeTracker`（前台新到不计、失活后按增量计、激活清零、历史缩水时夹住）+ `DockBadgeController`（订阅 `HistoryStore.$entries`、两条激活边），`AppDelegate.configure()` 幂等建控制器并在 `applicationDidBecomeActive/ResignActive` 各接一条。旧/新同一把尺（`NSApplication.shared.dockTile.badgeLabel`）：**旧 nil**（控制器创建前攒 2 条）→ **新「3」**（失活后新到 3 条）→ 激活 **nil**；纯读数 100→「99+」。像素通道具名 NOT-RUN：`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none badgeAfterActivate=nil`（Dock 图标由 WindowServer 画，进程里没有可截的 `contentView`；捕获卷 226 帧全是本进程窗口）。既有 226 帧逐字节不变、基线 **226/0/0/0**。
- **U-1545：判据与刀。** 5 条新用例：policy 真值表（0/负数/1/42/99/100/10000）、tracker（前台不计/失活计/激活清/缩水夹住）、**产品入口**（真实 `HistoryStore.add` → 真实 `NSApplication.shared.dockTile.badgeLabel`，旧 nil→新「3」→激活 nil）、AppDelegate 窄源守卫（configure 幂等建 + 两条激活边 + 默认 applyBadge 真写 `dockTile.badgeLabel`）。`M1119…M1127` **9/9 CAUGHT**（三张表：policy 4、controller 2、wiring 3；全部 `RESTORE_CLEAN=yes`）。预检 `tables=186 covered=168 arms=500 bad=0`、`ARM_TOTAL files=279 arms=984`、`BASH_ARMS 16 bad=0`；`HIDDEN_ARMS 表=273 可判=918 rot=0`。
- **U-1546：本地全量的 5 条滚动红 = 会话/顺序，不是产品回归。** 全量 **1132/57/5**（+5 条 DockBadge），5 个断言全在 `SelectionRevealAnimationTests`（3 条用例：reveal 2 断言 + product-duration 2 + static 1）。同一份代码单跑（`caffeinate -u` 唤醒后）**4/4 passed**：`SCROLL_REVEAL_CHANNEL 起点=0.0 中段=88.0 落点=600.0 起→中变化=88818 中→落变化=134400 重抓=no`；R423 单跑另有 8 个中间值/末 1438。R423 的 CI 卷 4/4 绿（U-1543）⇒ 按监督者口径坐实本地是整卷顺序/会话，具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；地板一个没动。
- **U-1547：① 367 与八步。** `HIDDEN_ARMS 表=273 可判=918 rot=0`（R423 270/909，本轮 +3 表 +9 臂）；预检 `tables=186 covered=168 arms=500 bad=0`、`ARM_TOTAL files=279 arms=984 dupes=0 repeats=0`。build **0 告警**；捕获 **226 帧 / 131 条 / 4 skip / 0 失败**；基线 `COMPARED=226 CHANGED=0 MISSING=0 ADDED=0`（无新增/变更帧，无需 update）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **0** 轮（本轮动了 Sources 3 文件；上一轮 as-of 423 现读 streak=1）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① Dock 角标的像素/帧通道（WindowServer 画；`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`，进程内 contentView=none）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`；CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 真机/多屏面板落点无截屏（447）；⑤ 真菜单栏表面、12 实时腿；⑥ `table-lazy-rows`；⑦ 设置能力闸门仍隐式（441）；⑧ 437–450 仍开；⑨ R424 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 421 · R424（第 423 轮 · 2026-10-27）：Dock 图标状态补「未读剪辑」角标（后台新到 3 条 → `dockTile.badgeLabel` 旧 nil/新「3」、激活清零；像素通道由 WindowServer 画 ⇒ 具名 NOT-RUN）；R423 跑 success、20/20 步、失败 0（搜索 4 行 2025→2411/宽 64→134；滚动 4/4 绿）；本地全量 5 条滚动红由 CI 绿证伪为会话/顺序（产品 3 文件，Dock 图标状态）

主窗口关掉/App 不在前台时，新到的剪辑在 Dock 上没有任何读数。新 `DockBadgePolicy`（0→nil、1…99→数字、>99→「99+」）+ `DockBadgeTracker`（前台不计、失活计增量、激活清零、缩水夹住）+ `DockBadgeController`（订阅 `HistoryStore.$entries` + 两条激活边），`AppDelegate.configure()` 幂等建并接两条激活边。旧/新同一把尺（真实 `NSApplication.shared.dockTile.badgeLabel`）：旧 nil（控制器前攒 2 条）→ 新「3」（失活后 3 条）→ 激活 nil；纯读数 100→「99+」。像素通道具名 `DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none`；既有 226 帧不变、基线 226/0/0/0。M1119–M1127 9/9；预检 186/168/500；HIDDEN 273/918 rot=0。R423 run `40460495274 ↔ 37f15d8` success、20/20 步、失败 0：搜索 4 行 light 2025→2411/宽 64→134、dark 2021→2416/64→134；floor judged=5/5 executed=76、REDS=0、无 unlisted；CI 滚动 4/4 绿（CHANNEL 0→73→600、重抓=no；TIME 2 中间值/末 1430）。本地全量 1132/57/5，5 断言全在 SelectionRevealAnimationTests，单跑 4/4 绿（0→88→600、变化 88818/134400、重抓=no）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449，不改门槛）。捕获 226/131/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | Dock 图标本体由 WindowServer 画，进程内没有可截视图 ⇒ 像素通道具名 NOT-RUN（`contentView=none`）；本轮的视觉证人往下沉到真实 `dockTile.badgeLabel` 的旧/新读数（nil→「3」→nil）与 policy 真值表。扣 3：没有一张能看到角标的帧。 |
| 判据有效性 | 15/15 | 产品入口测试用真实 `HistoryStore.add` 与真实 `dockTile.badgeLabel`；5 条用例覆盖策略/状态机/接线；M1119–M1127 9/9 CAUGHT。 |
| 假绿防御 | 15/15 | 旧读数（控制器前 nil）与新读数在同一用例、同一把尺上量；两张表各钉一侧（状态机与接线）；源守卫窄到 configure 块与两条激活边；每一刀都 `RESTORE_CLEAN=yes`。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，补的是「主窗口关掉后新剪辑无可见读数」这一档；扣 1：语义只按 App 激活清零，主窗口关但 App 仍前台时不计（450）。 |
| 台账一致性 | 15/15 | U-1543…U-1547、D-420、436 的 judged=5/5/executed=76、CI 滚动 4/4、搜索 4 行、本机隔离 4/4 都从日志解析。 |
| 交付诚实性 | 15/15 | 像素通道具名 NOT-RUN 并给能力证据；本地 5 条滚动红照实写，CI 绿后按监督者口径坐实为会话/顺序；不把系统绘制说成产品像素。 |
| 可复核性 | 15/15 | 旧/新 badgeLabel、policy 表、9 把刀、三张表互不混、precheck/rot/CI 原文、清账与换装读数都在。 |

均分 = 101/105 ≈ 14.4/15（96）。"""

DECISION_420 = u"""## D-420 Dock 角标只数「App 不在前台时新到的剪辑」，回到前台清零（R424）

- 背景：主窗口关掉后，采集仍在跑，但 Dock 图标对新到的剪辑没有任何读数；用户不知道后台攒了什么。
- 决定：`DockBadgePolicy` 只把 >0 的未读数写成角标（1…99 数字、>99「99+」）；`DockBadgeTracker` 只在 `!isActive` 时按 entries 增量累计，`applicationDidBecomeActive` 清零；历史缩水时把未读夹到当前条数；`DockBadgeController` 订阅 `HistoryStore.$entries`，由 `AppDelegate` 在 configure 幂等创建并接两条激活边。
- 理由：角标是"回来看看"的提示，不是计数器的第二份真值；前台时列表当场可见，再挂数字是噪音；系统画角标，进程里没有可截视图，所以像素证据要诚实降级成值读数 + 具名 NOT-RUN。
- 兼容性/迁移：不改任何既有视图、不动帧基线（226/0/0/0）；角标在 App 退出时随图标消失。
- 边界：只按 App 激活清零；主窗口关着但 App 仍前台时新到的剪辑不计（BACKLOG 450）。真机 Dock 截图的像素通道仍缺（屏幕录制权限 + 图标定位）。
- 回滚：删两个新文件与 `AppDelegate` 的三处接线即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### Dock 图标状态补「未读剪辑」角标（后台新到 3 条 → `dockTile.badgeLabel` 旧 nil/新「3」、激活清零；像素通道由 WindowServer 画 ⇒ 具名 NOT-RUN）；R423 跑 success、20/20 步、失败 0（搜索 4 行 2025→2411/宽 64→134；滚动 4/4 绿）；本地全量 5 条滚动红由 CI 绿证伪为会话/顺序（R424 / 第 423 轮 / Round 421 / U-1543…U-1547 · 产品 3 文件，Dock 图标状态）

"""

BACKLOG_SECTION = u"""437 追记（R424 · 仍开）：本轮补的是 Dock 未读角标；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R424 · 仍开）：CI 卷 `SelectionRevealAnimationTests` **4/4 passed**（CHANNEL 中段=73、TIME 2 中间值/末 1430），本机全量仍是 5 个断言红（3 条用例）、单跑 4/4 绿 ⇒ 会话/顺序已坐实；下一步仍按本条修法先量 `isActive/isHidden/窗口可见/runloop 模式`，不改门槛。

**450. Dock 角标的语义边界：只按 App 激活清零；主窗口关着但 App 仍前台时新到的剪辑不计；真机 Dock 像素通道仍缺**（R424 观察）
    现象：`DockBadgeTracker` 的计数窗口是 `!isActive`，所以「主窗口关掉、App 仍是前台」的那段时间里新到的剪辑不会挂角标；反过来说，用户在别的 App 里复制时角标会一直累计到切回来为止。像素侧：Dock 图标由 WindowServer 画，进程里 `dockTile.contentView=none`，本轮的 226 张捕获帧里没有一张能看见角标（具名 `DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）。
    修法（下一轮若需要）：先用户验收「累计到切回」这个语义是否合适（可选改成只报"有未读"的点或只报收藏），再决定是否加"窗口可见性"而不仅是 App 激活；像素证据要么走真机屏幕录制（权限 + Dock 图标定位），要么继续诚实记 NOT-RUN，不要用自制视图冒充系统角标。
"""

STATE_SECTION = u"""## R424 状态（2026-10-27 · 本地 · 第 423 轮 / Round 421）：Dock 图标状态补「未读剪辑」角标（后台新到 3 条 → `dockTile.badgeLabel` 旧 nil/新「3」、激活清零；像素通道由 WindowServer 画 ⇒ 具名 NOT-RUN）；R423 跑 success、20/20 步、失败 0（搜索 4 行 2025→2411/宽 64→134；滚动 4/4 绿）；本地全量 5 条滚动红由 CI 绿证伪为会话/顺序（产品 3 文件，Dock 图标状态）

最后更新：2026-10-27（本地 · R424 / 第 423 轮 / Round 421）：主窗口关掉/App 不在前台时，新到的剪辑此前在 Dock 上没有任何读数。新 `DockBadgePolicy`（0→nil、1…99→数字、>99→「99+」）+ `DockBadgeTracker`（前台不计、失活计增量、激活清零、缩水夹住）+ `DockBadgeController`（订阅 `HistoryStore.$entries`、两条激活边），`AppDelegate.configure()` 幂等建并接线。旧/新同一把尺（真实 `NSApplication.shared.dockTile.badgeLabel`）：旧 nil（控制器前攒 2 条）→ 新「3」（失活后 3 条）→ 激活 nil；纯读数 100→「99+」。像素通道具名 `DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none badgeAfterActivate=nil`；既有 226 帧逐字节不变、基线 **226/0/0/0**。`M1119–M1127` **9/9 CAUGHT**（policy 4 / controller 2 / wiring 3，RESTORE_CLEAN=yes）。R423 run `40460495274 ↔ 37f15d8` **success、20/20 步、失败步骤 0**：搜索无结果 4 行 `light 2025→2411 变化 2985 宽 64→134`、`dark 2021→2416 变化 3023 宽 64→134`（runner 1x）；floor `judged=5/5 executed=76 not-run=-`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`、`SUITE_CLEAN=0`、无 unlisted ⇒ **436 REDS=0**；CI 滚动 4/4 passed（`CHANNEL 起点=0.0 中段=73.0 落点=600.0 变化=21138/32400 重抓=no`、`TIME 采样=5 中间值=2 首=590 末=1430`）。本地全量 **1132/57/5**：5 个断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 唤醒后）**4/4 passed**（`0→88→600`、变化 `88818/134400`、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **226/131/4/0**；帧基线 **226/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **273/918 rot=0**；预检 **186/168/500 bad=0**、ARM **279 文件 / 984 把**；产品面连续零改动 **0** 轮（本轮动了 Sources 3 文件；上一轮 as-of 423 现读 streak=1）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R423 head 跑 success、20/20 步、失败步骤 0；搜索 4 行、滚动 4/4、floor judged=5/5 executed=76 REDS=0、无 unlisted。
② 产品：Dock 图标补未读角标（后台 3 条 → 「3」、激活 nil、100→「99+」）；像素通道具名 NOT-RUN；基线不动。
③ 判据：M1119–M1127 9/9；precheck 186/168/500；hidden rot 0；ARM 279 文件/984 把。
④ 436：judged=5/5 executed=76、OK=5/5、SUITE_CLEAN=0、无 unlisted；REDS=0。
⑤ 367：hidden 表 273 / 可判 918 / rot 0 / 上界 0。
⑥ 捕获 226/131/4/0；换装 ok；清账 162/63/0；帧基线 226/0/0/0；本地全量 1132/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 真机/多屏面板落点无截屏（447）；⑤ 真菜单栏表面、12 实时腿；⑥ `table-lazy-rows`；⑦ 设置能力闸门仍隐式（441）；⑧ 437–450 仍开；⑨ R424 新跑待 push 后读。

下一轮（R425）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R424 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 Dock 部署后 CI 是否仍全绿、搜索 4 行与滚动 4/4 是否稳定；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R424_REPORT_BULLET = u"""- **R424（Dock 图标状态）**：主窗口关掉/App 不在前台时，新到的剪辑此前在 Dock 上没有任何读数。新 `DockBadgePolicy`（0→nil、1…99→数字、>99→「99+」）+ `DockBadgeTracker`（前台不计、失活计增量、激活清零、缩水夹住）+ `DockBadgeController`（订阅 `HistoryStore.$entries` + 两条激活边），`AppDelegate.configure()` 幂等建并接线。旧/新同一把尺（真实 `NSApplication.shared.dockTile.badgeLabel`）：**旧 nil**（控制器前攒 2 条）→ **新「3」**（失活后 3 条）→ 激活 **nil**；纯读数 100→「99+」。像素通道具名 `DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none`（Dock 图标由 WindowServer 画，进程里没有可截的 contentView）；既有 226 帧逐字节不变、基线 226/0/0/0。M1119–M1127 9/9 CAUGHT（policy 4 / controller 2 / wiring 3）；预检 186/168/500 bad=0；HIDDEN 273/918 rot=0。R423 run `40460495274 ↔ 37f15d8` **success、20/20 步、失败步骤 0**：搜索无结果 4 行 `light 2025→2411 变化 2985 宽 64→134`、`dark 2021→2416 变化 3023 宽 64→134`（runner 1x）；floor `judged=5/5 executed=76 not-run=-`、`MOTION_FLOOR_OK=5/5`、`REDS=0`、`SUITE_CLEAN=0`、无 unlisted；CI 滚动 4/4 passed（`CHANNEL 0→73→600 变化=21138/32400 重抓=no`、`TIME 5 采样/2 中间值/末 1430`）。本地全量 **1132/57/5**：5 个断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑 **4/4 passed**（`0→88→600`、变化 88818/134400、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 226/131/4/0；帧基线 226/0/0/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 423 轮（R424" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R424 节")
if u"## Round 421 · R424" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 421")
if u"## D-420" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-420")
if u"Dock 图标状态补「未读剪辑」角标" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**450." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 450")
if state.count(u"## R423 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R423 状态"))
U_CELL_OLD = u"U-31 … U-1542（R423 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R423 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R423 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_420 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R423 状态", STATE_SECTION + u"## R423 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1547（R424 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R423 节 ②",
                                u"AGENT_STATE.md` 的 R424 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R424_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R424_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
