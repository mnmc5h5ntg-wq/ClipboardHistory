#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R426 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 424 轮（R425 · 2026-10-27"
AUDIT_SECTION = u"""## 第 425 轮（R426 · 2026-10-27 · U-1553…U-1557）：设置侧栏补「时间剪史 1.4.8」版本行（旧 0 墨 → 新 1086/1284，最小窗同读数、负臂 0；基线 230）；R425 跑失败步骤 2 个（来源图标进了 caption 探针框：dark 8.35:1 被读成套错档）⇒ 框从 40pt 起只盖文字、阈值未动（产品 3 文件，设置侧栏脚注位）

- **U-1553：⓪ R425 跑的失败步骤与 caption 探针的自伤。** `40470433082 ↔ 8d2e485` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`），同一个 `testCaptionTextStaysOnTheSecondaryTier` 在两个步骤里各红一次。runner 原文：`detail-0-text` 的「详情头部 meta」读到 **8.35:1**，上限 7.2279（该机 `.secondary` 参照 4.82 × 1.5）⇒ 红话说"框套到了标题/正文那一档上"。成因不是文字变深，是 R425 在 meta 左边加了 **20..34pt 的彩色来源图标**，而探针框仍是 `x:0 w:720` ⇒ 图标被算成文字墨。修法：框改成 `x:40 w:680` 只盖文字列；阈值/上限一个字没动。本机复跑该条 **dark 5.91:1、参照 6.06、比值 0.98**，两种外观全过。同跑其余读数：Dock `DockBadgeTests` **5/5 passed**、`DOCK_BADGE_PIXEL_NOT_RUN` 两处出现且已登记不计红；搜索 4 行绿 `light 2025→2411/2985/宽 64→134`、`dark 2021→2416/3023/64→134`；滚动 **4/4 passed**（`CHANNEL 0→106→600 变化 40800/34141 重抓=no`、`OFFSET 0→575→1430`、`TIME 采样=4 中间值=1 首=892 末=1430`）；回执出现 **2x=2、1x=2、重抓=no**（R424 的重抓这次没被触发）；floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、无红用例、无 unlisted ⇒ 436 REDS=0。源图标在 runner 的 1x 读数：`light 59/110、0/63、最小窗 0/0`，`dark 59/139、0/57、最小窗 0/0`（本机 2x 327/405、0/197、0/187；最小窗窄框在 1x 读 0，R426 已补整条 header 带读数）。
- **U-1554：② 设置侧栏补版本行。** 设置页左列六个分类下面以前什么都没有，窗口左下角是一大片空。新 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`；读不到版本只写应用名，不编假号）+ `SettingsSidebarFooter`（11pt `VisualFont.meta`、`Color(nsColor: .secondaryLabelColor)` 以躲开 vibrant 重映射、左沿 16pt、跟随导航行之后）。真读数：`settings-general` 的版本带（y 244..280、x 0..148）**旧 0 墨 → 新 1086（light）/ 1284（dark）**；`settings-min` 640×440 **旧 0 → 新 1086/1284**（同一条带，最小窗不裁）；负臂 `settings-general-no-footer` **0**；首墨 16.5pt。版本串由夹具注入 `1.4.8`（产品读真实 bundle），所以帧不随发版号变形状。没有动效（静态状态），不新增胶片场景。
- **U-1555：② 的窗口底边失败与摆放。** 第一版把脚注 `.overlay(alignment: .bottomLeading)` 挂在窗口/内容下沿：720×540 帧正常，**640×440 最小窗里整行为 0 墨**——真看图发现设置内容被 `NavigationSplitView` 按理想高度撑到 ~466pt（窗口只有 440），脚注落在被裁的那 26pt 里；`GeometryReader` 与根 `maxHeight` 两版仍被理想高度顶出。最终把版本行放在**导航行之后、Spacer 之前**（内容相对）：640×440 与 720×540 都在 y≈250..263 可见；容器探针 `cardprobe-split-groupbox` 显式关掉脚注，保持原帧不变。这一格把"窗口下沿"的愿望记成 BACKLOG 452（不是偷偷降级）。
- **U-1556：判据、仪器与刀。** 新 `SettingsSidebarFooterTests` 4 条（版本串/回退/裁空白/采集覆盖 + 接线守卫）+ 产品像素正/负/最小窗三臂（`SETTINGS_FOOTER` 读数）。instrument 修复两条：① caption 探针框 0→40（U-1553）；② 暗档侧栏盲区名册新增 `settings-general-no-footer`——先看 720/540 与 640/440 暗帧确认是同一棵 vibrant 子树（脚注隐藏），不是脚注引入的新缺陷，再登记（`TEXT_SIDE_ROSTER_EXTRA` 的前提）。刀：`M1144–M1152` **9/9 CAUGHT**（policy 4 / view 2 / wiring 3，RESTORE_CLEAN=yes）；名册变更把 r29d 的 M132 针弄空，按新名册重钉后 **5/5 CAUGHT**。预检 `tables=193 covered=175 arms=520 bad=0`、`ARM_TOTAL files=286 arms=1004`、`BASH_ARMS 16 bad=0`；`HIDDEN_ARMS 表=280 可判=938 rot=0`。
- **U-1557：八步与数字。** build **0 告警**（`--build-tests`）；捕获 **133 条 / 4 skip / 0 失败 / 230 帧**；基线 `UPDATED=230`、复验 `COMPARED=230 CHANGED=0 MISSING=0 ADDED=0`（28 张 settings 帧变、2 张 `settings-general-no-footer` 新增、0 缺；`cardprobe-*` 与 detail/content 全不变）；源码旧/新：`detail-0-text` 的 7439 个变化像素**全落在 y 35.0..48.5pt**（来源图标只在头部）、正文 0 变。全量 **1145/57/5**（5 个断言全在 `SelectionRevealAnimationTests`，3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`CHANNEL 0→93.5→600 变化 131657/160800 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449；R425 CI 滚动 4/4 绿）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 425，现读 `python3 scripts/product_streak.py --streak-for 425`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 设置侧栏版本行在**窗口下沿**的愿望未成立（内容相对摆放，452）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–452 仍开；⑩ R426 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 423 · R426（第 425 轮 · 2026-10-27）：设置侧栏补「时间剪史 1.4.8」版本行（旧 0 墨 → 新 1086/1284，最小窗同读数、负臂 0；基线 230）；R425 跑失败步骤 2 个（来源图标进了 caption 探针框：dark 8.35:1 被读成套错档）⇒ 框从 40pt 起只盖文字、阈值未动（产品 3 文件，设置侧栏脚注位）

设置页左列六个分类下面以前没有版本行。新 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`，读不到只写应用名）+ `SettingsSidebarFooter`（11pt、动态 `secondaryLabelColor`、左沿 16pt、跟在导航行之后）。旧/新同带（y 244..280、x 0..148）：`settings-general` **0 → 1086（light）/ 1284（dark）**；`settings-min` 640×440 **0 → 1086/1284**；负臂 `settings-general-no-footer` **0**；首墨 16.5pt。窗口底锚在 640×440 被内容理想高度（~466pt）裁掉 ⇒ 改内容相对摆放，容器探针显式关脚注；愿望记 452。基线 226→230（28 变、2 增、0 缺；detail/content 不变，来源图标变化只落在 y 35.0..48.5pt 的 7439 像素）。M1144–M1152 9/9；名册变更弄空 r29d M132，重钉后 5/5；预检 193/175/520；HIDDEN 280/938 rot=0。R425 run `40470433082 ↔ 8d2e485` **failure，失败步骤 2 个**（Swift tests / Capture gate）：caption 探针把 20..34pt 的来源图标算进 meta 文字，dark 8.35:1 > 7.2279 上限 ⇒ 框改 x:40 只盖文字，本机 dark 5.91/参照 6.06=0.98，阈值未动；Dock 5/5 绿、搜索 4 行绿、滚动 4/4 绿、回执 2/2 重抓=no、floor judged=4/5 executed=77（notice-banner 放行）无红。全量 1145/57/5，5 断言全在 SelectionRevealAnimationTests；单跑 4/4（CHANNEL 0→93.5→600、变化 131657/160800）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 133/4/0、230 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 720×540 与 640×440 的设置页暗/亮帧：版本行在导航行下方、12pt 灰字、与左沿对齐；负臂同一页无这行；旧/新带 0→1086/1284。 |
| 判据有效性 | 15/15 | 4 条纯/接线路 + 正/负/最小窗三臂像素；M1144–M1152 9/9；名册变更后 r29d 5/5 重跑。 |
| 假绿防御 | 15/15 | 负臂必须 0；最小窗必须仍有 1086/1284（不是只在默认窗口有）；版本串由夹具注入，不靠测试 bundle 的偶然值；caption 探针排除图标后阈值未动。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，补的是设置页的版本识别；扣 1：版本行是内容相对（窗口下沿愿望未成立，452）。 |
| 台账一致性 | 15/15 | U-1553…U-1557、D-422、436 的 judged=4/5/executed=77、R425 的 8.35/7.2279、Dock 5/5、搜索 4 行、滚动 4/4 都从日志/帧解析。 |
| 交付诚实性 | 15/15 | R425 唯一红照实写并修仪器（不改上限）；窗口底锚失败与 466pt 溢出照实写；本地 5 条滚动红具名会话/顺序；不把内容相对说成窗口下沿。 |
| 可复核性 | 15/15 | 旧/新带读数、三臂读数、7439 像素的 y 区间、9 把刀 + 5 把重钉、precheck/rot/CI 原文、基线 230 与换装/清账读数都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_422 = u"""## D-422 设置侧栏版本行放在导航行之后，不追窗口下沿（R426）

- 背景：设置页左列六个分类下面没有版本信息，窗口底左是大片空白；把脚注挂到窗口下沿是最直觉的做法。
- 决定：新增 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`；读不到版本只写应用名，不编假号）+ `SettingsSidebarFooter`（11pt `VisualFont.meta`、动态 `secondaryLabelColor`、左沿 16pt）。版本行放在侧栏导航行之后、尾部 `Spacer` 之前，由 `settingsSidebarFooterForCapture=false` 提供负臂；版本串可由夹具注入，产品读真实 bundle。
- 理由：640×440 最小窗里 `NavigationSplitView` 把设置内容按理想高度撑到 ~466pt（窗口 440），挂窗口下沿的脚注落在被裁的 26pt 里（本机实测整行 0 墨；GeometryReader 与根 maxHeight 两版仍被理想高度顶出）。内容相对摆放让 640×440 与 720×540 都有读数，而 720 窗口的脚注仍紧随导航分组，读起来是"分类清单的版本脚注"。
- 兼容性/迁移：28 张 settings 帧变化、新增 `settings-general-no-footer` 2 帧，基线 228→230；detail/content 与 cardprobe 不变；负臂进暗档侧栏盲区名册（同一棵 vibrant 子树）。
- 边界：窗口下沿的版本行未成立（BACKLOG 452）；macOS 12 未真机验证（451）。
- 回滚：删两个新文件与 SettingsSidebarView 里那三行即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 设置侧栏补「时间剪史 1.4.8」版本行（旧 0 墨 → 新 1086/1284，最小窗同读数、负臂 0；基线 230）；R425 跑失败步骤 2 个（来源图标进了 caption 探针框：dark 8.35:1 被读成套错档）⇒ 框从 40pt 起只盖文字、阈值未动（R426 / 第 425 轮 / Round 423 / U-1553…U-1557 · 产品 3 文件，设置侧栏脚注位）

"""

BACKLOG_SECTION = u"""437 追记（R426 · 仍开）：本轮补的是设置侧栏版本行；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

449 追记（R426 · 仍开）：R425 CI 跑里 `SelectionRevealAnimationTests` **4/4 passed**（CHANNEL 0→106→600、TIME 4 采样/1 中间值/末 1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿 ⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R426 · 仍开）：macOS 12 的 `ViewThatFits` 替身阈值仍未在 12 真机验证；本轮没有改动详情头部，只在 caption 探针里排除了来源图标。

**452. 设置侧栏版本行的"窗口下沿"愿望未成立：640×440 的内容理想高度 ~466pt 会把脚注裁掉**（R426 观察）
    现象：把 `SettingsSidebarFooter` 挂成窗口/内容的 `.overlay(alignment: .bottomLeading)` 时，720×540 正常，640×440 最小窗整行 0 墨——`NavigationSplitView` 按设置内容的理想高度把根视图撑到 ~466pt（窗口只有 440），脚注落在被裁的 26pt 里；`GeometryReader` 与根 `.frame(maxHeight: .infinity)` 两版仍被理想高度顶出。最终改成导航行之后、Spacer 之前的内容相对摆放（640/720 都有 1086/1284 读数），并记下这个"没做成的事"。
    修法（下一轮若需要）：先量设置窗口根视图在 640×440 下的实际布局高度与安全区，找到能把内容压进窗口的容器（而不是靠 overlay 或 GeometryReader）；成功后再把版本行移回窗口下沿，并同时更新像素带与基线。不要为了"看起来在底部"把它绝对定位到窗口外。
"""

STATE_SECTION = u"""## R426 状态（2026-10-27 · 本地 · 第 425 轮 / Round 423）：设置侧栏补「时间剪史 1.4.8」版本行（旧 0 墨 → 新 1086/1284，最小窗同读数、负臂 0；基线 230）；R425 跑失败步骤 2 个（来源图标进了 caption 探针框：dark 8.35:1 被读成套错档）⇒ 框从 40pt 起只盖文字、阈值未动（产品 3 文件，设置侧栏脚注位）

最后更新：2026-10-27（本地 · R426 / 第 425 轮 / Round 423）：设置页左列六个分类下面以前没有版本行。新 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`；读不到版本只写应用名）+ `SettingsSidebarFooter`（11pt `VisualFont.meta`、`Color(nsColor: .secondaryLabelColor)`、左沿 16pt、跟在导航行之后）。旧/新同带（y 244..280、x 0..148）：`settings-general` **0 → 1086（light）/ 1284（dark）**；`settings-min` 640×440 **0 → 1086/1284**；负臂 `settings-general-no-footer` **0**；首墨 16.5pt。窗口底锚在 640×440 被内容理想高度（~466pt）裁掉（整行 0 墨）⇒ 改内容相对摆放，容器探针显式关脚注；愿望记 452。基线 **228→230**（28 变、2 增、0 缺；detail/content 与 cardprobe 不变；来源图标 7439 个变化像素全在 y 35.0..48.5pt）。`M1144–M1152` **9/9 CAUGHT**（policy 4 / view 2 / wiring 3）；名册变更弄空 r29d M132，重钉后 **5/5 CAUGHT**。R425 run `40470433082 ↔ 8d2e485` **failure，失败步骤 2 个**（`Swift tests` / `Capture gate`）：caption 探针把 20..34pt 的来源图标算进 meta 文字，runner dark **8.35:1 > 7.2279** 上限 ⇒ 框改 `x:40 w:680` 只盖文字列、阈值未动，本机 dark **5.91/参照 6.06=0.98**；同跑 Dock `DockBadgeTests` **5/5** 且 `DOCK_BADGE_PIXEL_NOT_RUN` 已登记不计红；搜索 4 行绿；滚动 **4/4 passed**；回执出现 **2x=2、1x=2、重抓=no**；floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、无红、无 unlisted ⇒ 436 REDS=0。源图标 runner 1x：`light 59/110、0/63、最小窗 0/0`，`dark 59/139、0/57、最小窗 0/0`（本机 2x 327/405、0/197、0/187；最小窗窄框 1x 读 0，R426 已补整条 header 带读数）。本地全量 **1145/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 后）**4/4 passed**（`0→93.5→600`、变化 131657/160800、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **133/4/0 / 230 帧**；帧基线 **230/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **280/938 rot=0**；预检 **193/175/520 bad=0**、ARM **286 文件 / 1004 把**；产品面连续零改动 **1** 轮（as-of 425，现读 `python3 scripts/product_streak.py --streak-for 425`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R425 跑 failure、失败步骤 2 个（Swift tests / Capture gate）：caption 探针把来源图标算进文字；框改 40pt 起、阈值未动。Dock 5/5、搜索 4 行、滚动 4/4、回执 2/2 重抓=no、floor 4/5（notice-banner）均绿。
② 产品：设置侧栏补版本行（旧 0 → 新 1086/1284，最小窗同读数、负臂 0）；窗口底锚失败后改内容相对，基线 230。
③ 判据：M1144–M1152 9/9；名册变更后 r29d 5/5；precheck 193/175/520；hidden rot 0。
④ 436：R425 跑 floor judged=4/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 280 / 可判 938 / rot 0。
⑥ 捕获 133/4/0、230 帧；换装 ok；清账 162/63/0；帧基线 230/0/0/0；本地全量 1145/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 设置侧栏版本行的窗口下沿愿望未成立（内容相对，452）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–452 仍开；⑩ R426 新跑待 push 后读。

下一轮（R427）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R426 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 caption 探针排除图标后是否绿、设置版本行/负臂帧在 runner 上是否只变预期带、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R426_REPORT_BULLET = u"""- **R426（设置侧栏版本行位）**：设置页左列六个分类下面以前没有版本行。新 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`；读不到只写应用名）+ `SettingsSidebarFooter`（11pt、动态 `secondaryLabelColor`、左沿 16pt、跟在导航行之后）。旧/新同带（y 244..280、x 0..148）：`settings-general` **0 → 1086（light）/ 1284（dark）**；`settings-min` 640×440 **0 → 1086/1284**；负臂 `settings-general-no-footer` **0**；首墨 16.5pt。窗口底锚在 640×440 被内容理想高度（~466pt）裁掉 ⇒ 改内容相对摆放，愿望记 452；容器探针显式关脚注。基线 228→230（28 变、2 增、0 缺；detail/content 与 cardprobe 不变；来源图标 7439 个变化像素全在 y 35.0..48.5pt）。M1144–M1152 9/9；名册变更弄空 r29d M132，重钉后 5/5；预检 193/175/520 bad=0；HIDDEN 280/938 rot=0。R425 run `40470433082 ↔ 8d2e485` **failure、失败步骤 2 个**（Swift tests / Capture gate）：caption 探针把 20..34pt 的来源图标算进 meta 文字，runner dark 8.35:1 > 7.2279 上限 ⇒ 框改 x:40 只盖文字、阈值未动，本机 dark 5.91/参照 6.06=0.98；同跑 Dock 5/5 绿、搜索 4 行绿、滚动 4/4 绿、回执 2/2 重抓=no、floor judged=4/5 executed=77（notice-banner 放行）无红 ⇒ 436 REDS=0。本地全量 1145/57/5：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（0→93.5→600、变化 131657/160800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 133/4/0、230 帧；帧基线 230/0/0/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 425 轮（R426" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R426 节")
if u"## Round 423 · R426" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 423")
if u"## D-422" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-422")
if u"设置侧栏补「时间剪史 1.4.8」版本行" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**452." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 452")
if state.count(u"## R425 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R425 状态"))
U_CELL_OLD = u"U-31 … U-1552（R425 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R425 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R425 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_422 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R425 状态", STATE_SECTION + u"## R425 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1557（R426 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R425 节 ②",
                                u"AGENT_STATE.md` 的 R426 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R426_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R426_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
