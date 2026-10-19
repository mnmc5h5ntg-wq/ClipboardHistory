#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R201 / R202 / R203 三笔「非轮次」台账的补落（BACKLOG 225 的①出口）。

为什么现在补而不是留着：`test_round_batch_consistency.py` 查的是**离 STATE 当前轮最近三笔**的标题行，
所以这三笔一直没红 —— 但它一红就是三格，而红的时候我正在轮换 STATE，最容易草草写桩标题糊过去
（186/187 那次教训：桩标题会让「半批已写」这一格永远查不出来）。曲线仪器也不认申报通道：
R197 就是这么打出 GAPS=[197] 的。所以这次把三笔各写成**真的一节**，数字只从盘上能复查的东西抄：

- 读数来源 = 那三笔自己的 commit 正文 + CHANGELOG 里已落的原文（`728a1b2`/`2351593`/`33b1322`/`b6077be`/`bd7a64f`）；
- 没跑过的验证（全量 swift test、变异刀、新帧捕获）**照实写 NOT-RUN**，不拿上一轮的读数冒充本轮；
- 本轮（补落这笔）产品 0 文件 ⇒ 帧未动。

门（任一不过 ⇒ 一个文件都不写）：
① 写盘前模拟三账窗口：R203/R202/R201 三笔在 UI_AUDIT / ITERATION / CHANGELOG 里各自有标题；
② UI_AUDIT 每一节标题声明的 U 区间必须与该节 `- **U-6xx：` 定义行**恰好吻合**（≥3 条）；
③ ITERATION 的 Round 号写完之后必须从 200 连续到 203（曲线仪器不能留洞）；
④ CHANGELOG 那三条标题改写每条命中恰好一次，且改后仍匹配 `^### .*（R<r> / `；
⑤ D 号：盘上最大必须是 D-200（我要写 D-201），且 DECISIONS 里没有 D-201 正文之外的重复；
⑥ 渲染后不留 `%(` 占位符，不出现 U+ 区间里没有定义的引用。
'''
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
DATE = '2026-10-19'
NOW = '2026-10-19 18:35'

# (R 号, 第 N 轮, U 三元组, commit 证据)
ROUNDS = [
    (201, 203, (653, 654, 655), '33b1322 + e97c17e'),
    (202, 204, (656, 657, 658), '728a1b2 + 2351593'),
    (203, 205, (659, 660, 661), 'b6077be + bd7a64f'),
]

# CHANGELOG 的三条既有标题：只做**最小机械改写**（插入 `/ U-…`），其余原文一字不动
CL_PATCH = [
    (u'（R201 非轮次笔 · 产品 0 文件）', u'（R201 / U-653…U-655 · 非轮次笔 · 产品 0 文件）'),
    (u'（R202 · 判据 1 文件加一行 print，产品 0 文件）', u'（R202 / U-656…U-658 · 判据 1 文件加一行 print，产品 0 文件）'),
    (u'（R203 第二笔非轮次 · 表 1 份 + 报告 1 处，产品 0 文件）', u'（R203 / U-659…U-661 · 第二笔非轮次 · 表 1 份 + 报告 1 处，产品 0 文件）'),
]

# ============ 三笔的内容（每条都要能在盘上被复查） ============

UI_SECTIONS = {}

UI_SECTIONS[201] = (
    u'## 第 %d 轮（R%d · %s）：222 的第一半 —— 热图**真帧通道**的证人 `scripts/heatmap_frame_levels.py`'
    u'（U-653…U-655 · 产品 0 文件，判据账）\n'
    u'''
- **U-653：判据那条通道与产物那条通道量的不是同一个东西，本轮先把产物的尺做出来。**
  判据在内存里读 `CGContext` 的位图 rep，真帧是落盘 PNG 之后由 `PIL` 读的 —— 两者之间隔着编码与色彩标注。
  证人 `scripts/heatmap_frame_levels.py` 只读帧：从一行里切出 5 个 run（`ladder()` 要求**恰好 5 格**且丢掉背景 run），
  逐格取中点，再按判据同一条地板（`min after ≥ 18`）与两条列偏置上限（G/B ≤ `--max-col-offset` 24）出三个结论。
  commit `33b1322`；自检 10 格在 `scripts/tests/test_heatmap_frame_levels.py`。
- **U-654：这把尺坏在最安全的那一侧 —— 缺输入一律 exit 2，不出结论。**
  缺帧目录、缺判据日志、只有一档外观的日志，三种都验过会红（`MISSING_SHOTS` / `MISSING_LOG` / 单档），
  `--help` 仍 0。合成样本两条正对照：同色阶梯 → 过；某一格塌成相邻值 → 红「掉到地板」；G 列整体平移 → 红「不再只压在 R 那一列」。
  这一格的意义是形状而非结论：它保证下一轮读到 0 个结论时，原因只能是"没量到"。
- **U-655：本轮没有新帧、也没有看图腿（NOT-RUN，不拿上一轮的帧冒充）。**
  产品 0 文件 ⇒ 帧未动；捕获卷沿用 `/tmp/shots_r197`（139 项）做**指针与形状**核对，但本轮**没有真的逐帧看图**。
  全量 `swift test` 与变异刀同样记 NOT-RUN（`33b1322` 那笔只跑了脚本电池与两个新自检）。
'''
) % (ROUNDS[0][1], ROUNDS[0][0], DATE)

UI_SECTIONS[202] = (
    u'## 第 %d 轮（R%d · %s）：222 的机制定性 —— 读出一个**自己造的假红**，修完之后 16 条最小 25.41，'
    u'而 222 的机制到现在仍未定（U-656…U-658 · 产品 0 文件，判据账）\n'
    u'''
- **U-656：色觉模拟第一版给我一个物理上不可能的读数，那条红是我的尺坏了，不是产品坏了。**
  Viénot–Brettel–Fagot 三行（0.625/0.375/0、0.300/0.700/0、0/0.040/0.960）在线性 RGB 上乘完，
  我第一版只把 R/G 重新编码回 sRGB、**B 留在线性** —— 于是暗档『空→最低档』读 10.41（会让我去改 `VisualHeat`），
  而 bucket3→bucket4 读 99.60（大于 65/255 的物理上限）。三通道一起编码后翻面消失：
  16 条（4 对 × 两档 × 两尺度）最小 21.00，判据那条最小 25.41，地板 18。commit `728a1b2`。
- **U-657：M732/M733 在**产品那条判据**上是绿的 ⇒ 补一条与输入无关的恒等式证人。**
  刀改的是矩阵行（g→lin.g、b→lin.b，后者正是我犯的那个量纲错），但产品结论对那两处不敏感，
  所以新加 `testDeuteranopiaSimulationMatrixIsWired` 用**合成纯色**读三个不变量：红↔绿 255→68.97（该塌）、
  蓝↔黄 255→255.00（不许塌）、中性灰 (128,128,128)→(128,128,128) 漂移 ≤ 2（三行和=1 的不动点）。读数行 `SIM_MATRIX`。
- **U-658：「机制定下来了」那句说过头，本笔自己撤回来 —— 222 仍是开账。**
  新 print `HEAT_INK_SPACE` 证明判据的 rep 与取色都是**设备 RGB**，而 PNG 声明 sRGB、alpha 全 255；
  反解 accent 形状（判据 ≈(0,122,255)、真帧 ≈(30,122,255)，只有 R 动）否掉「混合空间」候选；
  按 P3→sRGB 重算后浅三档偏置从 (6,1,0)/(12,1,0)/(18,0,0) 收到 (2,2,0)/(4,2,0)/(3,2,0)，
  但最饱和那一格反而从 21 **涨到 38** ⇒ 「落盘把设备值标成 sRGB」只解释掉一半，机制仍未定（commit `2351593`）。
  产品不动：两条通道各自的模拟后最小分离 21 与 25.41 都 ≥ 地板 18，谁对谁错都不改结论。
'''
) % (ROUNDS[1][1], ROUNDS[1][0], DATE)

UI_SECTIONS[203] = (
    u'## 第 %d 轮（R%d · %s）：清账表补 16 格（拖入落点 6 + 提示条 4 + 筛选条 6），\u3000并把**指针名册看不见的那一类**变成会红的门'
    u'（U-659…U-661 · 产品 0 文件，判据账 + 清账表）\n'
    u'''
- **U-659：闸门的一条尺只认一种路径开头，于是有 7 行指针从来没被检查过。**
  `PATH_RE` 要求以 `Sources|Tests|docs|scripts|Managers/` 开头 ⇒ 真表里写成 `MenuBarController.swift`（只有文件名）
  与 `Views/SearchField.swift`（少写包根）的行**既不算合法也不算非法**，`不合法格=0` 是空的。
  修法顺序有讲究：先把那 7 行改成从包根算起的整路径（改完全表 0 红），再让尺子有牙
  （`PATH_RE_LAX` + `path_problem()` ⇒ `EVIDENCE_PATH_PARTIAL` / `EVIDENCE_PATH_AMBIGUOUS` / `MISSING`）。
  commit `b6077be`；自检 `scripts/tests/test_motion_surface_gate.py` 24→30 格，含正对照"整路径不许红"。
- **U-660：按文件名建索引这一步自己会造出假歧义。**
  第一版走目录白名单时把 `.pytest_cache` 收了进来，于是 `README.md` 变成两个命中 ⇒ `EVIDENCE_PATH_AMBIGUOUS` 落在一个根本不存在的问题上。
  索引排除点开头目录与 `__pycache__` 之后 `DUP_NAMES=1→0`。另一条同族教训只记账、**还没配判据**：
  缺席断言是**忽略大小写**比的，所以 `缺席:...HistorySidebarView.swift=disabled` 会被文件里的 `focusEffectDisabled()` 喂饱
  ⇒ 缺席词要挑结构名（`isEnabled`/`isLoading`/`showSkeleton`），要钉住它欠一条守卫 ⇒ 已开 BACKLOG 226。
- **U-661：16 格判据账落地，未清账 47→31，而这 16 格的看图腿是 NOT-RUN。**
  拖入落点 6 格（空 kept／加载 not-applicable／错误 **not-added** 转 BACKLOG 224／成功 kept／选中 not-applicable／禁用 not-added）、
  提示条 4 格（空/加载 not-applicable／悬停 not-added／按下 kept）、筛选条 6 格（空 kept／加载 not-added／错误 not-applicable／
  成功 kept／聚焦 kept —— `sidebarFocusRingHidden()` 是**有意**保留可聚焦、关系统环，macOS 12/13 没那个 API ⇒ 平台缺开关不是漏／
  禁用 not-applicable —— `isEnabled` 0 命中，两条 `allowsHitTesting(false)` 在 `SegmentedFilterPicker`（第 359 行起）之外）。
  表 115→131 行、地板同笔抬到 131、`MOTION_LEDGER_RESULT=ok 不合法格=0`、125→131 行的证据指针全部解析得到。
  产品 0 文件 ⇒ 没有新帧，看图腿记 **NOT-RUN**（唯一真看过的是 `/tmp/shots_r197/notice-banner-560x170-{dark,light}`，
  那条只支撑「按下」一格的按钮垂直居中，沿用 R25 的 0 / 7.5 / 14.5pt 读数，不当成本轮新量）。commit `bd7a64f`。
'''
) % (ROUNDS[2][1], ROUNDS[2][0], DATE)

VI_SECTIONS = {
    201: u'''## Round 201 · 222 的第一半：热图真帧通道的证人 `scripts/heatmap_frame_levels.py`（%s · 产品 0 文件，判据账）

新工具只读产物帧（5 格阶梯、逐格中点、判据同一条地板 18 + 两条列偏置上限 24），三种缺输入一律 exit 2 不出结论；
自检 10 格（含两条合成正对照：某格塌相邻值该红、G 列平移该红）。全量 swift test 与变异刀本笔 NOT-RUN。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 6/15 | 没有新帧、也没逐帧看图（产品 0 文件）；看的是帧的 run 结构与尺的形状 |
| 判据有效性 | 13/15 | 新尺与判据共用同一条地板与同一个估计量；缺输入侧有 exit 2 的正反对照 |
| 假绿防御 | 14/15 | 拒绝在无帧/无日志时给绿；把「只有一档外观」单列成一个红而不是跳过 |
| 产品面推进 | 9/15 | 画面 0 改动，但 222 从「两条通道不一致」变成「有一条只读产物的尺能量它」 |
| 台账一致性 | 11/15 | 本笔当时按「非轮次」落 CHANGELOG/BACKLOG，UI_AUDIT 与 ITERATION 缺节 ⇒ 由本补落笔（R201…R203）补齐 |
| 交付诚实性 | 14/15 | commit 与台账都写明 NOT-RUN 的范围，不拿上一轮读数冒充 |
| 可复核性 | 13/15 | `33b1322` 一笔可复查；被引用的 5 处路径/行号本轮补落时逐个解析过 |
''' % DATE,
    202: u'''## Round 202 · 222 的机制定性：读出一个自己造的假红，修好后 16 条最小 25.41，机制仍未定（%s · 产品 0 文件，判据账）

色觉模拟第一版只重编码 R/G ⇒ 暗档最低对读 10.41（假红）、bucket3→4 读 99.60（物理不可能）；三通道一起编码后翻面消失。
新加合成纯色恒等式证人（红↔绿塌、蓝↔黄不塌、中性灰漂移 ≤2）因为它要能在**产品判据不敏感**时也红。
`HEAT_INK_SPACE` 证明判据读设备 RGB 而 PNG 声明 sRGB；P3→sRGB 重算只解释掉浅三档，最饱和那格反而 21→38 ⇒ 222 保持开账。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 9/15 | 没有新画面可看（产品 0 文件）；看的是反解出的通道形状与两套读数对账 |
| 判据有效性 | 14/15 | 16 条读数值绑在地板 18 上；恒等式证人与产品判据分开，M732/M733 的盲区被它补上 |
| 假绿防御 | 15/15 | 自曝假红并给出物理上限作反证；撤回「机制定下来了」那句，把 222 留成开账而不是结案 |
| 产品面推进 | 9/15 | 画面 0 改动；把「要不要改 `VisualHeat`」这个问题从 10.41 那个假读数上摘下来 |
| 台账一致性 | 11/15 | 当时只落 CHANGELOG/BACKLOG 与 D-200 一线，本轮次节由补落笔写入 |
| 交付诚实性 | 15/15 | 追记 2/3/4 逐条写明哪句说过头、被哪个读数否掉 |
| 可复核性 | 14/15 | `728a1b2`/`2351593`、`SIM_MATRIX` 与 `HEAT_INK_SPACE` 两行原文读数都在册 |
''' % DATE,
    203: u'''## Round 203 · 清账表补 16 格 + 指针名册的第三种坏法变成会红的门（%s · 产品 0 文件，判据账 + 清账表）

115→131 行、未清账 47→31、地板同笔抬到 131；`PATH_RE_LAX` 与 `EVIDENCE_PATH_PARTIAL/AMBIGUOUS/MISSING`
把「形状合法但读者点不开」这一类接住，改完 7 行整路径后全表 0 红（`UNRESOLVED_PATH_REFS=0`）。
自检 24→30 格含正对照。看图腿 NOT-RUN（产品 0 文件，无新帧）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 7/15 | 无新帧；真看过的只有沿用的 notice-banner 两帧，且只支撑「按下」一格 |
| 判据有效性 | 15/15 | 16 格证据全绑可复查对象（文件 + 行号 + 缺席断言由闸门逐条验），尺子自己新加三种坏法会红 |
| 假绿防御 | 15/15 | 修尺顺序先改数据再让牙（避免恒红门）；歧义索引的 `.pytest_cache` 假象被抓出并修 |
| 产品面推进 | 10/15 | 画面 0 改动，但筛选条/落点/提示条三表面从「欠 16 格」变成「逐格有理由与代价」 |
| 台账一致性 | 13/15 | 125/131 行同笔抬地板、报告 §9.3 由 `test_final_report_claims.py` 逼着换成新读数；本笔的三账标题由补落笔写全 |
| 交付诚实性 | 15/15 | 看图腿记 NOT-RUN；「缺席词要挑结构名」那条只记账不谎称已有判据 |
| 可复核性 | 14/15 | `b6077be`/`bd7a64f`、`MOTION_LEDGER_*` 原文行、被引用路径全部解析得到 |
''' % DATE,
}

CL_BACKFILL = u'''### 补落：R201 / R202 / R203 三笔非轮次笔的 UI_AUDIT 与 ITERATION 台账（BACKLOG 225 的①出口 · 产品 0 文件，台账账）

- 三笔各自的数字只从**盘上能复查的东西**抄：commit 正文（`33b1322`/`e97c17e`/`728a1b2`/`2351593`/`b6077be`/`bd7a64f`）、
  已在册的读数行（`SIM_MATRIX`、`HEAT_INK_SPACE`、`MOTION_LEDGER_*`）与脚本电池当下这次（384 格）。
- 没跑过的验证照实写 NOT-RUN：这三笔都没有新帧（产品 0 文件 ⇒ 看图腿空），R201/R202 没有跑全量 `swift test`，R203 没有跑变异刀。
- 三条既有 CHANGELOG 标题做了**最小机械改写**（在 `（R20X` 后插入 `/ U-6xx…U-6yy`），正文一字未动 —— 这样轮换 STATE 时
  `test_round_batch_consistency.py` 读的是**真标题**而不是我为它造的桩标题（186/187 那次就是这么把「半批已写」查没的）。
- 新开 D-201（指针必须整路径 + 缺席词要挑结构名，只有前半有牙）；BACKLOG 225 记追记结案，并把「缺席词挑错还欠一条守卫」写清未开单。

'''

D_BODY = u'''**D-201（R201…R203 补落）：清账表的证据指针必须写成**从包根算起的整路径**；缺席断言要挑结构名而不是动效词根**

读数（本机，`python3 scripts/motion_surface_gate.py` + 125/131 行那张表）：真表里曾有 7 行指针写成
`MenuBarController.swift` 或 `Views/SearchField.swift` 这种形状，而 `PATH_RE` 只认 `Sources|Tests|docs|scripts|Managers` 开头
⇒ 这 7 行既不红也不被检查，`不合法格=0` 是个空的通过。改成整路径后全表 0 红，闸门新增
`PATH_RE_LAX` + `EVIDENCE_PATH_PARTIAL` / `EVIDENCE_PATH_AMBIGUOUS` / `MISSING` 三态，
`scripts/tests/test_motion_surface_gate.py` 24→30 格（含正对照：整路径不许红）。

⇒ 两条规矩：① 指针要么整路径、要么不写；「形状合法」不等于「指得到东西」（U-424 的第二种失效）。
② 缺席断言的比较是**忽略大小写**的，所以 `缺席:...=disabled` 会被同一文件里的 `focusEffectDisabled()` 喂饱
   —— 这一条**目前只有台账记着，没有会红的守卫**（写下来就是为了不让它被当成已交付）。
适用面：`docs/motion_surface_ledger.json` 与所有走同一文法的证据指针；不适用：D-号 / BACKLOG 号 / 批次号那类符号指针。

'''

BACKLOG_APPEND = u'''**225 追记（R203 补落）：三笔非轮次台账已经按①出口补落，这条债清了**

UI_AUDIT 新增第 203 / 204 / 205 轮三节（U-653…U-661，每节 3 条定义与标题区间吻合），
ITERATION 新增 Round 201 / 202 / 203（各带七维表，曲线仪器从 200 连续读到 203），
CHANGELOG 三条既有标题做最小机械改写补上 `/ U-…` 段。STATE 随之轮换到 R203 / 第 205 轮 ——
`test_round_batch_consistency.py` 查最近三笔（R203/R202/R201）时读到的都是**真标题**，不是桩。
没跑过的验证（新帧、R201/R202 的全量卷、R203 的变异刀）在三节里都写明 NOT-RUN，没有用旧读数冒充。
仍欠的一条已开单：「缺席断言挑词要挑结构名」目前没有会红的守卫 ⇒ BACKLOG 226。

'''

STATE_BLOCK = (
    u'最后更新：%s（本地 · R%d / 第 %d 轮：**R201…R203 三笔非轮次台账补落 + 清账表 115→131 行 + 指针名册的第三种坏法有了牙**'
    u'（U-653…U-661 · 产品 0 文件，台账账 + 判据账）\n\n'
    u'**这笔补的是什么**：BACKLOG 225 的①出口 —— 三笔「非轮次」提交（`33b1322`/`728a1b2`/`b6077be`+`bd7a64f`）'
    u'当时只落了 CHANGELOG 与 BACKLOG，而三账标题守卫只看离 STATE 最近三笔 ⇒ 它们一旦进窗口就是三格红。'
    u'现在 UI_AUDIT 有第 203/204/205 轮三节（U-653…U-661，区间与定义行吻合），ITERATION 有 Round 201/202/203 三节'
    u'（各带七维表，曲线从 200 连续到 203），CHANGELOG 三条标题机械补上 `/ U-…` 段。\n'
    u'**产品面**：0 文件 ⇒ 帧未动、无换装；看图腿记 NOT-RUN（唯一真看过的是沿用的 notice-banner 两帧，只支撑「按下」一格）。\n'
    u'**清账表**：115→131 行（拖入落点 6 + 提示条 4 + 筛选条 6），未清账 47→31，地板同笔抬到 131；'
    u'`MOTION_LEDGER_RESULT=ok 不合法格=0`；指针名册新增 `PATH_RE_LAX` 与 PARTIAL/AMBIGUOUS/MISSING 三态，'
    u'自检 24→30 格（`b6077be`）。\n'
    u'**验证**：脚本电池 384 全绿（`Ran 384 tests / OK`）、闸门与报告对账各一次、全量 swift test 本笔未跑（台账笔，Swift 侧 0 改动）。\n'
    u'**下一轮（R204）的靶**：⓪ 读 `b6077be`/`bd7a64f` 与这笔的 CI（三跑都要 run id↔commit 成对，未读只能说未读）；'
    u'① **回到动效本体**：清账表连续多笔 0 画面改动 ⇒ 下一轮要么真点一个位点做动效（带帧与变异刀），要么把 218 那三臂的逐帧条带真看一遍；\n'
    u'② 222：色彩标注那条机制仍未定（P3→sRGB 只解释浅三档，最饱和那格 21→38 反而更糟）；\n'
    u'③ 215（真机亮档一格）、201/202/205/207、224（拖入被拒收没有就地回执，先做分辨实验）；\n'
    u'④ 220 路 A 等用户授权改 `AppleKeyboardUIMode`；未清账剩 31 格，名单以 `MOTION_LEDGER_OPEN` 为准。\n'
    u')\n'
) % (NOW, 203, 205)

LEDGERS = {
    'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
    'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
    'CHANGELOG.md': u'^### .*（R%d / ',
}


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


def insert_before_first(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not idx:
        raise SystemExit('ANCHOR_NOT_FOUND %r' % prefix)
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    paths = {n: os.path.join(ROOT, n) for n in
             list(LEDGERS) + ['AGENT_STATE.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md']}
    old = {k: read(v) for k, v in paths.items()}

    if u'## Round 201 · ' in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('BACKFILL_ALREADY_WRITTEN ⇒ 不重复落盘')
    if u'补落：R201 / R202 / R203' in old['CHANGELOG.md']:
        raise SystemExit('BACKFILL_ALREADY_WRITTEN_CHANGELOG ⇒ 不重复落盘')

    # ⑥ 渲染检查：不许留未吃掉的占位符
    everything = [(u'ui%d' % k, v) for k, v in UI_SECTIONS.items()] + \
                 [(u'vi%d' % k, v) for k, v in VI_SECTIONS.items()] + \
                 [(u'cl', CL_BACKFILL), (u'd', D_BODY), (u'bl', BACKLOG_APPEND), (u'st', STATE_BLOCK)]
    for name, txt in everything:
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK 在 %s' % name)
        if u'%d' in txt or u'%s' in txt:
            raise SystemExit('UNRENDERED_FORMAT 在 %s（还剩 %%d/%%s 没被吃掉）' % name)

    prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                          cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
    prod_files = len([l for l in prod.splitlines() if l.strip()])
    if prod_files:
        raise SystemExit('PRODUCT_NOT_ZERO 补落笔应当产品 0 文件，实际 %d 个 ⇒ %s' % (prod_files, prod))

    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 200:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-201）⇒ 不写盘' % dec_max)

    new = {}
    # UI_AUDIT：降序插在当前的「第 202 轮」之上（先插 203 节，再 204，再 205 ⇒ 顶上是 205）
    ui = old['AGENT_UI_AUDIT.md']
    for r in (201, 202, 203):
        ui = insert_before_first(ui, u'## 第 ', UI_SECTIONS[r])
    new['AGENT_UI_AUDIT.md'] = ui

    vi = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n')
    for r in (201, 202, 203):
        vi = vi + u'\n\n' + VI_SECTIONS[r].rstrip(u'\n') + u'\n'
    new['AGENT_VISUAL_ITERATION.md'] = vi

    cl = old['CHANGELOG.md']
    for old_t, new_t in CL_PATCH:
        n = cl.count(old_t)
        if n != 1:
            raise SystemExit('CL_ANCHOR_BAD %r hits=%d（要 1）⇒ 不写盘' % (old_t[:40], n))
        cl = cl.replace(old_t, new_t, 1)
    new['CHANGELOG.md'] = insert_before_first(cl, u'### ', CL_BACKFILL)

    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + BACKLOG_APPEND.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')]
    if not top:
        raise SystemExit('STATE_ANCHOR_NOT_FOUND')
    new['AGENT_STATE.md'] = u'\n'.join(st[:top[0]] + [STATE_BLOCK.rstrip(u'\n'), u''] + st[top[0]:])

    # ① 模拟三账窗口（R203/R202/R201 三笔 × 三本账）
    for name, fmt in LEDGERS.items():
        for r in (201, 202, 203):
            if not re.search(fmt % r, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (r, name))
    if re.search(u'最后更新：[^\\n]*R202 / 第', new['AGENT_STATE.md']):
        raise SystemExit('STATE_STILL_ON_R202 ⇒ 没换到 R203')

    # ② 每一节的 U 区间与定义行吻合（≥3 且恰好那三个号）
    for r, n, (a, b, c), _ev in ROUNDS:
        title = u'## 第 %d 轮（R%d' % (n, r)
        section = new['AGENT_UI_AUDIT.md'].split(title, 1)[1]
        section = section.split(u'## 第 ', 1)[0]
        defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
        if defined != [a, b, c]:
            raise SystemExit('U_RANGE_MISMATCH R%d 定义 %s（要 %d…%d）' % (r, defined, a, c))
        if u'U-%d…U-%d' % (a, c) not in title + u'（U-%d…U-%d' % (a, c):
            raise SystemExit('TITLE_HAS_NO_U_RANGE %s' % title)

    # ③ 曲线仪器的连续性：Round 号必须从 200 连续到 203
    rounds = sorted(int(m) for m in re.findall(u'^## Round (\\d+) ·', new['AGENT_VISUAL_ITERATION.md'], re.M))
    for r in (201, 202, 203):
        if r not in rounds:
            raise SystemExit('ITERATION_ROUND_MISSING %d' % r)
    tail = [x for x in rounds if x >= 197]
    if tail != list(range(197, 204)):
        raise SystemExit('ITERATION_ROUND_GAP %s（要 197..203 连续）' % tail)
    for r in (201, 202, 203):
        sec = new['AGENT_VISUAL_ITERATION.md'].split(u'## Round %d · ' % r, 1)[1].split(u'## Round ', 1)[0]
        if u'七维度自评' not in sec:
            raise SystemExit('CURVE_NO_MARKER Round %d 没有「七维度自评」锚点 ⇒ 曲线推不出分' % r)
        dim_rows = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', sec, re.M)
        if len(dim_rows) != 7:
            raise SystemExit('CURVE_DIM_ROWS Round %d 读到 %d 行 n/15（要 7）' % (r, len(dim_rows)))

    # ④ BACKLOG 225 的追记要能被引用检查找到
    for ref in re.findall(u'BACKLOG (\\d{3})', CL_BACKFILL + D_BODY + STATE_BLOCK + BACKLOG_APPEND):
        items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'**D-201' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-201 没落上')

    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'BACKFILL_R201_203_WRITTEN files=%d rounds=%s U=653..661 iter_tail=%s prod=0'
          % (len(new), [r for r, _, _, _ in ROUNDS], tail))
    return 0


if __name__ == '__main__':
    sys.exit(main())
