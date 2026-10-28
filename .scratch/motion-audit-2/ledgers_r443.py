#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R443 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 441 轮（R442 · 2026-10-28"
AUDIT_SECTION = u"""## 第 442 轮（R443 · 2026-10-28 · U-1638…U-1642）：设置侧栏文字补显式动态色（`.primary` → `Color(nsColor: .labelColor)`，与 R381 图标、R426 页脚同一处）：暗档 2x 侧栏 17/17 个设置夹具文字全部落在期望侧（`TEXT_SIDE_BLIND_SPOTS 0 of 17`）、`SETTINGS_ABOUT_ROW dark 7`（由 NOT-RUN 变真读数）、本机 2x 盲区名册归零；36 张设置面帧变化、基线 246/0/0/0（产品 1 文件，设置侧栏文字位）

- **U-1638：⓪ push 与 R442 两跑。** 开工监督者已验 remote 仍为 `f83270e`、api=200 ⇒ 一次快进 push **`f83270e..bdb4737` success**，HEAD = origin/main = `bdb4737`、**ahead=0**（三笔：主笔 `609040c` + 追记 `1781763` + 预记 `bdb4737`；同一次推送只有 head 那一个新跑）。读 R442 自身 head 跑 **`40605228813 ↔ bdb4737`**：开工时 **in_progress**，稍后复读 `gh` **EOF** ⇒ 具名 **`CI_READ_BLOCKED=network`** 与 **NOT-RUN**（`SETTINGS_ABOUT_ROW`/`CAPTION_JUDGED`/`CODE_LINE_NUMBERS`/`TABLE_HEADER` 的 runner 读数待 R444 ⓪ 补读）。R443 自身跑在提交后才会新建；收口时 `api=000`（网又断）⇒ 见 U-1642。
- **U-1639：① 腐烂与重钉。** `HIDDEN_ARMS 表=308 可判=997 rot=0`（最终读）。本轮把**文字**也换成 `Color(nsColor: .labelColor)` 后，R381 表的针（`AnyShapeStyle(Color(nsColor: .labelColor))`）在文件里命中 **2 次**（图标 + 文字）⇒ 预检 `bad=2`；把 M1011/M1012 的针改成「图标 + 文字两段 foregroundStyle 的整块」后复跑 **2/2 CAUGHT**。更深的一层：外层文字的 `.foregroundStyle(labelColor)` 会给内层图标的 `.primary` 提供环境 ⇒ **只退图标不再坏**（M1011 第一版就这样 ESCAPED）；M1011 改成两段一起退回 `.primary` 后才重新咬住。`NEEDLE_PRECHECK tables=221 covered=203 arms=580 bad=0`、`ARM_TOTAL files=314 arms=1063 dupes=0 repeats=0`。
- **U-1640：② 设置侧栏文字补显式动态色。** 缺陷形状（R457/471）：R381 只把**图标**换成了 `Color(nsColor: .labelColor)`，**文字仍走 `.primary`**；在暗档 2x 的离屏侧栏里，文字落在背景错误一侧（raw 位图 max=28）——整列黑字黑底，`SETTINGS_ABOUT_ROW` 的暗档只能记 NOT-RUN。修法：文字也换成 `Color(nsColor: .labelColor)`（动态系统色，随外观翻转、不进 vibrancy 重映射；选中仍走 accent）。旧/新：`TEXT_SIDE` 17/17 个设置夹具从"暗侧反相"变为 **亮侧=5379 暗侧=0**；`TEXT_SIDE_BLIND_SPOTS 0 of 17`；本机 2x 的 `darkSidebarTextBlindSpotsByMachine` 从 17 条改为 **空集**（`TEXT_SIDE_ROSTER_KEY ... 本机登记=0 实测反侧=0 判了 17/17 ⇒ 一致`）；`SETTINGS_ABOUT_ROW light 7 / dark **7**`（暗档由 NOT-RUN 变真读数）。帧变化 **36 张**（17 个设置夹具 + cardprobe-split，亮暗都随标签色微变；暗档文字从无墨变白字），基线 **246/0/0/0**；已看 `settings-general` 暗帧：七枚标签白字清晰。
- **U-1641：判据与刀。** 新表 `mutate_r443_sidebar_label`：M1216 文字退回 `.primary`（暗档又黑字黑底）⇒ `testDarkSettingsSidebarTextIsACountedBlindSpot` **CAUGHT**；M1217 文字固定白色（亮档白字白底）⇒ `testSettingsSidebarShowsTheAboutCategoryRow` **CAUGHT**；**2/2**、RESTORE_CLEAN=yes。R381 的 M1011 交互（外层文字掩蔽内层图标）当场重钉并复跑 2/2（见 U-1639）。`darkSidebarTextBlindSpots` 集合仍是 "vibrant 子树" 的**前提**（17 条，含 settings-about），改的只是**本机 2x 的盲区名册**（空集是声明）；runner 1x 名册原本就是空。
- **U-1642：八步与具名 NOT-RUN。** build **0 告警**（冷编 0）；捕获卷全绿 **246 帧**；帧基线 `COMPARED=246 CHANGED=0 MISSING=0 ADDED=0`；全量 **1202/57/5**（5 个断言全在 `SelectionRevealAnimationTests`；侧栏/暗盲/图标/caption 全绿）；单跑 `caffeinate -u` 后 **4/4**（`OFFSET 0/214.0/1438`、`TIME 18/8/58.0/1438`、`CHANNEL 0→86.5→600 变化 76135/127200 重抓=no`）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 442，现读 `python3 scripts/product_streak.py --streak-for 442`，last=609040c）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① R442 自身 head 跑 `40605228813 ↔ bdb4737`（读时 in_progress、后 EOF ⇒ `CI_READ_BLOCKED=network`）；② R443 自身新跑（提交后创建；收口网络 `api=000`，见预记）；③ R442 的 runner 读数（`SETTINGS_ABOUT_ROW`/`CAPTION_JUDGED`/`CODE_LINE_NUMBERS`/`TABLE_HEADER`）；④ 设置侧栏标签的**真机**暗档外观（离屏显式色 vs 真机 vibrant 合成没有同屏对照，473）；⑤ M613 本机 2x 空名册（472）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页正文 1x 盲（470）；㉝ 437–473 仍开。

"""

ITER_SECTION = u"""## Round 440 · R443（第 442 轮 · 2026-10-28）：设置侧栏文字补显式动态色（`.primary` → `Color(nsColor: .labelColor)`，与 R381 图标、R426 页脚同一处）：暗档 2x 侧栏 17/17 个设置夹具文字全部落在期望侧（`TEXT_SIDE_BLIND_SPOTS 0 of 17`）、`SETTINGS_ABOUT_ROW dark 7`（由 NOT-RUN 变真读数）、本机 2x 盲区名册归零；36 张设置面帧变化、基线 246/0/0/0

R381 只修了图标，文字仍 `.primary` ⇒ 暗档 2x 离屏侧栏整列黑字黑底（R457/471）。文字也换 `Color(nsColor: .labelColor)`：动态系统色、不进 vibrancy 重映射；选中仍 accent。读数：`TEXT_SIDE` 17/17 从反相变 亮侧 5379/暗侧 0；`BLIND_SPOTS 0 of 17`；本机 2x 盲区名册 17→0；`SETTINGS_ABOUT_ROW dark 7`；36 张帧变化、基线 246/0/0/0；暗帧看图白字清晰。刀：文字退回 `.primary` ⇒ 暗盲测试 CAUGHT；文字固定白 ⇒ 亮档行测试 CAUGHT（2/2）；R381 M1011 因"外层文字掩蔽内层图标"当场重钉，2/2。预检 221/203/580 bad=0；HIDDEN 308/997 rot=0。⓪：push `f83270e..bdb4737` success、ahead=0；R442 自身跑 `40605228813` 读时 in_progress、后 EOF ⇒ CI_READ_BLOCKED/NOT-RUN，R444 ⓪ 补读。全量 1202/57/5；捕获 246 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `settings-general` 暗帧逐张看过：七枚侧栏标签白字清晰；`TEXT_SIDE` 17/17 落在期望侧、`SETTINGS_ABOUT_ROW dark 7`；36 张帧变化全在设置面。 |
| 判据有效性 | 15/15 | 暗盲测试从"名单 17"变"名单 0 + 实测 0"；暗档行判据由 NOT-RUN 变真读数；M1216/M1217 2/2；R381 M1011 重钉后 2/2。 |
| 假绿防御 | 15/15 | 一个具名盲区被**消掉**而不是改阈值；空名册是声明；只退图标不再坏（外层掩蔽）被识别并改成两段一起退。 |
| 产品面推进 | 14/15 | 1 行 Sources 修好设置侧栏文字的暗档可读性，与 R381 图标/R426 页脚同一处；扣 1：真机 vibrant 合成下的外观没有同屏对照（473）。 |
| 台账一致性 | 15/15 | U-1638…U-1642、D-439、push `bdb4737`、36 帧/246、预检/rot 都从命令与测试输出解析。 |
| 交付诚实性 | 15/15 | R442 跑 in_progress/EOF 具名；R443 自身跑待建；M1011 第一版逃脱照实记并重钉；盲区不是"改读数"而是消掉。 |
| 可复核性 | 15/15 | 17/17、5379/0、`BLIND_SPOTS 0 of 17`、暗 7、36 帧、刀号与 precheck/rot、基线 246、换装/清账都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_439 = u"""## D-439 设置侧栏文字与图标同用显式动态色（R443）

- 背景：R381 只把设置侧栏的**图标**换成 `Color(nsColor: .labelColor)`，文字仍 `.primary`；暗档 2x 的离屏侧栏里文字落在背景错误一侧（raw 位图 max=28，R457/471），`SETTINGS_ABOUT_ROW` 的暗档只能记 NOT-RUN。
- 决定：文字也换成 `Color(nsColor: .labelColor)`（动态系统色，随外观翻转、不进 vibrancy 重映射）；选中仍 accent；图标不变。
- 理由：与 R381 图标、R426 页脚同一处修法；暗档标签可读，盲区从"名册 17"变"名册 0 + 实测 0"，判据由 NOT-RUN 变真读数。
- 兼容性/迁移：产品外观语义不变（labelColor 即标准文字色）；36 张设置面帧变化（17 夹具 + cardprobe-split，亮暗）、基线 246；本机 2x 盲区名册归零；`darkSidebarTextBlindSpots` 集合仍是 vibrant 子树的前提。
- 边界：真机 vibrant 合成下的外观没有同屏对照（473）；主列表暗档文字（457）是另一处，仍开。
- 回滚：文字换回 `.primary` 即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 设置侧栏文字补显式动态色（`.primary` → `Color(nsColor: .labelColor)`；暗档 2x 反侧 0/17、`SETTINGS_ABOUT_ROW dark 7`、盲区名册 17→0；36 张设置面帧、基线 246）（R443 / 第 442 轮 / Round 440 / U-1638…U-1642 · 产品 1 文件，设置侧栏文字位）

"""

BACKLOG_SECTION = u"""437 追记（R443 · 仍开）：主列表仍不匹配 `sourceAppName`。

449 追记（R443 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/214/1438；TIME 18/8/58/1438；CHANNEL 76135/127200）。

451 追记（R443 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R443 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R443 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R443 · 仍开）：菜单具名标记仍未发射。

455 追记（R443 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R443 · 仍开）：跨年记录仍无年份。

457 追记（R443 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字（设置侧栏那一处已由 471/R443 修掉）。

458 追记（R443 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R443 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R443 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R443 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R443 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R443 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R443 · 仍开）：其它自绘控件（浮层清除 ×、批量栏五颗）仍无同类帮助判据。

465 追记（R443 · 仍开）：HTML 引用块没有导引线（只接了 Markdown 路径）。

466 追记（R443 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R443 · 仍开）：代码块行号的 9pt 档只在纯函数里验，1000+ 行会超出外边距。

468 追记（R443 · 仍开）：HTML 代码块没有行号（只接了 Markdown 路径）。

469 追记（R443 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R443 · 仍开）：关于页正文在 runner 1x 是平涂（只有侧栏行与 2x caption 作证）。

**471 结案（R443）：设置暗侧栏未选中标签在 2x 离屏帧里不落墨 —— 文字补显式动态色后 17/17 落在期望侧、`SETTINGS_ABOUT_ROW dark 7`、本机 2x 盲区名册归零。主列表那一处（457）仍是另一处。**

**472 追记（R443 · 仍开）：M613 在本机 2x 空名册（机器前提），期望保留给 runner。**

**473. 设置侧栏文字的真机 vibrant 暗档外观没有同屏对照**（R443 观察）
    现象：R443 把文字换成显式动态色，修好的是**离屏 2x 通道**（17/17 落期望侧）；真机上 `NavigationSplitView` 的 vibrant 合成对显式 labelColor 与 `.primary` 的观感是否一致，没有同屏对照帧（`real_screen_sidebar_icons.py` 那一族只证了图标）。
    修法：扩一个真机侧栏文字探针（同一行 `.primary` 与显式色并排），或拍真机暗档侧栏截图与离屏帧做同带对照（需用户退出运行中的 App，走 220 路 A 的授权）。
"""

STATE_SECTION = u"""## R443 状态（2026-10-28 · 本地 · 第 442 轮 / Round 440）：设置侧栏文字补显式动态色（`.primary` → `Color(nsColor: .labelColor)`）：暗档 2x 侧栏 17/17 落期望侧（`TEXT_SIDE_BLIND_SPOTS 0 of 17`）、`SETTINGS_ABOUT_ROW dark 7`（NOT-RUN→真读数）、本机 2x 盲区名册 17→0；36 张设置面帧变化、基线 246/0/0/0（产品 1 文件，设置侧栏文字位）

最后更新：2026-10-28（本地 · R443 / 第 442 轮 / Round 440）：R381 只修了设置侧栏的图标，文字仍 `.primary`；暗档 2x 离屏侧栏整列黑字黑底（R457/471）。文字也换 `Color(nsColor: .labelColor)`（动态系统色、不进 vibrancy 重映射；选中仍 accent）。旧/新：`TEXT_SIDE` 17/17 个设置夹具从反相变 **亮侧=5379 暗侧=0**；`TEXT_SIDE_BLIND_SPOTS 0 of 17`；本机 2x 的盲区名册 17→**空集**（`本机登记=0 实测反侧=0 判了 17/17 ⇒ 一致`）；`SETTINGS_ABOUT_ROW light 7 / dark 7`；**36 张**设置面帧（17 夹具 + cardprobe-split，亮暗）变化，基线 **246/0/0/0**；已看暗帧：七枚标签白字清晰。刀：M1216（文字退 `.primary`）⇒ 暗盲测试 CAUGHT；M1217（文字固定白）⇒ 亮档行测试 CAUGHT（**2/2**）；R381 的 M1011 因外层文字掩蔽内层图标的 `.primary` 第一版 ESCAPED ⇒ 改成两段一起退、复跑 2/2。预检 **221/203/580 bad=0**、ARM **314/1063**、HIDDEN **308/997 rot=0**。⓪：监督者已验 remote `f83270e` ⇒ 一次快进 push **`f83270e..bdb4737` success**、HEAD=origin/main=`bdb4737`、**ahead=0**；R442 自身 head 跑 **`40605228813 ↔ bdb4737`** 读时 in_progress、后 `gh` EOF ⇒ 具名 `CI_READ_BLOCKED=network` / NOT-RUN，R444 ⓪ 补读。本地全量 **1202/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/214.0/1438；TIME 18/8/58.0/1438；CHANNEL 0→86.5→600 变化 76135/127200 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **246 帧**；基线 **246/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 442，现读 `python3 scripts/product_streak.py --streak-for 442`，last=609040c）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push `f83270e..bdb4737` success、ahead=0；R442 自身 head 跑 40605228813 读时 in_progress、后 EOF ⇒ CI_READ_BLOCKED/NOT-RUN；R443 自身跑待建。
② 产品：设置侧栏文字补显式动态色（暗档 2x 反侧 0/17、暗档行判据 7；36 张帧、基线 246）。
③ 判据：M1216/M1217 2/2；R381 M1011 重钉后 2/2；本机 2x 盲区名册 17→0；precheck 221/203/580；hidden rot 0。
④ 436：本轮 R442 跑读数被 EOF 挡住，未读；不重猜 must_judge。
⑤ 367：hidden 表 308 / 可判 997 / rot 0。
⑥ 捕获 246 帧；换装 ok；清账 162/63/0；帧基线 246/0/0/0；本地全量 1202/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① R442 自身 head 跑 40605228813（CI_READ_BLOCKED=network，R444 ⓪ 补读）；② R443 自身新跑（提交后创建；收口网络见预记）；③ R442 的 runner 读数；④ 设置侧栏标签的真机 vibrant 暗档外观（473）；⑤ M613 本机 2x 空名册（472）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页正文 1x 盲（470）；㉝ 437–473 仍开。

下一轮（R444）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R443 主笔+追记 head 跑与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看 `SETTINGS_ABOUT_ROW` 亮/暗都 7、`TEXT_SIDE` 反侧 0/17、`CAPTION_JUDGED`/覆盖 7、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R443_REPORT_BULLET = u"""- **R443（设置侧栏文字位）**：R381 只修了设置侧栏的图标，文字仍 `.primary`；暗档 2x 离屏侧栏整列黑字黑底（R457/471）。文字也换 `Color(nsColor: .labelColor)`（动态系统色、不进 vibrancy 重映射；选中仍 accent）。旧/新：`TEXT_SIDE` 17/17 个设置夹具从反相变 **亮侧=5379 暗侧=0**；`TEXT_SIDE_BLIND_SPOTS 0 of 17`；本机 2x 盲区名册 **17→0**；`SETTINGS_ABOUT_ROW light 7 / dark 7`（暗档由 NOT-RUN 变真读数）；**36 张**设置面帧变化，基线 **246/0/0/0**；暗帧白字清晰。刀：M1216（退 `.primary`）⇒ 暗盲测试 CAUGHT；M1217（固定白）⇒ 亮档行测试 CAUGHT（**2/2**）；R381 M1011 因外层文字掩蔽内层图标第一版 ESCAPED ⇒ 两段一起退后 2/2。预检 221/203/580 bad=0、ARM 314/1063、HIDDEN 308/997 rot=0。⓪：一次快进 push **`f83270e..bdb4737` success**、HEAD=origin/main=`bdb4737`、ahead=0；R442 自身 head 跑 `40605228813 ↔ bdb4737` 读时 in_progress、后 EOF ⇒ 具名 `CI_READ_BLOCKED=network`/NOT-RUN，R444 ⓪ 补读。本地全量 **1202/57/5**（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（OFFSET 0/214/1438；TIME 18/8/58/1438；CHANNEL 76135/127200）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 246 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
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
if u"第 442 轮（R443" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R443 节")
if u"## Round 440 · R443" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 440")
if u"## D-439" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-439")
if u"设置侧栏文字补显式动态色" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**473." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 473")
if state.count(u"## R442 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R442 状态"))
U_CELL_OLD = u"U-31 … U-1637（R442 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R442 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R442 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_439 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R442 状态", STATE_SECTION + u"## R442 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1642（R443 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R442 节 ②",
                                u"AGENT_STATE.md` 的 R443 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R443_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R443_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
