# -*- coding: utf-8 -*-
"""R564 补记（STATE 里插 `### R564 补记`，带 R565 的 ⓪ 读单）。

用法：`python3 addendum_r564.py --check` 只验锚点；不带参数才真写。
幂等守卫 + 两种占位符形状都查（与 ledgers_r564 同一套规矩）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "PAIRS": '⓪ 笔 `8fd5b1f`（开工节 + 基线全现读 + 取靶方法换掉的预告）、A 笔 `65e3371`（守卫 + 三把刀 + 产品位回退的读数笔记；**该笔回退了 Sources，本轮产品 0 文件**）、台账笔 `235f243`（七本 + 派生格落盘后现读 + 新开 637）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间三笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。sources 格本轮**没有变化**（产品 0 文件 ⇒ `SOURCES_CELL 账上=R560/631f910 git=R560/631f910 一致=是`）。⚠ 本轮四笔的 subject 前缀与标题里的轮次身份行由**本轮自己落的那条守卫**判过：`COMMIT_ROUND_IDENTITY 笔=3 无R前缀=0 身份缺失=0 不一致=0`（写补记时那三笔），本补记笔自己那一笔由下一跑/下一轮判 —— **修尺那一笔签不了自己**。',
    "CI_CLOSE": '`41542718166 ↔ 6ef9ff1` 开场 in_progress（380s）⇒ 四格具名 NOT-RUN；**收口前到数并逐格转成读数**（`gh run view --json jobs` 逐步现读：20 步里只有 STEP[15] failure，其余 success）：(a) `BULLET_LEVELS` 首验=判到（`行=6 列=3 步进=[16, 16]px(16.0/16.0pt) 倍率=1.0x`、`NOT_RUN` 零行）；(b) `HEAT_LEGEND_COVERAGE` 连续第二跑判到、`NOT_RUN` 零行；(c) `过渡帧数` 第五数=**6**（每格 32.0ms ⇒ 五数 2/5/0/5/6）；(d) STEP[9] `名单外=无 名册未跳=无`（第五跑绿）、STEP[18] 绿 ⇒ 622 无新值。**唯一那朵红** = STEP[15] `SelectionRevealAnimationTests.testAnimatedRevealProducesIntermediateOffsets`（`中段=0.0`）⇒ 同码在 `41519677393↔f12f50d` 是绿、中间 `41531750912↔75b32d6` cancelled 无日志 ⇒ **判间歇、不署名本轮**（这条用例在 runner 上第二次红，R412 那次形状是 中段=1430）；本机侧有具名出口 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449），**runner 侧没有** ⇒ 449 的 runner 半边仍是缺口，不改门槛。',
    "READS": 'build 告警 **0**；判据卷 `UICaptureTests` **221/4 skipped/0 失败（603.0s）**；帧 **356 CHANGED=0 MISSING=0 ADDED=0**（产品 0 文件、判据草稿整条回退 ⇒ 基线本来就该不动）；全量 **1405/57/0（687.5s）**；预检三读**串行** `tables=364 covered=295 arms=757 bad=0`、`ARM_TOTAL files=457 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=451 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（本轮名册 +3 张表 ⇒ 三个数各 +3，`bad=0/dupes=0` 是"新刀没重复没漏登记"的证人）；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→95084，备份 `before-R564`）；清账 **162/63/0**；streak **台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `PRODUCT_STREAK ledger_round=563 streak=4 sections=539 as_of=last=631f910 last_round=559 newest=631f910 newest_round=559` ⇒ 复核 `PRODUCT_STREAK_LEDGER_OK streak=4`（**这一格又被门点过一次**：写台账时按上一轮的数推成 3，`PRODUCT_STREAK_LEDGER_STALE` 红 ⇒ 改成派生值 4；派生格只能落盘后现读，猜的和抄的都不算）；sources 格 `账上=R560/631f910 git=同 ⇒ 一致=是`；**占位符回读（percent 后接字母 那一形状）逐节现读 = 0**（七本各自定位本轮那一节后计数）；电池 **`Ran 706 / OK (skipped=5)`、退出码 0**（台账 + `--write` 之后一遍过；本轮新增 10 条 = 守卫模块，705→706）。',
    "SKIPPED": '**57 连七跑**（R558–R564 都是 57 ⇒ 只记现读，不动门、不修回 55）。',
    "FRAME_WITNESS": '帧 356 CHANGED=0 MISSING=0 ADDED=0',
    "STREAK": '4',
}

BODY = u"""### R564 补记（2026-11-03 · 第 563 轮 / Round 561 · 成对号 + R565 读单）

① **本轮成对号（一次性 push 的自证）**：%(PAIRS)s
② **⓪ 那一跑到数没有**：%(CI_CLOSE)s
③ **R565 的 ⓪ 必读**（逐条抄全部失败步骤；success 的步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时尚不存在 ⇒ 现在去读。四格各问什么：
  (a) **`BULLET_LEVELS` 第一次被 runner 验**（R562 落的判据，`6ef9ff1` 那一跑 in_progress 没读到）—— 预期 `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(8.0/8.0pt) 容差=1px 合并=1px`。**三条出路预先写死，不许临场决定**：判到 ⇒ 报 px 与 pt；打 `BULLET_LEVELS_NOT_RUN=detail-frame-plain` ⇒ 详情帧在 1x 没落墨（R483 家族）⇒ 具名入账并补内容墨证人，**不许读成「判过了」**；红在步进等距 ⇒ 先分辨是 1x 像素预算不够（合并容差在 1x 只剩 1px）还是产品真漂（对照 M1461 那条 `[32,38]px`=16/19pt 的红形状）⇒ 前者按 `scale` 派生容差、后者才是产品缺陷；**三种情况都不许降墨下界、不许改期望、不许加豁免**。⚠ 本机那次 LANCZOS 降采样只是**代理**，它不签这一格。
  (b) `HEAT_LEGEND_*` **复核**是否仍判到（`HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`）—— 首次签收已在 `41519677393↔f12f50d`，这一格只问"还在不在"；回到 `solid-unresolved` 就是尺被改坏，按读数修、不许降地板。
  (c) `过渡帧数=` **第五数**（已 2/5/0/5，每格 71.5/26.0/75.6/28.9ms）：读到几都按 629 既有口径具名入账，**不许重开产品排查、不许动 ≥2、不许改期望**；再 ≤1 就把两条出路的代价摆给用户 ⇒ **工作侧不许自行登记 `sampled`**。
  (d) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`（已连四跑绿）；STEP[18] 622 有无新值（第十四值仍 219.7ms/2 颗；120ms 锚点、容差 1 颗、`over_runs` 口径不动）。
- 仍挂着、永不重开：`41531750912↔75b32d6`（cancelled、`log not found: 125573433836`）、`41452722560↔58851c2`、`41455782587↔598b253`。
- **本轮新加的那条守卫在 runner 上没有读数**（`scripts/commit_round_identity.py` 只在电池里跑，CI 不跑 python 电池 ⇒ 具名「判据未接进 CI」，不许写成"runner 也签了"）。要不要把它接进 CI 那一跑，是**接门**的动作，要用户点头。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到 ⇒ 一个字结论也没写；629 写「(B) 已落地 + 635 已结案 + runner 四跑实测 2/5/0/5 ⇒ ≥2 在那台机器的钟上是间歇可满足」，**两条消红出路的代价仍摆给用户，本轮没有自行选**；**636 继续开单**（本轮一字未动它的措辞：只证「有对象可量 + 正文列步进不漂」，三级项目符的尺寸没有被判过）；**新开 637**（浮层三枚叠层徽标布局后的边长由谁决定：常量 9/10/9 ⇒ 布局后 9.5×14.5 / 10.0×14.5 / 9.0×13.5，高一律 = 常量+4.5pt、图钉宽 = 常量+0.5pt ⇒ 布局不由那三个常量决定；两条子问题与判据草稿路径都在单里）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 11 面不变**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、R560 任务勾选框标记字体）—— **本轮产品 0 文件 ⇒ 不抬禁碰数**（%(FRAME_WITNESS)s 就是这句话的证人；星那枚的墨读数在实验前后逐字相同是 R551/R555 两面的证人）；刀号 **M1466 起**（现读最高 M1465，本轮三把全 CAUGHT）；4.5 地板、150 上限、120ms 阈值、**Motion ≥2 帧地板**、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped %(SKIPPED)s
⑤ **本轮现读（收口时）**：%(READS)s
⑥ **本轮自伤（照实写）**：① 守卫第一版把 `Round = 前缀 - 2` 凭感觉写死 ⇒ 它第一个咬到自己本轮的 ⓪ 笔（`不一致:R564≠Round561`），现读近 12 笔才定出 `-1 / -3` —— **从账里派生的换算式必须先跑历史正对照再当判据用**。② M1463 首版 needle 写成 12 空格缩进 ⇒ `needle 命中 0`（刀根本没落下去），"登记前先跑一遍看命中 1"这条老规矩本轮又救了一次。③ 看图自伤：把 `detail-file-fallback-longname` 的文件名读成"被左右裁掉"，其实是我自己 170..1032px 的切框切掉了首尾 ⇒ 整帧现读文字末列 516.5pt、动作条首列 552pt，中间还空 35.5pt；**看图之前先确认看到的是整帧还是我切的框**。④ 判据草稿第一版把"负臂树里读不到那枚盒子"当成"徽标按需出现"的证据，实测负臂三枚都在树里、只是 `isHidden=true` ⇒ 那是尺坏不是产品坏，草稿撤下。⑤ **产品位这一格本轮没落地**：候选（浮层三枚徽标两档盒子）先被墨实验支持（会变）、再被布局树证否（统一常量得不到统一边长）⇒ 改动满足不了任何一条写得出的判据 ⇒ 回退，streak 到 %(STREAK)s；账里写成"逐位排除 + 具名 + 开 637"，**没有拿判据位与三把刀抵产品位**，也没有为了凑数去碰禁碰面或放宽任何门。

"""


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, t):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(t)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    bad = re.search(u"%(?=[a-zA-Z])", out)
    if bad:
        i = bad.start()
        sys.stderr.write("BARE_PERCENT_LEFT %s\n" % out[max(0, i - 30):i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv
    for key, value in NUM.items():
        if value.startswith(u"@@") and value.endswith(u"@@"):
            sys.stderr.write("NUM_NOT_FILLED %s\n" % key)
            return 1
    n = "AGENT_STATE.md"
    t = rd(n)
    if u"### R564 补记" in t:
        sys.stderr.write("ALREADY_WRITTEN addendum ⇒ 不许重跑\n")
        return 1
    a = u"## R564 状态（"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD state 状态节不在 ⇒ 先写台账再写补记\n")
        return 1
    # 补记插在**本轮状态节之后、本轮 ⓪ 开工节之前**（与 R560–R563 同一形状）
    j = t.index(u"## R564 ⓪ 开工")
    if not check:
        wr(n, t[:j] + fill(BODY).rstrip(u"\n") + u"\n" + t[j:])
    sys.stdout.write("ADDENDUM_R564_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())
