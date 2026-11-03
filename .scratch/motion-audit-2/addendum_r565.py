# -*- coding: utf-8 -*-
"""R565 补记（STATE 里插 `### R565 补记`，带 R566 的 ⓪ 读单）。

用法：`python3 addendum_r565.py --check` 只验锚点；不带参数才真写。
幂等守卫 + 两种占位符形状都查（与 ledgers_r565 同一套规矩）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "PAIRS": '⓪ 笔 `a7e1790`（开工节 + 读单改账 + 两个扫描的落空名单）、A 笔 `f6c2a1d`（产品 1 文件 + 判据 1 条 + 刀 M1466/M1467 + 帧 26 张同一笔 update）、B 笔 `020cef3`（修 R564 守卫写死的机器根 + 路径卫生守卫 + 刀 M1468/M1469）、台账笔 `20c55cf`（七本 + 派生格落盘后现读）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间四笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。sources 格本轮**有变化**（产品 1 文件）：`report_sources_cell.py --write` 之前现读 `账上=R560/631f910 git=R565/f6c2a1d 一致=否` ⇒ 写完复核 `一致=是`，**在同一笔台账里落**（R558/R561 那一族时序红本轮没犯）。',
    "CI_CLOSE": '两跑都到数且**同一形状**：`41552571306↔4cfcfc6`、`41552998637↔8eecbc7` = concluded failure，逐步现读 `gh run view --json jobs` ⇒ STEP[9] `Release script tests` failure、STEP[10]-[14] skipped、STEP[15]-[19] success。**红因不是任何一条视觉判据**，是 R564 那把 commit 守卫把自己的仓库根写成机器绝对路径，runner 上目录不存在 ⇒ `subprocess.run(cwd=ROOT)` 抛异常（CI 日志 `/tmp/r565-ci-8eecbc7.log` 第 8451-8470 行）。⇒ 回答 ⓪(f)：**分批不是原因，写死的根才是**；代价是两跑的 STEP[11] 帧基线名册门整段没跑。到数的格子：`BULLET_LEVELS` 第二跑仍判到（与首验逐字同）、`HEAT_LEGEND_COVERAGE` 连续第三跑判到且 `NOT_RUN` 零行、`过渡帧数` 第六数 = 6（六数 2/5/0/5/6/6，每格 …/32.0/27.0ms）、STEP[15] 这两跑 success ⇒ SelectionReveal 那朵间歇红未复现（累计 `6ef9ff1` 红 / 这两跑绿）；`SKIP_ROSTER` 零行按 634 记「内层红 ⇒ 无可对账对象」，既不记绿也不记红。',
    "READS": 'build 告警 **0**；判据卷 `UICaptureTests` **222/4 skipped/0 失败（572.2s）**（221→222 = 本轮新判据）；帧 **356 张：update 之前 `COMPARED=356 CHANGED=26 MISSING=0 ADDED=0`，26 张逐字名单 = 13 个 `quickpick-*` 夹具 × 明暗两档（`/tmp/r565-chain-compare.log`）⇒ 非浮层帧一帧未变**，同一笔 `frame_baseline.py update` 之后复跑 `CHANGED=0 MISSING=0 ADDED=0`；全量 **1406/57/0（619.4s）**；预检三读**串行** `tables=368 covered=295 arms=757 bad=0`、`ARM_TOTAL files=461 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=455 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（本轮名册 +4 张表 ⇒ 三个数各 +4，`bad=0/dupes=0` 是新刀没重复没漏登记的证人）；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→33353，备份 `before-R565`）；清账 **162/63/0**；streak **台账落盘之后**现读 ⇒ `PRODUCT_STREAK_LEDGER_OK streak=5`（⚠ 这是**未推状态**下门自己派生的数：门只认已推的产品笔，本轮产品笔 `f6c2a1d` 还在本地 ⇒ 5；push 之后同一命令会派生成 0，由下一轮现读覆盖 —— 第一次写 0 被 `PRODUCT_STREAK_LEDGER_STALE` 点过，这是同一格第五次被点）；sources 格 `--write` 之前 `账上=R560/631f910 git=R565/f6c2a1d 一致=否` ⇒ 写完复核一致；**占位符回读（percent 后接字母 那一形状）逐节现读 = 0**；电池 **`Ran 709 / OK (skipped=5)`、退出码 0**（台账 + `--write` 之后一遍过；本轮 +3 条 = 新守卫三条腿）。',
    "SKIPPED": '**57 连八跑**（R558–R565 都是 57 ⇒ 只记现读，不动门、不修回 55）。',
    "FRAME_WITNESS": '帧 26 张变更全部落在 `quickpick-*`、其余 330 张逐字节不变',
    "STREAK": '5（未推状态下门自己派生；push 后同一命令 = 0）',
}

BODY = u"""### R565 补记（2026-11-03 · 第 564 轮 / Round 562 · 成对号 + R566 读单）

① **本轮成对号（一次性 push 的自证）**：%(PAIRS)s
② **⓪ 那两跑到数没有**：%(CI_CLOSE)s
③ **R566 的 ⓪ 必读**（逐条抄全部失败步骤；success 的步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`，**不许从"不在失败名单"推**）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时尚不存在 ⇒ 现在去读。七格各问什么（⚠ 这一张表按 R565 开场那条规矩写：**先跟同一轮 ② 已落盘的读数交叉核对，再抄上一轮的表**）：
  (a) **`HINT_CONTRAST` 第一次被 runner 验**（本轮新判据 `testQuickPickKeyboardHintClearsTheContrastFloor`）—— 本机 2× 现读 light `底=255 字芯=(64,64,64) 对比=10.37:1`、dark `底=30 字芯=(209,209,209) 对比=10.92:1`（地板 4.5）。**三条出路预先写死**：判到 ⇒ 报两档比值；带内一个偏差像素都没有 ⇒ 判据自己会红（"没有对象"），那时先查捕获通道，**不许改成 skip**；比值掉到 4.5 以下 ⇒ 先分辨是 runner 的合成/抗锯齿把字芯冲淡（对照本机同一判据的 `字芯像素=` 与 `偏差像素=` 两个数）还是产品真的又变淡了，**不许降 4.5 地板、不许改期望、不许加豁免**。⚠ 比值与倍率无关（不像像素数那样要按 scale 派生），所以这一格**不该出现 `scale-too-low` 那类出口**；真出现了就是尺坏。
  (b) `BULLET_LEVELS` **第三跑**（首验 `41542718166↔6ef9ff1` 判到 `行=6 列=3 步进=[16,16]px(16.0/16.0pt) 倍率=1.0x`）⇒ 这一格只问"还在不在"，不许记成第二次首次。
  (c) `HEAT_LEGEND_*` **复核**是否仍判到（`HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`、`NOT_RUN` 应零行）—— 首次签收在 `41519677393↔f12f50d`，已连续两跑判到。
  (d) `过渡帧数=` **第六数**（已 2/5/0/5/6，每格 71.5/26.0/75.6/28.9/32.0ms）：读到几都按 629 既有口径具名入账，**不许重开产品排查、不许动 ≥2、不许改期望**；再 ≤1 就把两条出路的代价摆给用户 ⇒ **工作侧不许自行登记 `sampled`**。
  (e) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`（已连**五**跑绿 ⇒ 本轮数第六跑）；STEP[18] 622 有无新值（第十四值仍 219.7ms/2 颗；120ms 锚点、容差 1 颗、`over_runs` 口径不动）。
  (f) **STEP[15] `SelectionRevealAnimationTests.testAnimatedRevealProducesIntermediateOffsets` 这一族是第几跑红、形状是 `中段=0.0` 还是 R412 的 `1430`** —— 判间歇、不署名本轮；本机侧有具名出口 449 而 **runner 侧没有** ⇒ 449 的 runner 半边仍是缺口，不许为了消红改门或加豁免。
  (g) **分批 push 有没有造出"注定红的派生格"**：本轮若一次推完就没有这一格；若分了批，就要逐跑回答"那一跑的 STEP[9]/sources 是不是因为派生格排在台账之后而红"。红了就写自伤并回到一次性 push，**不许拿"修尺那一笔签不了自己"当默认通行证**。
- 仍挂着、永不重开：`41531750912↔75b32d6`（cancelled、`log not found: 125573433836`）、`41452722560↔58851c2`、`41455782587↔598b253`。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到 ⇒ 一个字结论也没写；629 写「(B) 已落地 + 635 已结案 + runner 五跑实测 2/5/0/5/6 ⇒ ≥2 在那台机器的钟上是间歇可满足」，**两条消红出路的代价仍摆给用户，本轮没有自行选**；**636 继续开单**（只证「有对象可量 + 正文列步进不漂」，三级项目符的尺寸没有被判过）；**637 继续开单**（本轮没碰浮层徽标；R565 的裸字号扫描又数了一遍那 4 处 `pointSize: 8`，仍是 637 的地盘）；**新开 638**（基线里 6 张帧互为逐字节副本：`row-favorite-off`=`row-pinned-off`=`row-text`、`content-paused-idle`=`content-with-history`、`quickpick-search-focus`=`quickpick-search-hover`、`detail-3-files`=`detail-3-files-row0` ⇒ 逐组都有名有姓地排除成"设计如此"，但副本帧不为任何断言单独作证，要判的是"并帧"还是"显式登记故意同图 + 一把新增必须红的刀"）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；R564 那条守卫**仍没接进 CI**（只在电池里跑）⇒ 具名「判据未接进 CI」，接不接归用户；**禁碰清单 12 面**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」的键名与字高、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、R560 任务勾选框标记字体、**R565 浮层键盘提示的颜色**（本轮把它从 tertiary 抬到 secondary ⇒ 禁的是改回去；R550 那一面仍是键名与字高））—— %(FRAME_WITNESS)s 与 `HINT_KEY_CAPS 高=7.85pt 宽=5.22pt 字号=11.0pt` 逐字不变是这句话的证人；刀号 **M1468 起且未使用**（现读最高 M1467；M1468 试落即撤 ⇒ 不占号）；4.5 墨地板、150 上限、120ms 阈值、**Motion ≥2 帧地板**、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped %(SKIPPED)s
⑤ **本轮现读（收口时）**：%(READS)s
⑥ **本轮自伤（照实写）**：① **同一族抄表错误第二次犯** —— `### R564 补记` ③ 的读单抄自 R563、没跟同一轮 ② 已落盘的读数交叉核对 ⇒ 三格过期（首验/第五数/四跑）+ 缺两格（STEP[15] 间歇红、分批派生格），本轮开场先做一格改账（改措辞与格子，不动任何门）。D-565 ④ 已写明：**这件事该升成一条会红的跨节对账检查**，还欠着。② 新判据第一版把**整帧众数**当提示底色 ⇒ light 带内 99.8% 像素都算"偏差"、字芯被抗锯齿边稀释成 (163,163,163)、对比报 2.46:1（与 numpy 独立通道的 3.36:1 对不上）⇒ 那朵红是尺坏；改成带内众数后两通道逐字一致。③ 更早一版把 gamma 编码的 `bgLuma/255` 去比线性光 `relLuma` ⇒ 暗档把**背景自己**排成字芯（报 1.02:1）。④ **M1468 是空刀**：把"字芯"从偏差前 5% 改成全部偏差像素，读数 6.01/9.16:1 仍过 4.5 地板 ⇒ 判据 PASSED ⇒ 撤掉、不登记、不占号（与 R560 的 M1455、R562 的两把同族）。⑤ 取靶三个扫描里前两个空手（逐字节撞号 8 组、裸字号 6 处）—— 都逐位留了排除证据，没有拿"看着像设计"交差；产品位由第三个扫描命中。

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
    if u"### R565 补记" in t:
        sys.stderr.write("ALREADY_WRITTEN addendum ⇒ 不许重跑\n")
        return 1
    if t.count(u"## R565 状态（") != 1:
        sys.stderr.write("ANCHOR_BAD state 状态节不在 ⇒ 先写台账再写补记\n")
        return 1
    j = t.index(u"## R565 ⓪ 开工")
    if not check:
        wr(n, t[:j] + fill(BODY).rstrip(u"\n") + u"\n" + t[j:])
    sys.stdout.write("ADDENDUM_R565_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())
