# R560 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r560.py`）

第 559 轮 / Round 557 · 2026-11-03。规矩：**已到手**只写真读到的；被打断/超时/没跑的进**待读**。

## 已到手

### ⓪ CI（开场）
- `41501679574 ↔ 7260562`（R559 补记笔 = 那一批头笔，含 R559 全部代码）开场 **queued、已等 297s**
  ⇒ 四格具名 NOT-RUN：(a) `HEAT_LEGEND_*` 在 runner 上走哪条；(b) `过渡帧数=` 第二个真数；
  (c) STEP[9] `SKIP_ROSTER`；(d) STEP[18]/[19]。不轮询。收口前再读一次 `queue`（R559 的先例：
  那一跑到收口时 concluded，两格当场从 NOT-RUN 改成读数）。
- 同批无独立跑 ⇒ `CI_UNREAD`：R559 的 `809b963`/`3a3c9a9`/`bad7788`/`73e91f4`/`2f26d4c`、R558 的 `b8949f5`/`1ea1bb7`。
- 永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、`log not found`）。

### ② 基线（本轮 ⓪ 现读，与 R559 收口同数 ⇒ 树未动）
帧 354；清账 162/63/0（`LEDGER_ABSENCE_RESULT=ok 不成立=0/63`）；
streak `PRODUCT_STREAK ledger_round=558 streak=2 last=2ca9501 last_round=556 newest=3a3c9a9 newest_round=558`；
预检 `tables=353 covered=295 arms=757 bad=0`、`ARM_TOTAL files=446 arms=1244 dupes=0 repeats=0`、
`HIDDEN_ARMS 表=440 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`；刀号最高 M1453 ⇒ 本轮 M1454 起。

### ③ 产品位：任务勾选框两态不同尺寸（看图 → 量 → 探针找成因）
- 旧值（`detail-tasks` 2x 帧，两档外观）：勾选标记 **21×20px = 10.50×10.00pt（墨 222）**、
  未勾选 **16×16px = 8.00×8.00pt（墨 112）**；暗档 21×21 / 16×16（墨 259/112）。
  两行正文左沿同为 x=73px ⇒ **文字对齐、框子不对齐**。
- 成因（一次性字体探针 `/tmp/r560-font-probe.swift`，不入库）：`☑` U+2611 在系统字体里有字形
  ⇒ 由 **.SFNS-Regular** 画（advance 11.71×16.00）；`☐` U+2610 系统字体里**没有**
  ⇒ AppKit 换到 **AppleSymbols**（advance 10.79×16.00）。两个态来自两份字体。
  同一探针：钉到 `Apple Symbols` 后两个字形度量相同（10.79×12.00，两份都落到 AppleSymbols）；
  `Menlo` 两者 7.83×15.00；`Helvetica`/`PingFang SC` 也都落到 AppleSymbols。
- 判据先写、旧值先红：`UICaptureTests/testTaskCheckboxStatesShareOneGlyphSize`
  ⇒ `TASK_BOX_SIZE light 勾选=21x20px 未勾选=16x16px 宽差=5px 高差=4px`、`dark … 宽差=5px 高差=5px`，
  **4 条断言红**（`/tmp/r560-crit-old.log`）。阈值：宽高差各 ≤1px（2x 上 = 0.5pt）；
  墨下界按 `scale` 派生（`8pt` 周长），带子 <2 行 ⇒ 具名 `TASK_BOX_NOT_RUN=runner-detail-frame-plain`（与 R450 同族），
  两行都在但框子没墨 ⇒ **红**（产品缺陷，不许读成通道限制）。
- 产品改动：`MarkdownPresentation.markerFont(for:)` 里**只给任务标记**钉 `Apple Symbols`（同 pointSize），
  项目符 `⦁ ◦ ▪` 与编号那条路一字不动（R549 禁碰面）。钉在同一个函数里是因为它同时是
  渲染字体与 `hangingIndent` 量制表位用的字体（分家 ⇒ 制表位漂，R488 族）。
- 新值（绿）：`TASK_BOX_SIZE light 勾选=16x16px(8.00×8.00pt) 未勾选=16x16px(8.00×8.00pt) 宽差=0px 高差=0px 墨=145/112`、
  `dark … 墨=154/112` ⇒ 勾选那一态从 10.5pt 降到 8pt 与未勾选对齐（未勾选本来就是 8pt，今天出厂的样子）。
- `swift build` / `swift build --build-tests` 告警 **0**。
- 兄弟判据旧值（改之前列，改完重读）：`TASK_DIM light 勾选=133.5 未勾选=85.2 差=48.3 墨数=1104/1175`、
  `dark 勾选=146.4 未勾选=184.3 差=-37.9 墨数=1233/1293`（它读 x 40..300 的正文带，标记被排除 ⇒ 预期不动）。

### 两把刀（全 CAUGHT）
- **M1454**（把字体钉撤掉 ⇒ 复现旧形状）CAUGHT：`light 勾选=21x20px 未勾选=16x16px 宽差=5px 高差=4px`、
  `dark … 宽差=5px 高差=5px`，两档各两条断言红；`RESTORE_CLEAN=yes`。
- **M1455 第一版是空刀，照实记**：把两个态分别钉到 Apple Symbols / **Menlo** ⇒ 实测
  `勾选=16x16px 未勾选=15x15px 宽差=1px 高差=1px` —— **1px 正好落在容差（≤1px）内 ⇒ PASSED**（R491 那一族：同值空刀不算刀）。
  换成 **Arial Unicode MS** 之后 CAUGHT：`勾选=16x16px 未勾选=18x18px 宽差=2px 高差=2px` 两档各两条红、`RESTORE_CLEAN=yes`。
  ⇒ 这条判据的契约是**像素同尺寸（≤1px = 0.5pt）**，不是"字体名字符串相同"；余量只有 1px（2 vs ≤1），
  这一点必须写进账，下一轮别把它当成"任何字体混用都会红"。

### 顺手量到的同类形状（**开单 636，本轮不改**：R549 项目符是禁碰面）
字体探针第二跑（`/tmp/r560-bullet-probe.swift`，一次性、不入库）现读三级项目符在系统字体 13pt 下：
- `⦁`(U+2981, depth0) advance **8.11×16.00**，实际字体 **.SFNS-Regular**
- `◦`(U+25E6, depth1) advance **6.06×16.00**，实际字体 **.SFNS-Regular**
- `▪`(U+25AA, depth2) advance **12.00×16.00**，实际字体 **.HiraKakuInterface-W4**（冬青黑体 ⇒ **回退**）
⇒ 与本轮任务框**同一类缺陷**：第三级项目符由另一份字体画。
**没测的**：今天没有任何夹具画到 depth2（未量帧上墨 bbox）⇒ 636 里写清"帧上有没有对象"待下一轮现读；
R549 是禁碰面 ⇒ 本轮只开单不动它。

### 重捕 + 帧名单 + 看图（刀代之后重捕，旧帧不算证人）
- 判据卷 `UICaptureTests`：**219 tests, 4 skipped, 0 failures（617.5s）**（R559 218 ⇒ +1 = 本轮新判据）。
- 帧对账：`FRAME_BASELINE_COMPARED=354 CHANGED=4 MISSING=0 ADDED=0`
  ⇒ 名单 = `detail-tasks-720x520-{light,dark}` + `detail-markdown-rendered-720x520-{light,dark}`
  = **正好是含任务标记的那两个夹具 × 两档外观**，没有名单外的帧 ⇒ 改动没有漏到别处。
  `update` 之后复跑 `CHANGED=0 MISSING=0 ADDED=0`。
- 兄弟判据 `TASK_DIM` 旧→新：**逐字未变**（light 133.5/85.2/差 48.3 墨 1104/1175；dark 146.4/184.3/-37.9 墨 1233/1293）。
- 新值（判据卷整卷里）：`TASK_BOX_SIZE light 勾选=16x16px(8.00×8.00pt) 未勾选=16x16px(8.00×8.00pt) 宽差=0px 高差=0px 墨=145/112 倍率=2.0x`、
  `dark … 墨=154/112`。
- 逐像素定位（旧 `/tmp/r559-frames/…` vs 新 `/tmp/r560-frames/…`）：
  light 差 **2134** px、dark 差 **2232** px，bbox `x 42…181 / y 277…340`（= pt x21.0…90.5 / y138.5…170.0）。拆开看：
  勾选行 标记列 350 px、正文列 **0**；未勾选行 标记列 137 px、正文列 **1647**。
  ⇒ **未勾选行的正文像素也变了，但不是排版移动**：两行正文左右沿旧/新同为 x=73…181；
  位移扫描 dx=−1/0/+1/+2 差异像素 = 1925/**1647**/1833/1999 ⇒ dx=0 最小；
  逐列墨数序列**逐列相同**、合计 **1343 = 1343** ⇒ 差异是**次像素抗锯齿层**（同一位置、RGB 末位不同）。
  这一格照实写：不许说"帧内容未变"，也不许把它读成"文字被挪动"。
- 看图（`/tmp/r560-tasks-oldvsnew.png`，上旧下新、先亮后暗、3× 最近邻）：
  旧 = 勾选框明显**更大更粗**（10.5pt 粗描边）而未勾选框小且细 ⇒ 一眼像两个控件；
  新 = 两框同尺寸同描边、勾那一撇仍清楚、8pt 框在 13pt 正文旁读得出是方框；正文位置没动。

## 待读（截断的链要重跑）
- 预检名册登记后的预检三读（**串行**）。
- 全量卷（有界 grep；skipped 57 再看一次，只记现读）。
- 换装本机（`--label R560`，撞名就 R560b）。
- 台账 7 本（**写之前先核三条硬格式**：七维表七行 / CHANGELOG `### …（R560 / ` 标题 / streak 带命令引用）
  → 提交 → `report_sources_cell.py --write` → 电池 → **一次性 push**。
- ⓪ 那跑若已开跑：四格读数（尤其 `TASK_BOX_*` 在 runner 上走哪条 —— 这条新判据**没做 1x 体检**，
  因为它的阈值全按 `scale` 派生；真数到手才算签收，拿不到就具名）。
