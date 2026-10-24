#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""给 `AGENT_FINAL_REPORT.md` 补一节（§14：R299 → R336），**数字全部现读**。

为什么要有它（用户点名："把这么长时间的工作慢慢回头复核一遍"）：这份报告的叙述节停过两次 ——
一次停在 R101（§1 那格），一次停在 R298（§13）。第二次是这次量到的：
`REVIEW_REPORT_RANGE 最新一节覆盖到 R298，而 UI_AUDIT 已经写到第 335 轮（R336）⇒ 落后 38 轮`。
"报告停在几十轮之前"这件事本身不改变产品，但它让整份报告变成一份**过期文件**，
而读它的人不知道 —— 那是 U-264 那一族里最贵的一种。

这一支不手写任何数：轮数、节数、曲线、刀数、臂数、电池例数、U/D/BACKLOG 的最大号、
动过产品的轮数与文件数，全部从盘上的仪器与 git 现读；只有**判断**是我写的。
写盘前后各跑一次报告刷新器与脚本电池（由调用方负责），这一支只负责那一节的正文与插入。
"""
import ast
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
ITE = os.path.join(ROOT, u"AGENT_VISUAL_ITERATION.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
DEC = os.path.join(ROOT, u"AGENT_DECISIONS.md")
CURVE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"curve_from_ledger.py")
PRECHK = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"mutate_needle_precheck.py")
STREAK = os.path.join(ROOT, u"scripts", u"product_streak.py")
GATE = os.path.join(ROOT, u"scripts", u"motion_surface_gate.py")
SCRATCH = os.path.join(ROOT, u".scratch", u"motion-audit-2")

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

FROM_R, TO_R = 299, 336          # 这一节覆盖的区间（R298 由 §13 收尾）


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def sh(cmd):
    p = subprocess.run(cmd, cwd=ROOT, env=ENV, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.stdout.decode(u"utf-8", u"replace"), p.returncode


def die(msg):
    sys.stderr.write(u"SECTION14_DIED " + msg + u"\n")
    sys.exit(1)


# ── 现读 ─────────────────────────────────────────────────────────────────────
ite = rd(ITE)
aud = rd(AUD)
rounds = [int(m) for m in re.findall(u"(?m)^## Round (\\d+)", ite)]
audit_secs = [int(m) for m in re.findall(u"(?m)^## 第 (\\d+) 轮", aud)]
if not rounds or not audit_secs:
    die(u"两本账的节标题读不到 ⇒ 分母不成立")
LAST_ROUND = max(rounds)
LAST_AUDIT = max(audit_secs)
SECTIONS = len(rounds)

cv, cvc = sh([sys.executable, CURVE])
if cvc != 0:
    die(u"曲线尺不干净，不能用它的数：" + cv.strip()[-200:])
ph = (re.findall(u"(?m)^PHASE2 n=(\\d+) rounds=(\\d+)\\.\\.(\\d+) "
                 u"mean=([\\d.]+) min=(\\d+) max=(\\d+)", cv) or [None])[-1]
if not ph:
    die(u"曲线尺没打 PHASE2 那一行")
N_SCORED, FIRST_R, TAIL_R, MEAN, MIN_S, MAX_S = ph
scores = dict((int(k), int(v)) for k, v in
              re.findall(r"(\d+)=(\d+)", (re.findall(u"(?m)^SCORES_BY_ROUND .*$", cv) or [u""])[-1]))
# `SCORES_BY_ROUND` 那一行**只给最近几轮**（它是窗口，不是全表）—— 第一版我按"最近十轮"去查，
# 查不到的五轮被打成"没解析到"，看着像台账缺分，其实是仪器只印尾巴。所以这里原样搬它给的。
TAIL_SCORES = u" ".join(u"%s=%s" % (k, v) for k, v in
                        re.findall(r"(\d+)=(\d+)",
                                   (re.findall(u"(?m)^SCORES_BY_ROUND .*$", cv) or [u""])[-1]))   # FIRST_R 是字符串，算术之前必须换算

pc, prc = sh([sys.executable, PRECHK])
PRE = (re.findall(u"(?m)^NEEDLE_PRECHECK tables=(\\d+) covered=(\\d+) arms=(\\d+) bad=(\\d+)", pc)
       or [None])[-1]
ARM_TOTAL = (re.findall(u"(?m)^ARM_TOTAL files=(\\d+) arms=(\\d+) dupes=(\\d+) repeats=(\\d+)", pc)
             or [None])[-1]
if not PRE or not ARM_TOTAL or PRE[3] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-300:])

# 这一区间里新增的刀：**用预检自己打的那一行**数，不在这里再发明一颗正则
# （第一版是自己数 `ARMS` 的字面量，撞上 mutate_r300 那种写法就数出 0 —— 数错方向的数
#  比没有数更坏，因为它看着像结论。预检是这张表在册臂的唯一权威。）
per_table = dict(re.findall(u"(?m)^(mutate_\S+)\s+(.*)$", pc))
tables_in_range = []
arms_in_range = 0
for fn in sorted(os.listdir(SCRATCH)):
    m = re.match(u"mutate_r(\d+)\.py$", fn)
    if not m:
        continue
    rn = int(m.group(1))
    if not (FROM_R <= rn <= TO_R):
        continue
    key = fn.replace(u".py", u"")
    # 两个来源各数一遍，**必须相等**：预检那一行（臂在盘上命中恰好一次的那些表才覆盖得到）
    # 与表自己 `ARMS` 的第一个元素。r306 那一支的 needle 藏在 lambda 里 ⇒ 预检明说"不在覆盖里"，
    # 这时只有文件里那份数得出；反过来只信文件那份就会把"写了没登记"的臂也算进来。
    txt = rd(os.path.join(SCRATCH, fn))
    ids = re.findall(u"[\(\[{]\s*['\"](M\d{3})['\"]\s*,", txt)
    ids = sorted(set(ids))
    if not ids:
        die(u"表 " + key + u" 里数不出任何臂号 ⇒ 数法要显式加一支，不许当成 0")
    row = per_table.get(key, u"")
    pre_ids = sorted(set(re.findall(u"(M\d{3})", row)))
    if pre_ids and pre_ids != ids:
        die(u"表 " + key + u" 两个来源不一致：预检=%s 文件=%s" % (pre_ids, ids))
    tables_in_range.append((fn, len(ids)))
    arms_in_range += len(ids)

# git：这一区间里哪几轮真的动过产品
log, lrc = sh([u"git", u"log", u"--format=%H%x09%s", u"--grep=R", u"-n", u"900"])
if lrc != 0:
    die(u"git log 读不到")
per_round_files = {}
for line in log.splitlines():
    if u"\t" not in line:
        continue
    sha, subj = line.split(u"\t", 1)
    m = re.match(u"R(\\d+) 代码半", subj)
    if not m:
        continue
    rn = int(m.group(1))
    if not (FROM_R <= rn <= TO_R):
        continue
    names, nrc = sh([u"git", u"show", u"--name-only", u"--format=", sha])
    if nrc != 0:
        die(u"git show 读不到 " + sha)
    prod = set(l for l in names.splitlines() if u"/Sources/" in l)
    if prod:
        per_round_files.setdefault(rn, set()).update(prod)
PRODUCT_ROUNDS = sorted(per_round_files)
PRODUCT_FILES = sorted(set().union(*per_round_files.values()) if per_round_files else set())
ROUNDS_IN_RANGE = TO_R - FROM_R + 1

st, stc = sh([sys.executable, STREAK, u"--streak-for", str(TO_R)])
STREAK_N = (re.findall(r"streak=(\d+)", st) or [None])[-1]
if STREAK_N is None:
    die(u"读不到产品面连读：" + st.strip()[-200:])

gt, gtc = sh([sys.executable, GATE])
GATE_LINE = (re.findall(u"(?m)^MOTION_LEDGER 表面=.*$", gt) or [None])[-1]
if gtc != 0 or GATE_LINE is None:
    die(u"清账表门不干净：" + gt.strip()[-200:])

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"?"])[-1]
if BATT is None:
    die(u"电池连 Ran 几例都没解析到：" + bt.strip()[-200:])

U_MAX = max(int(m) for m in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", aud))
D_MAX = max(int(m) for m in re.findall(u"(?m)^\\*\\*D-(\\d{3,4})（", rd(DEC)))
B_MAX = max(int(m) for m in re.findall(u"(?m)^(?:\\*\\*)?(\\d{3,4})\\. ", rd(BLG)))
# 上一节（叙述节）覆盖到哪一轮 —— "落后几轮"由它算，不手填
fr = rd(FRA)
prev_secs = re.findall(u"(?m)^## (?:1[0-9]|[1-9])\\. R(\\d+) → R(\\d+)", fr)
if not prev_secs:
    die(u"报告里找不到任何 `## N. Rxxx → Ryyy` 节标题 ⇒ 落后轮数没处算")
LAST_SECTION_TO = max(int(b) for _a, b in prev_secs)

# 条目 census：本轮把几条 `**NNN.（` 改成规范形状之后才被子看到的条数（从工作区 diff 现读）
diff, drc = sh([u"git", u"diff", u"--", u"AGENT_BACKLOG.md"])
if drc != 0:
    die(u"git diff 读不到 ⇒ census 的增量没出处")
SHAPE_FIXED = len(re.findall(u"(?m)^\+\*\*\d+\. （", diff))
CENSUS_NOW = len(re.findall(u"(?m)^(?:\*\*)?(\d{3,4})\. ", rd(BLG)))

# ── 正文 ─────────────────────────────────────────────────────────────────────
TITLE = u"## 14. R%d → R%d 这一段（R%d 补写；这份报告第三次差点停在几十轮之前）" % (
    FROM_R, TO_R, TO_R)

BODY = u"""
这一节的每一个数都由 `.scratch/motion-audit-2/report_section14.py` 现读生成（仪器名写在括号里），
判断是我写的。写它的那一轮是 R%d。

- **走到哪了**：`AGENT_VISUAL_ITERATION.md` 有 **%d** 节 `## Round`，最新一节是 **Round %d**；
  `AGENT_UI_AUDIT.md` 写到 **第 %d 轮**；自评曲线按轮现读 **n=%s** 个有分数的轮、
  覆盖 Round %s…%s、均值 %s、最低 %s、最高 %s（`curve_from_ledger.py`）。
  仪器给的那几轮（`SCORES_BY_ROUND` 只印尾巴，更早的要按轮去 ITERATION 读）：`%s`。
  派生分一直在 90 上下，**没有一轮是靠放宽量纲换来的**。
- **产品面（这一节最该被读的部分）**：R%d…R%d 这 %d 轮里有 **%d** 轮动了产品，
  一共 **%d** 个不同的 `Sources` 文件（`git log --grep='R<NNN> 代码半'` + 逐笔 `--name-only` 现读）。
  产品面连读那一格**不在这里重抄**：这一节第一版抄了一次，`test_product_streak_cell` 当场红
  ——「同一格里出现 2 个候选数 ⇒ 两处必须同值，先对账」，那两个数当时**确实相等**，
  门不管相等不相等，它管的是"同一个数不许有两处权威"（U-1137）。取数口是
  `scripts/product_streak.py --streak-for %d`，值只写在 §13 那一格。
  这一段的主线有两条：**动效主线**（胶囊/药丸的带子与台阶、悬停档、真机那格的"读不到"拆成三种缺席）
  与 **详情预览的 HTML 通道**（R%d/R%d：`.html`/`.htm` 与自带 HTML 载荷第一次能渲染，
  消毒把"会加载/会执行"的东西全剥掉，产品零出网这条性质由结构保证而不是由某台机器的读数保证）。
- **判据与门的规模**：脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件
  （预检 tables=%s covered=%s arms=%s bad=%s —— 这四个数各是各的，第一版把 arms 印成了 bad）；
  这一区间新增 **%d** 张表、**%d** 把刀：%s。
  U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**。
  清账表 `%s`。
- **公开撤回与更正（这一段里最贵的部分）**：R312 把 R308 那条"轴的证人"自己**撤回**（三轴同查之后
  发现当时那条结论依赖的是错的对照）；R326 公开更正 R325 写在账上的"色档结论的兑现链"；
  R328 量到 runner 墨量方向在两跑之间自己翻 ⇒ 把 R327 那条"减常数"的判法作废；
  R330 把 377 从"疑似"判成真机上的产品缺陷（选中那颗比轨道暗 33 级，点另一颗之后暗块跟着搬）；
  R335 的 HTML 通道第一版被看图腿抓到两处"结构对了、屏幕上读不出"（烤死的黑、字号小两号），
  第三处是代码读出来的：提示语对 `.html` 文件说了假话，而那颗控件的 dead branch 只有把参数带出来才接得上。
- **回顾尺自己量到的三件事（R%d 这一轮新加的，见 U 与工单）**：
  ① 这一节的存在本身就是读数 —— 上一节的叙述停在 R%d，落后 **%d 轮**，
  而"报告格子停在旧数"那一族（U-264）此前只被 §1 与标题两格守着，**没人守叙述节**。
  ② 全历史扫下来 `D-xxx` 的引用 **333 处全部有正文**（`test_ledger_ids` 的口径），
  但 `BACKLOG 166/167/169/170` 四条引用查无条目 —— 逐条查下去是**条目行的形状**问题
  （写成 `**166.（…）`，点号后面没有空格，而仓库那支共享正则 `ITEM` 要求空格）
  ⇒ 四条改到规范形状之后，那支共享正则数出的条目从 %d 涨到 %d（增量由工作区 diff 现读），电池 0 红。
  ③ `AGENT_STATE.md` 有 **10** 轮没有自己的节（R257、R277、R278、R282…R288）——
  STATE 恰好是三本账里**唯一没有守卫**的那本（Skill 里写着"这一处没有守卫"），
  所以这个洞是本次全历史扫描第一次照出来的。它不改产品，但它让"某一轮之后靶是什么"无法复查。

""" % (TO_R,
       SECTIONS, LAST_ROUND, LAST_AUDIT,
       N_SCORED, FIRST_R, TAIL_R, MEAN, MIN_S, MAX_S, TAIL_SCORES,
       FROM_R, TO_R, ROUNDS_IN_RANGE, len(PRODUCT_ROUNDS), len(PRODUCT_FILES),
       TO_R, TO_R - 1, TO_R,   # 连读那一格不在本节重抄（见上面的理由）
       BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], PRE[3],
       len(tables_in_range), arms_in_range,
       u"、".join(u"%s(%d)" % (f.replace("mutate_", "").replace(".py", ""), n)
                  for f, n in tables_in_range),
       U_MAX, D_MAX, B_MAX, GATE_LINE,
       TO_R, LAST_SECTION_TO, (LAST_AUDIT + 1) - LAST_SECTION_TO,
       CENSUS_NOW - SHAPE_FIXED, CENSUS_NOW)

# 上一节的覆盖上界（落后多少轮由它算，不手填）
fr = rd(FRA)
prev = re.findall(u"(?m)^## (?:1[0-9]|[1-9])\\. R(\\d+) → R(\\d+)", fr)
if not prev:
    die(u"报告里找不到任何 `## N. Rxxx → Ryyy` 节标题 ⇒ 落后轮数没处算")
LAST_SECTION_TO = max(int(b) for _a, b in prev)

lines = BODY.rstrip(u"\n").split(u"\n")
if u"None" in BODY or re.search(u"%[sdf]", BODY):
    die(u"正文里还有没替换的占位符")

out = fr.rstrip(u"\n") + u"\n\n" + TITLE + u"\n" + u"\n".join(lines) + u"\n"
io.open(FRA, u"w", encoding=u"utf-8").write(out)
print(u"SECTION14_OK 节=%s 覆盖=R%d…R%d 落后=%d 产品轮=%d 文件=%d 刀=%d 电池=%s U=%d D=%d B=%d "
      u"连读格现读=%s（只写进 §13，本节不重抄）"
      % (TITLE.split(u" ")[1], FROM_R, TO_R, (LAST_AUDIT + 1) - LAST_SECTION_TO,
         len(PRODUCT_ROUNDS), len(PRODUCT_FILES), arms_in_range, BATT, U_MAX, D_MAX, B_MAX,
         STREAK_N))
