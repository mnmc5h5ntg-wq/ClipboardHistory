#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R457 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


AUDIT_TITLE = u"## 第 455 轮（R456 · 2026-10-28"
AUDIT_SECTION = u"""## 第 456 轮（R457 · 2026-10-28 · U-1708…U-1712）：代码块制表位与 4 个空格同轴（旧 28.0/32.14、56.0/64.29、间隔 0/制表位 12 → 新 32.14/32.14、64.29/64.29、间隔 32.14/制表位 0；2 张新帧、基线 264→266）（产品 1 文件，代码块制表位）

- **U-1708：⓪ push 与 CI 读数。** 开工本地 ahead=0、HEAD=origin/main=`ca40810`；`git push origin main` 一次探针被拒（`Connection closed by 20.205.243.166 port 22`，no-op 也没发出去）⇒ **`PUSH_BLOCKED=network`（ahead=0、HEAD=`ca40810`）**；`gh run view 40664012233` 仍 **EOF** ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**（收口前再试一次）。沿用 R456 已读：`40653092761 ↔ d48bb05` **success**（`DEEMPHASIS_CONTRAST light 99/236/5.09、dark 177/50/5.98`；`TASK_DIM light 147.4/114.7 +32.7、dark 136.6/166.4 −29.8`；`STRIKE_DIM light 128.1/108.0 +20.1、dark 152.2/174.6 −22.3、隙 3/3`；`HISTORY_ROW_SOURCE light 139.0/74.0 差 65.0`、dark NOT-RUN；`WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat 轨=1`；`LIST_HANG_STYLE 16.0/16.0/0.0`；Motion `judged=5/5 not-run=-`）。`40645430259 ↔ 5c925a9` success；`40645469967 ↔ c041c8d` failure 只有 Motion receipt 1<2；`40640660665`/`40642482086`/`40642524490`/`40636558557` success；`40634880705 ↔ 9743379` 滚动会话采样红 + Motion 模式标签 1<2；`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810` 仍 NOT-RUN。436：**`MOTION_FLOOR_NOT_RUN=CI_READ_BLOCKED`**，不重猜 `must_judge`。
- **U-1709：① 腐烂与预检。** `HIDDEN_ARMS 表=322 可判=1027 rot=0`；`NEEDLE_PRECHECK tables=235 covered=217 arms=610 bad=0`、`ARM_TOTAL files=328 arms=1093`。本轮改 `paragraphStyle` 的共用分支，预检复跑确认没弄断旧针（R451 的列表制表位表仍命中）。
- **U-1710：② 代码块制表位。** 缺陷形状：代码块保留源码里的制表符，而 `paragraphStyle` 不碰代码块的制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt ⇒ 一个制表符比一级四空格缩进少 4.14pt、两级少 8.29pt，缩进不同的代码行排在不同竖轴上。修法：`paragraphStyle` 对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 字形推进`（32.14pt）；列表/表格分支不动。旧/新：`CODE_TAB_STOP light 制表符一级=28.00pt 四空格=32.14pt 差=−4.14pt｜二级=56.00/64.29 差=−8.29pt｜间隔=0.00 制表位=12` → `32.14/32.14 差=0.00｜64.29/64.29 差=0.00｜间隔=32.14 制表位=0`、dark 同形。**2 张新帧**（`detail-code-tabs` 亮/暗）、0 旧帧变化/缺失；基线 **264→266**（同 commit 更新）；已逐张看亮/暗：制表符段与四空格段的 `if`/`print` 落在同一条竖轴。
- **U-1711：判据与刀。** 新帧判据 `testCodeBlockTabsMatchFourSpaces` 从**产品渲染出来的 NSTextView**读布局（不是像素）：同一段代码里 `\\tif x {` 与 `    if x {` 的起始 x、`\\t\\tprint(1)` 与 `        print(1)` 的起始 x，并读该段的 `defaultTabInterval` / 显式制表位数。旧形态下四条断言全红（差 −4.14/−8.29、间隔 0、制表位 12）；新形态全绿。`M1251`（撤修复）/`M1252`（间隔改 2 个空格宽）/`M1253`（只设间隔不清默认制表位）⇒ **3/3 CAUGHT**、RESTORE_CLEAN=yes。
- **U-1712：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **266 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `266/0/0/0`；全量 **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**（卡在 `testSearchFieldIdealHeightIsStateIndependent`，日志 3.6M 行后同一行数分钟不动，已停；R456 完整卷 1260/56/0 之外本轮只拿到目标回归 **118 测试 / 2 skipped / 0 failures**，覆盖 Markdown/代码块/列表制表位/命中高亮/设置卡片节奏）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（版本 1.4.8）；`STORE-SIZE` 仍 1108/52/66；产品面连续零改动 **1** 轮（as-of 456，`python3 scripts/product_streak.py --streak-for 456`，last=643081c）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40664012233 ↔ d2a1e80`（CI_READ_BLOCKED）；② `40664181811 ↔ ca40810`（同上）；③ R457 自身跑（未创建）；④ 436 Motion floor（无新跑）；⑤ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；⑥ 纯文本文件预览的制表符仍是默认 28pt（490）；⑦ Markdown 表格单元格制表符（491）；⑧ 8 空格制表位源码仍会错（492）；⑨ 列表命中高亮的截断外/OCR（487）；⑩ 多文件第 2/3 个文件名命中（488）；⑪ 命中高亮选中底对比（489）；⑫ 弱化色选中态（485）；⑬ 行内码两侧标点无 padding（486）；⑭ HTML 的 `<del>`（484）；⑮ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑯ 设置内容列 1x 平涂；⑰ 设置脚注带 1x；⑱ 主窗口 content 帧 1x；⑲ 高夹具 1x；⑳ 13+ 菜单像素/标题；㉑ 真实拖拽；㉒ Dock 像素；㉓ 源图标最小窗文字 1x；㉔ 2x/extended；㉕ 固定块揭示偏移（455）；㉖ 跨年时间（456）；㉗ 主列表暗档文字盲区（457）；㉘ 真机/多屏（447）；㉙ 真菜单栏、12 实时腿；㉚ `table-lazy-rows`；㉛ HTML 六档字号（460）；㉜ 清除 × 命中区（461）；㉝ 分隔线令牌（462）；㉞ 展开态已加载内容无帧（463）；㉟ 其它自绘控件帮助文本（464）；㊱ HTML 引用块无导引线（465）；㊲ HTML 表格表头无同档（466）；㊳ 100+ 行行号（467）；㊴ HTML 代码块行号（468）；㊵ 行号选中/滚动两态（469）；㊶ 关于页 1x 盲（470）；㊷ M613 机器前提（472）；㊸ 真机 vibrant 暗档（473）；㊹ 长来源截断（474）；㊺ bundle ID 未搜（475）；㊻ 长首行标签省略无帧（476）；㊼ HTML 代码块无语言标签（477）；㊽ HTML `<hr>` 无通栏线（478）；㊾ HTML 表格体行无同一条线（479）；㊿ QuickPick 键盘提示 1x（480）；[51] HTML 任务列表无弱化（481）；[52] HTML 列表缩进（482）；[53] 中心刻度端点标签（483）；[54] HTML 的 `<del>`（484）；[55] 弱化色选中态（485）；[56] 行内码两侧标点无 padding（486）；[57] 437–492 的未结项仍开。

"""

ITER_SECTION = u"""## Round 454 · R457（第 456 轮 · 2026-10-28）：代码块制表位与 4 个空格同轴（旧 28.0/32.14、56.0/64.29、间隔 0 → 新 32.14/32.14、64.29/64.29、间隔 32.14；2 张新帧、基线 264→266）

代码块保留源码制表符，而 `paragraphStyle` 不碰代码块的制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt（一级差 4.14、两级差 8.29）。修复：对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 推进`。旧/新：`CODE_TAB_STOP light 28.00/32.14、56.00/64.29、间隔 0、制表位 12 → 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、dark 同形。2 张新帧（`detail-code-tabs` 亮/暗）、0 旧帧变化，基线 264→266/0/0/0；逐张看过两段缩进同轴。判据从渲染出的 NSTextView 读布局；旧形态四条全红；M1251–M1253 3/3；precheck 235/217/610、rot 322/1027=0。⓪ 网络不可达：push 探针被拒（ahead=0、HEAD ca40810）、gh EOF ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；436 无新跑具名。全量卡在 `testSearchFieldIdealHeightIsStateIndependent` ⇒ `FULL_SUITE_REREAD_NOT_RUN=load-hang`，目标回归 118/2/0；build 0 告警；换装 ok/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-code-tabs` 逐张看过：制表符段与四空格段的 `if`/`print` 同一条竖轴。 |
| 判据有效性 | 15/15 | 从产品渲染出的 NSTextView 读 4 个 x 与段样式；旧 28/32.14、新 32.14/32.14，差值 0。 |
| 假绿防御 | 14/15 | 旧形态先红留下旧读数；三把刀全 CAUGHT；扣 1：全量卷本轮挂起，只拿到目标回归 118/2/0。 |
| 产品面推进 | 15/15 | 代码块第一次把制表符与 4 空格对齐；只动 1 个 Sources 文件；Store 不动。 |
| 台账一致性 | 15/15 | U-1708…U-1712、D-453、266 帧、目标回归 118/2/0、间隔 32.14 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 断网、CI 读不到、436 无新跑、全量挂起全部具名；目标回归与完整卷分开写。 |
| 可复核性 | 15/15 | 28.00/32.14、56.00/64.29、间隔 0→32.14、制表位 12→0、刀号与 precheck 235/217/610、rot 322/1027、基线 266 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_453 = u"""## D-453 代码块制表符按 4 个空格定宽（R457）

- 背景：代码块保留源码制表符，`paragraphStyle` 不设代码块制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt（一级差 4.14、两级差 8.29）。
- 决定：对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 字形推进`；列表项/表格分支不动。
- 理由：缩进是代码的语义，制表符与 4 空格必须同轴；宽度由字体推进算出，不写死 32。
- 兼容性/迁移：新增 `detail-code-tabs` 亮/暗 2 张帧；旧帧 0 变化；基线 264→266 同 commit 更新。
- 边界：纯文本文件预览仍是 28pt（490）；Markdown 表格单元格（491）；8 空格制表位源码（492）。
- 回滚：删 `paragraphStyle` 里的 codeBlock 分支；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 代码块制表位与 4 个空格同轴（旧 28.0/32.14、56.0/64.29、间隔 0 → 新 32.14/32.14、64.29/64.29、间隔 32.14；2 张新帧、基线 264→266）（R457 / 第 456 轮 / Round 454 / U-1708…U-1712 · 产品 1 文件，代码块制表位）

"""

BACKLOG_SECTION = u"""**490. 纯文本文件预览里的制表符仍是默认 28pt**（R457 观察）
    现象：本轮只改 Markdown 代码块；`ChineseSelectableTextView` 的纯文本/日志预览还有同样的制表位问题。
    修法：把 4 空格制表位做成共享策略，纯文本预览也接上；补一条同形判据。

**491. Markdown 表格单元格里的制表符仍走默认制表位**（R457 观察）
    现象：`.table` 块沿用了 TextKit 默认 28pt；表格里的制表符会错位。
    修法：与代码块共用同一个制表位策略，或明确禁止表格里的制表符。

**492. 制表宽度固定为 4 个空格，读 8 空格制表位的源码会错位**（R457 观察）
    现象：产品选择 4 空格；一些项目按 8 空格制表位排版，同一段代码仍会不同轴。
    修法：如要做，给一个“制表宽度”设置并落成纯策略；当前不做，记边界。
"""

STATE_SECTION = u"""## R457 状态（2026-10-28 · 本地 · 第 456 轮 / Round 454）：代码块制表位与 4 个空格同轴（旧 28.0/32.14、56.0/64.29、间隔 0、制表位 12 → 新 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0；2 张新帧、基线 264→266）；全量挂起具名、目标回归 118/2/0；⓪ 网络不可达（产品 1 文件，代码块制表位）

最后更新：2026-10-28（本地 · R457 / 第 456 轮 / Round 454）：代码块保留源码制表符，而 `paragraphStyle` 不碰代码块的制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt ⇒ 一个制表符比一级四空格缩进少 4.14pt、两级少 8.29pt，缩进不同的代码行排在不同竖轴上。修法：`paragraphStyle` 对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 字形推进`（32.14pt）；列表/表格分支不动。旧/新：`CODE_TAB_STOP light 28.00/32.14、56.00/64.29、间隔 0、制表位 12 → 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、dark 同形。**2 张新帧**（`detail-code-tabs` 亮/暗）、0 旧帧变化/缺失；基线 **264→266**（同 commit 更新）；已逐张看亮/暗：制表符段与四空格段的 `if`/`print` 落在同一条竖轴。新帧判据 `testCodeBlockTabsMatchFourSpaces` 从产品渲染出的 NSTextView 读布局（4 个 x + 段样式）；旧形态四条全红；`M1251/M1252/M1253` **3/3 CAUGHT**、RESTORE_CLEAN。预检 **235/217/610 bad=0**、ARM **328/1093**、HIDDEN **322/1027 rot=0**。⓪：开工 ahead=0、HEAD=`ca40810`；`git push` 一次探针被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`（ahead=0、HEAD=`ca40810`）**；`gh` 读 `40664012233` 仍 EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；收口前再试一次。全量 **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**（卡在 `testSearchFieldIdealHeightIsStateIndependent`，日志 3.6M 行后同一行数分钟不动，已停）；目标回归 **118 测试 / 2 skipped / 0 failures**（Markdown/代码块/列表制表位/命中高亮/设置卡片节奏）。捕获卷 **266 帧**；基线 **266/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 456，`python3 scripts/product_streak.py --streak-for 456`，last=643081c）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push 探针被拒（ahead=0、HEAD ca40810）⇒ PUSH_BLOCKED=network；gh EOF ⇒ CI_READ_BLOCKED；436 无新跑 ⇒ MOTION_FLOOR_NOT_RUN；沿用 R456 已读。
② 产品：代码块制表位 = 4 个空格（旧 28/32.14、56/64.29 → 新同轴；2 张新帧、基线 266）。
③ 判据：旧形态四条红；M1251–M1253 3/3；precheck 235/217/610；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 322 / 可判 1027 / rot 0。
⑥ 捕获 266 帧；基线 266/0/0/0；build 0 告警；换装 ok/383=383；全量挂起具名，目标回归 118/2/0。

NOT-RUN / 阻塞（分开写）：① `40664012233 ↔ d2a1e80`（CI_READ_BLOCKED）；② `40664181811 ↔ ca40810`（同上）；③ R457 自身跑（未创建）；④ 436 Motion floor（无新跑）；⑤ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；⑥ 纯文本预览制表符（490）；⑦ 表格单元格制表符（491）；⑧ 8 空格制表位（492）；⑨ 命中高亮截断外/OCR（487）；⑩ 多文件第 2/3 个文件名（488）；⑪ 选中底高亮对比（489）；⑫ 弱化色选中态（485）；⑬ 行内码两侧标点（486）；⑭ HTML 的 `<del>`（484）；⑮ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑯ 设置内容列 1x 平涂；⑰ 设置脚注带 1x；⑱ 主窗口 content 帧 1x；⑲ 高夹具 1x；⑳ 13+ 菜单像素/标题；㉑ 真实拖拽；㉒ Dock 像素；㉓ 源图标最小窗文字 1x；㉔ 2x/extended；㉕ 固定块揭示偏移（455）；㉖ 跨年时间（456）；㉗ 主列表暗档文字盲区（457）；㉘ 真机/多屏（447）；㉙ 真菜单栏、12 实时腿；㉚ `table-lazy-rows`；㉛ HTML 六档字号（460）；㉜ 清除 × 命中区（461）；㉝ 分隔线令牌（462）；㉞ 展开态已加载内容无帧（463）；㉟ 其它自绘控件帮助文本（464）；㊱ HTML 引用块无导引线（465）；㊲ HTML 表格表头无同档（466）；㊳ 100+ 行行号（467）；㊴ HTML 代码块行号（468）；㊵ 行号选中/滚动两态（469）；㊶ 关于页 1x 盲（470）；㊷ M613 机器前提（472）；㊸ 真机 vibrant 暗档（473）；㊹ 长来源截断（474）；㊺ bundle ID 未搜（475）；㊻ 长首行标签省略无帧（476）；㊼ HTML 代码块无语言标签（477）；㊽ HTML `<hr>` 无通栏线（478）；㊾ HTML 表格体行无同一条线（479）；㊿ QuickPick 键盘提示 1x（480）；[51] HTML 任务列表无弱化（481）；[52] HTML 列表缩进（482）；[53] 中心刻度端点标签（483）；[54] HTML 的 `<del>`（484）；[55] 弱化色选中态（485）；[56] 行内码两侧标点（486）；[57] 437–492 的未结项仍开。

下一轮（R458）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R457 主笔+追记 head 跑、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`（DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（STRIKE_DIM）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `CODE_TAB_STOP` 两档 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0、`HISTORY_ROW_MATCH`、`INLINE_CODE_PAD` 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 5.09/5.98、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE` 16/16/0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108/102/1、`THEMATIC_RULE` 597/1/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；`FULL_SUITE_REREAD_NOT_RUN` 下一轮在较轻负载下重读（目标 1261/56/0）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R457_REPORT_BULLET = u"""- **R457（代码块制表位）**：代码块保留源码制表符，而 `paragraphStyle` 不碰代码块的制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt（一级差 4.14、两级差 8.29）。修法：对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 推进`。旧/新：`CODE_TAB_STOP light 28.00/32.14、56.00/64.29、间隔 0、制表位 12 → 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、dark 同形。**2 张新帧**（`detail-code-tabs` 亮/暗）、0 旧帧变化，基线 **264→266/0/0/0**；逐张看过两段缩进同轴。判据从渲染出的 NSTextView 读 4 个 x + 段样式；旧形态四条全红；`M1251/M1252/M1253` **3/3**；precheck 235/217/610 bad=0、ARM 328/1093、HIDDEN 322/1027 rot=0。⓪：push 探针被拒（`Connection closed ... port 22`）⇒ **`PUSH_BLOCKED=network`（ahead=0、HEAD=`ca40810`）**；gh EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；436 无新跑 ⇒ `MOTION_FLOOR_NOT_RUN`。全量 **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**（卡在 `testSearchFieldIdealHeightIsStateIndependent`，日志 3.6M 行后不动，已停）；目标回归 **118/2 skipped/0 failures**；捕获 266 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 456 轮（R457" in audit: raise SystemExit("REFUSED AUDIT 已有 R457")
if u"## Round 454 · R457" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 454")
if u"## D-453" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-453")
if u"代码块制表位与 4 个空格同轴" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**490." in backlog: raise SystemExit("REFUSED BACKLOG 已有 490")
if state.count(u"## R456 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R456 状态"))
U_CELL_OLD = u"U-31 … U-1707（R456 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R456 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_453 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R456 状态", STATE_SECTION + u"## R456 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1712（R457 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R456 节 ②", u"AGENT_STATE.md` 的 R457 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R457_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R457_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
