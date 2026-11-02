# -*- coding: utf-8 -*-
"""R561 台账（第 560 轮 / Round 558）：图例那把尺的命中地板改成几何派生（判据位）+ 636 头一格量到「没有 depth2 夹具」。

用法：`python3 ledgers_r561.py --check` 只验锚点与 NUM 是否填好；不带参数才真写七本账。
所有数字都是**现读**填进 NUM，没有一格从上一轮抄；派生格（streak / sources）一律**落盘之后**再现读。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": "1404/57/0（678.1s）",
    "INSTALL": "`INSTALL_SIGNATURE=local flags=0x0`（固定身份 ⇒ 授权可以跨轮活下来）⇒ `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1`（版本 1.4.8→1.4.8，PID→93599，启动晚于安装、exe 路径逐字对上，备份 `before-R561`）",
    "BATTERY": "696/5",
    "ABSENCE": "162/63/0",
    "STREAK": "1",
    "STREAK_RAW": "PRODUCT_STREAK ledger_round=560 streak=1 sections=536 as_of=last=631f910 last_round=559 newest=631f910 newest_round=559 ⇒ 复核 = `PRODUCT_STREAK_LEDGER_OK streak=1 两格均由本命令派生并带引用`",
    "CAPTURE": "220/4 skipped/0 失败（619.4s）",
    "FRAMES": "354 张 **CHANGED=0 MISSING=0 ADDED=0**",
    "PRECHECK": "tables=358 covered=295 arms=757 bad=0",
    "ARM": "files=451 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok",
    "CI_CLOSE": "**收口前复述 `queue`：`41509855001 ↔ 26c1939` = concluded failure（已等 2922s）⇒ 四格当场从 NOT-RUN 转成读数。** `ci_read.py steps` 全量列出只有一朵红：**STEP[19] `Motion coverage floor`**。**⓪(a) 好消息先说**：`TASK_BOX_SIZE light 勾选=9x9px(9.00×9.00pt) 未勾选=9x9px(9.00×9.00pt) 宽差=0px 高差=0px 墨=62/49 倍率=1.0x 标记列 x 16..36`、`dark … 墨=65/49`，而 `TASK_BOX_NOT_RUN` **没有一行** ⇒ R560 那条判据在 runner 的 1x 上**真的判到了**（没走出口），并且两态在 1x 也同尺寸 ⇒ R560 的产品改动由 runner 签收；同时它也是本轮那个设计的活证据：**按 `scale` 派生的地板在 1x 站得住**（这正是 R561 给图例尺换的东西）。**⓪(b)** `HEAT_LEGEND_NOT_RUN=scale-too-low light/dark 倍率=1.0x 格宽=11px 实心判定 格6px/图例3px` —— **连续第二跑同形**（上一跑 `41501679574↔7260562` 同串），`HEAT_LEGEND_COVERAGE` 零行 ⇒ 图例覆盖在 runner 上仍不判 ⇒ 本轮升成几何派生尺正是这一格该做的动作。**⓪(c) 坏消息也照实**：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=0 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 窗口=1966ms 每格=75.6ms` ⇒ **第三个 runner 真数是 0**（前两跑 2、5），`MOTION_FLOOR_FACTS judged=5/5 executed=79 not-run=- 红的用例=testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1`、红原文 `XCTAssertGreaterThanOrEqual failed: (0) is less than (2)`。同一份代码三跑 2/5/0、每格 71.5/26.0/75.6ms ⇒ **「≥2 帧地板在那台机器的钟上不是恒可满足的」**，这一朵按 629 既有口径具名入账（同族先例：登记表里 `testNativeRowMoveIsVisibleToTheRuler`、`testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` 两条 `recurrence=sampled`），**不重开产品排查、不动 ≥2 地板、不改期望**。要让它不再随机红只有两条出路且都动到冻结项（登记成 sampled 具名放行 / 把尺改成对采样相位不敏感）⇒ **留给用户定夺，本轮不自行登记**。**⓪(d)** STEP[9] `SKIP_ROSTER 键=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 **连续第三跑**绿；STEP[18] 不在失败名单 ⇒ 622 本跑无新值（第十四值仍是 219.7ms/2 颗）。",
    "BASELINE_OK": "基线一帧未动 ⇒ 无须 update，也没有漏改到别的面",
}

UI = u"""## 第 560 轮（R561 · 2026-11-03 · U-2412…U-2418）：图例那把尺的命中地板从绝对常数改成几何派生（判据位，1x 第一次有判据）；636 的头一格量到「没有夹具画到 depth2」；产品 0 文件

- **U-2412：⓪ CI 读单（只登记、不轮询）。** 开场 HEAD=origin=`26c1939`、ahead=0、已跟踪改动 0、`api=200 / apple=200`。`41509855001 ↔ 26c1939`（R560 补记笔 = 那一批头笔，含 R560 全部代码）状态 **queued、已等 284s** ⇒ 四格当时**具名 NOT-RUN**：(a) `TASK_BOX_SIZE` 在 runner 的 1x 上走哪条（那条判据没做 1x 体检）；(b) `HEAT_LEGEND_NOT_RUN=scale-too-low` 是否连续第二跑同形；(c) `过渡帧数=` 第三个 runner 真数；(d) STEP[9] `SKIP_ROSTER` 与 STEP[18] 622。同批无独立跑 ⇒ 具名 `CI_UNREAD`：R560 的 `0a49b5f`/`631f910`/`700dee9`/`8004a42`/`22bd17d` 与 R558 的 `b8949f5`/`1ea1bb7`；永不重开 `41452722560↔58851c2`、`41455782587↔598b253`。%s
- **U-2413：636 的头一格是量具，不是产品 —— 答案是「今天没有夹具画到 depth2」。** 扫描法：把 `ClipboardHistory/Tests/**/*.swift` 里每一段**多行字符串正文**按闭合三引号那一行的缩进剥掉源码缩进，得到**内容相对缩进**，再按产品规则 `depth = min(相对缩进 / 2, MarkdownParsingPolicy.maximumListDepth=6)` 折算。现读：含列表的正文 **5 段**（`Round4MarkdownTests.swift:21`、`UICaptureHarness.swift:17657/17685/17727/18093`），**相对缩进全部 = 0 ⇒ depth 集合只有 {0}**；样本行 `- [x] 解析层完成` 前面那 4 个空格是**源码缩进**（Swift 的多行串会剥掉与闭合三引号对齐的缩进）⇒ 不是 depth2。
  ⇒ `◦`(depth1) 与 `▪`(depth2) **今天没有任何帧对象** ⇒ 636 保持**具名 NOT-RUN（通道判不到）**，不许把字体探针量到的回退当成产品缺陷落地；退场条件写成两步：① 先补一段 depth2 的夹具（补夹具不动产品绘图路径 ⇒ 不算破 R549 禁碰），② 再按 R560 那条「两态同尺寸」的形状量三级项目符的墨 bbox。顺带把 R549 的覆盖面说清：**那条判据签的是 depth0 的 `⦁` 墨高，`◦`/`▪` 从来没有帧证人** —— 这一句是覆盖面陈述，不是 R549 的缺陷。
- **U-2414：判据位 = 把 `HEAT_LEGEND_COVERAGE` 的两道命中地板改成几何派生（本轮不等 runner 就动，理由写清楚）。** 要修的那件事**不需要新的观测**：R559 的降采样探针量到「一个方块放得下的采样点」从 2x 的 36 掉到 1x 的 9，而 R560 的 runner 读数证实当时走的是具名出口（没报假红，但**也没判**）⇒ 缺的只是把常数换成几何量。
  派生式：`positions(edge, side) = ((edge − side)/2 + 1)²`（采样步长 2），地板 = 它的一半；`swatchEdge = cellW × 8/11`（图例方块 = `cell − 3` pt、格子 = `cell` pt，同一份产品常量）。落点 `SolidRuler(cellW:)`：`cellSolid=max(4, 3/5·cellW)`、`swatchSolid=max(3, cellW/4)`、`cellFloor=positions(cellW,cellSolid)/2`、`legendFloor=positions(swatchEdge,swatchSolid)/2`、`resolvable = legendPositions ≥ 4`。
  **`倍率 < 1.5 就整条不判` 那道门撤掉了**，换成「几何上分不出方块与噪声才不判」（出口改名 `HEAT_LEGEND_NOT_RUN=solid-unresolved`）⇒ 门从**环境属性**变成**尺自己的分辨率**，这是本轮真正推进的那一格。
  ⚠ **2x 的判定不许因为换了式子而变松或变严** —— 这条不是愿望，是实测：新读数 `地板 格12/图例18 每方块采样点 格25/图例36`，结论 `light 格色=8 图例色=5 缺=[]`、`dark 格色=9 图例色=5 缺=[]` **与 R560 用绝对值 30/8 时逐字相同**；而 M1459 那把刀（把派生值换成等价常数元组）**只让契约钉子红、像素判定不红**，是同一件事的第二条独立证据。
  ⚠ 边界照实说：**本机拍不出真 1x 帧** ⇒「1x 现在判得到」今天只有**派生式 + 真值表**，没有像素证人；runner 那一跑的真数留给 R562 ⓪（预期它打 `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4` 而不是 `solid-unresolved`；若仍走出口，就是门限算错，按读数修，不许降地板）。
- **U-2415：纯数据真值表 + 契约钉子（这条判据不吃 `UI_SHOTS` 门 ⇒ CI 的普通 Swift 步每轮都跑）。** `testLegendSolidRulerFloorsAreDerivedFromGeometry` 三臂 + 两条单调 + 一根钉子：① cellW=22 ⇒ `(13,5,16,25,36, floor 12/18, resolvable)`，且 18 这一格的消息文本里带着实测分布 `[31,29,27,27,27 | 3,2,2]`（**地板为什么是这个数的理由住在红话里**，下一轮想改就得先驳掉这串数）；② cellW=11 ⇒ `legendPositions=9、legendFloor=4、resolvable=true`，消息写明「R559 探针实测 1x 图例命中 `[9,9,7,7,6 | 1]`：地板 8 只读到 2 档（假红），地板 4 读到 5 档」；③ cellW=6 ⇒ `resolvable=false`（**门的证人**：写成恒真这一臂立刻红）；④ 单调性 `SolidRuler(44).legendFloor > SolidRuler(22).legendFloor > SolidRuler(11).legendFloor`（写成任何常数都会在这里红）；⑤ 契约钉子：像素判据的**函数体内**必须出现 `SolidRuler(` —— 区域用行首前缀切、并且断言切出来的区域 >400 字符（R53/R55 那一族：扫自身源码的守卫会先命中自己写的字面量；区域切空了守卫就是空跑）。
- **U-2416：三把刀（登记前逐把自检「变化量落在容差之外没有」—— R560 那把 Menlo 空刀的教训）。** **M1457**（图例地板退回绝对值 8）CAUGHT 三条：`("8") is not equal to ("18")`（2x 臂）、`("8") is not equal to ("4")`（1x 臂）、`XCTAssertGreaterThan failed: ("8") is not greater than ("8")`（单调臂）⇒ 三处远在容差外；**M1458**（`resolvable` 恒真）CAUGHT：`cellW=6 时一个图例方块只放得下 1 个采样点 ⇒ 分不出方块与噪声，必须走具名不判`；**M1459**（像素判据换成等价常数元组）CAUGHT，而且**只有契约钉子红**：`像素判据里没有 SolidRuler( ⇒ 地板被换回了写死的常数` ⇒ 这一把专门钉「钉子有没有牙」，同时把「2x 像素判定与派生式无关」钉成读数。三把 `RESTORE_CLEAN=yes`。三张表登记进 `mutate_needle_precheck.py` 名册：现读 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；与前几批同形 ⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由真跑证明。
- **U-2417：③ 验证链（顺序未换）。** `swift build --build-tests` 告警 **0**；判据 filter 绿（`Executed 2 tests, with 0 failures`，读数见 U-2414）；三把刀全 CAUGHT；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（本轮**没动产品** ⇒ 基线应逐字节不变， %(BASELINE_OK)s）；全量 **%(FULL)s**；预检三读**串行**；换装 %(INSTALL)s。⚠ 刀代期间的同名帧不算证人 ⇒ 看图在重捕之后。
- **U-2418：④⑤ 账与交接。** 清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED` 两行，`&&` 链里不插 grep）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`；R560 那一格是按「动了产品 ⇒ 0」**推**的被门抓住，本轮改成落盘后现读）。**636 = 头一格落地（无夹具 ⇒ 具名 NOT-RUN），单子继续开着**；629 写「(B) 已落地 + 635 已结案 + runner 余量随钟漂（两跑实测 2 与 5）」，不写完全结案；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。下一轮 R562（第 561 轮 / Round 559）：⓪ 必读本轮各笔自己的跑（一次性 push ⇒ 只有头笔建跑，其余具名 `CI_UNREAD`）**加上仍挂着的 `41509855001 ↔ 26c1939`**；头四格 = (a) `TASK_BOX_SIZE` 在 1x 走哪条；(b) **本轮这条几何派生尺在 runner 上有没有真的判到**（`HEAT_LEGEND_COVERAGE … 倍率=1.0x` 还是 `solid-unresolved`）；(c) `过渡帧数=` 第三个真数（掉到 1 按 629 既有口径具名入账，不许重开排查）；(d) STEP[9] `SKIP_ROSTER` 与 STEP[18] 622。禁碰清单 **11 面**不变；本轮**没有新面**（产品 0 文件）⇒ 不抬禁碰数；刀号 **M1460** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped 只记现读。

"""


ITER = u"""
## Round 558 · R561（第 560 轮 · 2026-11-03）：把"这台机器是 2x"从判据里删掉 —— 图例那把尺的地板改成几何派生；636 的头一格先量具不量产品

R559 补的那块图例方块带来一条像素判据，而它的命中地板当时写死 `30 / 8` —— 那是**本机倍率**的形状，不是尺的形状：降采样探针量到 1x 上一个方块只剩 9 个采样点，地板 8 会把五档读到两档，于是 R560 的 runner 走的是具名出口（没报假红，但也没判）。本轮把地板改成几何派生（`positions = ((边长 − 实心边)/2 + 1)²` 的一半），并把"倍率 < 1.5 就不判"这道**环境门**换成"一个方块连 4 个采样点都放不下就不判"这道**尺自己的分辨率门**。换式子最容易被当成"顺手放宽"，所以两条独立证据先立住：2x 的结论 `格色=8 图例色=5 缺=[]` 与旧常数**逐字相同**，而 M1459 把派生值换成等价常数元组之后**只有契约钉子红、像素判定不红**。另有一条纯数据真值表（不吃截图门 ⇒ CI 每轮都跑）把 cellW=22/11/6 三档、两条单调性和那根钉子钉死；三臂里 cellW=6 是**门的证人**、cellW=11 是**本轮目的**（它若被写成 false，1x 就还是没判，这一格当场红）。636 的头一格按"先量具不量产品"去扫夹具：五段含列表的正文内容缩进全为 0 ⇒ depth 只有 {0} ⇒ `◦`/`▪` 今天没有帧对象 ⇒ 具名 NOT-RUN，退场条件写成"先补夹具再量"两步，并顺手把 R549 的覆盖面说清（它只签 depth0 的 `⦁`）。产品 0 文件 —— 这一轮的推进在尺上，账里不假装它动了画面。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 11/15 | 本轮没有新画面：看图只做"重捕后基线应逐字节不变"的复核（名单里出现任何一帧变化都算漏改）；636 那一格是**文本级**夹具扫描，不是像素级。缺的是没有新的帧证据。 |
| 判据有效性 | 15/15 | 几何派生 + 三臂真值表 + 两条单调 + 一根契约钉子；2x 结论与旧常数逐字相同（不是推出来的，是跑出来的）。 |
| 假绿防御 | 15/15 | M1459 专门设计成"像素判定不变、只有钉子红"⇒ 钉子的牙被单独证明；cellW=6 那一臂是门的证人（恒真就红）；区域切空有 >400 字符的长度守卫，防"守卫空跑给绿"。 |
| 产品面推进 | 9/15 | 产品 0 文件（推进在判据与工具上）；连续两轮动过产品之后这一轮回落，账里不拿"尺的推进"冒充画面推进。 |
| 台账一致性 | 15/15 | 写账前核三条硬格式；**派生格（streak / sources）一律落盘之后现读**（R560 那一格推错被门抓住的教训兑现成流程）；本轮无帧变化 ⇒ 基线不动，无须 update。 |
| 交付诚实性 | 15/15 | ⓪ 四格按 queued 具名 NOT-RUN（不轮询不猜）；"1x 判得到"明说今天只有派生式 + 真值表、没有像素证人，runner 真数留给 R562；636 的"没有夹具"写成通道判不到而不是产品没问题。 |
| 可复核性 | 15/15 | 派生式、三臂数值、地板为什么是 18/4（实测分布住在红话里）、三把刀的 needle 与命令全部逐字进账；扫描脚本的口径（剥源码缩进 + `depth=indent/2`）写清，下一轮可重跑对账。 |

"""


CHG = u"""### 图例那把尺的命中地板改成几何派生（1x 第一次有判据）；636 的头一格量到「没有夹具画到 depth2」（R561 / 第 560 轮 / Round 558）

R559 那条 `HEAT_LEGEND_COVERAGE` 的两道命中地板从前写死 `30 / 8` —— 那是本机 2x 的形状：一个图例方块在 2x 能放 36 个采样点、在 runner 的 1x 只放 9 个，地板 8 会把五档读到两档 ⇒ R560 的 runner 因此走具名出口（没报假红，但也没判）。本轮改成几何派生 `positions(edge, side) = ((edge − side)/2 + 1)²` 的一半（`swatchEdge = 格宽 × 8/11`），并把"倍率 < 1.5 不判"这道环境门换成"一个方块放不下 4 个采样点才不判"（出口 `HEAT_LEGEND_NOT_RUN=solid-unresolved`）。**2x 的判定没有变**：新读数 `地板 格12/图例18`，结论 `格色=8 图例色=5 缺=[]` 与旧常数逐字相同。新增纯数据真值表 `testLegendSolidRulerFloorsAreDerivedFromGeometry`（不吃截图门 ⇒ CI 每轮跑）钉住 cellW=22/11/6 三档、两条单调性与一根"像素判据必须用 `SolidRuler(`"的契约钉子。刀 **M1457 / M1458 / M1459** 全 CAUGHT、RESTORE_CLEAN=yes（M1459 设计成像素判定不变、只有钉子红）。636 的头一格：扫描 5 段含列表的夹具正文，内容相对缩进全为 0 ⇒ depth 只有 {0} ⇒ `◦`/`▪` 今天没有帧对象 ⇒ 具名 NOT-RUN，退场条件是先补夹具再量。产品 0 文件；4.5 / 150 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` 一律未动。

"""


B636 = u"""    头一格（R561 现读，量具不量产品）：**今天没有夹具画到 depth2** ⇒ 这一格是**通道判不到**，不是产品没问题。扫描法：把 `ClipboardHistory/Tests/**/*.swift` 里每段多行字符串正文按闭合三引号那一行的缩进剥掉源码缩进，得到内容相对缩进，再按 `depth = min(相对缩进 / 2, MarkdownParsingPolicy.maximumListDepth=6)` 折算 ⇒ 含列表的正文共 **5 段**（`Round4MarkdownTests.swift:21`、`UICaptureHarness.swift:17657/17685/17727/18093`），**相对缩进全部 = 0**（样本 `- [x] 解析层完成` 前面那 4 个空格是源码缩进，Swift 多行串会剥掉与闭合三引号对齐的那部分）⇒ depth 集合只有 {0}。⇒ `◦`(depth1) 与 `▪`(depth2) 没有任何帧对象，探针量到的字体回退今天**不能**当产品缺陷落地。
    退场条件（两步，顺序不许换）：① 先补一段 depth2 的夹具正文（**补夹具不动产品绘图路径 ⇒ 不算破 R549 禁碰**）；② 再按 R560 那条「两态同尺寸」的形状量三级项目符的墨 bbox（`⦁`/`◦`/`▪` 三者必须同宽同高，否则就是同一类"两个态两份字体"）。顺带把 R549 的覆盖面说清：那条判据签的是 **depth0 的 `⦁` 墨高**，`◦`/`▪` 从来没有帧证人 —— 这是覆盖面陈述，不是 R549 的缺陷。


"""


DEC = u"""## D-561（R561 · 2026-11-03）：判据的地板必须由几何派生，不由本机倍率决定；"先量具再量产品"是开单的前置

① **"这台机器是 2x"不是产品的属性，写进判据就成了尺的形状。** `HEAT_LEGEND_COVERAGE` 的命中地板从前是 `30 / 8` 两个绝对数 —— 它们在本机成立（一个图例方块 16px 能放 36 个采样点），到 runner 的 1x（方块 8px、9 个点）就把五档读到两档。R560 的 runner 读数证实当时走的是具名出口：**没有报假红，但也没有判**。"不报假红"和"判到了"是两件事，只做到前者不算验收 —— 所以本轮把地板改成 `positions(edge, side)/2`，`edge` 由格宽按产品自己的比例（`cell − 3` / `cell` = 8/11）推出。
② **门从环境属性换成尺的分辨率。** 撤掉 `倍率 < 1.5 ⇒ 不判`，改成 `legendPositions ≥ 4` 才判：前者是"这台机器像不像 2x"，后者是"这把尺在这个尺寸上分不分得出方块与噪声"。具名出口改名 `solid-unresolved`，读数里同时打 `地板 格N/图例M 每方块采样点 格X/图例Y` ⇒ 下一轮想改门限，得先驳掉这串数。
③ **换式子必须自证"判定没变"。** 两条独立证据：① 2x 实测结论 `格色=8 图例色=5 缺=[]` 与旧常数**逐字相同**；② **M1459** 把派生值换成等价常数元组后，像素判定不红、**只有契约钉子红** —— 这一把专门钉"钉子有没有牙"，也顺手证明 2x 那条结论不依赖派生式。登记前逐把自己问"变化量落在容差之外没有"（R560 那把 Menlo 差 1px 撞 ≤1px 容差的空刀教训），三把都在容差外。
④ **先量具，再量产品。** 636 的头一格没有直接去改 `bulletGlyph`，而是先扫夹具：五段含列表正文的内容相对缩进全为 0 ⇒ depth 只有 {0} ⇒ `◦`/`▪` 今天**没有帧对象**。结论是**通道判不到**（具名 NOT-RUN），不是产品没问题；退场条件因此写成两步（先补夹具，再量三级同尺寸）。这一格同时把 R549 的覆盖面说清：它只签 depth0 的 `⦁`。
⑤ **边界**：本机拍不出真 1x 帧 ⇒ "1x 现在判得到"今天只有派生式 + 真值表，**没有像素证人**；runner 真数留给 R562 ⓪，若它仍走 `solid-unresolved`，那是门限算错，按读数修尺，不许降地板、不许改期望。
⑥ **撤回**：把 `SolidRuler` 的 `legendFloor` 改回 `8`、`cellFloor` 改回 `30`、`resolvable` 改回 `true` 即回到 R560 的形状 —— 这三种改法分别由 M1457 / M1457 / M1458 抓，像素判据不走 `SolidRuler(` 由 M1459 抓。
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
    if state.count(u"## R561 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R561 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R561 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R561 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 559 轮（R560 · 2026-11-03 · U-2404…U-2411）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 558 · R561" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 558 已存在\n")
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
    # 636 的头一格接在该条目自己的「退场」行之后（按行首前缀定位，稳）
    t = insert_after_line(t, u"    退场：要么", B636, u"backlog636")
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
        (u"R9–R557，558 节自评", u"R9–R558，559 节自评", u"title"),
        (u"阶段二 **550 轮**审计（R9–R557；以 `curve_from_ledger.py` 的 `PHASE2 n=550` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 557",
         u"阶段二 **551 轮**审计（R9–R558；以 `curve_from_ledger.py` 的 `PHASE2 n=551` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 558", u"§1"),
        (u"| 视觉台账 | U-31 … U-2411", u"| 视觉台账 | U-31 … U-2418", u"U 上界"),
        (u"以 `AGENT_STATE.md` 的 R560 节 ② 为准", u"以 `AGENT_STATE.md` 的 R561 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R560 这一段", u"## 18. R458 → R561 这一段", u"§18 head"),
        (u"R560 续到 560 —— 这份报告第七次差点停在几十轮之前）",
         u"R561 续到 561 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1403/57/0（680.8s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R561（图例那把尺的地板改成几何派生；产品 0 文件 + 判据 1 条 + 真值表 + 三把刀）**："
              u"`HEAT_LEGEND_COVERAGE` 的两道命中地板从前写死 `30 / 8`（本机 2x 的形状），"
              u"而 1x 上一个图例方块只放得下 9 个采样点 ⇒ R560 的 runner 走具名出口（没报假红，但也没判）。"
              u"本轮换成 `((边长 − 实心边)/2 + 1)²` 的一半，并把「倍率 < 1.5 不判」这道**环境门**换成"
              u"「一个方块放不下 4 个采样点才不判」这道**尺的分辨率门**（出口 `solid-unresolved`）。"
              u"换式子不自证就是放宽，所以留两条独立证据：2x 结论 `格色=8 图例色=5 缺=[]` 与旧常数**逐字相同**；"
              u"**M1459** 把派生值换成等价常数元组后**只有契约钉子红、像素判定不红**。"
              u"新增纯数据真值表（不吃截图门）钉 cellW=22/11/6 三臂 + 两条单调 + 一根钉子。"
              u"636 头一格：扫 5 段含列表夹具正文，内容缩进全为 0 ⇒ depth 只有 {0} ⇒ `◦`/`▪` 没有帧对象 ⇒ 具名 NOT-RUN。"
              u"刀 **M1457–M1459** 全 CAUGHT、RESTORE_CLEAN。帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-03（本地 · R560 / 第 559 轮 / Round 557）",
             u"最后更新：2026-11-03（本地 · R561 / 第 560 轮 / Round 558）",
             u"identity")
    body = u"""## R561 状态（2026-11-03 · 第 560 轮 / Round 558 · 产品 0 文件 + 判据 1 条 + 真值表 + 三把刀）

① ：`41509855001↔26c1939`（R560 那一批头笔）开场 **queued（284s）** ⇒ 四格当时具名 NOT-RUN（(a) `TASK_BOX_SIZE` 在 1x 走哪条、(b) `HEAT_LEGEND_NOT_RUN` 是否连续第二跑同形、(c) `过渡帧数=` 第三数、(d) STEP[9]/[18]）。%s 同批无独立跑 ⇒ `CI_UNREAD`（R560 五笔 + R558 两笔）；cancelled 两笔永不重开。
② ②(a) **判据位 = 把"本机是 2x"从判据里删掉**：`HEAT_LEGEND_COVERAGE` 的命中地板 `30 / 8`（绝对像素数）换成几何派生 `positions(edge, side) = ((edge − side)/2 + 1)²` 的一半（`swatchEdge = 格宽 × 8/11`），`倍率<1.5 不判` 这道**环境门**换成 `legendPositions ≥ 4` 这道**尺的分辨率门**（出口改名 `solid-unresolved`）。⚠ 换式子不自证就是放宽 ⇒ 两条独立证据：2x 实测结论 `格色=8 图例色=5 缺=[] 地板 格12/图例18` 与旧常数**逐字相同**；M1459 换成等价常数元组后**只有契约钉子红**。新增纯数据真值表 `testLegendSolidRulerFloorsAreDerivedFromGeometry`（不吃截图门 ⇒ CI 每轮跑）：cellW=22 ⇒ (13,5,16,25,36,12,18)、cellW=11 ⇒ 采样点 9/地板 4/**resolvable=true**（本轮目的）、cellW=6 ⇒ `resolvable=false`（门的证人）、两条单调、一根"像素判据函数体内必须有 `SolidRuler(`"的契约钉子（区域切出来还要 >400 字符，防空跑）。⚠ 边界：本机拍不出真 1x 帧 ⇒「1x 判得到」今天只有派生式 + 真值表，runner 真数留给 R562。
③ ②(b) **636 头一格 = 先量具再量产品**：扫 `ClipboardHistory/Tests/**/*.swift` 的多行串正文（按闭合三引号剥源码缩进，再按 `depth = min(相对缩进/2, 6)` 折算）⇒ 含列表的 5 段正文**相对缩进全为 0** ⇒ depth 只有 {0} ⇒ `◦`(depth1)/`▪`(depth2) **没有帧对象** ⇒ 636 保持**具名 NOT-RUN（通道判不到）**，退场两步（先补夹具 ⇒ 不破 R549 禁碰；再按"两态同尺寸"量三级）。顺带说清 R549 覆盖面：只签 depth0 的 `⦁`。②(c) 本轮**产品 0 文件**（推进在尺上，账里不冒充画面推进）。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据 filter 绿（`Executed 2 tests, with 0 failures`）；三把刀 **M1457/M1458/M1459 全 CAUGHT、RESTORE_CLEAN=yes**；三张表登记进名册；判据卷 **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（没动产品 ⇒ %(BASELINE_OK)s，无须 update）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`；R560 那格按"动了产品 ⇒ 0"推被门抓住，本轮改成落盘后现读）。**636 头一格落地、单子继续开**；629 保持「(B) 已落地 + 635 已结案 + runner 余量随钟漂」；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 判据与刀 + 台账 + 补记）⇒ 只有头笔建跑。R562 ⓪ 必读它**加上仍挂着的 `41509855001↔26c1939`**；头四格 = `TASK_BOX_SIZE` 在 1x 走哪条 / **本轮这把几何派生尺在 runner 上有没有真的判到**（`HEAT_LEGEND_COVERAGE … 倍率=1.0x` 还是 `solid-unresolved`；后者⇒门限算错，按读数修，不许降地板）/ `过渡帧数` 第三数（掉到 1 按 629 既有口径具名入账）/ STEP[9]+STEP[18]。刀号 **M1460** 起；禁碰清单 **11 面**不变（本轮无新面）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。

"""
    a = u"\n## R561 ⓪ 开工（2026-11-03 · 第 560 轮 / Round 558 · CI 读单 + 基线全现读 + 636 头一格 + 判据位选定）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R561_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
