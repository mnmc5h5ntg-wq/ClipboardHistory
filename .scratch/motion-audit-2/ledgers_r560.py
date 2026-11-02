# -*- coding: utf-8 -*-
"""R560 台账（第 559 轮 / Round 557）：任务勾选框两个态钉到同一份字体（产品 1 文件 + 判据 1 条 + 两把刀）；新开 636。

用法：`python3 ledgers_r560.py --check` 只验锚点与 NUM 是否填好；不带参数才真写七本账。
所有数字都是**现读**填进 NUM，没有一格从上一轮抄。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NUM 必须在跑之前换成现读数（留 %(KEY)s 会被 NUM_NOT_FILLED 拦下）。
NUM = {
    "FULL": "1403/57/0（680.8s）",
    "INSTALL": "`INSTALL_SIGNATURE=local flags=0x0`（固定身份 ⇒ 授权可以跨轮活下来）⇒ `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1`（版本 1.4.8→1.4.8，PID→68706，启动晚于安装、exe 路径逐字对上，备份 `before-R560`）",
    "BATTERY": "696/5",
    "ABSENCE": "162/63/0",
    "STREAK": "1",
    "STREAK_RAW": "PRODUCT_STREAK ledger_round=559 streak=1 sections=535 last=3a3c9a9 last_round=558 newest=631f910 newest_round=559 ⇒ 写账时先按“动了产品 ⇒ 0”推了一格，落盘后 `--check` 报 `PRODUCT_STREAK_LEDGER_STALE 报告那一格写的是 0，git 派生是 1` ⇒ 派生格只能落盘后现读",
    "CAPTURE": "219/4 skipped/0 失败（617.5s）",
    "FRAMES": "354 张里 CHANGED=4 ⇒ 同一笔 `update` 之后复跑 `CHANGED=0 MISSING=0 ADDED=0`",
    "FRAME_LIST": "`detail-tasks-720x520-{light,dark}` + `detail-markdown-rendered-720x520-{light,dark}` = **正好是含任务标记的那两个夹具 × 两档外观**，名单外一帧都没有 ⇒ 改动没有漏到别处",
    "PRECHECK": "tables=355 covered=295 arms=757 bad=0",
    "ARM": "files=448 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=442 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok",
    "CI_CLOSE": "**收口前复述 `queue`：`41501679574 ↔ 7260562` = concluded failure（已等 2593s）⇒ 四格当场从 NOT-RUN 转成读数。** `ci_read.py steps` 只列出一朵红 —— **STEP[18] `On-screen probe coverage floor`**，正文 `PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1` + `FAILED testFrameIntervalsUnderStateChanges：最差帧 219.7ms 超过锚点 120ms，且超锚点的帧有 2 颗（容差 1 颗）` ⇒ **622 第十四值 = 219.7ms / 2 颗**（第十三值 225.3ms/3 颗）。归因对照：同一判据在 `41485625452↔8115ab8` 绿、在 R557 的 `41467585182↔ff15906` 红 ⇒ **同族既有红、按抽样出现**，R559 没碰那一卷 ⇒ 不署名为 R559 的回归；120ms 锚点与容差 1 颗都不动。**⓪(a) 预测被 runner 亲手证实**：`HEAT_LEGEND_NOT_RUN=scale-too-low light/dark 倍率=1.0x 格宽=11px 实心判定 格6px/图例3px`，而 `HEAT_LEGEND_COVERAGE` 在这一跑**没有一行** ⇒ 尺走了具名出口、没有报假红（R559 那次降采样探针量的 36→9 采样点是对的）。**⓪(b) `过渡帧数=` 的第二个 runner 真数 = 5**：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=2 首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=676ms 每格=26.0ms` ⇒ 这一跑每格 26.0ms（上一跑 71.5ms）⇒ 新口径在 runner 上已有两个数（**2 与 5**），629 那句「余量随钟漂」被两跑实测钉住；STEP[19] 不在失败名单 ⇒ 旧口径那朵红这一跑也没回来。**⓪(c)** STEP[9] `Release script tests` 不在失败名单 ⇒ 634 的修复**连续第二跑**绿。**⓪(d)** `TASK_BOX_SIZE`/`TASK_BOX_NOT_RUN` 在这一跑**没有一行** —— 那条判据属于本轮尚未推的代码 ⇒ 具名「判据不在这跑里（未推）」，**不许读成「没红」**；它的第一次 runner 读数留给 R561。",
    "TASK_DIM": "旧→新**逐字未变**（`TASK_DIM light 勾选=133.5 未勾选=85.2 差=48.3 墨数=1104/1175`、`dark 勾选=146.4 未勾选=184.3 差=-37.9 墨数=1233/1293`）",
    "SHOTS": "`/tmp/r560-tasks-oldvsnew.png`（上=旧、下=新，先亮档后暗档，3× 最近邻放大）",
}

UI = u"""## 第 559 轮（R560 · 2026-11-03 · U-2404…U-2411）：任务勾选框的两个态钉到同一份字体（产品 1 文件 + 判据 1 条 + 两把刀）；顺手量出第三级项目符也落在另一份字体上 ⇒ 新开 636

- **U-2404：⓪ CI 读单（只登记、不轮询）。** 开场 HEAD=origin=`7260562`、ahead=0、已跟踪改动 0、`api=200 / apple=200`。`41501679574 ↔ 7260562`（R559 补记笔 = 那一批头笔，内容含 R559 全部代码）状态 **queued、已等 297s** ⇒ 四格**具名 NOT-RUN**：(a) 新判据 `HEAT_LEGEND_*` 在 runner 上走 `scale-too-low` 还是判到；(b) `过渡帧数=` 的第二个 runner 真数（R559 首数 = 2、余量 0）；(c) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无`；(d) STEP[18]/[19] 复核。**没有轮询、没有拿"应该绿了"代替读数。** 同批无独立跑 ⇒ 具名 `CI_UNREAD`：R559 的 `809b963`/`3a3c9a9`/`bad7788`/`73e91f4`/`2f26d4c` 与 R558 的 `b8949f5`/`1ea1bb7`。永不重开：`41452722560↔58851c2`、`41455782587↔598b253`。%(CI_CLOSE)s
- **U-2405：产品位是看出来的、成因是量出来的 —— 不是"设计师给两个态定了两个尺寸"。** 看 `detail-tasks`：两行任务项正文逐字相同（`待办事项`），只有勾选态不同，而**两个框子明显不一样大**。逐像素现读（2x 帧）：勾选行标记墨 bbox **21×20px = 10.50×10.00pt（墨 222）**、未勾选行 **16×16px = 8.00×8.00pt（墨 112）**；暗档同形（21×21 / 16×16，墨 259/112）⇒ **同一个控件的两个态差 2.5pt**。两行正文左沿同为 x=73px ⇒ 文字是对齐的，不对齐的是框。
  成因不在产品代码里能读出来 —— `taskGlyph` 返回 `☑`(U+2611)/`☐`(U+2610) 两个**字符**，两者请求的是**同一个** `markerFont`（系统字体 13pt）。一次性字体探针（`/tmp/r560-font-probe.swift`，不入库 ⇒ 不能当证人，只当线索）现读：`☑` 由 **.SFNS-Regular** 画（advance 11.71×16.00），`☐` 在系统字体里**没有字形** ⇒ AppKit 换到 **AppleSymbols**（advance 10.79×16.00）⇒ **两个态来自两份字体**，框子自然不等大。同一探针给出候选：钉到 `Apple Symbols` 后两个字形度量完全相同（10.79×12.00，两份都落到 AppleSymbols）；`Menlo` 7.83×15.00 同度量；`Helvetica`/`PingFang SC` 也都把两者落到 AppleSymbols。
- **U-2406：判据先写、旧值先红。** 新判据 `UICaptureTests/testTaskCheckboxStatesShareOneGlyphSize`：① 两行带子由整行墨找（与 R450 的 `testCheckedTasksDimTheirText` **同一条找法** ⇒ 同一台机器上一条判得到、另一条不会瞎）；② 每行在**标记列**（x 16…36pt）里取墨 bbox；③ 断言宽差 ≤1px、高差 ≤1px（2x 上 = 0.5pt）。两种"读不到"分开处置，不混成一句：带子 <2 行 ⇒ 具名 `TASK_BOX_NOT_RUN=runner-detail-frame-plain`（与 R450 同族，那是**这台机器的帧是平的空帧**）；两行都在但标记列没墨 ⇒ **红**（`框子没画` 是产品缺陷，不许读成通道限制）。墨的下界按 `scale` 派生（`8.0 × scale` 个像素，理由是一个空方框的描边周长约 4s），**不写死像素数** —— R559 那一课：绝对像素地板在 1x 上会把"没有对象"读成假红。
  **旧值（红 4 条）**：`TASK_BOX_SIZE light 勾选=21x20px 未勾选=16x16px 宽差=5px 高差=4px`、`dark … 宽差=5px 高差=5px`（`/tmp/r560-crit-old.log`）。
- **U-2407：产品改法（共享绘图路径，先查再改）。** 只给**任务标记**这一条路钉一份"两个字形都有、度量相同"的具体字体（`taskMarkerFontName = "Apple Symbols"`，同 `pointSize`；取不到就退回原字体 —— 字体是系统状态，不是内部保证）。**钉在 `markerFont(for:)` 这一个函数里**：它既是渲染用的字体，也是 `hangingIndent` 量制表位用的字体，两处分开就会"画的字宽"与"让出来的位置"对不上（R488 那一族）。**项目符 `⦁  ▪` 与编号那条路一字不动**（R549 是禁碰面，见 U-2410 的 636）。
  改之前列出的受影响面：既有判据只有 `testCheckedTasksDimTheirText` 读这两行，旧值 `TASK_DIM light 勾选=133.5 未勾选=85.2 差=48.3 墨数=1104/1175`、`dark 勾选=146.4 未勾选=184.3 差=-37.9 墨数=1233/1293`（它读 x 40..300 的**正文**带，标记字形被排除 ⇒ 预期不动）；含任务标记的夹具正文有两处（`detail-tasks` 与共享的 `markdownFixtureBody`）。新值（绿）：`TASK_BOX_SIZE light 勾选=16x16px(8.00×8.00pt) 未勾选=16x16px(8.00×8.00pt) 宽差=0px 高差=0px 墨=145/112`、`dark … 墨=154/112` ⇒ **勾选那一态从 10.5pt 降到 8pt 去对齐未勾选**（未勾选本来就是 8pt，也就是今天出厂的样子 ⇒ 这一改是把少数派拉回多数派，不是把界面改成新样子）。兄弟判据重读：%(TASK_DIM)s。
- **U-2408：一把空刀 —— 第一版 M1455 砍不到东西，照实记。** M1454（把字体钉撤掉 ⇒ 复现旧形状）**CAUGHT**：`宽差=5px 高差=4px`（light）、`5px/5px`（dark），`RESTORE_CLEAN=yes`。M1455 的第一版把两个态分别钉到 Apple Symbols / **Menlo**，实测 `勾选=16x16px 未勾选=15x15px 宽差=1px 高差=1px` ⇒ **PASSED，不是 CAUGHT** —— 1px 正好落在容差（≤1px）里（R491 那一族：同值空刀不算刀）。换成 **Arial Unicode MS**（探针 advance 9.54×18.00）之后才 CAUGHT：`勾选=16x16px 未勾选=18x18px 宽差=2px 高差=2px`，两档各两条断言红、`RESTORE_CLEAN=yes`。
  ⇒ 这一格把契约说清楚：**这条判据钉的是"两个态的像素框同尺寸（≤1px = 0.5pt）"，不是"字体名字符串相同"**。所以"另一份字体但差 ≤1px"的写法它**不拦**，这是有意的（肉眼不可分辨的尺寸差不该是产品缺陷）；写账不许把它说成"任何字体混用都会红"。余量只有 1px（2 vs ≤1）也照实登记。
- **U-2409：重捕 + 逐张看图 + 基线同一笔 update。** 帧对账 `FRAME_BASELINE_COMPARED=354 %(FRAMES)s`；变化名单 %(FRAME_LIST)s。看图（%(SHOTS)s）：两行的框子现在同尺寸、正文左沿没有漂、8pt 的框在 13pt 正文旁仍读得出是"一个方框"（勾选里的那一撇没被吞）。⚠ 刀代之后同名旧帧不算证人 ⇒ 图是在重捕之后看的。
- **U-2410：顺手量到同一类缺陷的第二处 ⇒ 新开 636（只开单、不改面）。** 字体探针第二跑现读三级项目符在系统字体 13pt 下：`⦁`(U+2981, depth0) advance **8.11×16.00** 由 **.SFNS-Regular**；`◦`(U+25E6, depth1) **6.06×16.00** 由 **.SFNS-Regular**；`▪`(U+25AA, depth2) **12.00×16.00** 由 **.HiraKakuInterface-W4**（冬青黑体 ⇒ **回退**）。⇒ 与本轮任务框**同一类**：第三级项目符由另一份字体画。为什么本轮不动它：R549 项目符是**禁碰面**（那一轮的 ⦁ 墨高 2.8→3.9pt 是量过并签收的）。**没测的也写清**：今天没有任何夹具画到 depth2 ⇒ 帧上有没有对象未证 ⇒ 636 头一格就是先量"有没有 depth2 的帧"。**刀与名册**：**M1454**（撤钉）、**M1455**（两个态各钉一份字体）全 CAUGHT、RESTORE_CLEAN=yes；两张表登记进 `mutate_needle_precheck.py` 名册，现读 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`。⚠ 与前几批同形（`OLD`/`NEW` 常量 + `text.replace`）⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由真跑证明。
  **③ 验证链（顺序未换）**：`swift build` / `swift build --build-tests` 告警 **0**；判据 filter 先红（4 条）后绿（`宽差=0 高差=0`）；两把刀 CAUGHT；预检名册登记后 `bad=0`；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 + 基线同一笔 **%(FRAMES)s**；全量 **%(FULL)s**；预检三读**串行**；换装 %(INSTALL)s。
- **U-2411：④⑤ 账与交接。** 清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与补记之后复跑，结论只抄 `Ran`/`OK`/`FAILED` 两行，`&&` 链里不插 grep）；产品面连续零改动 **%(STREAK)s** 轮（as-of 559，现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`；本轮又动了 `Sources/` ⇒ 这一格由脚本派生、带取数命令引用，不抄 `--streak-for` 的口径差，那一格仍挂 BACKLOG 412）。**写台账之前先核了三条硬格式**（R559 的四朵自造红就是没做这一步）：七维表**七行**、CHANGELOG 是 `### …（R560 / ` **标题形状**、streak 一格**带命令引用** —— 落盘后电池第一遍的读数与是否再涨红，照实写在 STATE 的 R560 节 ⑤。**636 = 新开**（depth2 项目符落到冬青黑体）；629 保持「(B) 已落地 + 635 已结案 + runner 余量随钟漂」；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到，不写任何结论）。下一轮 R561（第 560 轮 / Round 558）：⓪ 必读本轮各笔自己的跑（一次性 push ⇒ 只有头笔建跑，其余具名 `CI_UNREAD`）**加上仍挂着的 `41501679574 ↔ 7260562`**，头四格 = (a) `HEAT_LEGEND_*` 在 runner 上走哪条；(b) `过渡帧数=` 第二个真数（掉到 1 就按 629 既有口径具名入账，不许重开排查）；(c) STEP[9] `SKIP_ROSTER`；(d) **本轮新判据 `TASK_BOX_SIZE` 在 runner 的 1x 上走哪条** —— 它没做 1x 体检（阈值全按 `scale` 派生），真数到手才算签收，若报 `TASK_BOX_NOT_RUN=runner-detail-frame-plain` 那是那条帧在 runner 上是平的空帧（与 R450 同族），**不许降墨下界、不许改期望**；禁碰清单 **10 面**不变；刀号 **M1457** 起（现读：本轮用到 M1454/M1455，M1456 未用 ⇒ 下一轮从 M1457 起，编号跨表唯一由 `ARM_TOTAL` 的 `dupes/repeats` 守）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。

"""


ITER = u"""
## Round 557 · R560（第 559 轮 · 2026-11-03）：任务勾选框的两个态原来由两份字体画；一把空刀把"判据到底钉什么"说清楚了

看 `detail-tasks` 时两行只差一个勾，框子却明显不一样大：逐像素量到勾选 21×20px（10.5pt）、未勾选 16×16px（8.0pt），而两行正文左沿同为 x=73px ⇒ 文字对齐、控件不对齐。代码里两个态请求的是**同一个** `markerFont`，所以这不是设计决定 —— 字体探针现读：`☑` 在系统字体里有字形（`.SFNS-Regular`），`☐` 没有 ⇒ AppKit 只给后者换到 AppleSymbols，于是"同一控件的两个态"实际是两份字体画的。修法沿用 R537 那一族：把任务标记钉到一份"两个字形都有、度量相同"的具体字体，且**只钉在 `markerFont(for:)` 一个地方** —— 它同时是渲染字体与 `hangingIndent` 量制表位的字体，分家就会让正文左沿与标记宽度对不上（R488 族）；项目符与编号那条路一字未动（R549 禁碰）。判据先写先红（宽差 5px、高差 4px，两档 4 条断言），改后 `宽差=0 高差=0`。本轮最值钱的一格是**一把空刀**：M1455 第一版把两个态分别钉到 Apple Symbols / Menlo，实测只差 1px，正好落在容差里 ⇒ PASSED 而不是 CAUGHT；换成 Arial Unicode MS（差 2px）才红。这件事把契约说清楚了：判据钉的是"两个态的像素框同尺寸（≤1px）"，**不是"字体名字符串相同"** —— 账里不许写成后者。顺手量到同一类缺陷的第二处（depth2 项目符 `▪` 落到冬青黑体），因为 R549 是禁碰面 ⇒ **只开单 636、不动面**，并写明"今天没有夹具画到 depth2"这一格未证。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 14/15 | 看图起头（两行框子不一样大）、逐像素定量（21×20 vs 16×16，两档外观）、重捕之后再看图确认 8pt 框仍读得出、正文左沿没漂。扣分：runner 的 1x 那一档今天没有证人。 |
| 判据有效性 | 15/15 | 判据先红后绿；两把刀方向不同（M1454 撤钉、M1455 两个态各钉一份字体）；两种"读不到"分开处置（带子不足 ⇒ 具名通道出口；框子没墨 ⇒ 红）。 |
| 假绿防御 | 15/15 | 本轮抓到的是**自己那把刀是空的**（Menlo 版 M1455 差 1px 落在容差内 ⇒ PASSED），换字体之后才 CAUGHT；并把"契约是像素同尺寸、不是字体名相同"写进账，防止下一轮把这句话说过头。 |
| 产品面推进 | 15/15 | 动了 `Sources/`（1 文件），有帧变化作证、有像素判据作证、两把刀；连续两轮落产品面。 |
| 台账一致性 | 15/15 | 七本齐；**写账前核了三条硬格式**（七维表七行 / CHANGELOG 标题形状 / streak 带命令引用），落盘后电池有没有再涨红照实写；基线与台账同一笔 update；sources 格排在产品笔之后派生。 |
| 交付诚实性 | 15/15 | ⓪ 四格按 queued 具名 NOT-RUN（没轮询、没猜）；空刀与"没做 1x 体检"都写进账；636 里"帧上有没有对象未证"明说；633 没拿到回执就不写结论。 |
| 可复核性 | 14/15 | 字体探针、两把刀命令、帧路径与 bbox、墨数全部逐字进账；⚠ 探针不入库 ⇒ 成因那一环只有本机一次性证据，下一轮要重跑才能复核（判据本身是像素的，不依赖探针）。 |

"""


CHG = u"""### 任务勾选框的两个态钉到同一份字体；第三级项目符开单 636（R560 / 第 559 轮 / Round 557）

`detail-tasks` 里两行任务项正文逐字相同、只有勾选态不同，但框子实测差 2.5pt（勾选 21×20px=10.50pt、未勾选 16×16px=8.00pt，两档外观同形）。代码里两个态请求的是同一个 `markerFont` —— 成因在字体层：`☑`(U+2611) 系统字体有字形，`☐`(U+2610) 没有 ⇒ AppKit 只给后者换到 AppleSymbols。本轮把**任务标记**钉到一份"两个字形都有、度量相同"的具体字体（`Apple Symbols`，同 pointSize），且只钉在 `markerFont(for:)` 一处（它同时是渲染字体与量制表位的字体）；项目符 `⦁ ◦ ▪` 与编号一字未动。新判据 `UICaptureTests/testTaskCheckboxStatesShareOneGlyphSize` 先红（宽差 5px / 高差 4px，两档 4 条）后绿（0 / 0）。刀 **M1454**（撤钉）、**M1455**（两个态各钉一份字体）全 CAUGHT、RESTORE_CLEAN；M1455 第一版用 Menlo 是**空刀**（差 1px 正落在 ≤1px 容差内），换 Arial Unicode MS 才红 ⇒ 契约是"像素同尺寸"，不是"字体名相同"。新开 **636**：depth2 项目符 `▪` 落到冬青黑体（同一类缺陷），因 R549 是禁碰面 ⇒ 只开单不改面。4.5 / 150 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` 一律未动。

"""


B636 = u"""**636. 第三级项目符 `▪` 由另一份字体画（与 635/任务框同一类：标记的字形来自回退字体）**（R560 字体探针现读并新开，本轮不改面）
    现读（系统字体 13pt，一次性探针 `/tmp/r560-bullet-probe.swift`）：`⦁`(U+2981, depth0) advance **8.11×16.00** 由 **.SFNS-Regular**；`◦`(U+25E6, depth1) **6.06×16.00** 由 **.SFNS-Regular**；`▪`(U+25AA, depth2) **12.00×16.00** 由 **.HiraKakuInterface-W4**（冬青黑体 ⇒ 系统字体里没有该字形，AppKit 回退）。⇒ 同一函数 `bulletGlyph(depth:)` 给出的三级项目符里，第三级与前两级不是同一份字体画的 —— 与 R560 修掉的任务勾选框（`☑` 走 .SFNS-Regular、`☐` 走 AppleSymbols，实测框子差 2.5pt）是**同一类缺陷**。
    为什么本轮只开单：R549（无序列表项目符 `⦁`）在**禁碰清单**里，那一轮的墨高 2.8→3.9pt 是量过并签收的；改 depth2 会动同一个函数与同一族判据，拿"顺手"的名义动它就是破禁碰规矩。
    下一轮的头一格（**未证的部分写在这里，别当成已知**）：今天**没有任何夹具画到 depth2** ⇒ 帧上有没有对象未证。先现读"有没有含三级列表的帧"：有 ⇒ 按 R560 那条判据的形状量三级的墨 bbox 是否同尺寸，再决定改法（钉具体字体，且必须钉在 `markerFont` 一处，让渲染与制表位同源）；没有 ⇒ 先补夹具再判，不许拿 advance 宽度当帧上判据。
    退场：要么"三级项目符同尺寸"这条判据配一把会红的刀落地，要么在账上具名"depth2 今天没有帧对象"并保持禁碰。


"""


DEC = u"""## D-560（R560 · 2026-11-03）：同一控件的两个态必须由同一份字体画；判据钉像素不钉字体名；砍不到东西的刀不算刀

① **两个态 = 一份字体**。`MarkdownPresentation.taskGlyph` 给勾选/未勾选返回 `☑`(U+2611)/`☐`(U+2610) 两个字符，两者请求同一个 `markerFont` —— 但**系统字体里只有 `☑` 有字形**，`☐` 被 AppKit 换到 AppleSymbols，于是同一张清单里两行的框子实测差 2.5pt（10.50×10.00 vs 8.00×8.00），而正文左沿都是 x=73px：文字对齐、控件不对齐。修法沿用 R537（代码语言标签改具体 Menlo-Bold）那一族：把**任务标记**钉到一份"两个字形都有、度量相同"的具体字体（`Apple Symbols`）。**只钉任务标记**：项目符 `⦁  ▪` 与编号那条路一字不动（R549 禁碰）。
② **钉在唯一取数口上**。`markerFont(for:)` 同时是渲染用的字体与 `hangingIndent` 量制表位用的字体 ⇒ 换字体必须在这一个函数里换。分两处改就会"画的字宽"与"让出来的位置"对不上（R488 那一族：制表位与字形不同源）。
③ **判据钉像素，不钉字体名**。契约写成"两个态的墨框宽高差 ≤1px（2x 上 = 0.5pt）"，不是"两份 `fontName` 字符串相等"。代价明说：另一份字体但差 ≤1px 的写法**不拦**（肉眼不可分辨的尺寸差不该算缺陷）。这条边界是被一把**空刀**逼出来的：M1455 第一版把两个态分别钉到 Apple Symbols / Menlo，实测 `16x16 vs 15x15`（差 1px）⇒ **PASSED**，不是 CAUGHT（R491：同值空刀不算刀）；换成 Arial Unicode MS（`16x16 vs 18x18`，差 2px）才红。⇒ 一把刀砍不到东西时，先问"它想砍的那件事是不是我真正在判的事"，把答案写进账，而不是悄悄把容差调小让刀变红。
④ **两种"读不到"必须分开**。带子 <2 行 ⇒ 具名 `TASK_BOX_NOT_RUN=runner-detail-frame-plain`（R450 同族：runner 的详情帧可能是平的空帧）；两行都在而标记列没墨 ⇒ **红**（框子没画是产品缺陷，不许读成通道限制）。墨的下界按 `scale` 派生（`8.0 × scale` 像素 ≈ 一个空方框的描边周长），不写死像素数 —— R559 刚为绝对像素地板在 1x 上会把"没有对象"读成假红记过一次。
⑤ **边界**：成因那一环（哪份字体画了哪个字形）只有**一次性字体探针**，不入库 ⇒ 不能当证人；判据本身是像素的，不依赖探针。同类缺陷的第二处（depth2 项目符 `▪` 落到冬青黑体）本轮**只开单 636 不改面**，因为 R549 是禁碰面，且"有没有夹具画到 depth2"今天未证。
⑥ **撤回**：把 `markerFont(for:)` 里那两行 `guard case … return NSFont(name:)` 换回 `return base` 即回到 R560 之前的形状（M1454 的形状会红）；帧基线退回上一笔 manifest 即可复原画面。
"""


def insert_after_line(t, line_prefix, block, label):
    u"""按**行首前缀**定位那一行，插到它后面（长行里有反引号与百分号时比抄整行稳）。"""
    hits = [i for i, ln in enumerate(t.split(u"\n")) if ln.startswith(line_prefix)]
    if len(hits) != 1:
        sys.stderr.write("ANCHOR_BAD %s lines=%d\n" % (label, len(hits)))
        sys.exit(1)
    i = t.index(line_prefix)
    j = t.find(u"\n", i)
    return t[:j + 1] + block + t[j + 1:]


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, t):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv

    for key, value in NUM.items():
        if u"%(" in value:
            sys.stderr.write("NUM_NOT_FILLED %s\n" % key)
            return 1


    state = rd("AGENT_STATE.md")
    if state.count(u"## R560 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R560 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R560 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R560 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 558 轮（R559 · 2026-11-03 · U-2395…U-2403）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 557 · R560" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 557 已存在\n")
        return 1
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(ITER))

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    a636 = u"**635. 「原文/渲染」标签的过渡接线没有任何会红的守卫**"
    t = once(t, a636, fill(B636) + a636, u"backlog636")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R556，557 节自评", u"R9–R557，558 节自评", u"title"),
        (u"阶段二 **549 轮**审计（R9–R556；以 `curve_from_ledger.py` 的 `PHASE2 n=549` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 556",
         u"阶段二 **550 轮**审计（R9–R557；以 `curve_from_ledger.py` 的 `PHASE2 n=550` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 557", u"§1"),
        (u"| 视觉台账 | U-31 … U-2403", u"| 视觉台账 | U-31 … U-2411", u"U 上界"),
        (u"产品面连续零改动轮数 = **2**（as-of 558；现读 `PRODUCT_STREAK ledger_round=558 streak=2 last=2ca9501 last_round=556 newest=3a3c9a9 newest_round=558`。⚠ 同一脚本 `--streak-for 559` 读 **1**，因为它按 subject 里的「第 558 轮」把本轮 A 笔归进 558 轮 ⇒ 口径差一那格仍挂 BACKLOG 412；账里用**门自己派生的那个数**）",
         u"产品面连续零改动轮数 = **%(STREAK)s**（as-of 559；现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`。⚠ 口径差一那格仍挂 BACKLOG 412：账里一律用**门自己派生的那个数并带取数命令引用**，不抄 `--streak-for` 的读数）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R559 节 ② 为准", u"以 `AGENT_STATE.md` 的 R560 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R559 这一段", u"## 18. R458 → R560 这一段", u"§18 head"),
        (u"R559 续到 559 —— 这份报告第七次差点停在几十轮之前）",
         u"R560 续到 560 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1402/57/0（699.0s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R560（任务勾选框两个态钉到同一份字体；产品 1 文件 + 判据 1 条 + 两把刀）**："
              u"`detail-tasks` 两行任务项的框子实测差 **2.5pt**（勾选 21×20px=10.50pt、未勾选 16×16px=8.00pt，两档外观同形），"
              u"而正文左沿同为 x=73px ⇒ 文字对齐、控件不对齐。代码里两个态请求同一个 `markerFont` —— "
              u"成因在字体层（探针现读：`☑` 走 `.SFNS-Regular`、`☐` 系统字体没字形 ⇒ AppKit 换 AppleSymbols）。"
              u"改法：只把**任务标记**钉到 `Apple Symbols`（两个字形度量相同），且钉在 `markerFont(for:)` 一处"
              u"（它同时是渲染字体与量制表位的字体）；项目符与编号一字未动。判据先红（宽差 5px/高差 4px，4 条）"
              u"后绿（0/0）。**一把空刀把契约说清楚**：M1455 第一版用 Menlo 只差 1px ⇒ PASSED，"
              u"换 Arial Unicode MS（差 2px）才 CAUGHT ⇒ 判据钉的是像素同尺寸（≤1px），不是字体名相同。"
              u"新开 **636**（depth2 项目符 `▪` 落到冬青黑体，R549 禁碰 ⇒ 只开单）。刀 **M1454–M1455** 全 CAUGHT。"
              u"帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-03（本地 · R559 / 第 558 轮 / Round 556）",
             u"最后更新：2026-11-03（本地 · R560 / 第 559 轮 / Round 557）",
             u"identity")
    body = u"""## R560 状态（2026-11-03 · 第 559 轮 / Round 557 · 产品 1 文件 + 判据 1 条 + 两把刀）

① ：`41501679574↔7260562`（R559 那一批的头笔）开场 **queued（已等 297s）** ⇒ 四格具名 NOT-RUN：(a) `HEAT_LEGEND_*` 在 runner 上走哪条、(b) `过渡帧数=` 第二个真数、(c) STEP[9] `SKIP_ROSTER`、(d) STEP[18]/[19]。%(CI_CLOSE)s 同批无独立跑 ⇒ `CI_UNREAD`（R559 五笔 + R558 两笔）；cancelled 两笔永不重开。
② ②(a) **产品位 = 任务勾选框的两个态由两份字体画**：`detail-tasks` 两行正文逐字相同、只有勾选态不同，框子实测差 2.5pt（勾选 21×20px=10.50×10.00pt 墨 222、未勾选 16×16px=8.00pt 墨 112；暗档同形），正文左沿同为 x=73px ⇒ 文字对齐、控件不对齐。成因由一次性字体探针现读：`☑`(U+2611) 走 **.SFNS-Regular**（advance 11.71×16.00）、`☐`(U+2610) 系统字体**无字形** ⇒ AppKit 换 **AppleSymbols**（10.79×16.00）。改法：只给任务标记钉 `Apple Symbols`（两个字形度量相同），钉在 `markerFont(for:)` 一处（渲染与量制表位同源，R488 族）；项目符 `⦁ ◦ ▪` 与编号一字未动（R549 禁碰）。判据 `testTaskCheckboxStatesShareOneGlyphSize` 先红（宽差 5px/高差 4px，两档 4 条断言）后绿（`宽差=0 高差=0`）；带子 <2 行 ⇒ 具名 `TASK_BOX_NOT_RUN=runner-detail-frame-plain`，两行都在而框子没墨 ⇒ **红**；墨下界按 `scale` 派生（不写死像素）。
③ ②(b) **一把空刀把契约说清楚**：M1454（撤钉）CAUGHT；M1455 第一版把两个态分别钉到 Apple Symbols / **Menlo** ⇒ 实测差 **1px**，正落在容差（≤1px）内 ⇒ **PASSED（空刀）**；换 **Arial Unicode MS** 后 `16x16 vs 18x18`（差 2px）才 CAUGHT。⇒ 这条判据钉的是**像素同尺寸**，不是"字体名相同"；账里不许写成后者，余量只有 1px 也照实登记。②(c) 同类缺陷第二处 ⇒ **新开 636**（depth2 项目符 `▪` 落到 **.HiraKakuInterface-W4**，advance 12.00×16.00，而 `⦁`/`◦` 是 .SFNS-Regular）：R549 禁碰 ⇒ 只开单不改面，且"有没有夹具画到 depth2"今天未证，写进 636 头一格。
④ ③ 验证链（顺序未换）：`swift build` / `--build-tests` 告警 **0**；判据 filter 先红后绿；两把刀全 CAUGHT、RESTORE_CLEAN=yes；两张表登记进名册（`bad=0`）；判据卷 **%(CAPTURE)s**；帧重捕 + 基线同一笔 **%(FRAMES)s**（名单 %(FRAME_LIST)s）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑤ ⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`；⚠ 本轮**写账前核了三条硬格式**（七维表七行 / CHANGELOG `### …（R560 / ` 标题 / streak 带命令引用）⇒ 落盘后第一遍电池有没有再涨红照实写在这里：%(BATTERY)s）；产品面连续零改动 **%(STREAK)s** 轮（现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`；本轮又动了 `Sources/`，这一格由脚本派生）。**636 = 新开**；629 保持「(B) 已落地 + 635 已结案 + runner 余量随钟漂」；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 产品与判据与刀 + 台账 + 补记）⇒ 只有头笔建跑，R561 ⓪ 必读它**加上仍挂着的 `41501679574↔7260562`**。刀号 **M1457** 起（M1456 未用）；禁碰清单 **10 面**不变；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。⚠ 新判据 `TASK_BOX_SIZE` **没做 1x 体检**（阈值全按 `scale` 派生）⇒ runner 第一跑真数到手才算签收；若报 `TASK_BOX_NOT_RUN=runner-detail-frame-plain` 那是那条帧在 runner 上是平的空帧（R450 同族），不许降墨下界、不许改期望。

"""
    a = u"\n## R560 ⓪ 开工（2026-11-03 · 第 559 轮 / Round 557 · CI 读单 + 基线全现读 + 产品位选定）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R560_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
