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
