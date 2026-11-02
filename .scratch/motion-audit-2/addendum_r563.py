# -*- coding: utf-8 -*-
"""R563 补记：本轮成对号（含 A 笔标题错标的正确读法）与 R564 的 ⓪ 读单。

写盘之后必须回读一次并数未渲染占位符（R561 的自伤、R563 写手已把两种形状都拦下）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R563 补记（2026-11-03 · 第 562 轮 / Round 560 · 成对号 + R564 读单）

① **本轮成对号（一次性 push 的自证，含一条标题错标的正确读法）**：⓪ 笔 `851b124`（开工节 + 改掉 R562 补记 ④ 那句互斥的「636 本轮结案」）、A 笔 `64d3192`（`materialBlindSpotFixtures` 补另一通道读数 + 撤掉的候选判据只留说明）、台账笔 `a13727c`（七本 + 派生格落盘后现读）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间三笔**没有独立跑** ⇒ 具名 `CI_UNREAD`，不许写成「没红」。
  ⚠ **A 笔 `64d3192` 的标题前缀写成「R562 A：」，是错标**：它自己的轮次身份行写的是 `第 562 轮 / Round 560` = **R563**，正文与 diff（只改 `Tests/` 一段注释）也都是 R563 的。正确读法 = **笔序是 R563 的 ⓪ 开工节 + A**，前缀那个号请当作笔误。**没有 amend**：监工本轮明令「不许 amend/重写已存在的标题」，系统层规矩也是默认新建一笔 ⇒ 代价是历史上永久留一条错标签，写进账而不是偷偷改。**守卫现读确认没被带错**：`python3 scripts/product_streak.py` ⇒ `ledger_round=562 streak=3 … last=631f910 last_round=559`（它按 subject 里的 `第 N 轮` 认身份，那一格是对的）；`--check` ⇒ `PRODUCT_STREAK_LEDGER_OK`（退出码 0）；`python3 scripts/ledger_absence_claims.py` ⇒ `格=162 声明=63 不成立=0/63`；电池里 `test_round_batch_consistency` 三格全绿（STATE 自报的 (R563, 第 562 轮) 与审计台账 `## 第 562 轮（R563` 标题逐字对上）⇒ **没有任何守卫把这笔读成 R562**。若下一轮要钉死这类错标，位置在这里：给 subject 的 `Rnnn` 前缀与正文 `第 N 轮` 加一把**一致性刀**（本轮不做，因为做它要改历史或改守卫口径，两样都不该顺手）。
② **⓪ 那跑收口前到数，但不是结论读数**：`41531750912 ↔ 75b32d6` = concluded **failure**（已等 4019s），而 `gh run view --json jobs` 现读 `build-and-test cancelled` ⇒ **失败的原因是作业被取消，不是任何一条判据红**；`ci_read.py readings` 直接报 `gh run view … --log 失败（exit=1）：log not found: 125573433836` ⇒ 日志从未落盘。**四格因此全部维持具名 NOT-RUN（成因 = cancelled、日志取不到）**：(a) `HEAT_LEGEND_*` 复核、(b) `BULLET_LEVELS` 在 runner 1x 走哪条、(c) `过渡帧数=` 第五数、(d) STEP[9] 第五跑 + STEP[18] 622。**这一对进「永不重开」名单**（与 `41452722560↔58851c2`、`41455782587↔598b253` 同形）。连带一条必须写清：**R562 那条新判据 `BULLET_LEVELS` 至今没有任何 runner 读数**（上一跑 `41519677393↔f12f50d` 不含它，这一跑没有日志）⇒ 账上是「判据未推」，既不是「判到了」也不是「走出口」。
③ **R564 的 ⓪ 必读**（逐条抄全部失败步骤；success 的步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时未创建 ⇒ 现在去读。四格各问什么：
  (a) **`BULLET_LEVELS` 第一次被 runner 验** —— 预期 `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(8.0/8.0pt) 容差=1px 合并=1px`。**三条出路预先写死，不许临场决定**：判到 ⇒ 报 px 与 pt；打 `BULLET_LEVELS_NOT_RUN=detail-frame-plain` ⇒ 详情帧在 1x 没落墨（R483 家族）⇒ 具名入账并补内容墨证人，**不许读成「判过了」**；红在步进等距 ⇒ 先分辨是 1x 像素预算不够（合并容差在 1x 只剩 1px）还是产品真漂（对照 M1461 那条 `[32,38]px`=16/19pt 的红形状）⇒ 前者按 `scale` 派生容差、后者才是产品缺陷；**三种情况都不许降墨下界、不许改期望、不许加豁免**。⚠ 本机那次 LANCZOS 降采样只是**代理**，它不签这一格。
  (b) `HEAT_LEGEND_*` **复核**是否仍判到（`HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`）—— 首次签收已在 `41519677393↔f12f50d`，这一格只问"还在不在"；回到 `solid-unresolved` 就是尺被改坏，按读数修、不许降地板。
  (c) `过渡帧数=` 第五数（已 2/5/0/5，每格 71.5/26.0/75.6/28.9ms）：读到几都按 629 既有口径具名入账，**不许重开产品排查、不许动 ≥2、不许改期望**；再 ≤1 就把两条出路的代价摆给用户 ⇒ **工作侧不许自行登记 `sampled`**。
  (d) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`；STEP[18] 622 有无新值（第十四值仍 219.7ms/2 颗；120ms 锚点、容差 1 颗、`over_runs` 口径不动）。
- 仍挂着、永不重开：`41531750912↔75b32d6`（cancelled、`log not found: 125573433836`）、`41452722560↔58851c2`、`41455782587↔598b253`；R562 的 `327bc53`/`ff2cb9f`/`5d71660`/`c8c950f`、R561 三笔、R560 五笔、R558 两笔 ⇒ 同批无独立跑 `CI_UNREAD`。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到 ⇒ 一个字结论也没写；629 写「(B) 已落地 + 635 已结案 + runner 三跑实测 2/5/0（第四跑读到 5 ⇒ 四跑 2/5/0/5）⇒ ≥2 在那台机器的钟上是间歇可满足」，**两条消红出路（登记 `sampled` / 把尺改成对采样相位不敏感）的代价仍摆给用户，本轮没有自行选**；**636 继续开单**（措辞已在四本账里统一：只证「有对象可量 + 正文列步进不漂」，三级项目符的尺寸没有被判过；定尺寸契约要撞 R549/R560 ⇒ 归用户）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 11 面不变**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、R560 任务勾选框标记字体）—— **本轮产品 0 文件 ⇒ 不抬禁碰数**（`FRAME_BASELINE_CHANGED=0` 就是这句话的证人）；刀号 **M1463 起且未使用**（现读最高仍是 M1462；本轮一把候选判据被撤 ⇒ 没登记刀）；4.5 地板、150 上限、120ms 阈值、**Motion ≥2 帧地板**、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped **57 连六跑**（R558–R563 都是 57 ⇒ 只记现读，不动门、不修回 55）。
⑤ **本轮现读（收口时）**：build 告警 **0**；判据卷 `UICaptureTests` **221/4 skipped/0 失败（602.2s）**；帧 **356 CHANGED=0 MISSING=0 ADDED=0**（只改了 `Tests/` 一段注释 ⇒ 基线本来就该不动）；全量 **1405/57/0（701.2s）**；预检三读**串行** `tables=361 covered=295 arms=757 bad=0`、`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→66415，备份 `before-R563`）；清账 **162/63/0**；streak **台账落盘之后**现读 `ledger_round=562 streak=3` ⇒ `PRODUCT_STREAK_LEDGER_OK streak=3`（报告那一格从前写 2，被 `PRODUCT_STREAK_LEDGER_STALE` 点过一次之后改成派生值）；sources 格 `账上=R560/631f910 git=同 ⇒ 一致=是`（产品 0 文件 ⇒ 无变化、无须补正笔）；**占位符回读 `%(?=[a-zA-Z])` 在「`## R563 状态` → `## R563 ⓪ 开工`」这一段 = 0**；电池 **`Ran 696 / OK (skipped=5)`、退出码 0**（台账 + `--write` 之后一遍过，**本轮没有格式红也没有重复写红** —— R562 那两条教训兑现成了代码：写手每一本都有幂等守卫、`fill()` 两种占位符形状都查、守卫正文里不出现它搜的串）。
⑥ **本轮自伤与"没干活"的区别（照实写）**：① A 笔 `64d3192` 的 subject 前缀错标成 `R562 A`（正文身份 `第 562 轮 / Round 560` 是对的）⇒ 不 amend，错标留在历史里并在这里点名，守卫现读确认没被带错（见 ①）。② **产品位这一格本轮没落地**：六个候选全部被自己的数否掉（读数没到 / 撞两个禁碰面 / 是通道不是产品 / 尺分不出对象 / 装饰性数据底 / 标题两行），streak 因此到 **3** —— 账里把它写成"候选逐位排除 + 具名"，**没有拿"改账 + 名册注释"冒充产品推进**，也没有为了凑数去碰禁碰面或放宽任何门。③ 一条候选判据（三枚行内标记的墨高）写到一半**撤掉**：它的"时间行最右一段墨"在 `link`（链环两圈）与 `textformat`（中文区域解析到 CJK 变体「格式」）上读到的是**笔画**（实测 5.5pt / 2.0pt 宽），而三枚标记真实墨高都 ≥8pt ⇒ 是尺坏不是产品坏 ⇒ 撤守卫、不登记刀、把"这条轴要判需要什么形状"写进 U-2430。④ **下一轮的取靶要请用户定向**：合法路径只剩 632 的两格（② 合成一次取样 = 要重钉估高度算式并配刀；① 图片整文件读 = 账上已判"可接受"）或用户指定一个面；我不再自己凑第七个候选。

"""


NUM = {}


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = (u"一律不动。\n"
              u"## R563 ⓪ 开工")
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    if u"### R563 补记" in t:
        sys.stderr.write("ALREADY_WRITTEN\n")
        return 1
    body = BLOCK
    for key, value in NUM.items():
        body = body.replace(u"@@%s@@" % key, value)
    left = re.search(u"@@[A-Z_]+@@", body)
    if left:
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % left.group(0))
        return 1
    bad = re.search(u"%(?=[a-zA-Z])", body)
    if bad:
        sys.stderr.write("BARE_PERCENT %s\n" % body[max(0, bad.start() - 40):bad.start() + 20])
        return 1
    if not check:
        new = anchor.split(u"\n")[0] + u"\n" + body.strip(u"\n") + u"\n\n" + u"## R563 ⓪ 开工"
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R563_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
