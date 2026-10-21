#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R289 补记：把 R282–R288 七轮补进 AGENT_VISUAL_ITERATION.md（Round 279…285）。

为什么必须补而不是申报：曲线那把尺**不认申报通道** —— `test_curve_gaps` 现读
`GAPS=[279, 280, 281, 282, 283, 284, 285]`，少一轮就把均值算高（R197 那轮就是这么发现的，
处置是 R198 的 `patch_r197_backfill.py`，同一个形状）。申报通道（SINGLE_LEDGER_ROUNDS）管的是
"三本账齐不齐"，管不到曲线。

分数怎么来的（这是**补记**，不是当时打的，每一格都写来源）：
· 产品面推进 = 0 —— 七笔提交 `git show --numstat -- ClipboardHistory/Sources` 现读全为 0 文件；
· 真实视觉审查 —— 提交正文里写着"眼睛腿 RUN"的才给分（R282 那一张 hover 帧），写着 NOT-RUN
  或没提的一律 0（R83：形容词不是读数，缺席也不许给分）；
· 其余五维 —— 按当轮提交正文与 BACKLOG 追记里可读的事实给：入库了几格判据、几把刀、
  有没有当场抓到自己的错、台账是否补齐。校准锚点是 R281（同一族的零产品轮，当时自评 64）。
"""
import io
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
CURVE = os.path.join(HERE, "curve_from_ledger.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进",
        u"台账一致性", u"交付诚实性", u"可复核性"]


def die(m):
    sys.stderr.write("BACKFILL_R289 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def curve_mean(allow_gaps=False):
    """补记**之前**这一读必然带断档（仪器按设计 rc!=0），所以 rc 只在补完之后才是判据。

    为什么不能一律看 rc：那会把"要修的东西"读成"仪器坏了"，脚本自己就动不起来；
    为什么补完之后必须看 rc：断档没清干净时，追记里那句 GAPS=none 就是假话。
    """
    out, rc = sh([sys.executable, CURVE])
    if rc != 0 and not allow_gaps:
        die("曲线仪器跑不动（rc=" + str(rc) + "）：\n" + out[-400:])
    m = re.search(r"^MEAN=([0-9.]+)\s+MIN=(\d+)", out, re.M)
    g = re.search(r"^GAPS=(\S+)", out, re.M)
    n = re.search(r"^ROUNDS=(\d+)", out, re.M)
    if not (m and g and n):
        die("曲线仪器没打 MEAN/GAPS/ROUNDS ⇒ 补记前后对不了账：" + out[-300:])
    return m.group(1), m.group(2), g.group(1), n.group(1)


BEFORE_MEAN, BEFORE_MIN, BEFORE_GAPS, BEFORE_N = curve_mean(allow_gaps=True)

# (Round 号, R 号, 第 N 轮, 标题尾巴, 七维分数, 各维理由, 三条腿)
SECTIONS = [
    (279, 282, 281,
     u"330 第三版：前提接线修对了，读数仍是 0 ⇒ 卡点被夹在自建宿主的更新路径这一侧",
     [3, 6, 11, 0, 8, 13, 9],
     u"真实视觉审查 3 —— 提交正文写着「眼睛腿 RUN（范围就那张 hover 帧）」，看的是既有那一张，没扫新位点；"
     u"判据有效性 6 —— 三臂形状（被摄对象 + blank 相对参照）是可判决的，但 spike 全回退、没入库；"
     u"假绿防御 11 —— 没有把「读数 0」读成「产品没有过程」，而是交回一个方向：卡点在自建宿主这一侧；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 8 —— 只落 BACKLOG 330 追记四并走 SINGLE_LEDGER 申报；"
     u"交付诚实性 13 —— 明写「读数仍是 0」，没替自己圆；可复核性 9 —— makeStore 正文与键类型写在追记里，代码不在盘上。",
     u"本轮落地：330 第三版 spike（被摄对象换成 ContentView(historyStore: makeStore())，点亮走 hoveredRowForCapture，"
     u"第三条 blank 臂做相对参照）。现读：前提差 0.0000 ⇒ 判定为「卡点仍在自建宿主这一侧」，spike 回退、判据与产品净变化 0。"),
    (280, 283, 282,
     u"330 的正对照排除了解释 a；第四/五版走 record(Scenario) + ObservableObject，第一次拿到可判决的读数",
     [0, 9, 13, 0, 8, 14, 10],
     u"真实视觉审查 0 —— 提交正文写着「眼睛腿 NOT-RUN」，按缺席给分等于替它圆；"
     u"判据有效性 9 —— 对照臂（同一驱动、只把悬停换成选中态）读出 帧=30 触发帧=4 峰值=0.011 动帧=1，"
     u"这是那条通道第一次给出「值变化进得了胶片、悬停淡入进不了」的形状；"
     u"假绿防御 13 —— 解释 a（通道看不见值动画）被自己的对照否证，第四版还先撞了一次「对象选错」（makeStore 没有多文件记录）；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 8 —— 追记五 + 申报；交付诚实性 14 —— 「这一位是一帧跳变」是读数推出来的，"
     u"且当场标了范围；可复核性 10 —— HOVER_FADE5 那一行的字段都在正文里。",
     u"本轮落地：330 第四/五版 + 正对照实验（selection 值变化那一臂）。现读：对照=selection 帧=30 峰值=0.011 动帧=1；"
     u"hover 臂 26 帧逐帧全等 ⇒ 悬停那一档在胶片里是一帧跳变。判据与产品净变化 0，未跑四件套。"),
    (281, 284, 283,
     u"330 收口成一条通道限制；新开 336（地板由被统计量自己推出时，0 地板会造出看着像结论的假数）",
     [0, 12, 13, 0, 11, 14, 12],
     u"真实视觉审查 0 —— 提交正文没提看图，按缺席记 0；"
     u"判据有效性 12 —— 零地板守卫第一次进电池（5 格），且它抓的是「0 颗却印得出像结论的数」这一族；"
     u"假绿防御 13 —— 第一版误点名三处合法写法 ⇒ 把判定单位从行改成整颗函数，改完再重跑（不是把三处塞进豁免）；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 11 —— 330 的收口 + 336 的开单都落在 BACKLOG；"
     u"交付诚实性 14 —— 330 不再被写成「产品没有淡入」，而是收成一条具名的通道限制；"
     u"可复核性 12 —— MotionCatalog.animation 第一行那个 guard 被逐字引用。",
     u"本轮落地：读源码发现 MotionCatalog.animation(for:) 的 guard animationsEnabled 是胶片探针自己的 A/B 开关 ⇒ 冒出第四种解释；"
     u"新增 scripts/tests/test_zero_floor_guard.py（5 格）+ 新开 336。判据与产品净变化 0。"),
    (282, 285, 284,
     u"336 的两把刀补齐：M838 尺轴（绝对下限识别弄瞎）／M839 对象轴",
     [0, 11, 12, 0, 10, 13, 12],
     u"真实视觉审查 0 —— 提交正文没提看图；判据有效性 11 —— 刀本身不是判据，但它让那条守卫的两侧都有证人；"
     u"假绿防御 12 —— 两把各钉一条轴（D-244），且登记进预检名册（D-248：登记与覆盖是两件事）；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 10 —— 只落 .scratch 表 + 预检；"
     u"交付诚实性 13 —— 理由里写的是仓库里那三处合法写法被点名的形状；可复核性 12 —— 表在盘上、可重跑。",
     u"本轮落地：mutate_r285.py（M838/M839）+ 预检登记。判据与产品净变化 0。"),
    (283, 286, 285,
     u"336 结案：零地板守卫扩到 Sources/，并补一格端到端对照防「把门扩成恒真」",
     [0, 13, 14, 0, 12, 15, 13],
     u"真实视觉审查 0 —— 提交正文没提看图；"
     u"判据有效性 13 —— 扫描范围从 scripts/Tests 扩到 ClipboardHistory/Sources/，现读 ZERO_FLOOR_SCAN files=175 → 283、offenders=0；"
     u"假绿防御 14 —— 新增那一格是端到端对照（造一棵树，坏的那支必须被点名），专门拦「扩范围把门扩成恒真」；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 12 —— 结案 + 补齐上一笔漏掉的追记；"
     u"交付诚实性 15 —— 公开自曝：上一笔提交信息写着「一单追记」而它当时因 heredoc 里 CJK 串夹 ASCII 双引号没写进去，"
     u"且 git 没接住 python 的退出码；可复核性 13 —— 卷从 5 格长到 6 格、电池 Ran 537 都写在正文。",
     u"本轮落地：test_zero_floor_guard.py 扩到 Sources/（6 格）+ 336 结案 + 一次流程自曝。脚本电池 Ran 537 OK (skipped=4)。"),
    (284, 287, 286,
     u"331 本机半落地：观测式名册进电池，恒等式闸门当场抓到两次我自己的归属错",
     [0, 13, 15, 0, 11, 15, 12],
     u"真实视觉审查 0 —— 提交正文没提看图；"
     u"判据有效性 13 —— 新卷 test_skip_roster.py 把「谁在这台机器上缺席」变成按机器键的双向对账；"
     u"假绿防御 15 —— 恒等式闸门（解析到的格数必须等于内层汇总的 skipped 数）当场抓到两次归属错："
     u"单行形状被漏掉、观察者被算成「名单外」；两次都不是靠放宽闸门收场，而是改归属并把排除动作本身写成会红的断言；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 11 —— 新卷 + 331 追记（追记第一版没落盘，见下一轮的自曝）；"
     u"交付诚实性 15 —— 「抓到的是我自己」写在正文里；可复核性 12 —— 子进程 + -v 的形状可重跑。",
     u"本轮落地：scripts/tests/test_skip_roster.py（观测式名册 + 恒等式闸门 + 双向对账）。判据与产品净变化 0（Swift 侧未动）。"),
    (285, 288, 287,
     u"331 的两把刀补齐：归属轴与排除轴各红在不同判据字样上",
     [0, 12, 13, 0, 10, 13, 12],
     u"真实视觉审查 0 —— 提交正文没提看图；判据有效性 12 —— 名册那条守卫从此两侧都有证人；"
     u"假绿防御 13 —— M840 把「同一行的结果」配对退回第一版的错法 ⇒ 恒等式闸门必须红且红话里要有「归属漏了」；"
     u"M841 把「排除观察者」那一行拆掉 ⇒ 必须红在「名单外出现 skip」。两把刀按**失败正文**判，不按格子名判（D-244）；"
     u"产品面推进 0 —— git 现读 0 文件；台账一致性 10 —— 只落 .scratch 表 + 预检；"
     u"交付诚实性 13 —— 上一笔（R287）漏掉的追记在这一笔补齐并自曝；"
     u"可复核性 12 —— 表在盘上、预检认它。",
     u"本轮落地：mutate_r288.py（M840/M841）+ 预检登记。判据与产品净变化 0。"),
]

TAIL_ANCHOR = u"## Round 286 · "
HEAD278 = u"## Round 278 · "


def render_section(round_no, r_no, nth, tail, scores, reasons, landed):
    total = sum(scores)
    rows = u"\n".join(u"| %s | %d/15 |" % (DIMS[i], scores[i]) for i in range(7))
    return (u"## Round %d · %s（R%d / 第 %d 轮）/ 【R289 补记】\n\n"
            u"这一节是 R289 补记的：当轮只落了 BACKLOG 与 .scratch，没写三本账，而曲线那把尺不认申报通道"
            u"（`test_curve_gaps` 现读 GAPS 里就有这一轮）。分数不是当时打的，是按当轮提交正文与追记里可读的事实重算，"
            u"校准锚点是同一族的 R281（自评 64）—— 看图与产品两格按缺席记 0，不给同情分。\n\n"
            u"%s\n\n"
            u"看图腿：见下面各维第一格的来源；读数腿：见「本轮落地」那一行。\n"
            u"七维度自评：\n"
            u"| 维度 | 分/满分 |\n%s\n"
            u"各维理由：%s。合计 **%d**/105。\n\n") % (
        round_no, tail, r_no, nth, landed, rows, reasons, total)


it_old = rd(ITER)
if re.search(u"^## Round 279 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 279 ⇒ 补记不幂等，先还原")
if it_old.count(TAIL_ANCHOR) != 1 or it_old.count(HEAD278) != 1:
    die(u"锚点不唯一：Round 278 命中 %d、Round 286 命中 %d" % (it_old.count(HEAD278), it_old.count(TAIL_ANCHOR)))
body = u"".join(render_section(*s) for s in SECTIONS)
it_new = it_old.replace(TAIL_ANCHOR, body + TAIL_ANCHOR, 1)


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行：" + u" | ".join(lost[:2])[:160])


must_preserve(it_old, it_new, "AGENT_VISUAL_ITERATION.md")
def inversions(text):
    ns = [int(m) for m in re.findall(u"^## Round (\\d+) · ", text, re.M)]
    return [(ns[i], ns[i + 1]) for i in range(len(ns) - 1) if ns[i] > ns[i + 1]]


heads = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
# 曲线仪器只问两件事：**尾轮是不是最大号**（CURVE_DROPS_TAIL），以及有没有断档。
# 它不要求全文件严格升序 —— 盘上现读第 2 与第 3 节本来就是倒的（历史形状），
# 所以这里比的是「倒挂的集合不许变大」，而不是「一个都不许有」：把既有事实当缺陷修，是另一种假绿。
if inversions(it_new) != inversions(it_old):
    die(u"补记改变了轮次倒挂：前 " + str(inversions(it_old)) + u" 后 " + str(inversions(it_new)))
if int(heads[-1]) != max(int(h) for h in heads):
    die(u"尾轮不是最大号（尾=" + heads[-1] + u" max=" + str(max(int(h) for h in heads)) + u"）⇒ CURVE_DROPS_TAIL")
new_part = heads[heads.index(u"279"):heads.index(u"286")]
if [int(x) for x in new_part] != list(range(279, 286)):
    die(u"补进去的七节不是 279…285 连续升序：" + str(new_part))
for s in SECTIONS:
    sec = it_new.split(u"## Round %d · " % s[0], 1)[1].split(u"## Round ", 1)[0]
    rows = re.findall(u"^\\| .+ \\| (\\d+)/15 \\|$", sec, re.M)
    if len(rows) != 7:
        die(u"Round %d 的七维表读到 %d 行 ⇒ 曲线会打 DERIVED_BAD" % (s[0], len(rows)))
    if sum(int(x) for x in rows) != sum(s[4]):
        die(u"Round %d 的表与合计对不上" % s[0])
    if re.search(u"自评 \\d+ ?/ ?100", sec):
        die(u"Round %d 里出现了显式自评行 ⇒ 会与推导值打架（两种来源不许混在一轮）" % s[0])

with io.open(ITER, "w", encoding="utf-8") as h:
    h.write(it_new)

AFTER_MEAN, AFTER_MIN, AFTER_GAPS, AFTER_N = curve_mean()
if AFTER_GAPS != u"none":
    die(u"补完之后曲线仍有断档：" + AFTER_GAPS)

# 把曲线的移动写进 338 的追记（它正是这一笔的对象）：数字来自仪器，不手抄（R88）。
NOTE = (u"  追记（R289）：补记已落 —— Round 279…285 七节进 AGENT_VISUAL_ITERATION.md（分数按当轮提交正文与追记重算，"
        u"标题带【R289 补记】）。曲线仪器现读：补记前 " + BEFORE_MEAN + u"（ROUNDS=" + BEFORE_N +
        u"，GAPS=" + BEFORE_GAPS + u"）→ 补记后 " + AFTER_MEAN + u"（ROUNDS=" + AFTER_N +
        u"，GAPS=" + AFTER_GAPS + u"，MIN=" + AFTER_MIN + u"）。**均值下降不是这一轮变差，是原来那条曲线少算了七轮**："
        u"那七轮里 产品面推进 与 真实视觉审查 两格按 git 与提交正文现读全为 0。"
        u"三本账的申报通道另管：R284–R288 在 AGENT_UI_AUDIT 与 CHANGELOG 里仍没有标题行，"
        u"已按 R188 的规矩写进 test_round_batch_consistency.SINGLE_LEDGER_ROUNDS（申报而不是补桩）。"
        u"本单剩下的：要么把这两本账的正文补齐，要么保持申报 —— 但申报现在是有牙的（窗口三轮内会红）。")

bk_old = rd(BACKLOG)
if u"追记（R289）：补记已落" in bk_old:
    die(u"338 的追记已经在盘上 ⇒ 不幂等")
bk_new = bk_old.rstrip(u"\n") + u"\n" + NOTE + u"\n"
must_preserve(bk_old, bk_new, "AGENT_BACKLOG.md")
if bk_new.count(u"**338. ") != 1:
    die(u"338 那一单不在盘上 ⇒ 追记没有归属")
with io.open(BACKLOG, "w", encoding="utf-8") as h:
    h.write(bk_new)

print(u"BACKFILL_R289 OK rounds=%d curve %s→%s gaps %s→%s min=%s" % (
    len(SECTIONS), BEFORE_MEAN, AFTER_MEAN, BEFORE_GAPS, AFTER_GAPS, AFTER_MIN))
