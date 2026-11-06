# -*- coding: utf-8 -*-
"""R588 补记笔的 STATE 那一节：⓪ 两跑到数 + 三条预测由脚本判 + 五把刀末态由本笔签 + ⑨ 封条。

锚：`## R588 状态（` 第一次出现处（补记插在它**上面**，与 R585/R586/R587 补记同形）。
写前断言锚命中一次、写后回读计数；幂等：盘上已有 `## R588 补记` 就什么都不做。
本节文本必须过它自己那条守卫 —— 所以写完后立刻跑 `scripts/stage_gate_claims.py`（判最新一节）。
"""
import io
import re

ROOT = "/Users/wangziyi/Codex_Project0"
P = ROOT + "/AGENT_STATE.md"
ANCHOR = u"## R588 状态（"
HEAD = u"## R588 补记（"

BLOCK = u"""## R588 补记（第 587 轮 / Round 585 · 产品 0 文件）：⓪ 两跑到数 —— 三条预测由脚本判，其中一条**不中**，而不中的原因是我这把尺取错了那一步

⓪·1 **R587 那两跑到数**（取值时刻=2026-11-06 09:05，`ci_status_r588.py` 现读、`gh run view --json status,conclusion,headSha` 逐跑配）：
    · `42130898663 ↔ f01ba38` ⇒ `completed / failure`，全部失败步骤逐字 `STEP[15] Swift tests (executed-count gate)`、
      `STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`（三朵，没只盯自己新加那一步）。
    · `42131401738 ↔ 7abd77d` ⇒ `completed / failure`，`STEP[15]/[17]/[18]/[19]` 四朵 —— 比主笔多一朵 `STEP[18] On-screen probe coverage floor`。
    · **归因**：前三朵与 R587 补记 ⓪·3 ⑥ 那条归因锚（`42118421683 / 42119000322` 同形 `STEP[15]/[17]/[19]`）逐字同形状
      ⇒ 不是 R587 引入的回归，它已经挂着好几轮了。**STEP[18] 那一朵是新读数**：主笔那跑它是
      `本次下结论=8 本次跑过=8 红=0`，补记那跑是 `本次下结论=3 本次跑过=7 红=1`，而 `7abd77d` 现读只动了 `AGENT_STATE.md`
      加它自己的写手脚本（两本、0 判据、0 产品）⇒ 同一判据在两跑之间**读数会漂**，不能读成「上一轮绿了」，也不能读成 R587 的回归。
⓪·2 **R587 交下来的三条预测由脚本判**（`ci_status_r588.py` 的 `PREDICTIONS`，标签与判法一字未动，不目测对拍）：
      `① SCALE_NOT_RUN 是这一支唯一出口 = 不中`、`② BAKE 那一行带四个新格子 = 中`、`③ 既有字段含义一字未改 = 中`（两跑四条读数一致）。
    **不中那一条错在我的尺，不在被预测的东西** —— 这一句必须和读数一起记，否则就成了「预测没中」这四个字：
    · 判法要求「门的正文里必须出现 `FRAME_BASELINE_SCALE_NOT_RUN=`」，而 `read_gate_lines` 在步骤名可用时只收步骤名含
      `Frame baseline` 的那两步 ⇒ 门那一步今天**一条 SCALE 行都没有**（现读直方图 `FRAME_BASELINE_SCALE*` 行数=0）；
      那 24 条 NOT_RUN 全在 `Release script tests`（电池），且逐字是 `no-frames（当轮分布=（无） 基线倍率=（不知道））` ⇒ **合成上下文**，不是真语料。
    · 按整跑重数一次（这是**第二个读数**，标时刻，不覆盖上面那个「不中」）：SCALE 家族直方图只有 `SCALE_NOT_RUN=24 / SCALE_SIZELESS=23`，
      而 `_TIE_NOT_JUDGED` 与 `_AMBIGUOUS` **各 0 条** ⇒ 预测的**内容**（不判出口只有一条）成立，**测试的形状**错了：
      我把「哪一步会印这条通道」当成已知，而没有现读那一跑的步骤分布。
    · 处置：标签与判法留在 `ci_status_r588.py` 里一字不改（回头改预测=改合同，R557 那条「数迟到只写补记、不回头改账」）；
      R589 写新预测时必须带上「正文从哪一步取」这一格。
⓪·3 **到数那一趟顺出来一条新事实（本笔不修，写成 R589 的第一个产品位）**：门那一步「当轮说得出倍率、基线说不出」这一格
    **一行都不印** ⇒ 倍率那一维在 runner 的门上是**静默**，而静默与「量了没问题」在输出里逐字相同 —— 这是靶 3 那一族的**第四处**，
    只是它不在档位循环里、在 if 链里，所以 `tier_reporting_shape.py` **认不出这种形状**（它只扫循环，不扫 if 链）。
    证人（逐字，取值时刻=本补记，取自 `42130898663` 的 `Frame baseline vs working manifest (fixture-set gate)` 那一步，该步含倍率的行只有 1 条）：
    `FRAME_BASELINE_BAKE 出处=无 commit=（无） 轮=（无） 倍率=（不知道） 口径帧数=（无） 倍率分布=（无） 不一致帧数=0 无尺寸段=0 原因=（无）`；
    代码形状 `frame_baseline.py:812` 那条 MISMATCH 要 `bake["scale"]` 非空、`:818` 那条 NOT_RUN 要 `not current_scale`
    ⇒ 两个条件同时不成立时无人出声。R589 两条路都要点名：扩那条守卫去认 if 链，或开新单并把它挂进对账；**不许**把这一格读成「runner 上这一维绿了」。
⓪·4 **本轮主笔那一跑**：`42139904001 ↔ b8939ce` 现读 `status=in_progress`、`conclusion=` 空 ⇒ **未到数**（取值时刻 09:05；
    没轮询等待、没拿本机读数顶它、没把「还没读到」写成「没有红」；进行中的 job 打 `--log` 得 0 字节是通道还没内容，不是内容里没有）。
⓪·5 **本补记笔自己那一跑 ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`**（修尺/补账那一笔的跑签不了自己，R555 / R565 / R584–R587 补记同一条）。
⓪·6 **R589 的 ⓪ 要读的五格**（前四条的判法写在 `ci_status_r588.py` 的 `PREDICTIONS_R589`，由脚本判、不由下一轮念）：
    ①`42139904001 ↔ b8939ce` 到数之后读**全部**失败步骤；②本补记那一跑（现取成对号再读）；
    ③`STEP[9]` 里 `TIER_SHAPE_RESULT=ok` 且 `档位循环=3 带return=0 无可数格=0` 第一次在 runner 上出现；
    ④`STEP[9]` 里 `STAGE_GATE_RESULT=ok`（判的最新一节是 R588）⇒ 这条守卫的外部证人到手；
    ⑤`FRAME_STATE_STOPS not-run=` 与 `RUNG_STEP_TIER_COVERAGE not-run=` 今天都不该出现 ⇒ 出现就是 runner 少了一档帧，不是本轮判据变了。
    另加本节 ⓪·3 那条静默与 ⓪·1 那朵 STEP[18] 漂移 —— 两条都不许从问题开始猜。

① **forward 更正（改账不删原文）**：主笔 ⓪ 那格「两跑都未到数 ⇒ 三条预测一条不判」在**当时**是对的，从本笔起它下面多了读数
    ⇒ 本笔在上面补这一节，不回改 R588 那一格；R587 补记 ⓪·2 那句 `RUN_UNFETCHED` 已由 R588 主笔 forward 过，本笔也不再动它。

② **五把刀的末态由本笔签**（主笔明写「M1557/M1558/M1559 的末态由补记那一笔现读，本笔不许提前替它们签字」）：
    `M1555 / M1556`（档位形状）与 `M1557 / M1558 / M1559`（第③段守卫）现读**全部** `预检=PASSED`、`CAUGHT (rc=1)`、`RESTORE_CLEAN=yes`；
    取完数把四张被改过的仪器对 HEAD 做 md5 —— `frame_recording_proof / stage_gate_claims / tier_reporting_shape / hover_two_state_diff`
    **四个都同**、`git status scripts/` 空；复跑两卷判据 `Ran 27 tests … OK`。
    M1558 的末态读数里那句 `判的范围=STATE R588` 只有在台账落盘**之后**才拿得到 ⇒ 这五把刀分两趟落，正对 R587 ⑨·2 那条「刀的执行对象要跟着判据走」。

③ **本轮唯一向前的一句话（只算 §3 第②段）**：第③段（着色器）今天仍**一字未写**，证人三条与主笔同 —— `Sources/` 空、
    `STAGE2_CLICKTHROUGH_BLOCKED` 与 `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS` 两条具名阻塞都没撤、规格 §3 第③段那一行没划。
    本节所有推进（守卫、刀、看图、名册）都在取证面，归属在这里说清楚：**没有一件属于第③段**，也不靠「②③」并列蒙过去。
    守卫现在是会红的：`--section R587` 现读 `断言=1 冒充段号=2 拦路=3 ⇒ STAGE_GATE_RESULT=red`（那三处留在历史台账里当永久证人），
    最新一节现读 `断言=0 冒充段号=0 提及或反向=9 ⇒ STAGE_GATE_RESULT=ok`。

④ **⑨ 的封条**：主笔 ⑨ 到 ⑨·9 为止，本补记**不往 ⑨ 加新格**；本节新增的自陈只有两句 ——
    (a) ⓪·2 那条不中的预测是我自己写坏的尺（没现读「哪一步印这条通道」就当成已知），
    (b) 派生格取早了：主笔 STATE 记 `判据卷 +24 / 新卷 15` 而终值是 `+27 / 18`；`product_streak.py --streak-for 588` 落盘前读 20、
    本笔现读 **21**（差的就是含本笔那一趟）⇒ 两个时刻都记、不回头改。
    门复算现读（09:06，本笔落盘**前**那一趟）：`RED_NAME_RECONCILIATION 节=R588 红名=11 计入行=7 编号去重=7 不计入=4 未标=0 对不上=0 口径=已启用`。

⑤ **台账计数器（本笔只动 STATE 一本）**：`## R588 补记` 形状写前现读=0、写后=1；UI/ITER/BACKLOG/DEC/FINAL/CHANGE 六本一字未动。
    禁碰清单照旧逐轮携带：本轮没碰 `Sources/`、没碰捕获侧 Swift（`UICaptureHarness.swift` 那 11 处一字未动 ⇒ 只登记成 661）、
    没动三张按机器登记的表与 `registeredOffscreenVerdict(scale:)`、没动 `FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10` 与 4.5 墨地板 / 150 上限 /
    120ms / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / 像素容差 1.5 / `--allow-missing`、名册与豁免表一字未改、
    `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED` 与 `FRAME_BASELINE_DRIFT_NOT_JUDGED` 两条具名不判没撤、第③段着色器一字未写。

"""

text = io.open(P, encoding="utf-8").read()
if text.count(HEAD) >= 1:
    print(u"DRY：盘上已有 `## R588 补记`（幂等重放）⇒ 不动")
    raise SystemExit(0)
n = text.count(ANCHOR)
assert n == 1, u"锚 `## R588 状态（` 命中 %d 次 ⇒ 不是唯一，停" % n
print(u"锚后首行=%s" % text.split(ANCHOR, 1)[1].splitlines()[0][:60])
new = text.replace(ANCHOR, BLOCK + ANCHOR, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(new)
back = io.open(P, encoding="utf-8").read()
print(u"写后回读：补记=%d 主节=%d 新增字符=%d"
      % (back.count(HEAD), back.count(ANCHOR), len(new) - len(text)))
m = re.search(r"(?m)^最后更新：(\d{4}-\d{2}-\d{2})（本地 · R(\d+) / 第 (\d+) 轮 / Round (\d+)）$", back)
print(u"最后更新行=%s" % (m.group(0) if m else u"（没读到）"))
