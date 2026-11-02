# -*- coding: utf-8 -*-
"""R558 台账（第 557 轮 / Round 555）：629 按 (B) 换判据对象落地 + 634 拆三态 + 新开 635。

用法：`python3 ledgers_r558.py --check` 只验锚点；不带参数才真写七本账。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": "1400/57/0（748.1s）",
    "INSTALL": "`INSTALL_SIGNATURE=local`（Authority=ClipboardHistory Local Signing）⇒ `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1`（版本 1.4.8→1.4.8，PID→92658，备份 `before-R558`）",
    "BATTERY": "696/5",
    "ABSENCE": "162/63/0",
    "STREAK": "1",
    "CAPTURE": "217/4 skipped/0 失败（781.0s）",
    "FRAMES": "354 CHANGED=0 MISSING=0 ADDED=0",
    "PRECHECK": "tables=349 covered=295 arms=757 bad=0",
    "ARM": "files=442 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=436 可判=1183 rot=0 抽不出=6 处置=ok",
}

UI = u"""## 第 557 轮（R558 · 2026-11-03 · U-2387…U-2394）：629 按 (B) 换判据对象落地（判据 1 文件 + 电池观察者 1 文件 + 四把刀）；顺手量出「这条胶片不能为接线签字」并新开 635

- **U-2387：⓪ CI 读单（只登记、不轮询）。** HEAD=origin=`ff15906`、ahead=0、已跟踪改动 0。三跑收口时已到手且本轮逐条对照：`41450045802↔5ba5b2f`、`41450081248↔680aea3`、`41450601769↔ccab101` 全部 conclusion=failure，唯一失败步骤都是 **STEP[9] Release script tests**（红名 = sources-cell 那一族 + `test_skip_roster`）；本轮另用 `gh run view --json jobs` 把整张步骤表读全 ⇒ **STEP[1]–[8] 与 STEP[15]–[19] 全是 success**，只有 STEP[10]–[14] 被连带 skipped。**`ci_read.py steps` 只列 failure/skipped，会把这件事藏起来**：上一轮我由它推过「后面的判据步骤没跑」，是反话（那三跑里 629 的三个 runner 真数就是这么读到的）。`41452722560↔58851c2` 与 `41455782587↔598b253` 各跑 15m01s 被 **cancelled**、0 失败步骤、`--log` 直接 `log not found: 125311960175` ⇒ 具名 NOT-RUN（第四种「读到 0 行」的坏法）。
  **收口前补读（本轮 ⓪ 那四跑 + ⓪ 笔自己的跑，`ci_read.py queue` 现读，全部已 concluded）**：
  - `41465486002 ↔ 5d05578`（R557 台账笔）= **success**；`41467173705 ↔ 61285b6`（R557 补记笔）= **success**；`41469418563 ↔ 2f85c5d`（**本轮 ⓪ 笔**，纯台账、账上格与 git 一致）= **success** ⇒ R557 那一条因果链被 runner 亲手签掉了：**sources 格一致的那三跑 STEP[9] 全绿**，而格不一致的 `ce4da8f` 红 ⇒ `test_skip_roster` 的「内层没有结论行」确实是**借来的红**（634 的机制成立），不是 flake。
  - `41464892684 ↔ ce4da8f`（R557 刀表笔）= **failure**，失败步骤只有 **STEP[9]**（10–14 skipped）⇒ 与预测一致：那一笔推的时候 R557 台账还没写，账上格必然与 git 不一致 ⇒ **本轮不再分批 push**。
  - `41467585182 ↔ ff15906`（R557 补记第二笔）= **failure**，STEP[9] **绿**，红在 **STEP[18] On-screen probe coverage floor** + **STEP[19] Motion coverage floor** 两朵：`PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1`，红名 `testFrameIntervalsUnderStateChanges：最差帧 225.3ms 超过锚点 120ms，且超锚点的帧有 3 颗（容差 1 颗）` ⇒ **622 的第十三值 = 225.3ms / 3 颗**（阈值 120ms 与容差 1 颗都不动）；另一朵 `MOTION_FLOOR_SUITE_RED=1 … 未登记的红用例：testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1`、`judged=4/5 executed=77 not-run=notice-banner`、`MOTION_FLOOR_NOT_SEEN=2`（两条登记红这一遍没抽中，只说明没抽中，不说明修好了）。
  - 同一跑的旧口径读数（`ci_read.py readings`，正文从 `Motion filmstrip (report-only)` 步骤取）：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=1 峰值=0.0193 声明=200ms 窗口=756ms 每格=29.1ms 相邻帧差=[0.0000×8,0.0193,0.0000,0.0000]` ⇒ **runner 上旧口径第四次读数就是那朵红本身（1 < 2）**。⚠ 这一行**不能**推出新口径会读几：旧行给的是二值阈值的相邻差，新尺要的是连续距离 —— 这正是本轮把两把尺一起打印的原因。⇒ **629 的新口径在 runner 上仍 NOT-RUN**（新尺在未推的那一笔里），R559 头一格读它。
- **U-2388：旧值先量 —— 一把砍不到东西的刀把一个假绿挖了出来。** M1446 的第一版按常规设计成「摘掉 `MarkdownModeButton` 的 `.id(title)`」，实测 **PASSED（不是 CAUGHT）**：本机读数与未变异**逐字相同**。于是补一支一次性探针（`.scratch/motion-audit-2/probe_r558_what_the_film_measures.py`，不入库）把三行接线一根一根摘、再全摘：**四臂的 `过渡帧数`/`相邻差帧数`/`峰值`/`相邻差序列` 与未变异全部相同**，只有 `窗口`/`每格` 随时钟抖（321–330ms / 12.4–12.7ms）。⇒ 这条胶片能为「用户看到没有中间态」签字，**不能为那三行接线签字**；而现读全仓 `grep -rl "id(title)" ClipboardHistory/Tests/` 只命中 `MotionFilmstripTests.swift` 自己 ⇒ 那三行**没有任何会红的守卫**（既没有管线证人也没有契约钉子）⇒ 新开 **635**，本轮不改产品、不动那三行。探针第二半同时给出**对象**证据：这卷里唯一在变的像素是 `行 25…34 列 69…89`（160×60 的 1x 帧，10×21px），正是 11pt 两个汉字的字形框，且逐帧变化像素 132→107→95→66→27→3→0 递减、暗墨像素 8→5→1→2→7→9 →交叉淡入是真的在演。
- **U-2389：629 按 (B) 落地 —— 判据对象从「相邻差的非零格数」换成「两端夹逼的连续距离」。** 依据是 R557 补记里那三个 runner 真数（每格 22.6–28.1ms、27 帧里只 2 格非零、其余逐格 `0.0000`）：旧口径吃的 `changedFraction` 是**二值阈值**占比（单像素 max(|Δrgb|,|Δa|) > 8 才算变），它在淡入中段就饱和 ⇒ 一次过程在这把尺上只剩两条**边**，数的是边、分母是那台机器的钟，相位一挪就从 2 掉到 1。新口径 `sandwichFrameCount` 不碰相邻帧，用连续量 `meanDistance`（同一张采样网格、同一组四通道取 `max` 再取平均，不过阈值）分别量每帧离「触发前静置」与离「落定后静置」，**两边都 ≥ 首末差 × `stepFloorRatio`** 才算过程帧；「这一卷有没有拍到交换」仍由**原有**的阈值口径 `endpointChangedFraction ≥ minimumVisibleChange` 把关 ⇒ 两把尺各管各的量纲，谁也不抄谁的地板。**地板 ≥2 一个字没动**，120ms 阈值、`.contentFade` 声明时长、4.5/150/2x 8.0pt/1x 6.0pt 全部不动。同笔把场景的**驱动**换成产品自己的那条路（原来是夹具 `withAnimation(contentFade){ toggle() }` —— 插值是夹具给的；产品调用点是 `markdownMode = markdownMode.toggled()`，不带 withAnimation）。新值本机现读：`过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 峰值=0.0097 每格=12.5ms`，逐帧 `离前=[0.0003,0.0013,0.0018,0.0021,…0.0030]` 单调上升、`离后=[0.0029,…0.0000]` 单调下降 ⇒ 中间态有 5 帧，余量不是零。旧口径的数与新口径的数**一起打印**（R146 那一课：换口径这件事要在日志里看得见两个数），读数另加 `唯一变化区=` 让「对象是标签」这句话下一轮还能复查。
  **最终现读（收口前重跑那一次，`/tmp/r558-films/motion-readings.log`）**：`帧数=27 过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 峰值=0.0145 声明=200ms 窗口=329ms 每格=12.6ms`，`离前=[0.0000,0.0011,0.0018,0.0020,0.0024,0.0026,0.0028,0.0029,0.0030,0.0030,0.0030,0.0030]` 单调升、`离后=[0.0031,0.0023,0.0016,0.0011,0.0008,0.0005,0.0003,0.0002,0.0001,0.0001,0.0000,0.0000]` 单调降，`唯一变化区=行 25…34 列 69…89（10×21px，帧 160×60）`。
  **真实看图（重捕之后，不是 M1446 变异时那张）**：`/tmp/r558-films/markdown-mode-label-1x-strip.png` 放大逐格读 —— 第 0–1 格「原文」、**第 2–3 格两幅字半透明叠在一起（看得见 ghost）**、第 4 格起「渲染」落定；逐格暗墨像素 `13,13,9,7,12,13,15,17`（中段掉到 7 再升回 17）⇒ 中间态不是只有读数，肉眼看得见。⚠ 上一 turn 遗留在 `/tmp/motion-films` 的那张 strip 是**变异时**的产物（27 格逐格相同、暗墨恒 13），不能当证人 —— 本轮重捕后才看图，这一格照实写。
- **U-2390：真值表 + 负向臂 —— 新尺必须有牙，而且不许悄悄换回去。** `testSandwichCountJudgesInterpolationNotSamplingPhase`（合成帧，不吃 `CLIPBOARD_HISTORY_UI_MOTION` 门 ⇒ CI 的普通 Swift 步就跑）四臂：台阶保持四帧 = 新 **4** / 旧 **2**；同一次过渡粗相位 = 旧 **1**（正是 runner 那朵红的形状）而新 **0**（硬切就该读 0，不是读 1 蒙混）；密采斜坡 = 新 **3**；**只离前态 1/255 的那一帧 = 新 1** —— 最后这一臂是**余量本身的证人**：合成端点是逐字节相同的，没有它，「把 `>= 余量` 写成 `> 0`」这种改法在前三臂上读数一模一样，刀就砍不到东西。负向臂 M1446 重做成「抹平状态差」：夹具把 title 钉成常量 ⇒ 现读 `过渡帧数=0 首末连续差=0.0000 峰值=0.0000`，两条断言各红一次（`根本没拍到任何交换` 与 `只读到 0 个中间帧`）⇒ 判据不是恒绿机器，且「没交换」与「硬切」两种成因各有各的一句话。
- **U-2391：634 落地 —— 观察者不许把被观察者的红借成自己的缺席。** `scripts/tests/test_skip_roster.py` 从前只有两种读数（有 `OK (skipped=N)` / 「内层没有结论行」），而 `SKIPPED_SUMMARY` 只认 OK 形状 ⇒ 内层只要有任何一条红，汇总行就是 `FAILED (…)`，这一格就以「没跑完」红 —— runner 三跑实测与 sources-cell 那一族同时红，本机 R553/R554/R556 那三次「flake」标签也是同一件事。现在抽出纯函数 `inner_summary_verdict` 给**三种**读数：`no-summary`（真缺席 ⇒ `SKIP_ROSTER_INNER_NO_SUMMARY=1` 具名出口，不许冒充缺席也不许读成通过）/ `inner-red`（仍然红，但正文必须带内层汇总行与原样红名）/ `ok`（照旧对账）。真值表 `test_inner_summary_has_three_readings_not_two` 把三份文本并排喂进去，并把「旧那颗尺在 red 文本上取到 None」一起钉住 ⇒ 下一轮有人把它合回去就红。摘录里 `skipped=` 一律改写成 `跳过了=`（R292/341 那条键名规矩，读数行不许与 unittest 的结论行抢键名）。**没有放宽任何门**：红还是红，只是不再谎报成因。
- **U-2392：刀与名册。** **M1446**（夹具 title 钉成常量 ⇒ 判据必须红）CAUGHT；**M1447**（`if dBefore >= margin && dAfter >= margin` 改成 `> 0 &&` 摘掉余量）CAUGHT：`("2") is not equal to ("1") - 只离前态 1/255 的那一帧不该算过程帧`；**M1448**（`&&` 换成 `||` 只看一端）CAUGHT 三条：`("6") is not equal to ("0") - 一帧硬换却被新口径数出中间帧`、`("6")…("4")`、`("3")…("1")`；**M1449**（把三种读数合回两种：`inner-red` 那一支改回返回 `no-summary`）CAUGHT：`'inner-red' != 'no-summary'`。四把全 `RESTORE_CLEAN=yes`。四张表登记进 `mutate_needle_precheck.py` 的名册，现读 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`。⚠ 这四张表与 R557 那三张同形（`OLD`/`NEW` 常量 + `text.replace`），静态抽不出 needle ⇒ 它们**不在 `covered` 里**，会红性只由真跑证明；这条限制照实写进账，不当成覆盖。
  **本轮自己造出来的那一朵红（照实入账，不藏）**：新尺 `meanDistance` 被既有名册守卫 `testEveryTwoStateRulerReadsBothAxes`（AXIS_GUARD）点成「两态尺只读亮度」⇒ 读数 `名册=5` 而扫到 `6`，全量出现 **1 红**（取证跑 `/tmp/r558-full.log`，那一跑是修之前的树，只算取证不算最终数）。成因不是产品：`alpha` 参与判定的那一步我写成了 `max(rgb, alpha)`，而这一格按**行**读「同一行里既有这根轴、又跟别的东西比大小」。**修法走的是补形状，不是登记豁免、不是放宽守卫**：改成 `sum += Double(rgb > alpha ? rgb : alpha)`（计算逐字等价），复跑 AXIS_GUARD `Executed 1 test, with 0 failures`。退场条件：这一格从此不许因为新尺而加名单；若哪条真只读一根轴，必须带 ≥60 字理由并且下一轮现读 `名册=N 扫到=N` 相等。这一格也是 D-558 第⑤条的由来。
- **U-2393：③ 验证链（顺序未换）。** `swift build --build-tests` 告警 **0**；判据 filter（真值表 + AXIS_GUARD 复跑 `Executed 1 test, with 0 failures`）绿；四把刀全 CAUGHT；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s`（本轮产品 0 文件 ⇒ 画面应逐字节不变，基线无须 update）；全量 **%(FULL)s**；换装 %(INSTALL)s。链条里唯一一朵红是本轮自己造的（U-2392 末段那格 AXIS_GUARD），修的是新尺的写法而不是名册。
- **U-2394：④⑤ 账与交接。** 清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与补记之后复跑，结论只抄 `Ran`/`OK`/`FAILED` 两行，`&&` 链里不插 grep）；产品面连续零改动 **%(STREAK)s** 轮（as-of 557，`python3 scripts/product_streak.py --streak-for 557` 现读，last=`2ca9501`/556）⇒ 本轮**产品 0 文件**（动的是判据 1 文件 + 电池观察者 1 文件），所以那一格下一轮仍由脚本派生，不手抄。**629 = 落地**（换判据对象 + 负向臂 + 真值表；≥2 地板未动）；**634 = 落地**（三态读数 + 具名出口）；**635 = 新开**（那三行接线没有任何会红的守卫）；622/624/627 继续；628/625/626/569/616/632 已落地那半不重开；**633 仍等用户人工回执**。⑥ 的新规矩本轮兑现：产品/判据/刀/台账**全部落盘并跑完电池之后一次性 push**，不分批 ⇒ 不再造出 STEP[9] 注定红的中间跑（R557 自伤那一格）。下一轮 R559（第 558 轮 / Round 556）：必读本轮各笔自己的跑（逐条抄全部失败步骤，success 步骤另读 `jobs[].steps`）—— ⓪ 笔那跑 `41469418563 ↔ 2f85c5d` 已到手 success，A/台账/补记三笔取号时未创建 ⇒ 具名 NOT-RUN；**头一格 = 复核 runner 上新的 `过渡帧数=`（新口径）读几**，以及 634 之后 STEP[9] 的 `test_skip_roster` 还红不红；禁碰清单 9 面不变；刀号 **M1450** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板均不动。

"""

ITER = u"""
## Round 555 · R558（第 557 轮 · 2026-11-03）：629 换判据对象落地；一把砍不到东西的刀挖出一个假绿

判据对象从「相邻差的非零格数」（二值阈值、分母是那台机器的钟、数的是边）换成「两端夹逼的连续距离」（平均幅度、分母是首末差、数的是中间帧），`≥2` 这个数字没动。落地前 M1446 按常规设计成「摘掉产品那三行接线」，实测**砍不到东西** —— 四臂探针证明那三行全摘之后读数逐字相同，于是这条胶片过去几轮的绿里有一枚是假绿（它不为接线签字，而全仓没有任何 grep 守卫钉那三行 ⇒ 新开 635）。负向臂因此重做成「抹平状态差」，加上合成四臂真值表（含"只离前态 1/255"那一臂，它是余量本身的证人）。634 同轮落地：观察者从前把内层的红读成「内层没有结论行」，现在拆成三态并配真值表，红还是红，只是不再谎报成因。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 14/15 | 重捕之后逐格看了：第 2–3 格两幅字半透明叠在一起（ghost 看得见），逐格暗墨 13,13,9,7,12,13,15,17；并拒掉了 M1446 变异时那张 27 格相同的旧 strip。 |
| 判据有效性 | 15/15 | 负向臂（抹平状态差 ⇒ 判据红）+ 四臂真值表（硬切 ⇒ 0、台阶保持 ⇒ 4、粗相位 ⇒ 0 而旧口径 1）+ 接线探针（证明判据**不**为接线签字，写进 635 不伪装成产品判据）。 |
| 假绿防御 | 15/15 | 本轮的最大产出就是一个假绿被挖出来；`covered` 里抽不出 needle 的四张表照实登记为"不在覆盖里"。 |
| 产品面推进 | 11/15 | 产品 0 文件（协议允许：真实推进落在判据卷 + 观察者本身），但接线那一格只做到"发现没有守卫"，没做到"补上守卫"。 |
| 台账一致性 | 14/15 | 七本齐；sources 格按 R556 教训排在产品笔之后（本轮无产品笔 ⇒ 由现读 `账上=… git=…` 自证）；streak 由脚本派生。 |
| 交付诚实性 | 15/15 | 上一轮我写的「(B) 已选中」被本轮实测加了一层限定：换对象之前先证明对象是谁；M1446 的失败没有藏起来，改成了负向臂并新开 635。 |
| 可复核性 | 15/15 | 探针脚本、四把刀命令、真值表四臂数字、八跑成对号全部入账；一次性 push 的自证写进收口报告。 |

均分 = 99/105 ≈ 14.1/15（94）。
"""

CHG = u"""### 629 的判据对象换成「两端夹逼的连续距离」；电池观察者不再借红（R558 / 第 557 轮 / Round 555 / U-2387…U-2394 · 产品 0 文件 + 判据 1 文件 + 观察者 1 文件）

`MOTION_MARKDOWN_MODE_FADE` 的 `过渡帧数` 从前数「相邻差 ≥ 各自峰值 ×15% 的格数」—— 那颗 `changedFraction` 是二值阈值占比，淡入中段就饱和，于是一次过程在 runner 上只剩两条边（27 帧里 2 格非零），相位一挪就掉到 1 ⇒ 判据把采样钟读成产品硬切。现在换成连续距离的两端夹逼：每帧分别量它离「触发前静置」与离「落定后静置」，两边都 ≥ 首末差 × `stepFloorRatio` 才算过程帧；「有没有交换」仍由原有阈值口径把关。`≥2` 地板、120ms 阈值、`.contentFade` 声明时长**全部不动**；旧口径的数与新口径一起打印。场景的驱动同时换成产品自己的 action（从前是夹具 `withAnimation` 给的插值）。新增合成真值表四臂 + 负向臂（title 钉成常量 ⇒ 判据必须红）。**探针实测**：把产品的 `.id(title)`/`.transition(.opacity)`/`.animation(value:)` 三行分别摘、全摘，读数逐字不变 ⇒ 这条胶片不能为那三行接线签字，而全仓没有任何 grep 守卫钉着它们 ⇒ 新开 BACKLOG 635。另把 `test_skip_roster` 从前「内层没有结论行」这一句借红拆成三态读数（`no-summary` 具名出口 / `inner-red` 仍红并带内层红名 / `ok` 照旧对账）+ 真值表（634 结案）。刀 **M1446–M1449** 全 CAUGHT。本轮自己造过一朵红并已修：新尺 `meanDistance` 被既有 AXIS_GUARD 名册点成「只读亮度」（扫到 6 / 名册 5）⇒ **改写法**（`max(rgb, alpha)` → `rgb > alpha ? rgb : alpha`，计算等价）而不是加豁免或放门，复跑名册守卫 0 失败。帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；清账 %(ABSENCE)s；电池 %(BATTERY)s。

"""

B629 = u"""    落地（R558，(B) 换判据对象）。依据 = R557 补记那三个 runner 真数（每格 22.6–28.1ms、27 帧只 2 格相邻差非零）⇒ (A) 加密录制被否：加密只多得 `0.0000`。改的对象：`过渡帧数` 从前是「相邻差 ≥ 峰值×15% 的格数」，而 `changedFraction` 是**二值阈值**占比（单像素差 >8 才算变），淡入中段早已越过阈值 ⇒ 一次过程只剩两条边，数边的那把尺分母是采样钟；现在换成连续量 `meanDistance`（平均 max(|Δrgb|,|Δa|)/255）的**两端夹逼** —— 每帧离「触发前静置」与离「落定后静置」都 ≥ 首末差 × `stepFloorRatio` 才算过程帧。「有没有交换」仍由原有阈值口径 `endpointChangedFraction ≥ minimumVisibleChange` 把关（两把尺各管各的量纲）。`≥2` 地板、120ms 阈值、声明时长、`.contentFade` 0.20 **都不动**。驱动同步换成产品自己的 action（从前夹具 `withAnimation` 自己造插值）。本机新值：`过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 唯一变化区=行 25…34 列 69…89`；粗相位那臂新读 0 而旧读 1 ⇒ 硬切仍会被判硬切，不再靠相位。证人：合成四臂真值表 + 负向臂 M1446。
    **但这一格带一条限定，另开 635**：把 `MarkdownModeButton` 的 `.id(title)`/`.transition(.opacity)`/`.animation(value: title)` 三行分别摘、全摘，本机读数逐字不变（只有 `窗口`/`每格` 随时钟抖）⇒ 这条胶片**不能为那三行接线签字**，它签的是「标签那一块有没有中间态」；而全仓除了这条胶片自己没有 grep 守卫钉那三行。所以 629 的"产品接没接"那一半没有被判据覆盖，转进 635。

"""

B634 = u"""    落地（R558，拆成三态 + 真值表）。`scripts/tests/test_skip_roster.py` 抽出纯函数 `inner_summary_verdict(text)` ⇒ `no-summary`（真缺席 ⇒ `SKIP_ROSTER_INNER_NO_SUMMARY=1` 具名出口）/ `inner-red`（仍然红，正文带内层汇总行与原样红名，`skipped=` 摘成 `跳过了=` 免得被台账生成器借走键名）/ `ok`（照旧对账）。真值表 `test_inner_summary_has_three_readings_not_two` 把三份文本并排喂进去，并钉住「旧那颗尺在 red 文本上取到 None」= 借红的机制本身。`FAIL: ` / `ERROR: ` 行由 `RED_NAMES` 抓出。没放宽任何门：红还是红，只是不再谎报成因；电池从 695 变 696（新增真值表那一格）。刀 **M1449**（把三态合回两态）CAUGHT：`'inner-red' != 'no-summary'`。
    待 runner 复核：本轮之前那三跑的 `test_skip_roster` 红是**借来的**（同批红名是 sources-cell 那一族）；本轮一次性 push 之后，若 STEP[9] 只剩别的红而这一格绿，就证明拆法有效。

"""

B635 = u"""**635. 「原文/渲染」标签的过渡接线没有任何会红的守卫**（R558 探针现读并新开）
    现象：`DetailView.MarkdownModeButton` 里 `.id(title)` + `.transition(.opacity)` + `.animation(MotionCatalog.animation(for: .contentFade), value: title)` 三行是 R400 为"控件名字别一帧硬换"加的；本轮把它们**分别摘、全摘**做成一次性探针（`probe_r558_what_the_film_measures.py`），`MOTION_MARKDOWN_MODE_FADE` 的 `过渡帧数`/`相邻差帧数`/`峰值`/`相邻差序列` 与未变异**逐字相同**（只有 `窗口`/`每格` 随时钟抖 321–330ms / 12.4–12.7ms）⇒ 胶片测到的插值不来自那三行（SwiftUI 对 `Text` 内容变化在事务里另有默认过渡）。
    现读覆盖面：`grep -rl "id(title)" ClipboardHistory/Tests/` 只命中 `MotionFilmstripTests.swift` 自己 ⇒ 既没有管线证人，也没有契约钉子。
    为什么算缺陷不是噪音：接线可以被删掉而全套判据照绿，等于这条动效在账上被记成"已验收"，而下一次真回归（把那三行删了或换成 `.transition(.move)`）不会有任何东西红 —— 这是"检测面比缺陷面窄"的同族（R421 / R482）。
    修法（下一轮，不许顺手改产品）：要么给这接线补一条**会红的钉子**（例如把场景的驱动固定成"不带 withAnimation 的产品 action"，再用一把刀摘掉 `.id(title)` 证明判据变红；现在做不到 ⇒ 需要先量出那三行在这条通道里到底改变什么），要么把它降级成**具名不判**（`MOTION_NOT_RUN=markdown-wiring-unjudged`）并让 629 那句话只说"标签有没有中间态"，不再暗示接线被验过。两条路都要配证人，不许只写注释。
    退场：下一轮要么真跑出「摘接线 ⇒ 判据红」的刀号，要么账上出现具名 NOT_RUN 读数；两者都没有 ⇒ 629 那半句"产品接线已验"必须撤回。
    关联：629（本轮已按 (B) 换对象落地，但带这条限定）、634（同一轮里另一条"观察者说假话"的形状）。

"""

DEC = u"""
## D-558 刀砍不到东西时，先怀疑尺的对象，再决定刀的目标（R558）

- 背景：M1446 按惯例设计成「摘掉产品那三行接线 ⇒ 判据必须红」，实测 PASSED。常规处置是把刀换个位置再试，本轮的处置是把它当成**读数**：一条对产品的接线不敏感的判据，它的对象就不是那三行。
- 决定：① 先用一次性探针把"哪一行在承重"问出来（分别摘 / 全摘，四臂同批读数对照），再改判据；② 刀的目标从"产品接线"改成"状态差本身"（title 钉成常量 ⇒ 判据必须红），把"接线没被覆盖"这件事转成 BACKLOG 635 而不是藏起来；③ 新尺不给新阈值 ——「有没有交换」用原有阈值口径（`endpointChangedFraction`/`minimumVisibleChange`），「过程里有几帧」用连续距离 × 原有 `stepFloorRatio`，两把尺各管各的量纲；④ 新尺必配**余量自己的证人**（合成"只离前态 1/255"那一臂），否则"把 `>= 余量` 写成 `> 0`"这类改法在所有真数据上读数不变，刀没有靶；⑤ **新尺一律去满足既有的名册守卫，不靠登记豁免绕过** —— `meanDistance` 被 AXIS_GUARD 点成"只读亮度"之后，本轮改的是它的**写法**（`max(rgb, alpha)` → `rgb > alpha ? rgb : alpha`，计算等价），豁免名单一条没加、门一寸没放；登记豁免是"把红变成没红"，改写法是"让尺真的说得清"。
- 推论（写给下一轮的同一族）：**判据必须由被审对象自己的路径驱动**。这条胶片从前由夹具的 `withAnimation` 驱动，于是它把"夹具演了一段插值"记成"产品有过渡"，而摘掉产品三行接线照样绿 ⇒ 凡是"场景 trigger 里自己包了 withAnimation/transaction"的动效判据，都要先问一遍：把产品那几行摘掉，这条判据还红吗？不红 ⇒ 它判的是夹具。（`MarkdownModeButton` 那一格转成 635。）
- 理由：本项目反复栽在"绿的东西比红的东西危险"（第二轮 N-1 绕过 adapter、R532 名册漏登记、R555 借来的红）。一把砍不到东西的刀是**免费的**假绿探测器，本轮用它换掉了三跑以来那条判据的签字效力，值得。
- 兼容性/迁移：`MOTION_MARKDOWN_MODE_FADE` 的 `过渡帧数=` 键名保留（含义换成新口径），旧口径另起一格 `相邻差帧数=`；历史台账里的 `过渡帧数=2/4` 是旧口径的数，不追改，R557 补记那张表已经写明是旧口径。
- 边界：本轮**没有**动产品（那三行原样保留），也**没有**因为"新尺读数更大"就宣布 629 的产品问题消失；635 单独记账。
- 撤回：把 `sandwichFrameCount` 换回 `transitionFrameCount(deltas(…))` 即回到旧口径（M1447/M1448 的形状会把差异暴露出来）；把场景驱动改回 `withAnimation(...) { toggle() }` 即回到 R557 之前的驱动。
"""


B622 = u"""    复查（R558）：新增**第十三值** —— `41467585182 ↔ ff15906` STEP[18] `PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1`，红名 `testFrameIntervalsUnderStateChanges：最差帧 225.3ms 超过锚点 120ms，且超锚点的帧有 3 颗（容差 1 颗）` ⇒ 225.3ms / 3 颗（第十三值，颗数第一次越过 2）。同跑 STEP[19] 另带 629 的未登记红（`MOTION_FLOOR_SUITE_RED=1 … testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1`、`judged=4/5 executed=77 not-run=notice-banner`、`MOTION_FLOOR_NOT_SEEN=2`）⇒ 两朵红同一跑，本轮都没碰这两卷，按同族入账。120ms 阈值、容差 1 颗、`over_runs` 口径一律不动，frame 半继续开单。

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


def insert_after(t, anchor, block, label):
    i = t.find(anchor)
    if i < 0 or t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, t.count(anchor)))
        sys.exit(1)
    j = t.find("\n\n", i)
    if j < 0:
        sys.stderr.write("ANCHOR_BAD %s no-blank-line-tail\n" % label)
        sys.exit(1)
    return t[:j + 1] + block + t[j + 1:]


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

    state = rd("AGENT_STATE.md")
    if state.count(u"## R558 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R558 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 556 轮（R557 · 2026-11-02 · U-2379…U-2386）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 555 · R558" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 555 已存在\n")
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
    # 622：第十三值接在 R555 那条复查之后
    t = insert_after_line(t, u"    复查（R555）：⓪ 五跑全读", B622, u"backlog622")
    # 629：把 (B) 落地那两行接在 R557 补记那句「挂起（R557）」之后
    t = insert_after(t, u"R558 只要那一跑到手，就按那三个数在 (A)/(B) 里选一条落地。\n", B629, u"backlog629")
    # 634：接在那条「关联：本轮的 stale-cell 窗口由推送顺序造成…」之后
    t = insert_after(t, u"规矩见 `AGENT_STATE.md` 的 R557 补记 ④。\n", B634, u"backlog634")
    # 635：新开，插在 634 之上
    a635 = u"**634. 电池里两条红其实是同一条"
    t = once(t, a635, B635 + u"\n" + a635, u"backlog635")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + DEC)

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R554，555 节自评", u"R9–R555，556 节自评", u"title"),
        (u"阶段二 **547 轮**审计（R9–R554；以 `curve_from_ledger.py` 的 `PHASE2 n=547` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 554",
         u"阶段二 **548 轮**审计（R9–R555；以 `curve_from_ledger.py` 的 `PHASE2 n=548` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 555", u"§1"),
        (u"| 视觉台账 | U-31 … U-2386", u"| 视觉台账 | U-31 … U-2394", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 556）", u"产品面连续零改动轮数 = **1**（as-of 557）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R557 节 ② 为准", u"以 `AGENT_STATE.md` 的 R558 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R557 这一段", u"## 18. R458 → R558 这一段", u"§18 head"),
        (u"R557 续到 557 —— 这份报告第七次差点停在几十轮之前）",
         u"R558 续到 558 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, old, new, label)
    anchor = u"帧 354 CHANGED=0 MISSING=0 ADDED=0；全量 1399/55/0（765.8s）；build 0 告警；电池 695/5。\n"
    bullet = (u"- **R558（629 换判据对象落地 + 634 拆三态；产品 0 文件 + 判据 1 文件 + 观察者 1 文件）**："
              u"`过渡帧数` 从前数「相邻差 ≥ 峰值×15% 的格数」（二值阈值、分母是采样钟），"
              u"换成连续距离的两端夹逼（每帧离两端都 ≥ 首末差×15% 才算过程帧）；`≥2` 地板、120ms、声明时长不动，"
              u"旧口径与新口径一起打印。本机新值 `过渡帧数=5 相邻差帧数=4 首末连续差=0.0031`，"
              u"唯一变化区 = 行 25…34 列 69…89（就是字形框）。**一把砍不到东西的刀挖出假绿**："
              u"产品那三行接线分别摘、全摘，读数逐字不变 ⇒ 胶片不为接线签字，而全仓没有 grep 守卫钉它们 ⇒ 新开 635。"
              u"负向臂 M1446（title 钉成常量 ⇒ 判据红）+ 合成四臂真值表 + 634 三态读数（借红拆成具名出口/内层红/可对账），"
              u"刀 **M1446–M1449** 全 CAUGHT、RESTORE_CLEAN。电池 695⇒696（新增真值表那一格）。"
              u"帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-02（本地 · R557 / 第 556 轮 / Round 554）",
             u"最后更新：2026-11-03（本地 · R558 / 第 557 轮 / Round 555）",
             u"identity")
    body = u"""## R558 状态（2026-11-03 · 第 557 轮 / Round 555 · 产品 0 文件 + 判据 1 文件 + 观察者 1 文件 + 四把刀）

① ⓪：三跑（`41450045802↔5ba5b2f`、`41450081248↔680aea3`、`41450601769↔ccab101`）conclusion=failure 且唯一失败步骤都是 **STEP[9] Release script tests**（红名 sources-cell 那一族 + `test_skip_roster`），而 **STEP[1]–[8]、STEP[15]–[19] 全 success**（`ci_read.py steps` 只列 failure/skipped ⇒ 必须另读 `gh run view --json jobs`）；`41452722560↔58851c2`、`41455782587↔598b253` 各 15m01s **cancelled**、0 失败步骤、`--log` 404 ⇒ 具名 NOT-RUN；本轮四跑 `41464892684↔ce4da8f`/`41465486002↔5d05578`/`41467173705↔61285b6`/`41467585182↔ff15906` 取号时全 in_progress ⇒ NOT-RUN。622/624/627 三跑无新红；569 的倍率口径连三跑无红。
② ②(a) **629 按 (B) 落地**：判据对象从「相邻差 ≥ 峰值×15% 的格数」（`changedFraction` 是二值阈值占比 ⇒ 淡入中段饱和、只剩两条边、分母是采样钟）换成 `meanDistance` 的**两端夹逼**（每帧离前静置与离后静置都 ≥ 首末差 × `stepFloorRatio` 才算过程帧）；「有没有交换」仍由原有 `endpointChangedFraction ≥ minimumVisibleChange` 把关 ⇒ 两把尺各管各的量纲、没有新阈值；**`≥2` 地板、120ms、`.contentFade` 0.20、声明时长全部不动**，旧口径与新口径一起打印。驱动同时换成产品自己的 action。本机新值 `过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 每格=12.5ms 唯一变化区=行 25…34 列 69…89`。证人：合成四臂真值表（台阶保持 新4/旧2；粗相位 旧1/新0；密采 3；只离前态 1/255 ⇒ 1，这一臂是余量自己的证人）+ 负向臂 M1446（title 常量 ⇒ `过渡帧数=0 首末连续差=0.0000` 两条断言各红一次）。
③ ②(b) **634 落地**：`inner_summary_verdict` 三态（`no-summary` ⇒ `SKIP_ROSTER_INNER_NO_SUMMARY=1` 具名出口；`inner-red` ⇒ 仍红且带内层汇总行与原样红名，`skipped=` 摘成 `跳过了=`；`ok` ⇒ 照旧对账）+ 真值表钉住"旧尺在 red 文本上取到 None"= 借红的机制；没放宽任何门。②(c) **换新类别的真实推进 = 挖掉一枚假绿**：M1446 第一版「摘产品接线」实测 **PASSED** ⇒ 一次性探针四臂（分别摘 `.id(title)`/`.transition(.opacity)`/`.animation(value:)`、三条全摘）读数与未变异**逐字相同** ⇒ 这条胶片不为那三行接线签字，而 `grep -rl "id(title)" ClipboardHistory/Tests/` 只命中胶片自己 ⇒ **新开 635**（本轮不改产品、不动那三行）。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据 filter 绿；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s`；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账后复跑，只抄 `Ran`/`OK`/`FAILED`）；产品面连续零改动 **%(STREAK)s** 轮（as-of 557，`python3 scripts/product_streak.py --streak-for 557` 现读，last=`2ca9501`/556）⇒ 本轮产品 0 文件。刀 **M1446–M1449** 全 CAUGHT、RESTORE_CLEAN=yes；四张表已登记进预检名册（与前几批同形：静态抽不出 needle ⇒ 不在 `covered` 里，只由真跑签字）。⑥ 新规矩兑现：全部落盘 + 电池过了之后**一次性 push**（不分批 ⇒ 不再造 STEP[9] 注定红的中间跑）。**R559 必读本轮各笔的跑 + 上面那四跑**（逐条抄全部失败步骤，success 步骤另读 `jobs[].steps`），头一格 = runner 上新的 `过渡帧数=` 读几 + `test_skip_roster` 拆完之后还红不红。633 仍等用户回执；622/624/627/635 继续；628/625/626/569/616/632 已落地那半不重开；禁碰清单 9 面不变；刀号 **M1450** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 与 1x 6.0pt 均不动。

"""
    a = u"\n## R558 ⓪ 开工（2026-11-02 · 第 557 轮 / Round 555 · CI 读单 + 基线全现读）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R558_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
