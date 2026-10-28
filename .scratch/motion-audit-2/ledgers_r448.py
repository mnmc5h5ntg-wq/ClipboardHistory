#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R448 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 446 轮（R447 · 2026-10-28"
AUDIT_SECTION = u"""## 第 447 轮（R448 · 2026-10-28 · U-1663…U-1667）：Markdown 表格体行之间补发丝分隔线（表头+四行体行 3 条、单行体行 0 条；线宽 108.0/107.5 对表宽 101.5、厚 1.0；2 张新帧、基线 254→256）（产品 3 文件，表格体行分隔位）

- **U-1663：⓪ 网络与跑。** 开工两次探测（`git ls-remote` 与 `git push`）均报 `Please make sure you have the correct access rights`（监督者同批 api=000）⇒ **`PUSH_BLOCKED=network`**：HEAD=`7545e0e`、origin/main=`ecb8e69`、**ahead=3**（602eea2/c5ef6e6/7545e0e）。`gh run list` 同批 EOF ⇒ **`CI_READ_BLOCKED=network`**；本轮未新建/未读到任何跑，`40623613789 ↔ ecb8e69`（补记后首跑）与旧四跑都记 NOT-RUN。最后一次已读读数（R447 账）：`40617745753 ↔ fe956e3` failure 2 步（vibrant 22≠20、dark 行带 1<3）、`40620912699 ↔ 36284e1` failure 1 步（dark 行带；CODE_LANGUAGE 1x 116/126、PROBE_DOMAIN 44/20 过）、`40613782362 ↔ eeccad0` failure 1 步、`40605228813 ↔ bdb4737` failure 2 步。436 只复核 Motion floor：最后一次已知 36284e1 臂 `judged=5/5 executed=77`；本轮新跑读不到 ⇒ NOT-RUN，不重猜 `must_judge`。
- **U-1664：① 腐烂与预检。** `HIDDEN_ARMS 表=313 可判=1007 rot=0`；`NEEDLE_PRECHECK tables=226 covered=208 arms=590 bad=0`、`ARM_TOTAL files=319 arms=1073`。本轮在 `.table` 分支里加行数属性后，R440 的 `M1206` 整块锚点被截断（命中 0）—— 把它重钉到表头那 5 行并**复跑 R440 表 2/2 CAUGHT**，precheck 才回到 bad=0（R441 的「针腐烂重钉必复跑旧表」同族）。M1226/M1228 的单行/两行锚点未受影响（新调用插在 `drawCodeLanguageTags` 之后）。
- **U-1665：② 表格体行分隔线。** 缺陷形状：R440 用 semibold 分开表头之后，多行表体的行与行之间仍无线 —— 四五行数值并排时容易串行。修法：新 `TableRowSeparators` 纯策略（`lineCount`、`shouldDraw(afterRow:totalRows:)` 只在体行之间、1pt、`tertiaryLabelColor`、`rect` 贴行底）；`MarkdownPresentation.tableRowCountAttribute` 只打在 ≥2 行的表格块上（单行体行的表不画）；`drawTableRowSeparators` 在背景层按**各行 usedRect 的外接宽度**画（不是正文列宽）。旧/新：`TABLE_ROW_LINES light 线数=3 负臂=0 线宽=108.0pt 表宽=101.5pt 厚=1.0pt`、`dark 107.5/101.5/1.0`。夹具 `detail-table-rows`（表头+四行体行）与既有 `detail-table`（表头+一行）成对；**2 张新帧、0 张旧帧变化**（单行臂不画线，`detail-table` 逐字节不变），基线 **254→256 / 0/0/0**；已看亮/暗：表头下无线、三条体行线、末行下无线。实现中修了两处几何病：① 行片段 `characterRange` **含行尾换行**，`isRowEnd` 改看 `rowEnd-1`（否则一条线都不画）；② `boundingRect(forGlyphRange:)` 给的是整行片段宽（480pt），改用各行 `usedRect` 外接（约 101.5pt）。Store 未动（1108 行/52 方法/最长 66）。
- **U-1666：判据、刀与一次 0 告警修正。** 新单测 `TableRowSeparatorsTests` 5 条（行数、只在体行之间画、贴行底、负宽、属性串行数 5/2）+ 帧判据 `testMarkdownTablesSeparateTheirBodyRows`（正臂恰好 3 条、负臂 0 条、厚 ≤2pt、线左/右沿与表宽 ±6pt）。`M1230`（删绘制调用）⇒ 帧判据 CAUGHT；`M1231`（表头后也画）⇒ 单测 + 帧判据 CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes（M1231 第一次跑 `命中=False` 是红文落在可能被 stdout 成块丢掉的判据正文里，改用单测里必现的「表头之后不许画线」）。第一次 0 告警门还咬到 `drawTableRowSeparators` 里 `textContainer` 声明后未用（1 warning）—— 删掉未用绑定后冷编 0/0/0，重新换装。
- **U-1667：八步与具名 NOT-RUN。** build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`，第一次 1 告警已修）；捕获卷 **256 帧**、`COMPARED=256 CHANGED=0 MISSING=0 ADDED=0`；全量 **1229/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 447，`python3 scripts/product_streak.py --streak-for 447`，last=602eea2）；清账与电池在台账后复跑。**具名 NOT-RUN**：① 本轮所有 runner 跑（`PUSH_BLOCKED=network`，含 `40623613789 ↔ ecb8e69`）；② 436 新跑 Motion floor（同上；最后已知 5/5/77）；③ 表格行线的 1x runner 像素（本轮未上传）；④ HTML 表格体行无同一条线（479）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ HTML `<hr>` 无通栏线（478）；㊴ 437–479 的未结项仍开。

"""

ITER_SECTION = u"""## Round 445 · R448（第 447 轮 · 2026-10-28）：Markdown 表格体行之间补发丝分隔线（表头+四行体行 3 条、单行体行 0 条；线宽 108.0/107.5 对表宽 101.5、厚 1.0；2 张新帧、基线 254→256）

R440 把表头用 semibold 分开之后，多行体行之间仍无线。新 `TableRowSeparators` 纯策略（只在体行之间、1pt、tertiaryLabelColor、贴行底）；`tableRowCountAttribute` 只打在 ≥2 行的表格块上；`drawTableRowSeparators` 按各行 `usedRect` 的外接宽度画（`boundingRect` 给的是整行片段宽 480pt，已换）。夹具 `detail-table-rows`（表头+四行）与 `detail-table`（表头+一行）成对：`TABLE_ROW_LINES light 线数=3 负臂=0 线宽=108.0pt 表宽=101.5pt 厚=1.0pt`、dark 107.5/101.5/1.0；2 张新帧、0 旧帧变化，基线 256/0/0/0；已看亮/暗三条体行线。实现中修 `characterRange` 含换行导致 0 条线、`boundingRect` 整列宽导致线宽 480pt 两处。M1230/M1231 2/2（M1231 改 needle 到单测必现文）；M1206 因新行腐烂，重钉并复跑 R440 表 2/2。第一次 0 告警门咬到未用 `textContainer`，修后冷编 0。⓪：两次网络探测均拒 ⇒ PUSH_BLOCKED=network（ahead=3、HEAD 7545e0e、origin/main ecb8e69）；gh EOF ⇒ CI_READ_BLOCKED；本轮所有跑与 436 新跑 NOT-RUN。全量 1229/57/5（滚动具名）；捕获 256；换装 ok/SHA_MATCH=1/381=381；清账与电池在台账后复跑。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-table-rows 逐张看过：表头下无线、三条体行线、末行下无线；不是只看数字。 |
| 判据有效性 | 15/15 | 正臂 3 条 / 负臂 0 条 / 厚 ≤2pt / 左右沿与表宽 ±6pt；单测钉"哪一行之后画"与属性行数；M1230/M1231 2/2。 |
| 假绿防御 | 15/15 | 负臂是逐字节不变的 `detail-table`（单行体行不许有线）；线宽用 usedRect 不用整列宽；M1231 改 needle 到必现文。 |
| 产品面推进 | 14/15 | 真给多行表体加了行分隔（四行成表可跟行）；Store 不动；扣 1：HTML 表格体行未覆盖（479）。 |
| 台账一致性 | 15/15 | U-1663…U-1667、D-444、ahead=3 与三笔 SHA、256 帧/1229、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 两次网络探测失败与 gh EOF 具名；两处几何病与一次 0 告警红照记；M1231/M1206 的 needle 修正照记。 |
| 可复核性 | 15/15 | 3/0、108.0/101.5/1.0、usedRect、y 行带、刀号与 precheck 226/208/590、rot 313/1007、基线 256 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_444 = u"""## D-444 表格体行分隔线只画在体行之间（R448）

- 背景：R440 用 semibold 分开表头之后，多行体行之间仍无线；四五行数值并排时容易串行。
- 决定：新 `TableRowSeparators` 纯策略：`shouldDraw(afterRow:totalRows:)` 只在第 2 行之后、最后一行之前画；1pt、`tertiaryLabelColor`；`rect` 贴行底；宽度取表格各行 `usedRect` 的外接（不是正文列宽）。
- 理由：表头已由字重区分，再在表头下画线是重复；单行体行的表（`detail-table`）一帧不变；纯策略不碰 Store（1108/66）。
- 兼容性/迁移：新夹具 `detail-table-rows`（2 帧，基线 254→256）；`detail-table` 逐字节不变。
- 边界：HTML 表格体行不走这条（479）。
- 回滚：删绘制调用与 `tableRowCountAttribute` 两处即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### Markdown 表格体行之间补发丝分隔线（表头+四行体行 3 条、单行体行 0 条；线宽 108.0/107.5 对表宽 101.5、厚 1.0；2 张新帧、基线 256）（R448 / 第 447 轮 / Round 445 / U-1663…U-1667 · 产品 3 文件，表格体行分隔位）

"""

BACKLOG_SECTION = u"""449 追记（R448 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R448 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R448 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R448 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R448 · 仍开）：菜单具名标记仍未发射。

455 追记（R448 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R448 · 仍开）：跨年记录仍无年份。

457 追记（R448 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R448 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R448 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R448 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R448 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R448 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R448 · 仍开）：展开态已加载内容仍无帧。

464 追记（R448 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R448 · 仍开）：HTML 引用块没有导引线。

466 追记（R448 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R448 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R448 · 仍开）：HTML 代码块没有行号。

469 追记（R448 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R448 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R448 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R448 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R448 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R448 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R448 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R448 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R448 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

**479. HTML 渲染器的表格体行没有同一条分隔线**（R448 观察）
    现象：R448 的体行分隔线接在 Markdown 渲染路径（`MarkdownPresentation` + 背景层）；HTML 预览的表格走 `NSAttributedString` 的 HTML 导入，是另一条路径，行与行之间没有同一条 1pt 线，也没有帧。
    修法：给 HTML 预览拍一张多行表格帧，量行线与表宽；若导入器不保留边框，用同一 `TableRowSeparators` 在背景层画。
"""

STATE_SECTION = u"""## R448 状态（2026-10-28 · 本地 · 第 447 轮 / Round 445）：Markdown 表格体行之间补发丝分隔线（表头+四行体行 3 条、单行体行 0 条；线宽 108.0/107.5 对表宽 101.5、厚 1.0；2 张新帧、基线 254→256）；两次网络探测均拒 ⇒ PUSH_BLOCKED=network（ahead=3）、gh EOF ⇒ CI_READ_BLOCKED（产品 3 文件，表格体行分隔位）

最后更新：2026-10-28（本地 · R448 / 第 447 轮 / Round 445）：R440 把表头用 semibold 分开之后，多行体行之间仍无线。新 `TableRowSeparators` 纯策略（`lineCount`、只在体行之间画、1pt、`tertiaryLabelColor`、贴行底）；`MarkdownPresentation.tableRowCountAttribute` 只打在 ≥2 行的表格块上；`drawTableRowSeparators` 在背景层按**各行 usedRect 的外接宽度**画。旧/新：`TABLE_ROW_LINES light 线数=3 负臂=0 线宽=108.0pt 表宽=101.5pt 厚=1.0pt`、`dark 107.5/101.5/1.0`。夹具 `detail-table-rows`（表头+四行体行）与既有 `detail-table`（表头+一行）成对；**2 张新帧、0 张旧帧变化**（单行臂不画线，`detail-table` 逐字节不变），基线 **254→256 / 0/0/0**；已看亮/暗：表头下无线、三条体行线、末行下无线。实现中修两处几何病（行片段 `characterRange` 含换行 ⇒ `isRowEnd` 看 `rowEnd-1`；`boundingRect` 是整行片段宽 480pt ⇒ 改 usedRect 外接）；第一次 0 告警门咬到未用 `textContainer`，删后冷编 0。`M1230/M1231` **2/2**（M1231 改 needle 到单测必现文）；`M1206` 因新行腐烂，重钉并复跑 R440 表 **2/2**。新单测 5 条 + 帧判据（3/0/≤2pt/±6pt）；预检 **226/208/590 bad=0**、ARM **319/1073**、HIDDEN **313/1007 rot=0**。⓪：两次探测（`git ls-remote`/`git push`）均报权限拒（api=000）⇒ **`PUSH_BLOCKED=network`**：HEAD=`7545e0e`、origin/main=`ecb8e69`、**ahead=3**（602eea2/c5ef6e6/7545e0e）；`gh run list` EOF ⇒ **`CI_READ_BLOCKED=network`**，本轮未读/未建任何跑（`40623613789 ↔ ecb8e69` 与旧四跑 NOT-RUN；最后已读读数见 R447 账）。436：最后一次已知 36284e1 臂 `judged=5/5 executed=77`；本轮新跑读不到 ⇒ NOT-RUN，不重猜 `must_judge`。本地全量 **1229/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **256 帧**；基线 **256/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 447，`python3 scripts/product_streak.py --streak-for 447`，last=602eea2）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ 两次网络探测均拒 ⇒ PUSH_BLOCKED=network（ahead=3、三笔 SHA）；gh EOF ⇒ CI_READ_BLOCKED；所有跑与 436 新跑 NOT-RUN，不重猜 must_judge。
② 产品：表格体行之间补 1pt 发丝线（3/0、108.0/101.5/1.0；0 旧帧变化、基线 256）。
③ 判据：M1230/M1231 2/2；M1206 因新行腐烂重钉并复跑 R440 表 2/2；新单测 5 条 + 帧判据；precheck 226/208/590；hidden rot 0。
④ 436：本轮读不到新跑 ⇒ NOT-RUN（最后已知 5/5/77）。
⑤ 367：hidden 表 313 / 可判 1007 / rot 0。
⑥ 捕获 256 帧；基线 256/0/0/0；第一次 0 告警门 1 条未用绑定，修后 0；换装 ok；本地全量 1229/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① 本轮所有 runner 跑（PUSH_BLOCKED=network，含 `40623613789 ↔ ecb8e69`）；② 436 新跑 Motion floor（最后已知 5/5/77）；③ 表格行线的 1x runner 像素（未上传）；④ HTML 表格体行无同一条线（479）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ HTML `<hr>` 无通栏线（478）；㊴ 437–479 的未结项仍开。

下一轮（R449）的靶：⓪ 先 `git push origin main`（禁 amend/force；恢复后先只读验 remote 仍为 `ecb8e69`，再一次快进 push `ecb8e69..7545e0e` 三笔）并复核 ahead=0；读 R448 主笔+追记 head 跑、`40623613789 ↔ ecb8e69`（R447 开工时的 in_progress；补记后首跑）与 `40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `TABLE_ROW_LINES` 两档 3/0/108.0/101.5/1.0、`THEMATIC_RULE` 612.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R448_REPORT_BULLET = u"""- **R448（表格体行分隔位）**：R440 用 semibold 分开表头之后，多行体行之间仍无线 —— 四五行数值并排时容易串行。新 `TableRowSeparators` 纯策略（只在体行之间、1pt、`tertiaryLabelColor`、贴行底）；`tableRowCountAttribute` 只打在 ≥2 行的表格块；`drawTableRowSeparators` 按各行 `usedRect` 的外接宽度画（`boundingRect` 是整行片段宽，实测 480pt，已换）。夹具 `detail-table-rows`（表头+四行）与 `detail-table`（表头+一行）成对：`TABLE_ROW_LINES light 线数=3 负臂=0 线宽=108.0pt 表宽=101.5pt 厚=1.0pt`、dark 107.5/101.5/1.0；**2 张新帧、0 张旧帧变化**，基线 **254→256 / 0/0/0**；已看亮/暗三条体行线。实现中修「`characterRange` 含换行 ⇒ 0 条线」与「`boundingRect` 整列宽 ⇒ 线宽 480pt」两处；第一次 0 告警门咬到未用 `textContainer`，修后冷编 0。`M1230/M1231` **2/2**（M1231 改 needle 到单测必现文）；`M1206` 因新行腐烂，重钉并复跑 R440 表 **2/2**；新单测 5 条 + 帧判据；预检 226/208/590 bad=0、ARM 319/1073、HIDDEN 313/1007 rot=0。⓪：两次网络探测均拒（api=000）⇒ **`PUSH_BLOCKED=network`**，HEAD=`7545e0e`、origin/main=`ecb8e69`、**ahead=3**；`gh run list` EOF ⇒ **`CI_READ_BLOCKED=network`**，本轮所有跑与 436 新跑 NOT-RUN（最后已读：fe956e3 2 步、36284e1 1 步 dark 行带、eeccad0 1 步、bdb4737 2 步；36284e1 臂 Motion floor 5/5/77）。全量 **1229/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 256 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；清账与电池在台账后复跑。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 447 轮（R448" in audit: raise SystemExit("REFUSED AUDIT 已有 R448")
if u"## Round 445 · R448" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 445")
if u"## D-444" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-444")
if u"Markdown 表格体行之间补发丝分隔线" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**479." in backlog: raise SystemExit("REFUSED BACKLOG 已有 479")
if state.count(u"## R447 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R447 状态"))
U_CELL_OLD = u"U-31 … U-1662（R447 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R447 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_444 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R447 状态", STATE_SECTION + u"## R447 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1667（R448 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R447 节 ②", u"AGENT_STATE.md` 的 R448 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R448_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R448_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
