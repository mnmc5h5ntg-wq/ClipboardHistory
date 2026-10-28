#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R446 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 444 轮（R445 · 2026-10-28"
AUDIT_SECTION = u"""## 第 445 轮（R446 · 2026-10-28 · U-1653…U-1657）：代码块补语言标签（解析层认出语言、渲染层从未显示；首行右侧标签墨 316/381、无语言臂 0；同文对照帧 + 2 张新帧、基线 250→252）（产品 3 文件，代码块语言标识位）

- **U-1653：⓪ push 与两跑。** 开工先只读验 remote 仍为 `eeccad0`，一次快进 push **`eeccad0..fe956e3` success**（三笔：R445 主笔 56486a9 + 追记 8921042 + 预记 fe956e3），HEAD = origin/main = `fe956e3`、**ahead=0**。新 head 跑 **`40617745753 ↔ fe956e3`** 在 ⓪ 时仍 **in_progress** ⇒ NOT-RUN（R445 代码的首跑，R447 ⓪ 必须读）。`40613782362 ↔ eeccad0` failure、失败步骤 **1 个**：`testProbesDoNotSitOnVibrantColumns` 在 `UICaptureHarness.swift:14396` 读 `XCTAssertEqual failed: ("22") is not equal to ("20") - 非放行的那 20 条必须全部真的判到 ⇒ 有 -2 条被悄悄跳过`；同跑其余读数：`CODE_LINE_NUMBERS light/dark 54.0pt/3/21.0pt/100%`、`HISTORY_ROW_SOURCE light 139.0/74.0 差 65.0 左 97.0/97.0` 与 dark `HISTORY_ROW_SOURCE_NOT_RUN=runner-1x-sidebar-plain`、`SETTINGS_ABOUT_ROW 7/7`、`TABLE_HEADER 1.10/1.11`、`PROBE_DOMAIN 22/20`（红）+ `PROBE_DOMAIN_NOT_RUN 放行 22 条`（settings 族整族未绘制）。`HISTORY_SEARCH_SOURCE` 在 eeccad0 上**不存在**（R445 的测试随 fe956e3 才进仓库）⇒ 具名 `NOT-RUN=test-not-in-commit`，不是 0。`40605228813 ↔ bdb4737` failure、失败步骤 **2 个**：同一个 vibrant 22≠20 + `testSettingsSidebarShowsTheAboutCategoryRow light 0≠7`（R442 时代的仪器病；后者 R443 已修、前者本轮修）。
- **U-1654：① 腐烂与预检。** `HIDDEN_ARMS 表=311 可判=1003 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=224 covered=206 arms=586 bad=0`、`ARM_TOTAL files=317 arms=1069 dupes=0 repeats=0`。新表 `mutate_r446_code_language` 已登记。
- **U-1655：② 代码块补语言标签。** 缺陷形状：`MarkdownBlock.Kind.codeBlock(language:)` 从围栏信息串里认出了语言，但 `MarkdownPresentation` 只用了行数、从没把语言交给呈现层 —— ```` ```swift ```` 与 ```` ```python ```` 在详情里长得一模一样（作者写下的信息被丢）。修法：新 `CodeLanguageTag` 纯策略（别名归一化、未知原样大写截 12、`text/plaintext` 不标、非 ASCII 不标；`fits` 保证首行正文与标签间至少 24pt；右沿内缩 10pt、9pt semibold、`secondaryLabelColor`）；`MarkdownPresentation.codeLanguageAttribute` 只打在代码块正文；`ChineseSelectableNSTextView.drawCodeLanguageTags` 在**首行**右侧画，放不下就不画（长行宁可没有标签，也不遮代码）；标签不进文本存储（复制代码不会多出字母）。旧/新：`CODE_LANGUAGE light 右区=492..628pt 标签墨=316 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`；`dark 381`。夹具：`detail-code`（```swift）与新的 `detail-code-plain`（```，三行逐字相同）成对；**2 张新帧、4 张旧帧变化**（detail-code 亮/暗 + detail-markdown-rendered 亮/暗，后者也有一行 swift 代码块），基线 **250→252 / 0/0/0**；已看：亮/暗 SWIFT 都在首行右缘、plain 臂无标签、markdown 样例的一行 swift 块右上也有 SWIFT。Store 未动（1108 行/52 方法/最长 66）。
- **U-1656：判据、刀与一次 needle 修正。** 新单测 `CodeLanguageTagTests` 6 条（已知别名、未知回退、中性/空/非 ASCII、截断、`fits` 临界两臂、右对齐/垂直居中）+ 帧判据 `testCodeBlocksShowTheirLanguage`（标签墨地板 12·scale²=1x 12/2x 48；无语言臂 0、第二行 0、行号带 3/3、正文左沿同轴 ±0.5）。`M1226`（删绘制调用）⇒ 帧判据 CAUGHT；`M1227`（`fits` 恒真）⇒ 单测 `testTagIsSkippedWhenTheFirstLineWouldCollide` CAUGHT ⇒ **2/2**、红得对 2、RESTORE_CLEAN=yes。M1226 第一次跑报 `命中=False`：刀表 needle 写的是「没把围栏里的语言」，实际红文是「**没有**把围栏里的语言」—— 与 R439 同族的漏字；修 needle 后复跑 2/2（不是放水，刀本来就红）。
- **U-1657：八步与具名 NOT-RUN。** build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`）；捕获卷 **252 帧**、基线 `COMPARED=252 CHANGED=0 MISSING=0 ADDED=0`；全量 **1218/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 445，`product_streak --streak-for 445`，last=56486a9）；清账在台账后复跑；电池 `Ran 683 / OK (skipped=5)`。**具名 NOT-RUN**：① `40617745753 ↔ fe956e3`（⓪ 时 in_progress；R445 代码首跑）；② `40613782362` 上的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 新跑 Motion floor（head 跑未完成）；④ 长首行代码块无标签帧（476）；⑤ HTML 代码块无语言标签（477）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 长来源截断（474）；㊱ bundle ID 未搜（475）；㊲ 437–477 的未结项仍开。

"""

ITER_SECTION = u"""## Round 443 · R446（第 445 轮 · 2026-10-28）：代码块补语言标签（解析层已有语言、渲染层从未显示；首行右侧标签墨 316/381、无语言臂 0；同文对照帧 + 2 张新帧、基线 250→252）

解析层从围栏信息串认出语言（`codeBlock(language:)`），呈现层只用了行数。新 `CodeLanguageTag` 纯策略：别名归一化（python/py→PYTHON、js→JS、c++→C++…）、未知原样大写截 12、`text/plaintext` 与非 ASCII 不标；`fits` 要求首行正文右沿与标签间至少 24pt，否则不画（长行宁可没有标签也不遮代码）；9pt semibold、右沿内缩 10pt。`codeLanguageAttribute` 只打在代码块正文，`drawCodeLanguageTags` 在 `drawBackground` 的首行右侧画；标签不进文本存储。夹具 `detail-code`（```swift）与新 `detail-code-plain`（```，三行逐字相同）；读数 `CODE_LANGUAGE light 标签墨=316 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0`、dark 381。2 张新帧 + 4 张旧帧变化（detail-markdown-rendered 也有一行 swift 块），基线 252/0/0/0。M1226/M1227 2/2（M1226 首次 needle 漏「有」字，修后复跑红得对）。⓪：push eeccad0..fe956e3 success、ahead=0；40613782362 failure 唯一红＝vibrant judged 22≠20（2 条 nil-vibrant 不可判说明段被漏扣，已修）；HISTORY_SEARCH_SOURCE 在 eeccad0 上 test-not-in-commit ⇒ NOT-RUN；40605228813 failure 2 步（同一 vibrant + 设置关于行 0≠7，后者 R443 已修）；head 跑 40617745753 in_progress ⇒ NOT-RUN。全量 1218/57/5（滚动具名）；捕获 252；换装 ok/SHA_MATCH=1/381=381；清账在台账后复跑；电池 `Ran 683 / OK (skipped=5)`。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 逐张看了 detail-code 亮/暗（首行右缘 SWIFT）、detail-code-plain（无标签）、detail-markdown-rendered（一行 swift 块也有 SWIFT），不是只看数字。 |
| 判据有效性 | 15/15 | 同文两臂（仅围栏信息串不同）+ 右区墨量、第二行 0、行号带 3/3、正文左同轴；单测钉标签文本与放不下不画；M1226/M1227 2/2。 |
| 假绿防御 | 15/15 | 无语言臂同区 0 才证明右区墨来自标签；标签不进文本存储；1x 地板按 scale²（12）；M1226 首次漏字被如实记下并修 needle。 |
| 产品面推进 | 14/15 | 真把解析层已认出的语言接到可见处（代码块身份第一次可读）；Store 不动；扣 1：长首行省略标签无帧（476）、HTML 代码块未覆盖（477）。 |
| 台账一致性 | 15/15 | U-1653…U-1657、D-442、push fe956e3、252 帧/1218、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | in_progress 与 test-not-in-commit 都具名；vibrant 22≠20 的 -2 成因写明；M1226 首跑命中失败照记。 |
| 可复核性 | 15/15 | 右区=492..628pt、标签墨 316/381、无语言臂 0、行号带 3/3、正文左 21.0/21.0、刀号与 precheck/rot、基线 252 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_442 = u"""## D-442 代码块语言标签画在首行右侧、放不下就不画（R446）

- 背景：解析层从围栏信息串认出 `language`（`MarkdownBlock.Kind.codeBlock(language:)`），呈现层只用了行数；` ```swift ` 与 ` ```python ` 在详情里没有区别。
- 决定：新 `CodeLanguageTag` 纯策略归一化标签（别名表 + 未知大写截 12；`text/plaintext`/非 ASCII 不标）；标签画在代码块**第一行**右侧、右沿内缩 10pt；`fits` 要求首行正文右沿 + 24pt ≤ 标签左沿，否则不画。标签不进文本存储。
- 理由：语言是作者写下的内容，不能丢；画在背景层不挤动代码与行号；长行省略比遮字诚实；纯策略可单测，Store 不动（1108/66）。
- 兼容性/迁移：新夹具 `detail-code-plain`（与 `detail-code` 三行逐字相同，只差围栏信息串）；基线 250→252；`detail-markdown-rendered` 也因一行 swift 块变化。
- 边界：长首行不画（476 无帧）；HTML 代码块不走这条（477）；标签是元信息，用 `secondaryLabelColor`，不抢代码。
- 回滚：删 `drawCodeLanguageTags` 调用与 `codeLanguageAttribute` 两处即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 代码块补语言标签（解析层已有语言、渲染层从未显示；首行右侧 SWIFT 墨 316/381、无语言臂 0；同文对照帧 + 2 张新帧、基线 252）（R446 / 第 445 轮 / Round 443 / U-1653…U-1657 · 产品 3 文件，代码块语言标识位）

"""

BACKLOG_SECTION = u"""449 追记（R446 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R446 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R446 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R446 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R446 · 仍开）：菜单具名标记仍未发射。

455 追记（R446 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R446 · 仍开）：跨年记录仍无年份。

457 追记（R446 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R446 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R446 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R446 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R446 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R446 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R446 · 仍开）：展开态已加载内容仍无帧。

464 追记（R446 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R446 · 仍开）：HTML 引用块没有导引线。

466 追记（R446 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R446 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R446 · 仍开）：HTML 代码块没有行号。

469 追记（R446 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R446 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R446 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R446 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R446 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R446 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

**476. 代码块语言标签在长首行时被省略，没有帧**（R446 观察）
    现象：`CodeLanguageTag.fits` 在首行正文太靠右时不画标签（避免遮代码）；单测钉了临界，但帧上只有"短行 → 有标签"这一臂，长行那一臂没有像素证人。
    修法：加一个首行很长（正文右沿越过标签左沿）的代码块夹具，断言两臂都不画、且正文与行号几何不变。

**477. HTML 渲染器的代码块没有语言标签**（R446 观察）
    现象：语言标签只接在 Markdown 渲染路径（`MarkdownPresentation`）；HTML 预览里的 `<pre><code class="language-swift">` 没有同类标识（与 468 的 HTML 行号同族）。
    修法：给 HTML 渲染路径保留 `class` 里的 language，共用 `CodeLanguageTag` 与绘制层，补一帧与单测。
"""

STATE_SECTION = u"""## R446 状态（2026-10-28 · 本地 · 第 445 轮 / Round 443）：代码块补语言标签（解析层已有语言、渲染层从未显示；首行右侧标签墨 316/381、无语言臂 0；同文对照帧 + 2 张新帧、基线 250→252）；vibrant judged 22≠20 的 -2 条成因已修（产品 3 文件，代码块语言标识位）

最后更新：2026-10-28（本地 · R446 / 第 445 轮 / Round 443）：解析层从围栏信息串认出语言，呈现层只用了行数 —— ` ```swift ` 与 ` ```python ` 在详情里没有区别。新 `CodeLanguageTag` 纯策略（别名归一化、未知原样大写截 12、`text/plaintext` 与非 ASCII 不标；`fits` 要求首行正文右沿与标签间 ≥24pt，否则不画）；`MarkdownPresentation.codeLanguageAttribute` 只打在代码块正文；`ChineseSelectableNSTextView.drawCodeLanguageTags` 在首行右侧画（9pt semibold、右沿内缩 10pt、`secondaryLabelColor`），标签不进文本存储。读数：`CODE_LANGUAGE light 右区=492..628pt 标签墨=316 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`；`dark 381`（同形）。夹具 `detail-code`（```swift）与新 `detail-code-plain`（```，三行逐字相同）成对；**2 张新帧、4 张旧帧变化**（detail-code 亮/暗 + detail-markdown-rendered 亮/暗），基线 **250→252 / 0/0/0**；已看亮/暗 SWIFT、plain 无标签、markdown 一行 swift 块也有 SWIFT。`M1226/M1227` **2/2**（M1226 首跑红文漏「有」字，修 needle 后复跑红得对）；新单测 6 条 + 帧判据；预检 **224/206/586 bad=0**、ARM **317/1069**、HIDDEN **311/1003 rot=0**。⓪：一次快进 push **`eeccad0..fe956e3` success**（三笔）、HEAD=origin/main=`fe956e3`、**ahead=0**；head 跑 **`40617745753 ↔ fe956e3`** 在 ⓪ 时 **in_progress** ⇒ NOT-RUN（R445 代码首跑）；`40613782362 ↔ eeccad0` failure **1 步**＝vibrant judged 22≠20（2 条 nil-vibrant 不可判说明段被漏扣；本轮仪器修好，本地 44/44）；同跑 `CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`TABLE_HEADER 1.10/1.11`、`PROBE_DOMAIN 22/20` 与 `PROBE_DOMAIN_NOT_RUN 22`；`HISTORY_SEARCH_SOURCE` 在 eeccad0 上 test-not-in-commit ⇒ NOT-RUN；`40605228813 ↔ bdb4737` failure **2 步**（同一 vibrant + 设置关于行 0≠7，后者 R443 已修）。本地全量 **1218/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **252 帧**；基线 **252/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 445，`product_streak --streak-for 445`，last=56486a9）。清账在台账后复跑；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push eeccad0..fe956e3 success、ahead=0；eeccad0 唯一红＝vibrant 22≠20 已定位到 2 条 nil-vibrant 说明段并修；HISTORY_SEARCH_SOURCE 在 eeccad0 上不存在 ⇒ NOT-RUN；bdb4737 的 2 步红对上（后者 R443 已修）；head 跑 in_progress ⇒ NOT-RUN。
② 产品：代码块补语言标签（首行右侧、放不下不画；2 张新帧、4 张旧帧变化、基线 252）。
③ 判据：M1226/M1227 2/2；新单测 6 条 + 帧判据（标签墨/无语言臂/第二行/行号/正文左）；precheck 224/206/586；hidden rot 0。
④ 436：head 跑未完成，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 311 / 可判 1003 / rot 0。
⑥ 捕获 252 帧；基线 252/0/0/0；build 0 告警；换装 ok；本地全量 1218/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40617745753 ↔ fe956e3`（in_progress）；② eeccad0 的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 新跑 Motion floor；④ 长首行标签省略无帧（476）；⑤ HTML 代码块无语言标签（477）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 长来源截断（474）；㊱ bundle ID 未搜（475）；㊲ 437–477 的未结项仍开。

下一轮（R447）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R446 主笔+追记 head 跑、`40617745753 ↔ fe956e3`（R445 代码首跑）与 `40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `CODE_LANGUAGE` 两档 316/381/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1/行带 3（fe956e3 上才有）、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R446_REPORT_BULLET = u"""- **R446（代码块语言标识位）**：解析层从围栏信息串认出 `language`，呈现层只用了行数 —— ` ```swift ` 与 ` ```python ` 在详情里没有区别。新 `CodeLanguageTag` 纯策略（别名归一化、未知大写截 12、`text/plaintext`/非 ASCII 不标；`fits` 要求首行正文右沿与标签间 ≥24pt，否则不画）；`codeLanguageAttribute` 只打在代码块正文；`drawCodeLanguageTags` 在首行右侧画（9pt semibold、右沿内缩 10pt、`secondaryLabelColor`），不进文本存储。夹具 `detail-code`（```swift）与新 `detail-code-plain`（```，三行逐字相同）：`CODE_LANGUAGE light 右区=492..628pt 标签墨=316 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0`、dark 381；**2 张新帧、4 张旧帧变化**（detail-markdown-rendered 也有一行 swift 块），基线 **250→252 / 0/0/0**；已看亮/暗 SWIFT、plain 无标签。`M1226/M1227` **2/2**（M1226 首跑 needle 漏「有」字，修后复跑红得对）；新单测 6 条 + 帧判据；预检 224/206/586 bad=0、ARM 317/1069、HIDDEN 311/1003 rot=0。⓪：一次快进 push **`eeccad0..fe956e3` success**、HEAD=origin/main=`fe956e3`、ahead=0；head 跑 `40617745753 ↔ fe956e3` 在 ⓪ 时 in_progress ⇒ NOT-RUN；`40613782362 ↔ eeccad0` failure 唯一红＝vibrant judged 22≠20（2 条 nil-vibrant 说明段漏扣，已修，本地 44/44），同跑 CODE_LINE_NUMBERS 54.0/3/21.0/100%、HISTORY_ROW_SOURCE 139.0/74.0、SETTINGS_ABOUT_ROW 7/7、TABLE_HEADER 1.10/1.11；HISTORY_SEARCH_SOURCE 在 eeccad0 上 test-not-in-commit ⇒ NOT-RUN；`40605228813 ↔ bdb4737` failure 2 步（同一 vibrant + 设置关于行 0≠7，后者 R443 已修）。全量 **1218/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 252 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；清账在台账后复跑；电池 `Ran 683 / OK (skipped=5)`。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 445 轮（R446" in audit: raise SystemExit("REFUSED AUDIT 已有 R446")
if u"## Round 443 · R446" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 443")
if u"## D-442" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-442")
if u"代码块补语言标签" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**476." in backlog: raise SystemExit("REFUSED BACKLOG 已有 476")
if state.count(u"## R445 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R445 状态"))
U_CELL_OLD = u"U-31 … U-1652（R445 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R445 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_442 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R445 状态", STATE_SECTION + u"## R445 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1657（R446 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R445 节 ②", u"AGENT_STATE.md` 的 R446 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R446_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R446_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
