# R562 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r562.py`）

第 561 轮 / Round 559 · 2026-11-03。规矩：**已到手**只写真读到的；被打断/超时/没跑的进**待读**；截断的日志不算读数。

## 已到手

### ⓪ CI（开场）
- `41519677393 ↔ f12f50d`（R561 那一批头笔 = 补记笔）状态 **queued、已等 232s**；`steps` 打 `conclusion=` 空串、`JOB build-and-test ⇒` 空 ⇒ **没有结论**，不是「没红」。
  ⇒ 三格具名 NOT-RUN：(a) `SolidRuler` 在 runner 真 1x 帧上判没判到；(b) `过渡帧数` 第四数；(c) STEP[9] 第四跑 + STEP[18] 622。
  收口前复述一次 `queue`，到数就改写成读数。
- `41509855001 ↔ 26c1939` = concluded failure（只红 STEP[19]）⇒ 已读，读数在 `### R561 补记` ②，不重读。
- `CI_UNREAD`：R561 中间三笔 `5e08357`/`a8adab4`/`324c513`；R560 五笔；R558 两笔。
- 永不重开：`41452722560↔58851c2`、`41455782587↔598b253`。

### ② 基线（全部本轮现读，命令写在 STATE ② 格）
- 帧基线 `count=354`（`docs/frame_baseline.json`，`frames` 字典同长）。
- `NEEDLE_PRECHECK tables=358 covered=295 arms=757 bad=0`；`ARM_TOTAL files=451 arms=1244 dupes=0 repeats=0`；`HIDDEN_ARMS 表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`。
  ⚠ 抄错一次：`scripts/hidden_arms.py --arm-total` **没有这个参数** ⇒ usage 报错 + 退出码 2；`ARM_TOTAL` 那行是 `mutate_needle_precheck.py` 打的。报错不是读数。
- 清账 `LEDGER_ABSENCE_RESULT=ok 不成立=0/63`；`PRODUCT_STREAK ledger_round=560 streak=1 last=631f910 last_round=559 newest=631f910 newest_round=559`（开工现读；收口那格落盘后重读）。
- 刀号最高 **M1459** ⇒ 本轮 **M1460** 起。
- 判据卷 / 全量卷 / 换装：本轮**还没跑** ⇒ 具名 `NOT_RUN=this-round-not-yet-run`，不许拿上一轮的收口读数冒充。

### ③ git / 网络前置
`git log --oneline -1` = `f12f50d`；已跟踪改动 0；ahead=0；`api.github.com=200 / www.apple.com=200`。

### ④ 本轮前置自检（第一次就用上了）
`state_r562_open.py` 落盘后回读：`%(?=[a-zA-Z])` 在「`## R562 ⓪ 开工` → `## R561 状态`」这一段 = **0**（R561 那笔落了一个进去，第四回同坑）。

## 待读（截断的链要重跑）

- ② 的第二格：636 退场第一步 —— 先看清夹具该放在哪个文件、哪个 `markdownSample`，再补 depth1/depth2 正文，重捕帧看那三级列表长什么样（**先看图**）。
- 新判据「三级同尺寸」的**先红后绿**（旧值→新值都要现读打印）；若红在禁碰面 ⇒ 不动产品，只开单 + 摆代价。
- 刀 M1460 起：登记前自问变化量是否出容差。
- build 0 告警 → filter → 刀 → 名册登记 → 判据卷 → 重捕帧 + 同一笔 `update` → 全量 → 预检三读**串行** → 换装（备份 `before-R562`，label 撞名就 R562b）→ 台账 → 各笔本地提交 → `report_sources_cell --write` → 电池 → **一次性 push** → ahead=0。
- ⓪ 那跑 `41519677393↔f12f50d` 收口前复述：三格读数（(a) 最要紧 —— 若仍走出口，R563 的头格就是修派生式）。

### ⑤ 第二格落地：636 退场第一步 = 夹具 + 判据（产品 0 文件）

- 新夹具 `detail-markdown-bullet-nested`（720×520，两档外观）+ 夹具正文 `UICaptureTests.nestedBulletFixtureBody`
  （刻意写成转义串而不是三引号块：三引号按闭合行整块 dedent ⇒ 内容缩进会被吃掉，R561 扫夹具命中的就是这个）。
- **看图**（`/tmp/r562-bullets-{light,dark}.png`，列表区 2 倍放大）：三级阶梯读起来一致，
  第三级的 `▪` 没有比第一级的 `⦁` 明显大；正文列逐级右移，肉眼看不出哪一级被推歪。
- **像素现读**（一次性探针 `.scratch/motion-audit-2/probe_r562_nested_bullets.py`，本机 2x）：
  light 项目符墨 bbox 8×8 / 7×6 / 8×8 px（4.00 / 3.00 / 4.00pt），dark 9×9 / 7×7 / 8×8 px；
  正文左沿 x=73 / 105 / 137 px ⇒ 步进 **32px / 32px = 16.0pt / 16.0pt，漂移 0px**。
- 新判据 `testNestedBulletLevelsKeepOneUniformTextColumn` 绿（`Executed 1 test, with 0 failures`）：
  `BULLET_LEVELS light 行=6 列=3 步进=[32, 32]px(16.0/16.0pt) 容差=2px 合并=1px 筛除 宽≤16px 隙≥8px 倍率=2.0x 列x=73px 墨高=8px(4.00pt) 列x=105px 墨高=6px(3.00pt) 列x=137px 墨高=8px(4.00pt)`、
  dark 同形（墨高 9/7/8px）。判两格：**列数 == 产品解析出的深度集合**（对象证人）+ **相邻步进彼此相等（≤1pt）且 ≥8pt**（防塌平）。
  三级各自的墨 bbox **只印不判** —— R549 有意三档三个字形，「三级同尺寸」会把设计钉成缺陷。
- ⇒ **636 的断言被证伪**（机制 + 像素两条）：`▪` 确实由冬青黑体回退画出、advance 12.00pt 比 `⦁` 宽，
  但正文列取 `max(minimumAdvance=16, markerWidth+2)` ⇒ 12+2=14 ≤ 16 被钳位吸收 ⇒ 列不漂 ⇒ 与 R560 那个"两态差 2.5pt"**不是同一类**。
- 刀：**M1460 CAUGHT**（夹具两行缩进一起抹平 ⇒ 解析 {0,1}、帧上 2 列，两格同时红）、
  **M1461 CAUGHT**（产品 `ListHangingIndent.minimumAdvance` 16→12 ⇒ 步进 [32,38]px=16/19pt，红在等距断言，出容差 2px）、
  **M1462 CAUGHT**（合并容差 0.5pt→20pt ⇒ 三列塌成两列，红在列数断言）；三把 `RESTORE_CLEAN=yes`。
  ⚠ **一把空刀已撤回、没登记**：第一版 M1460 只抹平一行 ⇒ 读数逐字不变（另一行还留着 depth2）；
  第一版 M1462 把「项目符宽 ≤8pt」抬到 40pt ⇒ 读数逐字不变（工具栏那行在 y=73..93px，被 **y 窗口**筛掉，
  不是被宽度筛掉 ⇒ 这道宽度筛在当前帧上是冗余的）。两条都写进账，不藏。
- 预检（登记三张表之后）：`tables=361 covered=295 arms=757 bad=0`、`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`；
  三张新表与前几批同形 ⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由上面三把真跑证明。
- 帧：`FRAME_BASELINE_COMPARED=356 CHANGED=0 MISSING=0 ADDED=2` ⇒ **既有 354 张逐字节不变**
  （= R549 那张 `detail-markdown-bullet` 与全部禁碰面一帧未动），新增的就是这张夹具的两档。

### ⑥ 断点之后（同一 turn 未死：判据卷进程活着跑完 ⇒ 读数来自完整日志，不是截断日志）

- 监督侧判我「turn 结束 ⇒ 那一卷读数抹掉 ⇒ 重跑」；**现读 `pgrep` 得到 pid 22512 的 `xctest` 仍在跑**，日志 `/tmp/r562-capture.log` 在增长 ⇒ 处置是**等它跑完读完整日志**，不重跑（重跑会拿两份读数冒充两件事）。到手：**Executed 221 tests, with 4 tests skipped and 0 failures in 675.061s**（R561 是 220/4/0 ⇒ +1 就是本轮这条）。
- 帧基线（update 之前）：`COMPARED=356 CHANGED=0 MISSING=0 ADDED=2`，新增的两个名字逐字是
  `detail-markdown-bullet-nested-720x520-dark.png` / `…-light.png` ⇒ **名单外一个帧也没有**，且既有 354 张逐字节不变（= 产品 0 文件、禁碰面一帧未动的证人）。
- update 之后复跑：`COMPARED=356 CHANGED=0 MISSING=0 ADDED=0`。
- **1x 降采样体检**（`probe_r562_1x_preview.py`，LANCZOS 把 2x 帧缩到 1x 再跑同一把尺的四道筛）：
  `light 1.0x 带=7 行=7 筛后=6 列=3 左沿=[36, 52, 68] 步进=[16, 16] 容差=1px 步进地板=8px`、dark 同形
  ⇒ 列数不塌、步进等距（漂移 0px vs 容差 1px）、步进 16px ≥ 地板 8px（余量 2 倍）。
  ⚠ 它**不是**真 1x 渲染 ⇒ 只回答"筛子还剩多少余量"，不回答"runner 判到了"；后者只能由含这条判据那一笔的跑作证。

### ⑦ 收尾（全量之后 → 台账 → 补正 → 电池 → 一次性 push）

- 全量 **1405/57/0（686.4s）**；预检三读串行 `tables=361 covered=295 arms=757 bad=0`、`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`；换装 `INSTALL_RESULT=ok 433=433 SMOKE_OK=1 SIGNATURE=local` PID 30437、备份 `before-R562`。
- ⓪ 那跑**收口前到数**：`41519677393↔f12f50d` = concluded **success** ⇒ (a) `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4 每方块采样点 格9/图例9 缺=[]` ×4 行、`HEAT_LEGEND_NOT_RUN` 零行 ⇒ **R561 的几何派生尺被 runner 签收，预测的两个地板数逐字命中**；(b) `过渡帧数` 第四数 = **5**（每格 28.9ms、STEP[19] success）⇒ 四跑 2/5/0/5；(c) STEP[9] 第四跑绿、STEP[18] success ⇒ 622 无新值。`BULLET_LEVELS` 零行 = **判据未推**（那一跑不含本轮判据），不是通道坏。
- 台账四步：写手第一次崩在 ITER 的 `fill()`（**账的正文里写了「percent+左括号」字面量 ⇒ 守卫命中自己**），但 UI 那一本已写盘 ⇒ 重跑写成两份 ⇒ `test_ui_audit_ids_are_unique` 真红 ⇒ 去重 + 给写手补幂等守卫（补正笔 `c8c950f`）。电池 4 红（3 时序 + 1 借红报告）→ 2 红（1 真红 + 借红报告）→ **`Ran 696 / OK (skipped=5)`**。
- 派生格全部落盘后现读：streak **2**（`PRODUCT_STREAK_LEDGER_OK`；报告那一格从前写 1 被 `PRODUCT_STREAK_LEDGER_STALE` 点过一次）、sources `一致=是`、占位符回读 **0**。
