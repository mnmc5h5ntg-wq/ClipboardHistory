# R561 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r561.py`）

第 560 轮 / Round 558 · 2026-11-03。规矩：**已到手**只写真读到的；被打断/超时/没跑的进**待读**。

## 已到手

### ⓪ CI（开场）
- `41509855001 ↔ 26c1939`（R560 补记笔 = 那一批头笔，含 R560 全部代码）开场 **queued、已等 284s**
  ⇒ 四格具名 NOT-RUN：(a) `TASK_BOX_SIZE` 在 1x 走哪条；(b) `HEAT_LEGEND_*` 是否连续第二跑同形；
  (c) `过渡帧数=` 第三数；(d) STEP[9]/[18]。不轮询。
- 同批无独立跑 ⇒ `CI_UNREAD`：R560 的 `0a49b5f`/`631f910`/`700dee9`/`8004a42`/`22bd17d`、R558 的 `b8949f5`/`1ea1bb7`。
- 永不重开：`41452722560↔58851c2`、`41455782587↔598b253`。

### ② 基线（现读）
帧 354；清账 162/63/0；streak `ledger_round=559 streak=1 last=3a3c9a9 last_round=558 newest=631f910 newest_round=559`；
预检 `tables=355 covered=295 arms=757 bad=0`、`ARM_TOTAL files=448 arms=1244`、`HIDDEN_ARMS 表=442 可判=1183`；
刀号最高 M1455 ⇒ 本轮 M1457/M1458/M1459（M1456 未用）。

### ③ 636 头一格：**没有夹具画到 depth2**（量具不量产品）
扫描法：把 `ClipboardHistory/Tests/**/*.swift` 里每段多行字符串正文按"闭合那一行三引号的缩进"剥掉源码缩进，
算内容相对缩进，再按产品规则 `depth = min(相对缩进 / 2, maximumListDepth=6)` 折算。
现读：含列表的正文 **5 段**（`Round4MarkdownTests.swift:21`、`UICaptureHarness.swift:17657/17685/17727/18093`），
**相对缩进全部 = 0 ⇒ depth 集合只有 {0}**。样本 `- [x] 解析层完成` 那 4 个空格是**源码缩进**，不是内容缩进。
⇒ `◦`(depth1) 与 `▪`(depth2) **今天没有任何帧对象** ⇒ 636 保持具名 NOT-RUN（通道判不到），
不许拿字体探针量到的回退当产品缺陷落地；退场条件两步：先补 depth2 夹具（补夹具不动产品绘图路径 ⇒ 不算破 R549 禁碰），再量。
顺带把 R549 覆盖面说清：那条判据签的是 depth0 的 `⦁` 墨高，`◦`/`▪` 从来没有帧证人。

### ④ 判据位：图例那把尺的地板改成几何派生（`SolidRuler`）
- 改动：`testHeatmapLegendCoversEveryCellColor` 的两道绝对地板 `minHits: 30 / 8` 换成
  `ruler.cellFloor / ruler.legendFloor`；`倍率<1.5 ⇒ 具名不判` 那道门撤掉，换成
  `resolvable = legendPositions >= 4`（几何上分不出方块与噪声才不判），出口改名 `HEAT_LEGEND_NOT_RUN=solid-unresolved`。
- 派生式：`positions(edge, side) = ((edge − side)/2 + 1)²`（采样步长 2），地板 = 它的一半；
  `swatchEdge = cellW × 8/11`（图例方块 = `cell − 3` pt、格子 = `cell` pt）。
- **2x 等价性实测**（关键，不许因为换派生式就悄悄变判定）：新值
  `HEAT_LEGEND_COVERAGE light 格色=8 图例色=5 缺=[] 格宽=22px 倍率=2.0x 实心判定 格13px/图例5px 地板 格12/图例18 每方块采样点 格25/图例36`、
  `dark 格色=9 图例色=5 缺=[]` ⇒ 与 R560 用绝对值 30/8 时的结论**逐字相同**（`格色=8/9 图例色=5 缺=[]`）。
- 新增纯数据真值表 `testLegendSolidRulerFloorsAreDerivedFromGeometry`（不吃 `UI_SHOTS` 门 ⇒ CI 普通 Swift 步每轮跑）：
  cellW=22 ⇒ (13,5,16,25,36,12,18,resolvable)；cellW=11 ⇒ (6,3,8,9→floor 4, **resolvable=true**)；
  cellW=6 ⇒ `resolvable=false`；再加单调性两格 + **契约钉子**（像素判据函数体内必须有 `SolidRuler(`，
  区域限定在那条判据自己的函数体，并断言切出来的区域 >400 字符，防"区域取不到就空跑给绿"）。
- `swift build --build-tests` 告警 **0**；两条判据合跑 `Executed 2 tests, with 0 failures`（1.765s）。
- ⚠ **本机拍不出真 1x 帧** ⇒ "1x 现在判得到"这句话今天是**派生式的推论 + 真值表**，不是像素证人；
  runner 真数留给 R562 ⓪（这一跑会走 `HEAT_LEGEND_COVERAGE … 倍率=1.0x` 而不是 `solid-unresolved`，若仍不判就是门限算错了）。

### 三把刀（全 CAUGHT、RESTORE_CLEAN=yes）
- **M1457**（图例地板退回绝对值 8）CAUGHT 三条：`("8") is not equal to ("18")`（2x 臂）、
  `("8") is not equal to ("4")`（1x 臂，正文就是"1x 的地板必须是几何派生的 4"）、
  `XCTAssertGreaterThan failed: ("8") is not greater than ("8")`（单调性臂）⇒ 变化量远在容差外。
- **M1458**（`resolvable` 写成恒真）CAUGHT：`cellW=6 时一个图例方块只放得下 1 个采样点 ⇒ 分不出方块与噪声，必须走具名不判`。
- **M1459**（像素判据里换成等价常数元组）CAUGHT，而且**只有契约钉子红**：
  `像素判据里没有 SolidRuler( ⇒ 地板被换回了写死的常数` ⇒ 这一把专门钉"钉子有没有牙"，
  它同时证明 2x 的**像素判定与派生式无关**（30/8 与 12/18 在本机给出同一个 `格色=8 图例色=5 缺=[]`）。

## 待读（截断的链要重跑）

- 判据卷 `UICaptureTests` 整卷（+1 条真值表 ⇒ 预期 220）。
- 重捕帧 + 基线对账（本轮**没动产品** ⇒ 预期 CHANGED=0；若非零就是漏改，要查）。
- 全量卷（skipped 57 第四跑，只记现读）。
- 预检三读（**串行**）。
- 换装本机（`--label R561`，撞名就 R561b）。
- 台账 7 本（写之前核三条硬格式；**派生格落盘之后现读**）→ 提交 → `report_sources_cell.py --write`
  → 电池 → **一次性 push**。
- ⓪ 那跑 `41509855001↔26c1939` 收口前复述：四格读数（尤其 `TASK_BOX_SIZE` 在 1x 的形状）。

## 收口时到手（本段是「待读」那一节的对账，全部现读、不抄上一轮）

- 判据卷 `UICaptureTests`：**Executed 220 tests, with 4 tests skipped and 0 failures in 619.432s**（/tmp/r561-capture.log）。
- 帧重捕 + 基线对账：`FRAME_BASELINE_AGAINST=working COMPARED=354 CHANGED=0 MISSING=0 ADDED=0`（/tmp/r561-compare.log）⇒ 产品 0 文件 ⇒ 基线一帧未动，**无须 update**（这一格如果非零就是漏改到别的面）。
- 全量卷：**Executed 1404 tests, with 57 tests skipped and 0 failures in 678.053 (678.142) seconds**（/tmp/r561-full.log，327MB ⇒ 只用有界 grep 取汇总行）。
- 预检三读（**串行**，与 swift 卷并行会撞 `.build` 锁）：`tables=358 covered=295 arms=757 bad=0`、`ARM_TOTAL files=451 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（/tmp/r561-precheck3.log、/tmp/r561-hidden3.log）。
- 换装本机（`--label R561`）：`INSTALL_RESULT=ok INSTALL_SHA_MATCH=1 INSTALL_ENTRIES=433=433 SMOKE_OK=1 INSTALL_SIGNATURE=local flags=0x0`、版本 1.4.8→1.4.8、PID→93599、备份 `before-R561`（/tmp/r561-install.log）。
- 清账表：**162/63/0**。streak（**台账落盘之后**现读）：`PRODUCT_STREAK ledger_round=560 streak=1 last=631f910 last_round=559 newest=631f910 newest_round=559` ⇒ 复核 `PRODUCT_STREAK_LEDGER_OK streak=1`。
- 电池：**Ran 696 tests / OK (skipped=5)**、退出码 0（台账 + `report_sources_cell.py --write` 之后复跑；`--write` 读数 `账上=R560/631f910 git=R560/631f910 一致=是` ⇒ 本轮 sources 格无需补正笔）。
- ⓪ 那跑 `41509855001↔26c1939` **收口前到数**（开场是 queued）：conclusion=**failure**，`steps` 全量只列一朵红 = **STEP[19] `Motion coverage floor`**；(a) `TASK_BOX_SIZE light/dark 9x9px 宽差=0 高差=0 倍率=1.0x` + `TASK_BOX_NOT_RUN` 零行；(b) `HEAT_LEGEND_NOT_RUN=scale-too-low … 格宽=11px` 连续第二跑同形、`HEAT_LEGEND_COVERAGE` 零行；(c) `过渡帧数=0`（每格 75.6ms，**同批旧口径读到 2 帧**）、`MOTION_FLOOR_REDS=1`、`红的用例=testMarkdownModeLabelChangeIsAVisibleProcess`；(d) `gh run view --json jobs` 现读 9/18=`success`、19=`failure` ⇒ STEP[9] 连续第三跑绿、622 本跑无新值。

## 本轮自伤（两条，都写进补记 ⑥）

1. 台账笔 `324c513` 的 STATE ① 格里落盘了一个没渲染的占位符（同一坑第四回，U-450/U-943 记过）⇒ 补记笔逐字补回，并留下可复查读数：正则 `%(?=[a-zA-Z])` 在「`## R561 状态` → `### R561 补记`」这一段=**0**（补正前=1）。根因是**通道**：写台账的脚本没有「渲染后回读一次」的闸门。
2. 给补记打补丁的脚本又撞了 **CJK 串里 ASCII 双引号**那条（`SyntaxError: invalid character '≥'` 那族的兄弟：这次是 `invalid syntax`，因为我在一对 `"` 里写了 `"零"`）⇒ 改 `py_compile` 先过再落盘；顺带把「红原文逐字」那句里我自己打错的「夹迫」按日志逐字对回「夹逼」——**声明逐字之前先 `startswith` 对一遍**，不然"逐字"是我自己的转述。
