# -*- coding: utf-8 -*-
"""R562 补记：本轮成对号（含收口前到数的 runner 三格）与 R563 的 ⓪ 读单。

写盘之后必须回读一次并数未渲染占位符（R561 的自伤）：
  python3 -c "import io,re;t=io.open('AGENT_STATE.md',encoding='utf-8').read();s=t[t.index(u'## R562 状态'):t.index(u'### R562 补记')];print(len(re.findall(r'%(?=[a-zA-Z])',s)))"
要求 0。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R562 补记（2026-11-03 · 第 561 轮 / Round 559 · 成对号 + R563 读单）

① **本轮成对号（一次性 push 的自证）**：⓪ 笔 `327bc53`（纯台账开工节）、A 笔 `ff2cb9f`（夹具 1 张 + 判据 1 条 + 三把刀 + 名册 + 两个探针脚本）、台账笔与补正笔 `@@LEDGER@@`（七本 + 帧基线**同一笔** update + 636 半落地；补正那笔删掉 UI 那一本被写重复的一节并给写手补幂等守卫）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间四笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。本补记笔自己的跑取号时尚不存在 ⇒ 具名 NOT-RUN，R563 现读。sources 格本轮**没有变化**（产品 0 文件 ⇒ `@@SOURCES@@`）。
② **⓪ 那跑收口前到数**：`@@CI_CLOSE@@`
③ **R563 的 ⓪ 必读**（逐条抄全部失败步骤；success 步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时未创建 ⇒ 现在去读。三格各问什么：
  (a) **R561 那把几何派生尺在 runner 上判到了没有** —— `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4` 还是 `HEAT_LEGEND_NOT_RUN=solid-unresolved`。仍走出口 ⇒ 派生式在真 1x 帧上算错（**不是产品问题**），按读数修，**不许降地板、不许改期望、不许加豁免**。
  (b) **本轮这条 `BULLET_LEVELS` 在 runner 1x 走哪条** —— 预期 `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(8.0/8.0pt)`；若打 `BULLET_LEVELS_NOT_RUN=detail-frame-plain` ⇒ 详情帧在 1x 没落墨（R483 家族），具名入账并补内容墨证人，**不许读成"判过了"**；若红在步进等距 ⇒ 先分辨是 1x 的**像素预算**不够（合并容差 1px 在 1x 只剩 1px）还是产品真的漂（对照 `M1461` 那条 19pt 的红话形状），前者按 `scale` 派生容差、后者才是产品缺陷。⚠ 本机只做过**降采样体检**（`@@ONEX@@`），它不签这一格。
  (c) `MOTION_MARKDOWN_MODE_FADE … 过渡帧数=` 的**第四个** runner 真数：三跑已 2/5/0 ⇒ 无论读到几都**按 629 既有口径具名入账**，不许重开产品排查；若再次 ≤1，把「登记成 `sampled`」与「把尺改成对采样相位不敏感」两条出路的**代价**摆给用户定夺（**工作侧不许自行登记 `sampled`**，那会改 CI 拦什么）。
  (d) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`（第五跑）；STEP[18] 622 有无新值（第十四值 219.7ms/2 颗；120ms 锚点、容差 1 颗、`over_runs` 口径一律不动）。
- 仍挂着、永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、`log not found`）；R561 中间三笔、R560 五笔、R558 两笔 ⇒ 同批无独立跑 `CI_UNREAD`。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到，账里没写任何结论；629 写「(B) 已落地 + 635 已结案 + **runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足**」，不写完全结案，两条出路等用户点头；**636 本轮结案**（缺陷断言被机制 + 像素两条证伪，判据与三把刀已落地，退场条件被显式改写成第三条 —— 结案的是**我自己上一轮开的单**，不是别人给的门）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 11 面不变**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、R560 任务勾选框标记字体）—— **本轮产品 0 文件 ⇒ 不抬禁碰数**（`FRAME_BASELINE_CHANGED=0` 就是这句话的证人）；刀号 **M1463** 起（现读最高 M1462）；4.5 地板、150 上限、120ms 阈值、**Motion ≥2 帧地板**、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%` 一律不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped **@@SKIPPED_STREAK@@**（只记现读，不动门、不修回 55）。
⑤ **本轮现读（收口时）**：`@@CLOSE_READINGS@@`
⑥ **本轮自伤与空刀（照实记）**：`@@SELF_INJURY@@`

"""


NUM = {
    "LEDGER": (u"`5d71660`（七本 + 帧基线**同一笔** update）与补正笔 `c8c950f`（UI 那一本被写了两份 ⇒ 去重 + 幂等守卫）"),
    "SOURCES": (u"`账上=R560/631f910 git=R560/631f910 一致=是` ⇒ 本轮产品 0 文件 ⇒ sources 格**没有变化**、无须补正笔"),
    "CI_CLOSE": (
        u"**收口前复述 `queue`：`41519677393 ↔ f12f50d` = concluded **success**（已等 3591s）⇒ 三格当场从 NOT-RUN 转成读数**，"
        u"并按 `gh run view --json jobs` 现读 7/9/11/15/16/17/18/19 全部 `success`（不是从「不在失败名单」推的）。\n"
        u"- **⓪(a) 本轮最要紧的一条：R561 那把几何派生尺在 runner 上真的判到了** —— "
        u"`HEAT_LEGEND_COVERAGE light 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`"
        u"（dark 同形；4 行，来自 `Offscreen frame capture` 与 `Swift tests` 两步），而 `HEAT_LEGEND_NOT_RUN` **没有一行** ⇒ "
        u"连续三跑的 `scale-too-low` 出口断了，且 **R561 账上预测的「倍率=1.0x 地板 格4/图例4」被 runner 逐字证实**（连那两个数都没差）。"
        u"⚠ 口径说清：这一跑的 sha 是 `f12f50d`（R561 头笔）⇒ 它签的是 **R561 那次改尺**，不是本轮那条新判据。\n"
        u"- **⓪(b) `过渡帧数=` 第四个 runner 真数 = 5** —— 逐字 `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=2 "
        u"首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=752ms 每格=28.9ms`，STEP[19] 本跑 `success` ⇒ 四跑并排 **2 / 5 / 0 / 5**"
        u"（每格 71.5 / 26.0 / 75.6 / 28.9ms）⇒ 629 那句升级为「**≥2 在那台机器的钟上是间歇可满足的**」；按既有口径具名入账，"
        u"**没重开产品排查、没动 ≥2、没改期望、没自行登记 `sampled`**。\n"
        u"- **⓪(c)** STEP[9] `SKIP_ROSTER 键=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 **连续第四跑**绿；"
        u"STEP[18] `On-screen probe coverage floor` = `success` ⇒ 622 本跑无新值（第十四值仍是 219.7ms/2 颗）。\n"
        u"- **另记一格具名**：`BULLET_LEVELS` 在这一跑**没有一行**，而这不是通道坏 —— 这一跑根本不含本轮那条判据（它在补记之前未推的 `ff2cb9f` 里）"
        u"⇒ 具名「**判据未推**」，不许写成「runner 上判不到」，也不许拿它当「这条尺在 1x 走出口」的证据 ⇒ 那一格留给 R563 ⓪。"),
    "ONEX": (u"`light 1.0x 带=7 行=7 筛后=6 列=3 左沿=[36, 52, 68] 步进=[16, 16] 容差=1px 步进地板=8px`、dark 同形 ⇒ 列数不塌、"
             u"步进等距（漂移 0px vs 容差 1px）、步进 16px ≥ 地板 8px（余量 2 倍）。⚠ 它是 LANCZOS 降采样的**代理**、不是真 1x 渲染 ⇒ "
             u"只回答「四道筛还剩多少余量」，不回答「runner 判到了」"),
    "SKIPPED_STREAK": u"57 **连五跑稳定**（R558–R562 都是 57 ⇒ 只记现读，不动门、不修回 55）",
    "CLOSE_READINGS": (
        u"build 告警 **0**；判据 filter 绿（`Executed 1 test, with 0 failures`，读数 `BULLET_LEVELS light 行=6 列=3 步进=[32, 32]px"
        u"(16.0/16.0pt) … 列x=73px 墨高=8px(4.00pt) 列x=105px 墨高=6px(3.00pt) 列x=137px 墨高=8px(4.00pt)`、dark 墨高 9/7/8px）；"
        u"三把刀 **M1460/M1461/M1462 全 CAUGHT、RESTORE_CLEAN=yes**（M1461 把产品 `minimumAdvance` 16→12 ⇒ 步进实测翻成 `[32, 38]px`=16/19pt）；"
        u"**两把空刀在登记前撤掉**（只抹平一行缩进；把宽度筛抬到 40pt ⇒ 工具栏那行其实是被 y 窗口筛掉的 ⇒ 那道筛当前冗余）；"
        u"三张表登记进名册 ⇒ 预检 **tables=361 covered=295 arms=757 bad=0**、`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`、"
        u"`HIDDEN_ARMS 表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（三读**串行**）；判据卷 `UICaptureTests` **221/4 skipped/0 失败（675.1s）**"
        u"（R561 是 220 ⇒ +1 就是本轮这条）；帧 **update 之前 `COMPARED=356 CHANGED=0 MISSING=0 ADDED=2`（新增逐字是 "
        u"`detail-markdown-bullet-nested-720x520-light.png` / `…-dark.png`，名单外一个帧也没有 ⇒ 既有 354 张逐字节不变 = 产品 0 文件与禁碰面未动的证人），"
        u"同一笔 `update` 之后复跑 `356 / 0 / 0 / 0`**；全量 **1405/57/0（686.4s）**；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / "
        u"INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→30437，备份 `before-R562`）；"
        u"清账 **162/63/0**；streak **落盘之后**现读 `PRODUCT_STREAK ledger_round=561 streak=2 sections=538 …` ⇒ "
        u"`PRODUCT_STREAK_LEDGER_OK streak=2`（R561/R562 两轮都是产品 0 文件 ⇒ 连读到 2；报告那一格从前写着 1，被门 `PRODUCT_STREAK_LEDGER_STALE` 点过一次之后改成派生值）；"
        u"电池 **`Ran 696 / OK (skipped=5)`、退出码 0**（台账 + 补正 + `--write` 之后复跑）。"),
    "SELF_INJURY": (
        u"① **同一族的第五回，这次是「中途崩 ⇒ 一本写两份」**：第一次跑到 ITERATION 那一本时 `fill()` 被自家新加的守卫拦下 —— "
        u"我在**账的正文里**写了「percent+左括号」这个字面量当说明，守卫命中我自己写的字面量（R55 / M276 那一族的形状），"
        u"而 UI_AUDIT 那一本**已经写盘** ⇒ 修完 prose 重跑就把 R562 那一节写了两份 ⇒ `test_ui_audit_ids_are_unique` 抓出 U-2419…U-2425 各定义两次。"
        u"处置：删掉第一份（两份逐字节相同、各 7179 字符，所以不丢内容），并把**幂等守卫补进写手**（UI 那一本已写过就拒绝重跑 —— STATE 那一本从前就有这道守卫，这次给 UI 补上）。"
        u"⚠ 教训不是「小心点」，是两条：**(i) 守卫搜的串不许出现在守卫自己的正文里**（要提它就得拆开写或换成中文形状）；"
        u"**(ii) 写多本账的脚本要么全有幂等守卫、要么先全部 dry-run 再统一写**（只给一本加守卫 = 崩在中间时另一半照样重复）。"
        u"② **占位符这一回守住了**：`%(?=[a-zA-Z])` 在「`## R562 状态` → `### R562 补记`」这一段 = **0**（写手 `fill()` 这轮起两种形状都查：具名占位符与裸 percent+字母），"
        u"派生格（streak / sources）一律落盘之后现读 ⇒ R561 那格未渲染占位符的事没重演。③ 全程没有放宽任何门、没有加豁免、没有改期望；"
        u"电池从 4 红（三朵时序红 + 一朵 634 形状的借红报告）→ 2 红（一朵真红 + 借红报告）→ **0 红**，两朵真红都是我自己写账写出来的，修的是账与写手，不是门。"),
}



def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = (u"与声明时长一字未改。\n"
              u"## R562 ⓪ 开工")
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    if u"### R562 补记" in t:
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
        new = anchor.split(u"\n")[0] + u"\n" + body.strip(u"\n") + u"\n\n" + u"## R562 ⓪ 开工"
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R562_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
