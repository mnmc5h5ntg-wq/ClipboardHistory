#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R449 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 447 轮（R448 · 2026-10-28"
AUDIT_SECTION = u"""## 第 448 轮（R449 · 2026-10-28 · U-1668…U-1672）：QuickPick 底部补键盘操作提示（旧帧底部 26pt 带 0 墨 → 新 1566/1848；提示在表格可见区下方 4pt；12 张 QuickPick 帧变化、基线名单 256）（产品 3 文件，浮层键盘提示位）

- **U-1668：⓪ push 与五跑。** 开工 remote=`107f2b3`、ahead=0，`git push` 为 **no-op（Everything up-to-date）**。`gh run list` 开始时读到 **`40629776895 ↔ 0737460`（R448 主笔+追记 head）与 `40629867848 ↔ 107f2b3`（预记 head）都 in_progress** ⇒ NOT-RUN；随后 `gh` 单跑与列表均 **EOF** ⇒ **`CI_READ_BLOCKED=network`**，这两跑的 `TABLE_ROW_LINES` 与 R449 自身的跑本轮未读。已读：`40623613789 ↔ ecb8e69` failure **仅 1 步＝Motion coverage floor**（Swift 全绿：`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1` + dark `NOT_RUN 行带=1`；`CODE_LANGUAGE 116/126`；`PROBE_DOMAIN 44/20`）；Motion 原文 `MOTION_FLOOR_FACTS judged=5/5 executed=77`、`MOTION_FLOOR_SUITE_RED=1`＝`testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（1x 只有 1 个过渡帧，要 ≥2，采样红、未登记）。旧跑：`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已由补记修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。436 只复核 Motion floor：`judged=5/5 executed=77`；receipt 采样红原样重跑，**不改门槛、不重猜 must_judge**。
- **U-1669：① 腐烂与预检。** `HIDDEN_ARMS 表=314 可判=1009 rot=0`；`NEEDLE_PRECHECK tables=227 covered=209 arms=592 bad=0`、`ARM_TOTAL files=320 arms=1075`。本轮改的是 `QuickPickController` 的约束区，没有弄断旧针（R63/R104/R407/R409/R415/R435 的锚点全部命中一次）。
- **U-1670：② QuickPick 底部键盘操作提示。** 缺陷形状：`↑`/`↓` 选择、`↵` 粘贴、`esc` 关闭全靠用户猜 —— 面板底部一直是空白（旧 `quickpick-list` 帧底部 26pt 带实测 **0 墨**）。修法：新 `QuickPickKeyboardHint` 纯策略（文案、11pt、`tertiaryLabelColor`、16pt 高、下内缩 6pt、上间距 4pt）；`QuickPickController` 底部加一行 label（identifier `quickPickKeyboardHint`），表格 stack 底边改钉到提示顶 −4pt（表格让出这一行）。旧/新同带：`QUICKPICK_HINT light 底部墨=0→1566、dark 0→1848`（底部 26pt 带、x 12..408）；产品视图树：文本＝`↑↓ 选择 · ↵ 粘贴 · esc 关闭`、提示顶 22.0 ≤ 表格可见区底 26.0（4pt 间隙）。**12 张 QuickPick 帧变化（list/typed/empty/hover/search-hover/search-focus × 亮/暗）、0 新增、0 缺失**；基线名单仍 **256**（`FRAME_BASELINE_UPDATED=256`，同 commit 更新）；已看亮/暗：提示居中、在空白区、不压候选行。Store 未动（1108 行/52 方法/最长 66）。
- **U-1671：判据、刀与一次 0 告警修正。** 新帧判据 `testQuickPickShowsKeyboardHints`：① 视图树里存在 `quickPickKeyboardHint`、文本逐字相等、提示顶 ≤ 表格可见区底 +2（不压行）；② 帧底部 26pt 带墨 ≥12·scale²（2x 48，实测 1566/1848；旧帧同带 0）。`M1232`（提示文本清空）⇒ 判据 CAUGHT（底部带 0 墨 + 文本不对）；`M1233`（表格底边退回 content 底部、提示不占位）⇒ 判据 CAUGHT（提示顶压到表格可见区底）⇒ **2/2**、RESTORE_CLEAN=yes。第一次 0 告警门咬到新测试里嵌套 `allSubviews` 的 **MainActor 隔离**（`subviews` 从 nonisolated 上下文引用，1 warning）—— 给局部函数加 `@MainActor` 后冷编 0/0/0。
- **U-1672：八步与具名 NOT-RUN。** build **0 告警**（第一次 1 warning 已修）；捕获卷 **256 帧**、`COMPARED=256 CHANGED=0 MISSING=0 ADDED=0`（更新后）；全量 **1230/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 448，`python3 scripts/product_streak.py --streak-for 448`，last=324ced6）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40629776895 ↔ 0737460`（in_progress 后 gh EOF；TABLE_ROW_LINES 未读）；② `40629867848 ↔ 107f2b3`（同上）；③ R449 自身跑（提交后创建）；④ 436 新跑 Motion floor（最后已知 5/5/77）；⑤ `QUICKPICK_HINT` 的 runner 1x 读数（gh 断）；⑥ 提示文案的 12 帧 runner 读数；⑦ HTML 表格体行无同一条线（479）；⑧ 设置内容列 1x 平涂；⑨ 设置脚注带 1x；⑩ 主窗口 content 帧 1x；⑪ 高夹具 1x；⑫ 13+ 菜单像素/标题；⑬ 真实拖拽；⑭ Dock 像素；⑮ 源图标最小窗文字 1x；⑯ 本地全量 5 条滚动红（449）；⑰ 2x/extended；⑱ 固定块揭示偏移（455）；⑲ 跨年时间（456）；⑳ 主列表暗档文字盲区（457）；㉑ 真机/多屏（447）；㉒ 真菜单栏、12 实时腿；㉓ `table-lazy-rows`；㉔ HTML 六档字号（460）；㉕ 清除 × 命中区（461）；㉖ 分隔线令牌（462）；㉗ 展开态已加载内容无帧（463）；㉘ 其它自绘控件帮助文本（464）；㉙ HTML 引用块无导引线（465）；㉚ HTML 表格表头无同档（466）；㉛ 100+ 行行号（467）；㉜ HTML 代码块行号（468）；㉝ 行号选中/滚动两态（469）；㉞ 关于页 1x 盲（470）；㉟ M613 机器前提（472）；㊱ 真机 vibrant 暗档（473）；㊲ 长来源截断（474）；㊳ bundle ID 未搜（475）；㊴ 长首行标签省略无帧（476）；㊵ HTML 代码块无语言标签（477）；㊶ HTML `<hr>` 无通栏线（478）；㊷ 437–480 的未结项仍开。

"""

ITER_SECTION = u"""## Round 446 · R449（第 448 轮 · 2026-10-28）：QuickPick 底部补键盘操作提示（旧帧底部 26pt 带 0 墨 → 新 1566/1848；提示在表格可见区下方 4pt；12 张 QuickPick 帧变化、基线 256）

QuickPick 的 ↑/↓、↵、esc 全靠猜，面板底部一直是空白（旧 `quickpick-list` 底部 26pt 带 0 墨）。新 `QuickPickKeyboardHint` 纯策略（`↑↓ 选择 · ↵ 粘贴 · esc 关闭`、11pt、tertiaryLabelColor、16pt 高、下内缩 6、上间距 4）；控制器底部加 label（identifier `quickPickKeyboardHint`），表格 stack 底边改钉到提示顶 −4。读数：`QUICKPICK_HINT light 底部墨=1566（旧 0）、dark 1848（旧 0）`；视图树文本逐字相等、提示顶 22.0 ≤ 表格可见区底 26.0。12 张 QuickPick 帧变化、0 新增/缺失，基线名单 256（同 commit 更新）；已看亮/暗提示居中、不压候选。M1232/M1233 2/2；第一次 0 告警门咬到测试里 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0。⓪：开工 no-op push（remote 107f2b3、ahead=0）；40629776895/40629867848 读时 in_progress、随后 gh EOF ⇒ CI_READ_BLOCKED；ecb8e69 仅 Motion floor 采样红（testCopyReceipt 1<2）；436 最后已知 judged=5/5 executed=77。全量 1230/57/5（滚动具名）；捕获 256；换装 ok/SHA_MATCH=1/381=381；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 quickpick-list 逐张看过：提示居中在底部空白区、不压候选行；不是只看数字。 |
| 判据有效性 | 15/15 | 视图树文本+位置（不压行）与帧底部 26pt 带墨量两头钉；旧帧同带 0；M1232/M1233 2/2。 |
| 假绿防御 | 15/15 | 位置断言防"提示压表"；底部带 x 限定去掉面板边缘；旧帧 0 作对照；第一次 0 告警红照记。 |
| 产品面推进 | 14/15 | 第一次把 QuickPick 的键盘操作写进产品；Store 不动；扣 1：1x runner 读数未读（gh 断）。 |
| 台账一致性 | 15/15 | U-1668…U-1672、D-445、no-op push/ahead=0、256 帧/1230、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 两跑 in_progress/EOF 具名；ecb8e69 的 Motion floor 采样红与 receipt 1<2 原文照记；0 告警红照记。 |
| 可复核性 | 15/15 | 0→1566/1848、提示顶/表底 22/26、12 帧名单、刀号与 precheck 227/209/592、rot 314/1009、基线 256 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_445 = u"""## D-445 QuickPick 底部键盘提示占一行、表格让出这一行（R449）

- 背景：QuickPick 的 ↑/↓、↵、esc 全靠猜；面板底部一直是空白（旧帧底部 26pt 带 0 墨）。
- 决定：新 `QuickPickKeyboardHint`（固定文案、11pt、`tertiaryLabelColor`、16pt 高）；控制器底部加 label，表格 stack 底边钉到提示顶 −4pt。
- 理由：键盘操作是 QuickPick 的核心交互，提示必须在面板里常驻；提示与候选行分开（视图树断言不压行），不挤掉可见行（仍 ≥2 行契约）。
- 兼容性/迁移：12 张 QuickPick 帧变化、0 新增/缺失；基线名单 256 同 commit 更新。
- 边界：只说明三组键；1x runner 读数本轮因 gh 断网未读（480）。
- 回滚：删 label 与两条约束、stack 底边恢复 content 底部即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### QuickPick 底部补键盘操作提示（旧帧底部 26pt 带 0 墨 → 新 1566/1848；提示在表格可见区下方 4pt；12 张 QuickPick 帧变化、基线 256）（R449 / 第 448 轮 / Round 446 / U-1668…U-1672 · 产品 3 文件，浮层键盘提示位）

"""

BACKLOG_SECTION = u"""449 追记（R449 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R449 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R449 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R449 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R449 · 仍开）：菜单具名标记仍未发射。

455 追记（R449 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R449 · 仍开）：跨年记录仍无年份。

457 追记（R449 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R449 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R449 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R449 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R449 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R449 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R449 · 仍开）：展开态已加载内容仍无帧。

464 追记（R449 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R449 · 仍开）：HTML 引用块没有导引线。

466 追记（R449 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R449 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R449 · 仍开）：HTML 代码块没有行号。

469 追记（R449 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R449 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R449 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R449 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R449 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R449 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R449 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R449 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R449 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R449 · 仍开）：HTML 表格体行没有同一条分隔线。

**480. QuickPick 键盘提示的 runner 1x 像素读数本轮未读**（R449 观察）
    现象：R449 的提示在本地 2x 帧读到 1566/1848 墨，但 gh 断网，`40629776895/40629867848/`R449 自身跑都没读；1x runner 上 11pt tertiary 文案是否落墨、12 张 QuickPick 帧是否全绿，尚无读数。
    修法：下轮 ⓪ 读这几跑的 `QUICKPICK_HINT` 与基线；若 1x 读不到，具名 `QUICKPICK_HINT_NOT_RUN`，不把"没读到"当"没画"。
"""

STATE_SECTION = u"""## R449 状态（2026-10-28 · 本地 · 第 448 轮 / Round 446）：QuickPick 底部补键盘操作提示（旧帧底部 26pt 带 0 墨 → 新 1566/1848；提示在表格可见区下方 4pt；12 张 QuickPick 帧变化、基线名单 256）；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED（产品 3 文件，浮层键盘提示位）

最后更新：2026-10-28（本地 · R449 / 第 448 轮 / Round 446）：`↑`/`↓` 选择、`↵` 粘贴、`esc` 关闭全靠用户猜 —— 面板底部一直是空白（旧 `quickpick-list` 帧底部 26pt 带实测 **0 墨**）。新 `QuickPickKeyboardHint` 纯策略（文案、11pt、`tertiaryLabelColor`、16pt 高、下内缩 6pt、上间距 4pt）；`QuickPickController` 底部加一行 label（identifier `quickPickKeyboardHint`），表格 stack 底边改钉到提示顶 −4pt。读数：`QUICKPICK_HINT light 底部墨=0→1566、dark 0→1848`（底部 26pt 带、x 12..408）；产品视图树：文本＝`↑↓ 选择 · ↵ 粘贴 · esc 关闭`、提示顶 22.0 ≤ 表格可见区底 26.0（4pt 间隙）。**12 张 QuickPick 帧变化、0 新增/缺失**；基线名单 **256**（`FRAME_BASELINE_UPDATED=256`，同 commit 更新）；已看亮/暗提示居中、不压候选行。`M1232/M1233` **2/2**（M1232 文本清空⇒底部 0 墨；M1233 表格底边退回⇒提示压表）；新帧判据两头钉；第一次 0 告警门咬到新测试里 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0。预检 **227/209/592 bad=0**、ARM **320/1075**、HIDDEN **314/1009 rot=0**。⓪：开工 remote=`107f2b3`、ahead=0，`git push` 为 **no-op**；`gh run list` 读到 `40629776895 ↔ 0737460` 与 `40629867848 ↔ 107f2b3` 均 **in_progress** ⇒ NOT-RUN，随后 `gh` 单跑/列表 **EOF** ⇒ **`CI_READ_BLOCKED=network`**；已读 `40623613789 ↔ ecb8e69` failure **仅 Motion floor**（Swift 全绿；`MOTION_FLOOR_FACTS judged=5/5 executed=77`、`MOTION_FLOOR_SUITE_RED=1`＝`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1 帧<2 采样红、未登记），receipt 采样原样重跑、不改门槛；旧跑 `40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。本地全量 **1230/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **256 帧**；基线 **256/0/0/0**；build **0 告警**（第一次 1 warning 已修）；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 448，`python3 scripts/product_streak.py --streak-for 448`，last=324ced6）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ 开工 no-op push（remote 107f2b3、ahead=0）；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED；ecb8e69 仅 Motion floor 采样红（receipt 1<2），原样重跑不改门槛；旧跑读数已取。
② 产品：QuickPick 底部键盘提示（0→1566/1848；12 帧变化、基线 256）。
③ 判据：M1232/M1233 2/2；新帧判据（文本/位置/墨量）；第一次 0 告警门 1 条 MainActor 隔离，修后 0；precheck 227/209/592；hidden rot 0。
④ 436：最后已知 judged=5/5 executed=77；新跑读不到 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 314 / 可判 1009 / rot 0。
⑥ 捕获 256 帧；基线 256/0/0/0；build 0 告警；换装 ok；本地全量 1230/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40629776895 ↔ 0737460`（in_progress 后 gh EOF；TABLE_ROW_LINES 未读）；② `40629867848 ↔ 107f2b3`（同上）；③ R449 自身跑（提交后创建）；④ 436 新跑 Motion floor（最后已知 5/5/77）；⑤ `QUICKPICK_HINT` 的 runner 1x 读数（gh 断）；⑥ 12 帧 QuickPick 的 runner 读数；⑦ HTML 表格体行无同一条线（479）；⑧ 设置内容列 1x 平涂；⑨ 设置脚注带 1x；⑩ 主窗口 content 帧 1x；⑪ 高夹具 1x；⑫ 13+ 菜单像素/标题；⑬ 真实拖拽；⑭ Dock 像素；⑮ 源图标最小窗文字 1x；⑯ 本地全量 5 条滚动红（449）；⑰ 2x/extended；⑱ 固定块揭示偏移（455）；⑲ 跨年时间（456）；⑳ 主列表暗档文字盲区（457）；㉑ 真机/多屏（447）；㉒ 真菜单栏、12 实时腿；㉓ `table-lazy-rows`；㉔ HTML 六档字号（460）；㉕ 清除 × 命中区（461）；㉖ 分隔线令牌（462）；㉗ 展开态已加载内容无帧（463）；㉘ 其它自绘控件帮助文本（464）；㉙ HTML 引用块无导引线（465）；㉚ HTML 表格表头无同档（466）；㉛ 100+ 行行号（467）；㉜ HTML 代码块行号（468）；㉝ 行号选中/滚动两态（469）；㉞ 关于页 1x 盲（470）；㉟ M613 机器前提（472）；㊱ 真机 vibrant 暗档（473）；㊲ 长来源截断（474）；㊳ bundle ID 未搜（475）；㊴ 长首行标签省略无帧（476）；㊵ HTML 代码块无语言标签（477）；㊶ HTML `<hr>` 无通栏线（478）；㊷ 437–480 的未结项仍开。

下一轮（R450）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R449 主笔+追记 head 跑、`40629776895 ↔ 0737460`（R448 主笔+追记 head；含 TABLE_ROW_LINES）、`40629867848 ↔ 107f2b3`（R448 预记 head）与 `40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `QUICKPICK_HINT` 两档 1566/1848/0 与 12 帧、`TABLE_ROW_LINES` 3/0/108.0/101.5/1.0、`THEMATIC_RULE` 612.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R449_REPORT_BULLET = u"""- **R449（浮层键盘提示位）**：QuickPick 的 ↑/↓、↵、esc 全靠用户猜，面板底部一直是空白（旧 `quickpick-list` 帧底部 26pt 带实测 **0 墨**）。新 `QuickPickKeyboardHint` 纯策略（`↑↓ 选择 · ↵ 粘贴 · esc 关闭`、11pt、`tertiaryLabelColor`、16pt 高、下内缩 6、上间距 4）；控制器底部加 label（identifier `quickPickKeyboardHint`），表格 stack 底边钉到提示顶 −4。读数：`QUICKPICK_HINT light 底部墨=0→1566、dark 0→1848`（底部 26pt 带、x 12..408）；视图树文本逐字相等、提示顶 22.0 ≤ 表格可见区底 26.0（4pt 间隙）。**12 张 QuickPick 帧变化、0 新增/缺失**；基线名单 **256**（同 commit 更新）；已看亮/暗提示居中、不压候选行。`M1232/M1233` **2/2**（文本清空⇒底部 0 墨；表格底边退回⇒提示压表）；新帧判据两头钉；第一次 0 告警门咬到新测试 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0；预检 227/209/592 bad=0、ARM 320/1075、HIDDEN 314/1009 rot=0。⓪：开工 remote=`107f2b3`、ahead=0，`git push` 为 **no-op**；`40629776895 ↔ 0737460` 与 `40629867848 ↔ 107f2b3` 读时 in_progress、随后 gh EOF ⇒ `CI_READ_BLOCKED`；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（Swift 全绿；`judged=5/5 executed=77`、`testCopyReceipt...` 1 帧<2 采样红、未登记），receipt 采样原样重跑、不改门槛；旧跑 36284e1 failure 1 步（dark 行带，已修）、fe956e3 failure 2 步、eeccad0 failure 1 步。全量 **1230/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 256 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；电池 683/5；清账在台账后复跑。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 448 轮（R449" in audit: raise SystemExit("REFUSED AUDIT 已有 R449")
if u"## Round 446 · R449" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 446")
if u"## D-445" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-445")
if u"QuickPick 底部补键盘操作提示" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**480." in backlog: raise SystemExit("REFUSED BACKLOG 已有 480")
if state.count(u"## R448 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R448 状态"))
U_CELL_OLD = u"U-31 … U-1667（R448 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R448 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_445 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R448 状态", STATE_SECTION + u"## R448 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1672（R449 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R448 节 ②", u"AGENT_STATE.md` 的 R449 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R449_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R449_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
