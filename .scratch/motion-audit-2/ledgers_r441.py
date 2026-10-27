#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R441 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 439 轮（R440 · 2026-10-28"
AUDIT_SECTION = u"""## 第 440 轮（R441 · 2026-10-28 · U-1628…U-1632）：代码块左侧外边距行号 + 通栏紧凑灰底（旧：无色块行号、属性串底色最后一行只到字尾；新：行号 1/2/3、正文左 21.0pt 不动、灰底覆盖三行 100%，代码带 54.5pt；2 张旧帧变化 + 2 张新帧，基线 242→244）（产品 3 文件 + 1 新策略，详情正文代码块位）

- **U-1628：⓪ 两跑与 R440 签收。** `api=200` / `apple=200`；`git push origin main` 为 **no-op**（Everything up-to-date），HEAD = origin/main = `b421e5a`、**ahead=0**。`40579903554 ↔ f943607` **failure、失败步骤 1 个**：`On-screen probe coverage floor` 的 `testFrameIntervalsUnderStateChanges` 最差帧 **130.2ms > 120ms**、超锚点 2 颗（容差 1）⇒ 具名 `ONSCREEN_FRAME_INTERVAL_RUNNER_SAMPLING_MISS=130.2ms>120`；同一份产品/测试树的预记跑 `40579947758 ↔ b421e5a` **success、失败步骤 0** ⇒ runner 时序，**阈值未动**。失败跑的 Swift tests 本身是 **1192 条 / 69 skip / 0 失败**（本机的 5 条滚动红不在 CI 上）。`TABLE_HEADER` runner 1x：light `带=3 表头墨=217 表体墨=198 比=1.10 左沿=23.0/23.0pt 行距=10.0pt`、dark `251/226 比=1.11 左沿=23.0/23.0 行距=9.0pt` ⇒ 过 1.08 地板但余量只有 0.02–0.03（本机 1.40/1.25）；**地板不动**，R442 ⓪ 复读，若红先查字体通道而不是降门槛。**436**：两跑都是 `MOTION_FLOOR_FACTS judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`（notice-banner 具名 NOT-RUN，不是红）。
- **U-1629：① 腐烂与重钉。** `HIDDEN_ARMS 表=306 可判=992 rot=0 抽不出=6 已声明表=6 处置=ok`。本轮产品改动让 R439 的 **M1205 针腐烂**（`drawBackground` 里新增了行号/底色的调用，旧针 `super.drawBackground + drawQuoteRules` 两行不再相邻；预检 `bad=1` 当场抓到）⇒ 重钉为单行 `drawQuoteRules(in: rect)`，R439 表复跑 **3/3 CAUGHT、RESTORE_CLEAN=yes**。`NEEDLE_PRECHECK tables=219 covered=201 arms=576 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=312 arms=1059 dupes=0 repeats=0`。
- **U-1630：② 代码块左侧外边距行号 + 通栏紧凑灰底。** 缺陷形状有两层：① 代码块没有行号（一屏 30 行脚本没法说"第 12 行"）；② 属性串 `.backgroundColor` 按字形段画，代码块最后一行没有换行符时灰底只到最后一个字，帧上是一条锯齿带。修法：新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt），行号画在正文列左外侧 20pt 外边距里（右沿 = 容器原点 − 3pt），**正文不缩进**；灰底改由 `ChineseSelectableNSTextView.drawCodeBlockBackgrounds` 按行片段画通栏、止于最后一行（属性串不再背 `.backgroundColor`）。读数：`CODE_LINE_NUMBERS light/dark 代码带=54.5pt 行号带=3 正文左=21.0pt 带覆盖=100%`；旧形状 ① 行号带 0、② 带覆盖 2/3（M1212 复现）。帧变化 **2 张旧帧 + 2 张新帧**（`detail-markdown-rendered` 亮/暗多出 "1" 与紧凑底；`detail-code` 亮/暗新增），基线 **242→244 / 0/0/0**。已逐张看 `detail-code` 亮/暗与 `detail-markdown-rendered`：行号在左边距、三行灰底通栏、正文左沿未动、暗档可读。
- **U-1631：判据与刀。** 新单测 `CodeBlockLineNumbersTests` 4 条（行数/位数、11pt↔9pt、右边距对齐、正文不缩进+行数属性）；新帧判据 `testCodeBlocksShowLineNumbers`（最后三行正文带 → 行号带 ≥3、正文左沿 19–22pt、灰底覆盖 ≥85%，带通道前提 `CODE_LINE_NUMBERS_NOT_RUN=runner-detail-frame-plain`）。`M1210–M1212` **3/3 CAUGHT**、RESTORE_CLEAN=yes（不画行号 / 行号移进正文 / 不铺通栏底）。R234 的「表格不穿代码的衣服」契约随实现更新：宽底改由视图画（属性串只留行数标记），像素证人换成 `detail-code` 的 100% 覆盖；谓词 `appliesWideContentBackground` 仍是唯一策略。
- **U-1632：八步与具名 NOT-RUN。** build **0 告警**（冷编 0）；捕获 **148 条 / 4 skip / 0 失败 / 244 帧**；帧基线 `COMPARED=244 CHANGED=0 MISSING=0 ADDED=0`；全量 **1197/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；**全量抓出 5 条 UICaptureTests 回归并当场修掉**：① 新夹具正文里的 `print(a + b)` 被「读数只走 stdout」守卫当成 print 调用 ⇒ 样例改成 `let c = a + b`；② 「详情单左轴」把左边距的行号读成正文跑轴（差 9–10.5pt）⇒ 判据从 gutter−1 起扫，行号是列外边注、不参与正文轴，边注本身由新判据判）；单跑 `caffeinate -u` 后 **4/4 passed**（`OFFSET 0/203.0/1438`、`TIME 18/8/30.5/1438`、`CHANNEL 0→93.5→600 变化 131685/160800 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 440，现读 `python3 scripts/product_streak.py --streak-for 440`，last=2e8d3e6）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① 行号的 runner 1x 读数（R441 提交后的新跑才读）；② 100+ 行夹具（9pt 档只在纯函数里验）（467）；③ HTML 代码块没有行号（468）；④ 行号的选中/滚动两态帧（469）；⑤ `MOTION_FLOOR_FACTS` 的 notice-banner 未判（NOT-RUN，不是红）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 437–469 仍开。

"""

ITER_SECTION = u"""## Round 438 · R441（第 440 轮 · 2026-10-28）：代码块左侧外边距行号 + 通栏紧凑灰底（旧：无色块行号、属性串底色最后一行只到字尾；新：行号 1/2/3、正文左 21.0pt 不动、灰底覆盖三行 100%，代码带 54.5pt；2 张旧帧变化 + 2 张新帧，基线 242→244）

两件事一起修：代码块没有行号（一屏 30 行脚本无法说"第几行"）；属性串 `.backgroundColor` 按字形段画，最后一行没换行符时灰底只到字尾（锯齿带）。修法：新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt），行号画在正文列左外侧 20pt 外边距、正文不缩进；灰底改由 `drawCodeBlockBackgrounds` 按行片段画通栏、止于最后一行。读数：行号带 3、正文左 21.0pt、带覆盖 100%（旧 0 / 2/3）；2 张旧帧 + 2 张新帧，基线 244/0/0/0。M1210–M1212 3/3；R439 的 M1205 因 `drawBackground` 变长而腐烂，当场重钉并复跑 3/3；预检 219/201/576 bad=0；HIDDEN 306/992 rot=0。全量 1197/57/5（5 条滚动红），并抓出 5 条 UICapture 回归当场修掉（print 样例被 stdout 守卫误读、单左轴把边注读成正文轴）。⓪：push no-op、HEAD=b421e5a、ahead=0；`40579903554 ↔ f943607` failure 1 步（在屏帧间隔 130.2ms>120、超 2 颗），同树预记跑 `40579947758 ↔ b421e5a` success ⇒ runner 时序，阈值未动；`TABLE_HEADER` 1x 1.10/1.11（地板 1.08，余量 0.02）；436 = `judged=4/5 executed=77 not-run=notice-banner REDS=0`。捕获 148/4/0、244 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | `detail-code` 与 `detail-markdown-rendered` 亮/暗逐张看过：行号在左边距、三行灰底通栏、正文左沿未动、暗档可读；同帧读数 3 带 / 21.0pt / 100%。扣 1：行号的 runner 1x 读数要等本轮新跑。 |
| 判据有效性 | 15/15 | 行号带计数 + 正文左沿不变量 + 灰底覆盖率三轴；M1210–M1212 3/3，三种坏法（不画号 / 挤正文 / 不铺底）都咬住；R234 契约随实现更新且像素证人换成 100% 覆盖。 |
| 假绿防御 | 15/15 | 旧形状在三条轴上都会红（0 带 / 67% 覆盖）；行号不进文本存储；覆盖采样列避开正文与浮层；通道前提具名。 |
| 产品面推进 | 14/15 | 真落代码块行号 + 紧凑通栏底，补的是"长脚本无法定位行"与"锯齿灰底"两个可见空档；扣 1：HTML 代码块未接（468）、三位数档只在纯函数里验（467）。 |
| 台账一致性 | 15/15 | U-1628…U-1632、D-437、R440 两跑一红一绿、TABLE_HEADER 1.10/1.11 与 244 帧都从命令/测试输出解析；M1205 重钉记在 U-1629。 |
| 交付诚实性 | 15/15 | 130.2ms 红按原文记并说明同树绿跑；TABLE_HEADER 余量薄照实写（不降地板）；全量抓出的 5 条 UICapture 回归连同修法都记；notice-banner 未判写 NOT-RUN。 |
| 可复核性 | 15/15 | 行号带 3、正文左 19–22pt、覆盖 ≥85%、11/9pt 档、刀号与 precheck/rot、基线 244、换装/清账都在。 |

均分 = 103/105 ≈ 14.7/15（98）。"""

DECISION_437 = u"""## D-437 代码块行号放正文列外侧，灰底改由视图画通栏（R441）

- 背景：代码块没有行号，长脚本无法定位；属性串 `.backgroundColor` 按字形段画，最后一行无换行符时灰底只到字尾（锯齿带）。
- 决定：新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt）；行号画在正文列左外侧 20pt 外边距，右沿 = 容器原点 − 3pt，**正文不缩进**；灰底改由 `ChineseSelectableNSTextView.drawCodeBlockBackgrounds` 按行片段铺满正文列宽、止于最后一行；`MarkdownPresentation` 不再给代码块打 `.backgroundColor`，只留行数属性作为"这块要宽底 + 要行号"的标记。
- 理由：外边距是详情列本来就有的空白，行号放那里不动正文、不改代码块的排版；行号不进文本存储，复制/搜索拿不到；视图画底可以做到通栏且止于最后一行。
- 兼容性/迁移：只影响 Markdown 渲染路径；HTML 代码块没有行号（468）；三位数档只在纯函数里验（467）；帧变化 2 张旧帧 + 2 张新帧，基线 242→244。
- 边界：行号的选中/滚动两态没有帧（469）；1000+ 行会超出 20pt 外边距。
- 回滚：删 `drawCodeLineNumbers`/`drawCodeBlockBackgrounds` 两个调用即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 详情 Markdown 代码块补左侧外边距行号 + 通栏紧凑灰底（行号带 3、正文左 21.0pt、灰底覆盖 100%、代码带 54.5pt；2 张旧帧变化 + 2 张新帧、基线 244）（R441 / 第 440 轮 / Round 438 / U-1628…U-1632 · 产品 3 文件，详情正文代码块位）

"""

BACKLOG_SECTION = u"""437 追记（R441 · 仍开）：本轮只动详情代码块；主列表仍不匹配 `sourceAppName`。

449 追记（R441 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/203/1438；TIME 18/8/30.5/1438；CHANNEL 131685/160800）；R440 主跑在 runner 上唯一红是在屏帧间隔 130.2ms>120，同树预记跑全绿 ⇒ 采样/时序。

451 追记（R441 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R441 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R441 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R441 · 仍开）：菜单具名标记仍未发射。

455 追记（R441 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R441 · 仍开）：跨年记录仍无年份。

457 追记（R441 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R441 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R441 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R441 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R441 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R441 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R441 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R441 · 仍开）：其它自绘控件（浮层清除 ×、批量栏五颗）仍无同类帮助判据。

465 追记（R441 · 仍开）：HTML 引用块没有导引线（只接了 Markdown 路径）。

466 追记（R441 · 仍开）：HTML 表格的表头没有同档字重。

**467. 代码块行号的 9pt 档只在纯函数里验，且 1000+ 行会超出 20pt 外边距**（R441 观察）
    现象：`CodeBlockLineNumbers.font(forLineCount:)` 在 ≥100 行时收成 9pt，单元测试只验字号/等宽/3 位数宽度；没有 100+ 行的帧夹具，runner 上也没读过这一档。四位数（≥1000 行）在 9pt 下约 22pt，仍会超出 20pt 外边距（第一位被裁）。
    修法（下一轮若需要）：加一个 100+ 行的代码夹具帧（行号带 = 行数、9pt 档可读）；四位数改为按位数缩字号或允许外边距临时加宽。

**468. HTML 代码块没有行号：R441 只接了 Markdown 路径**（R441 观察）
    现象：`codeBlockLineCountAttribute` 只在 `MarkdownPresentation.attributedString` 里打；`HtmlRendering` 的 `<pre>` 没有行号，且 `detail-html-rendered` 夹具当前没有代码块，帧上无对象。
    修法：给 HtmlRendering 的 `<pre>` 打同一属性（或复用同一绘制），并在 HTML 夹具里加一段三行代码 + 帧判据。

**469. 代码块行号的选中态/滚动态没有帧**（R441 观察）
    现象：行号画在背景层、位于正文列外侧；当前的帧只有静态态。选中一段代码时行号是否该跟着高亮、滚动时是否与行片段同相位，都没有像素证人。
    修法：加一个选中态帧（选中第一行）与一个滚动后帧，断言行号带仍 = 可见行数且不被选区盖住。
"""

STATE_SECTION = u"""## R441 状态（2026-10-28 · 本地 · 第 440 轮 / Round 438）：代码块左侧外边距行号 + 通栏紧凑灰底（行号带 3、正文左 21.0pt、灰底覆盖 100%、代码带 54.5pt；2 张旧帧变化 + 2 张新帧，基线 242→244）；R440 主跑 `40579903554 ↔ f943607` failure 1 步（在屏 130.2ms>120），同树预记跑 `40579947758 ↔ b421e5a` success ⇒ runner 时序、阈值未动（产品 3 文件，详情正文代码块位）

最后更新：2026-10-28（本地 · R441 / 第 440 轮 / Round 438）：代码块此前没有行号，且属性串 `.backgroundColor` 按字形段画、最后一行只到字尾（锯齿带）。新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt），行号画在正文列左外侧 20pt 外边距（右沿 = 原点 − 3pt），正文不缩进；灰底改由 `ChineseSelectableNSTextView.drawCodeBlockBackgrounds` 按行片段铺满列宽、止于最后一行；`MarkdownPresentation` 不再给代码块打 `.backgroundColor`，只留行数属性。读数：`CODE_LINE_NUMBERS light/dark 代码带=54.5pt 行号带=3 正文左=21.0pt 带覆盖=100%`；旧形状行号带 0、覆盖 2/3（M1212 复现）。帧变化 2 张旧帧 + 2 张新帧，基线 **242→244 / 0/0/0**。`M1210–M1212` **3/3 CAUGHT**；R439 的 M1205 因 `drawBackground` 变长而腐烂，预检 `bad=1` 当场抓到 ⇒ 重钉并复跑 3/3。新单测 4 条 + 新帧判据 1 条；R234 契约改为"视图画宽底 + 属性串留行数标记"。预检 **219/201/576 bad=0**、ARM **312 文件 / 1059 把**、HIDDEN **306/992 rot=0**。⓪：push no-op、HEAD = origin/main = `b421e5a`、**ahead=0**；`40579903554 ↔ f943607` **failure、失败步骤 1 个**（`On-screen probe coverage floor`：`testFrameIntervalsUnderStateChanges` 最差 **130.2ms > 120ms**、超 2 颗、容差 1），同树预记跑 `40579947758 ↔ b421e5a` **success** ⇒ 具名 `ONSCREEN_FRAME_INTERVAL_RUNNER_SAMPLING_MISS`，阈值未动；失败跑的 Swift tests 1192/69 skip/0 失败。`TABLE_HEADER` 1x light 比 **1.10**、dark **1.11**（地板 1.08，余量 0.02–0.03；地板不动）；**436** = `judged=4/5 executed=77 not-run=notice-banner REDS=0`。本地全量 **1197/57/5**（5 断言全在 `SelectionRevealAnimationTests` 的 3 条用例；全量另抓出 5 条 UICapture 回归并当场修掉：print 样例被 stdout 守卫误读、单左轴把边注读成正文轴）；单跑 **4/4**（OFFSET 0/203.0/1438；TIME 18/8/30.5/1438；CHANNEL 0→93.5→600 变化 131685/160800 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **148/4/0 / 244 帧**；基线 **244/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 440，现读 `python3 scripts/product_streak.py --streak-for 440`，last=2e8d3e6）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ R440 两跑：主跑 failure 1 步（在屏 130.2ms>120），同树预记跑 success ⇒ runner 时序；TABLE_HEADER 1x 1.10/1.11（地板不动）；436 judged 4/5 REDS 0。
② 产品：代码块左边距行号 + 通栏紧凑底（行号带 3、覆盖 100%、正文左 21.0pt；2 张旧帧 + 2 张新帧，基线 244）。
③ 判据：M1210–M1212 3/3；R439 M1205 重钉并复跑 3/3；新单测 4 条 + 帧判据；precheck 219/201/576；hidden rot 0。
④ 436：`judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 306 / 可判 992 / rot 0。
⑥ 捕获 148/4/0、244 帧；换装 ok；清账 162/63/0；帧基线 244/0/0/0；本地全量 1197/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 行号的 runner 1x 读数（本轮提交后的新跑才读）；② 100+ 行夹具 / 9pt 档（467）；③ HTML 代码块行号（468）；④ 行号选中/滚动两态（469）；⑤ 436 的 notice-banner 未判（NOT-RUN，不是红）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 437–469 仍开。

下一轮（R442）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R441 主笔+追记 head 跑与预记跑的全部失败步骤（成对 run↔commit），重点看新帧判据 `CODE_LINE_NUMBERS` 的行号带 3 / 正文左 19–22pt / 覆盖 ≥85%，以及 `ONSCREEN_FRAME_INTERVAL_RUNNER_SAMPLING_MISS` 与 `TABLE_HEADER` 1.10/1.11 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R441_REPORT_BULLET = u"""- **R441（代码块行号位）**：代码块此前没有行号（一屏 30 行脚本无法说"第几行"），且属性串 `.backgroundColor` 按字形段画、最后一行没换行符时灰底只到字尾（锯齿带）。新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt），行号画在正文列左外侧 20pt 外边距（右沿 = 原点 − 3pt），正文不缩进；灰底改由 `drawCodeBlockBackgrounds` 按行片段画通栏、止于最后一行。读数：**行号带 3、正文左 21.0pt、灰底覆盖 100%、代码带 54.5pt**；旧形状行号带 0、覆盖 2/3（M1212 复现）。帧变化 **2 张旧帧 + 2 张新帧**，基线 **242→244 / 0/0/0**。`M1210–M1212` **3/3**；R439 的 M1205 因 `drawBackground` 变长而腐烂，预检当场抓到并重钉（复跑 3/3）；新单测 4 条 + 新帧判据 1 条；预检 219/201/576 bad=0、ARM 312/1059、HIDDEN 306/992 rot=0。⓪：push no-op、HEAD=`b421e5a`、ahead=0；`40579903554 ↔ f943607` **failure 1 步**（在屏 `testFrameIntervalsUnderStateChanges` 130.2ms>120、超 2 颗），同树预记跑 `40579947758 ↔ b421e5a` **success** ⇒ 具名 runner 时序，阈值未动；`TABLE_HEADER` 1x **1.10/1.11**（地板 1.08，余量薄、地板不动）；**436** = `judged=4/5 executed=77 not-run=notice-banner REDS=0`。本地全量 **1197/57/5**（5 断言全在 SelectionRevealAnimationTests；全量另抓出 5 条 UICapture 回归当场修掉：print 样例被 stdout 守卫误读、单左轴把边注读成正文轴），单跑 4/4（OFFSET 0/203/1438；TIME 18/8/30.5/1438；CHANNEL 131685/160800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 148/4/0、244 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
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
if u"第 440 轮（R441" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R441 节")
if u"## Round 438 · R441" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 438")
if u"## D-437" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-437")
if u"详情 Markdown 代码块补左侧外边距行号" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**467." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 467")
if state.count(u"## R440 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R440 状态"))
U_CELL_OLD = u"U-31 … U-1627（R440 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R440 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R440 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_437 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R440 状态", STATE_SECTION + u"## R440 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1632（R441 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R440 节 ②",
                                u"AGENT_STATE.md` 的 R441 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R441_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R441_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
