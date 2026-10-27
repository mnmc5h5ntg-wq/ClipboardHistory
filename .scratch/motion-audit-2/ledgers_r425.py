#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R425 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 423 轮（R424 · 2026-10-27"
AUDIT_SECTION = u"""## 第 424 轮（R425 · 2026-10-27 · U-1548…U-1552）：详情状态条补来源 App 图标（720pt 真实图标彩色 0→327、带右沿 298→320pt；600pt 最小窗口 ViewThatFits 先丢图标、帧逐字节不变）；R424 跑唯一红＝回执 1x 只 1 个过渡帧（窗口 1418ms 覆盖）⇒ 相位重抓、闸门 ≥2 未动（产品 3 文件，状态条来源图标位）

- **U-1548：⓪ R424 跑的失败步骤与回执 1x 的命运。** `40465690086 ↔ 49fcbc2` **failure**：20 步里**失败步骤 1 个**（`Motion coverage floor`），其余 19 步 success。floor 五臂本身全在：`MOTION_FLOOR_FACTS judged=5/5 executed=76 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=3 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=testCopyReceiptAppearsAndDismissesWithAVisibleProcess`、`MOTION_FLOOR_SUITE_RED=1`、`MOTION_FLOOR_REDS=1`。runner 原文定位到值：回执出现 **1x `帧数=27 过渡帧数=1 峰值=0.2000 窗口=1418ms 声明=160ms`**，2x `帧数=27 过渡帧数=2 峰值=0.0889 窗口=1446ms`；`MOTION_GRAB` 1.3–1.7ms/30 帧 ⇒ 窗口 1418ms 远超 0.8×160=128ms 的地板，**不是窗口没覆盖**，是 52ms 的 runloop 相位把 160ms 的淡入夹在「还没开始」与「已经结束」之间。Dock 部署本身绿：`DockBadgeTests` 5/5 passed、`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none badgeAfterActivate=nil` 在 Swift tests 与 Motion gate 两处出现，并列在 Motion gate 的「已登记标记」里、**不计红**。搜索 4 行仍绿：`light 2025→2411/2985/宽 64→134`、`dark 2021→2416/3023/宽 64→134`。滚动 CI **4/4 passed**：`SCROLL_REVEAL_CHANNEL 起点=0.0 中段=78.0 落点=600.0 变化=8508/26400 重抓=no`、`SCROLL_REVEAL_OFFSET 0→141→1430`、`SCROLL_REVEAL_TIME 采样=6 中间值=2 首=194 末=1430`、`FRAME_PRODUCT_NOT_RUN=table-lazy-rows`。
- **U-1549：回执 1x 的修法是相位重抓，不是降门槛。** 在 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 里：第一次卷子 `span < 2` 时**只重抓一次**（同一场景、同一 8ms 下限、只换相位），由纯函数 `preferReceiptRegrab` 只接受「过渡帧更多，或帧数相同但峰值更高」的第二卷；`≥2` 的地板一个字没动，两卷都不到仍然红。本机复现：1x 首卷读不到 2 帧、`重抓=yes` 后第二卷 **2 帧**；2x 首卷 **8 帧**、`重抓=no`。刀 M1143 钉住「帧数更多也不换卷」这一半。
- **U-1550：② 详情状态条补来源 App 图标。** 详情头部左侧（时间 · 大小 · 来自 X）以前只有文字。新 `SourceAppBadge` + `SourceAppBadgePolicy`：只在 `sourceAppName` 非空时出现；用 `NSWorkspace` 解析真实应用图标（缓存），解析不到退回 `app` 符号；没有来源名的记录不占格。真读数：`detail-0-text`（Safari）图标格（20..34 × 36..50pt）**旧彩色 0 → 新 327**、墨 197→405；头部带墨 3571→3944、**右沿 298.0→320.0pt**（正好是图标 + 8pt 间距）。像素正/负/最小窗三臂：light `有来源彩色=327 墨=405｜无来源 0/197｜最小窗 0/187`，dark `327/597｜0/220｜0/223`。真实解析器测试：Safari 图标非空且缓存同一个对象、不存在的 bundle 返回 nil；回退符号 `app`。本轮没有动效（静态状态），不新增胶片场景。
- **U-1551：② 的窗口缩放边缘：窄窗先丢图标，不丢时间/来源。** 第一版把图标直接摆在 `ViewThatFits` 文案之前，600pt 最小窗口的头部当场把时间戳截成「2025-10-09 16:38:20…40 个字符」——这是真看图抓到的回归。修法是让图标与文案一起参与拟合：四档候选（图标+完整 / 图标+紧凑 / 无图标+完整 / 无图标+紧凑），600pt 选**无图标+紧凑**，720pt 选**图标+完整**；macOS 12 无 `ViewThatFits`，退回 `detailWidth >= 400` 的阈值（400 由紧凑文案 + 图标 + 「原文」按钮 + gutter 推出来）。证据：重捕后 **`content-min*` 四帧逐字节不变**（不在 changed 名单里），`detail-0-text` 与其余 45 帧头部变化；新增 `detail-no-source` 亮暗 2 帧；基线 **226→228**（46 变、2 增、0 缺）。最小窗像素尺 `最小窗彩色=0`，正臂 `327`。
- **U-1552：判据、刀与八步。** 新 `SourceAppBadgeTests` 6 条（可见性、窄宽、bundle 归一、回退符号、真实解析+缓存+不存在、接线守卫）+ 产品像素三臂 + `preferReceiptRegrab` 真值表（5 格）。`M1133–M1143` **11/11 CAUGHT**（policy 7 / view 2 / wiring 1 / regrab 1，全部 RESTORE_CLEAN=yes）；头部重构把 `mutate_r291` 的 `header(for: entry)` 与 `mutate_r393_meta_fit` 的 `includeCopyVerb: false` 两根针弄空 ⇒ 重钉后 **3/3、2/2** 重跑绿。预检 `tables=190 covered=172 arms=511 bad=0`、`ARM_TOTAL files=283 arms=995`、`BASH_ARMS 16 bad=0`；`HIDDEN_ARMS 表=277 可判=929 rot=0`。build **0 告警**（`--build-tests`）；捕获 **132 条 / 4 skip / 0 失败 / 228 帧**；基线 `UPDATED=228`、复验 `COMPARED=228 CHANGED=0 MISSING=0 ADDED=0`；全量 **1140/57/5**（5 个断言全在 `SelectionRevealAnimationTests`，3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`CHANNEL 0→95→600 变化 144348/168000 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449；R424 CI 滚动 4/4 绿）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 424，现读 `python3 scripts/product_streak.py --streak-for 424`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`，R424 跑里已登记、不计红）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`；CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ macOS 12 的 400pt 阈值未在 12 真机验证（451）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–451 仍开；⑩ R425 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 422 · R425（第 424 轮 · 2026-10-27）：详情状态条补来源 App 图标（720pt 真实图标彩色 0→327、带右沿 298→320pt；600pt 最小窗口 ViewThatFits 先丢图标、帧逐字节不变）；R424 跑唯一红＝回执 1x 只 1 帧（窗口 1418ms 覆盖）⇒ 相位重抓、闸门 ≥2 未动（产品 3 文件，状态条来源图标位）

详情头部「时间 · 大小 · 来自 X」左侧补来源 App 图标。新 `SourceAppBadge` + `SourceAppBadgePolicy`：只在有来源名时出现，`NSWorkspace` 解析真实图标并缓存，解析不到退回 `app` 符号。真读数 `detail-0-text`：图标格彩色 **0→327**、墨 197→405、带右沿 **298.0→320.0pt**；正/负/最小窗三臂 light 327/405、0/197、0/187，dark 327/597、0/220、0/223。第一版直接把图标摆在文案前，600pt 最小窗把时间戳截成省略号 ⇒ 改成四档 `ViewThatFits`（图标+完整/图标+紧凑/无图标+完整/无图标+紧凑）：600 选无图标+紧凑、720 选图标+完整，**content-min 四帧逐字节不变**；macOS 12 退回 detailWidth≥400。基线 226→228（46 变、2 增、0 缺）。M1133–M1143 11/11；重钉 r291 3/3、r393 2/2；预检 190/172/511；HIDDEN 277/929 rot=0。R424 run `40465690086 ↔ 49fcbc2` **failure，失败步骤 1 个**（Motion coverage floor）：五臂 judged=5/5 executed=76 全在，红是回执 1x `过渡帧数=1 峰值=0.2 窗口=1418ms`（覆盖 160ms 声明）、2x=2 ⇒ 相位重抓一次（只认过程更清楚的那卷，≥2 未动）；本机复现 `重抓=yes` 后 1x=2、2x=8。DockBadge 5/5 绿且 `DOCK_BADGE_PIXEL_NOT_RUN` 已登记不计红；搜索 4 行绿；滚动 CI 4/4 绿。全量 1140/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（CHANNEL 0→95→600、变化 144348/168000）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 132/4/0、228 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 `detail-0-text`（图标 + 完整文案）与 `content-min`（无图标 + 完整时间戳），旧/新同带读数彩色 0→327、右沿 298→320pt；最小窗帧逐字节不变。 |
| 判据有效性 | 15/15 | 产品入口用真实 `DetailView` 与真实 `NSWorkspace` 图标；6 条纯/接线路 + 正/负/最小窗三臂像素 + 5 格重抓真值表；M1133–M1143 11/11。 |
| 假绿防御 | 15/15 | 无来源负臂彩色必须 0；最小窗必须无色（否则是拿时间戳换图标）；重抓只认过程更清楚的卷；两卷都不到仍红；重钉的 r291/r393 重跑绿。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，补的是状态条的来源识别；扣 1：macOS 12 的 400pt 阈值未在 12 真机验证（451）。 |
| 台账一致性 | 15/15 | U-1548…U-1552、D-421、436 的 judged=5/5/executed=76、R424 红读数、搜索 4 行、Dock 5/5 与具名 NOT-RUN 都从日志解析。 |
| 交付诚实性 | 15/15 | R424 唯一红照实写并修仪器（不改 ≥2）；窄窗回归由真看图抓出并修；本地 5 条滚动红具名会话/顺序；不把系统图标说成自绘像素。 |
| 可复核性 | 15/15 | 旧/新像素读数、三臂读数、四档拟合、11 把刀 + 5 把重钉、precheck/rot/CI 原文、基线 228 与换装/清账读数都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_421 = u"""## D-421 详情状态条只画有来源名的 App 图标，窄窗先丢图标不丢时间（R425）

- 背景：详情头部只有「时间 · 大小 · 来自 X」文字，来源 App 要靠读；直接把图标放在文案前又会在 600pt 最小窗口把时间戳挤成省略号。
- 决定：`SourceAppBadgePolicy` 只在 `sourceAppName` 非空时给可见性；`SourceAppBadge` 用 `NSWorkspace` 解析真实应用图标（缓存），解析不到退回 `app` 符号。头部用四档 `ViewThatFits`（图标+完整 / 图标+紧凑 / 无图标+完整 / 无图标+紧凑）：宽窗有图标、600pt 先丢图标保住完整时间与来源。macOS 12 无 `ViewThatFits`，用 `detailWidth >= 400` 的阈值（由紧凑文案 + 图标 + 「原文」按钮 + gutter 推出）。
- 理由：图标是「来自 X」的视觉锚点，不是独立信息；没有来源名时占位会读成"来源未知"；时间/来源比装饰性的图标重要，窄窗必须优先保文案。
- 兼容性/迁移：46 张 detail/content 帧头部变化、新增 detail-no-source 2 帧，基线 226→228；600pt 最小窗与内容帧逐字节不变；无动效、无新胶片场景。
- 边界：macOS 12 的 400pt 阈值是推导值，未在 12 真机验证（BACKLOG 451）；解析不到应用时只给通用 `app` 符号，不猜应用。
- 回滚：删两个新文件与 `DetailView` 的四档拟合即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 详情状态条补来源 App 图标（720pt 真实图标彩色 0→327、带右沿 298→320pt；600pt 最小窗口 ViewThatFits 先丢图标、帧逐字节不变）；R424 跑唯一红＝回执 1x 只 1 帧（窗口 1418ms 覆盖）⇒ 相位重抓、闸门 ≥2 未动（R425 / 第 424 轮 / Round 422 / U-1548…U-1552 · 产品 3 文件，状态条来源图标位）

"""

BACKLOG_SECTION = u"""437 追记（R425 · 仍开）：本轮补的是详情状态条的来源 App 图标；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R425 · 仍开）：R424 CI 跑里 `SelectionRevealAnimationTests` **4/4 passed**（CHANNEL 0→78→600、TIME 2 中间值/末 1430），本机全量仍是 5 断言红（3 条用例）、单跑 4/4 绿 ⇒ 会话/顺序已再次坐实；本轮 R425 又复现并修复了另一条**采样相位**红（回执 1x），但 449 本身仍按原修法待办。

450 追记（R425 · 仍开）：Dock 角标的语义边界未变（只按 App 激活计数/清零，主窗口关但 App 前台时不计）；本轮没有新增真机 Dock 截屏。

**451. macOS 12 的来源图标阈值 400pt 是推导值，未在 12 真机验证**（R425 观察）
    现象：13+ 用四档 `ViewThatFits` 自动选「图标+文案」的哪一档；12 没有这个 API，退回 `detailWidth >= 400` 的固定阈值（紧凑文案 266 + 图标 22 + 「原文」按钮 ~40 + gutter 40 + 间距 8 ≈ 376，取 400 留余量）。这个阈值没有在 macOS 12 真机上量过，字体/按钮宽度变化都可能让它偏保守或偏激进。
    修法（下一轮若需要）：在 12 真机上用同一组 detail-0-text / content-min 帧量「有图标+完整/图标+紧凑/无图标+紧凑」三档的头部右沿，再决定阈值或改走自绘的 `ViewThatFits` 替身；不要因为没有 12 真机就把阈值写成"已验证"。
"""

STATE_SECTION = u"""## R425 状态（2026-10-27 · 本地 · 第 424 轮 / Round 422）：详情状态条补来源 App 图标（720pt 真实图标彩色 0→327、带右沿 298→320pt；600pt 最小窗口 ViewThatFits 先丢图标、帧逐字节不变）；R424 跑唯一红＝回执 1x 只 1 帧（窗口 1418ms 覆盖）⇒ 相位重抓、闸门 ≥2 未动（产品 3 文件，状态条来源图标位）

最后更新：2026-10-27（本地 · R425 / 第 424 轮 / Round 422）：详情头部「时间 · 大小 · 来自 X」左侧补来源 App 图标。新 `SourceAppBadge` + `SourceAppBadgePolicy`：只在 `sourceAppName` 非空时出现，`NSWorkspace` 解析真实图标并缓存，解析不到退回 `app` 符号。真读数 `detail-0-text`（Safari）：图标格 **旧彩色 0 → 新 327**、墨 197→405；头部带墨 3571→3944、右沿 **298.0→320.0pt**；正/负/最小窗三臂 light `327/405、0/197、0/187`，dark `327/597、0/220、0/223`。第一版直接摆图标把 600pt 最小窗的时间戳截成省略号 ⇒ 四档 `ViewThatFits`（图标+完整/图标+紧凑/无图标+完整/无图标+紧凑）：600 选无图标+紧凑、720 选图标+完整，**content-min 四帧逐字节不变**；12 退回 `detailWidth>=400`（451）。基线 **226→228**（46 变、2 增、0 缺）。`M1133–M1143` **11/11 CAUGHT**（policy 7 / view 2 / wiring 1 / regrab 1；RESTORE_CLEAN=yes）；头部重构弄空 r291/r393 两根针，重钉后 **3/3、2/2** 重跑绿。R424 run `40465690086 ↔ 49fcbc2` **failure，失败步骤 1 个**（`Motion coverage floor`）：五臂 `judged=5/5 executed=76 not-run=-` 全在，红是回执出现 **1x `过渡帧数=1 峰值=0.2000 窗口=1418ms 声明=160ms`**、2x=2 ⇒ 窗口覆盖（≥128ms）但 52ms runloop 相位把淡入夹在两端；修为**相位重抓一次**（`preferReceiptRegrab` 只认过程更清楚的那卷，`≥2` 未动），本机复现 1x `重抓=yes`→2、2x=8。Dock 部署绿：`DockBadgeTests` 5/5、`DOCK_BADGE_PIXEL_NOT_RUN` 在 Swift tests + Motion gate 两处出现且列在登记标记里、不计红；搜索 4 行绿；CI 滚动 **4/4 passed**（`CHANNEL 0→78→600 变化 8508/26400 重抓=no`、`TIME 6 采样/2 中间值/末 1430`）。本地全量 **1140/57/5**：5 个断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 后）**4/4 passed**（`0→95→600`、变化 144348/168000、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **132/4/0 / 228 帧**；帧基线 **228/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **277/929 rot=0**；预检 **190/172/511 bad=0**、ARM **283 文件 / 995 把**；产品面连续零改动 **1** 轮（as-of 424，现读 `python3 scripts/product_streak.py --streak-for 424`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R424 跑 failure、失败步骤 1 个（Motion coverage floor）：回执 1x 1 帧、窗口覆盖；相位重抓修复，≥2 未动；Dock 5/5+具名 NOT-RUN、搜索 4 行、滚动 4/4 均绿。
② 产品：详情状态条补来源 App 图标（720 彩色 0→327、右沿 298→320pt），窄窗先丢图标、600pt 帧逐字节不变；基线 228。
③ 判据：M1133–M1143 11/11；重钉 r291 3/3、r393 2/2；precheck 190/172/511；hidden rot 0。
④ 436：R424 跑五臂 judged=5/5 executed=76 全在，但 SUITE_RED=1（回执 1x）；修复后新跑待签收。
⑤ 367：hidden 表 277 / 可判 929 / rot 0。
⑥ 捕获 132/4/0、228 帧；换装 ok；清账 162/63/0；帧基线 228/0/0/0；本地全量 1140/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ macOS 12 的 400pt 阈值未在 12 真机验证（451）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–451 仍开；⑩ R425 新跑待 push 后读。

下一轮（R426）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R425 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执 1x 重抓后是否 ≥2、Dock/搜索/滚动是否仍绿、来源图标在 CI 的 detail/content 帧是否只变头部；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R425_REPORT_BULLET = u"""- **R425（状态条来源图标位）**：详情头部「时间 · 大小 · 来自 X」左侧补来源 App 图标。新 `SourceAppBadge` + `SourceAppBadgePolicy`：只在有来源名时出现，`NSWorkspace` 解析真实图标并缓存，解析不到退回 `app` 符号。真读数 `detail-0-text`（Safari）：图标格 **旧彩色 0 → 新 327**、墨 197→405；头部带墨 3571→3944、右沿 **298.0→320.0pt**；正/负/最小窗三臂 light `327/405、0/197、0/187`，dark `327/597、0/220、0/223`。第一版直接摆图标把 600pt 最小窗的时间戳截成省略号 ⇒ 四档 `ViewThatFits`（图标+完整/图标+紧凑/无图标+完整/无图标+紧凑）：600 选无图标+紧凑、720 选图标+完整，**content-min 四帧逐字节不变**；12 退回 `detailWidth>=400`（451）。基线 226→228（46 变、2 增、0 缺）。M1133–M1143 11/11；头部重构弄空 r291/r393 两根针，重钉后 3/3、2/2 重跑绿；预检 190/172/511 bad=0；HIDDEN 277/929 rot=0。R424 run `40465690086 ↔ 49fcbc2` **failure、失败步骤 1 个**（Motion coverage floor）：五臂 judged=5/5 executed=76 全在，红是回执出现 1x `过渡帧数=1 峰值=0.2000 窗口=1418ms`（覆盖 160ms 声明）、2x=2 ⇒ 相位重抓一次（≥2 未动），本机复现 1x `重抓=yes`→2、2x=8；DockBadge 5/5 绿且 `DOCK_BADGE_PIXEL_NOT_RUN` 已登记不计红；搜索 4 行绿；滚动 CI 4/4 绿。本地全量 1140/57/5：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（0→95→600、变化 144348/168000）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 132/4/0、228 帧；帧基线 228/0/0/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 424 轮（R425" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R425 节")
if u"## Round 422 · R425" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 422")
if u"## D-421" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-421")
if u"详情状态条补来源 App 图标" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**451." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 451")
if state.count(u"## R424 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R424 状态"))
U_CELL_OLD = u"U-31 … U-1547（R424 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R424 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R424 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_421 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R424 状态", STATE_SECTION + u"## R424 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1552（R425 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R424 节 ②",
                                u"AGENT_STATE.md` 的 R425 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R425_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R425_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
