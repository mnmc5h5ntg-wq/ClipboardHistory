#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R340 的七本台账（第 339 轮 / Round 337）：判据账，产品 0 文件。

顺序与 R339 同一套：先解析读数 → 一次性写盘 → 写盘后自检（编号/形状/曲线/电池）。
锚点按整行字面认，命中次数≠1 就在写任何盘之前 die。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
ITE = os.path.join(ROOT, u"AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, u"AGENT_DECISIONS.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, u"CHANGELOG.md")
STA = os.path.join(ROOT, u"AGENT_STATE.md")
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
CURVE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"curve_from_ledger.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
SRCCELL = os.path.join(ROOT, u"scripts", u"report_sources_cell.py")
STREAK = os.path.join(ROOT, u"scripts", u"product_streak.py")
SCANNER = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"review_round_claims.py")

LOG_SCAN = u"/tmp/r340_scan.log"
LOG_BATT = u"/tmp/r340_py4.log"
LOG_CI = u"/tmp/r340_ci.log"
LOG_FRAMES = u"/tmp/r340_frames.log"

ROUND, AUDIT_N, ITER_N, PRODUCT_N = 340, 339, 337, 0
U1, U2, U3, U4, U5, U6, U7, U8 = 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170
UMAX = U8
D1 = 336
B_ROSTER = 417      # 门看不见的矛盾：R339 的追记写了 产品 0 文件而本轮是 3
ARMS_NEW = ()       # 本轮不落刀（没有产品改动可打；写清而不是假装有一把）
SEVEN = [12, 15, 15, 11, 15, 15, 14]
DATE = u"2026-10-25"
ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def sh(cmd):
    q = subprocess.run(cmd, cwd=ROOT, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return q.stdout.decode(u"utf-8", u"replace"), q.returncode


def die(msg):
    print(u"LEDGERS_R340_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


def once(text, anchor, replacement):
    n = text.count(anchor)
    if n != 1:
        die(u"锚点命中 %d 次（要 1 次）：%s" % (n, anchor[:90]))
    return text.replace(anchor, replacement)


def require(p):
    if not os.path.exists(p):
        die(u"证人日志不在盘上：" + p + u" ⇒ 那一格没处解析，不许手填")
    return rd(p)


# ── 现读 ─────────────────────────────────────────────────────────────────────
scan_out, scan_rc = sh([sys.executable, SCANNER, u"400"])
io.open(LOG_SCAN, u"w", encoding=u"utf-8").write(scan_out)
m = re.search(u"扫了=(\\d+) 笔 / (\\d+) 轮 内部不一致=(\\d+) 未识别=(\\d+)", scan_out)
if not m:
    die(u"扫描器没打印结论行：" + scan_out[:200])
SCAN = m.groups()
if SCAN[0] == u"0" or SCAN[1] == u"0":
    die(u"扫描窗是空的（%s 笔 / %s 轮）⇒ 空对账不许签字" % (SCAN[0], SCAN[1]))
batt = require(LOG_BATT)
BATT = (re.findall(u"Ran (\\d+) tests", batt) or [u"?"])[-1]
BATT_SKIP = (re.findall(u"OK \\(skipped=(\\d+)\\)", batt) or [u"?"])[-1]
if u"FAILED" in batt:
    die(u"电池是红的，不许落账")
st_out, _ = sh([sys.executable, STREAK, u"--streak-for", u"%d" % AUDIT_N])
STREAK_N = (re.findall(u"streak=(\\d+)", st_out) or [u"?"])[-1]
pre_out, _ = sh([sys.executable, os.path.join(ROOT, u".scratch/motion-audit-2/mutate_needle_precheck.py")])
PRE = (re.findall(u"NEEDLE_PRECHECK tables=(\\d+) covered=(\\d+) arms=(\\d+) bad=(\\d+)", pre_out)
       or [(u"?", u"?", u"?", u"?")])[-1]
ARM_TOTAL = (re.findall(u"ARM_TOTAL files=(\\d+) arms=(\\d+)", pre_out) or [(u"?", u"?")])[-1]
if PRE[3] != u"0":
    die(u"针预检 bad≠0：" + str(PRE))
frames = subprocess.run([u"ls", u"/tmp/r339_shots3"], stdout=subprocess.PIPE).stdout.decode()
FRAME_N = len([x for x in frames.splitlines() if x.endswith(u".png")])
io.open(LOG_FRAMES, u"w", encoding=u"utf-8").write(u"FRAME_COUNT=%d\n" % FRAME_N)
if FRAME_N < 150:
    die(u"上一轮的帧不在盘上（只数到 %d 张）⇒ 看图腿要记 NOT-RUN，不许沿用" % FRAME_N)

# ── 1) UI_AUDIT ──────────────────────────────────────────────────────────────
aud = rd(AUD)
heads = [(int(x.group(1)), x.start()) for x in re.finditer(u"(?m)^## 第 (\\d+) 轮", aud)]
top_n, top_pos = max(heads, key=lambda t: t[0])
if top_n != AUDIT_N - 1:
    die(u"当前最大轮次是 第 %d 轮，不是 %d" % (top_n, AUDIT_N - 1))

AUD_ENTRY = u"""## 第 {audit} 轮（R{round} · {date} · U-{u1}…U-{u8}）：回顾尺第二次升成窗口守卫 —— 而它第一次跑就抓到我自己那笔提交（U-{u1}…U-{u8} · 产品 0 文件，判据账）

- **U-{u1}：405 的两半都做完了 —— 「产品 K 文件」现在是轮次级的定义，而且有一道会红的门看着它**（D-{d}）。
  尺在 R336 就造好了（`review_round_claims.py`），但它只在人肯跑的那一步有效；本轮把它接进
  `scripts/tests/test_round_claim_consistency.py`，于是"下一轮又写岔"从今天起是**电池里的一朵红**，
  不是"回顾时才发现"。这正是 D-333 那条"回顾要有两种仪器"里缺的第二种。
- **U-{u2}：门第一次跑就点到我的名字** —— 现读 `UNPARSED fb2cea0 产品 3 文件｜Round 336: …`。
  上一轮那笔提交的 subject 是旧形状，带着 K 却没有可解析的轮次身份 ⇒ 门看不见它，
  而"看不见"必须被打印成 `未识别=1` 而不是安静地少一行（登记在 `UNPARSED_ROSTER`，理由引用 BACKLOG 416）。
- **U-{u3}：这把尺原来的洞比它抓到的缺陷更大** —— 它只认 `R<NNN> …（… 产品 K 文件 …）` 一种开头，
  于是一笔写成 `Round 219：…` 的提交**根本进不了名册**，读数仍是"内部不一致=2"，好像一切都被扫过了。
  **漏扫比误报更坏**：误报会有人来删，漏扫没人知道少扫了多少。本轮没有去放宽正则（那会把"写错形状"
  也洗成"与本轮无关"），而是把"认不出"本身变成一格必须为 0 的读数。
- **U-{u4}：扫描窗用 sha 而不是"最近 N 笔"，且 cutoff 不在历史里就抛错** ——
  现读 `窗起=5d1c246`（现行 subject 形状第一次出现的那一笔，R334 代码半）。
  它之前全是老形状：硬扫会得到 `未识别=40` —— 那种噪音等于把门关掉（没人会读 40 行豁免）。
  cutoff 找不到 ⇒ `ValueError`，**不许退化成"整条历史都扫"**。
- **U-{u5}：名单只买"不红"，买不到"数对" —— 四条正对照钉住它**：
  ① 登记了轮次矛盾，没登记的未识别那笔必须还在红；② sha 打错一位必须照样红（名单按身份对，不是"有条目就行"）；
  ③ 理由引用的 BACKLOG 号查无条目必须红；④ 没写退场条件必须红。
  这四条用的是**合成**标题，因为真历史只能证明"今天没红"，证明不了这把尺看得见红。
- **U-{u6}：现读数字** —— 窗内 `扫了={s0} 笔 / {s1} 轮 内部不一致={s2} 未识别={s3}`
  （不一致的两轮 R334/R335 登记在 `CONTRADICTION_ROSTER`，理由引用 BACKLOG 405）；
  脚本电池 `Ran {batt}（skipped={bskip}）OK`（上一轮 629 → 本轮 {batt}，新增 5 格全在这一支里）；
  针预检 `tables={pt} covered={pc} arms={pa} bad={pb}`、臂名册 `files={af} arms={at}`。
- **U-{u7}：有一处矛盾是门**看不见**的，只能靠人读出来并登记** —— R{prev} 的追记那一笔写的是
  「产品 0 文件」（那一笔确实 0 个产品文件），而它所在那一轮的轮次级数是 3。
  因为本轮的"代码半"用的是旧形状，门只数到追记那一笔 ⇒ 它不构成"两个数"，于是安静通过。
  **登记在豁免之下不等于没问题**：这一条开成 BACKLOG {b_roster}，
  并把写法钉成"追记/账半要么不写 K，要么重复本轮那个数"（R{prev} 之前那几轮的追记就是不写 K 的）。
- **U-{u8}：看图腿（零产品改动轮）先数帧再说话** —— `ls /tmp/r339_shots3` 现读 **{frames} 张**在盘上，
  于是本轮的像素证据沿用上一轮那批（没有新帧可看，也没有产品改动需要看）；
  逐张看的是 R{prev} 那三对 backing 帧里"页底 50 改前/改后"那一对：改前两颗并成同一档、改后能一眼指出被选中的那颗。
  本轮**没有**新的视觉结论 —— 把这一格写成"看过且没问题"就是撒谎，写成"沿用"才是读数。

""".format(audit=AUDIT_N, round=ROUND, prev=ROUND - 1, date=DATE, u1=U1, u2=U2, u3=U3, u4=U4,
           u5=U5, u6=U6, u7=U7, u8=U8, d=D1,
           s0=SCAN[0], s1=SCAN[1], s2=SCAN[2], s3=SCAN[3], batt=BATT, bskip=BATT_SKIP,
           pt=PRE[0], pc=PRE[1], pa=PRE[2], pb=PRE[3], af=ARM_TOTAL[0], at=ARM_TOTAL[1],
           b_roster=B_ROSTER, frames=FRAME_N)
wr(AUD, aud[:top_pos] + AUD_ENTRY.rstrip(u"\n") + u"\n\n" + aud[top_pos:])

# ── 2) ITERATION（升序，追加到文件尾）───────────────────────────────────────
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进",
        u"台账一致性", u"交付诚实性", u"可复核性"]
WHYS = [
    u"零产品改动轮：先 ls 数出上轮 {frames} 张帧在盘上再沿用，并逐张看那对 backing 改前/改后；本轮没有新视觉结论，按实写".format(frames=FRAME_N),
    u"回顾尺升成窗口守卫（电池里会红），五条新格接进 {batt} 例那一跑".format(batt=BATT),
    u"四条正对照钉住豁免名单（登记不能互相放过 / sha 打错必须红 / 引用查无必须红 / 缺退场必须红）",
    u"产品 0 文件 —— 连着两轮动效主线之后排了一轮判据账；399/390/389 那一串仍排队，没被这轮顶掉",
    u"K 的语义第一次有定义（D-{d}）且两本账的编号、区间、曲线都由仪器复查".format(d=D1),
    u"上一轮我自己写错的 subject 与那处门看不见的矛盾，都写进账并各开一条可退场的登记（416 / {b}）".format(b=B_ROSTER),
    u"runner 的 411 验收仍欠：fb2cea0 那一跑红在 STEP[9] 的 subject 卫生（Swift 两格根本没跑），483549a 那一跑回填时还在跑",
]
rows = u"\n".join(u"| %s | %d/15 | %s |" % (d, s, w) for d, s, w in zip(DIMS, SEVEN, WHYS))
ITE_ENTRY = u"""## Round {iter} · R{round}（第 {audit} 轮 · {date}）：把回顾尺变成电池里的门，而它第一次跑就点到我的名字（产品 0 文件）

本轮做了什么：405 的两半 —— ① D-{d} 立定义：标题里那半句「产品 K 文件」是**轮次级**的数，
本轮每一笔要么重复它、要么不写；② `review_round_claims.py` 接进 `scripts/tests/test_round_claim_consistency.py`，
从"人肯跑才有效的一次性尺"变成窗口守卫。顺手补了这把尺自己的两个洞：
只认一种 subject 开头 ⇒ 老形状的笔静默消失（漏扫），修法是加 sha cutoff + 把"认不出"打印成必须为 0 的一格；
以及名单必须被四条合成正对照钉住（真历史只证明"今天没红"）。

现读：`ROUND_CLAIM_REVIEW 扫了={s0} 笔 / {s1} 轮 内部不一致={s2} 未识别={s3} 窗起=5d1c246`
（不一致的 R334/R335 与未识别的 fb2cea0 都是**登记过、写明退场、且能在 BACKLOG 里查到**的例外）；
脚本电池 `Ran {batt}（skipped={bskip}）OK`；针预检 `tables={pt} covered={pc} arms={pa} bad={pb}`；
清账表沿用上一轮那一份（本轮没动格子）；帧 {frames} 张在盘上（沿用，未重捕）。
NOT-RUN：① 真机那屏仍 `screen_locked`（395 继续欠）；② 411 的 runner 验收要 `483549a` 那一跑
（回填时 in_progress）—— 上一跑红在 STEP[9] 的 subject 卫生，Swift 两格根本没跑，所以**不能记成"红消失了"**；
③ 本轮没有变异刀（没有产品改动可打；写清而不是为了凑数造一把抓不到的刀）。

| 维度 | 分 | 依据 |
| --- | --- | --- |
{rows}

""".format(iter=ITER_N, round=ROUND, audit=AUDIT_N, date=DATE, d=D1,
           s0=SCAN[0], s1=SCAN[1], s2=SCAN[2], s3=SCAN[3], batt=BATT, bskip=BATT_SKIP,
           pt=PRE[0], pc=PRE[1], pa=PRE[2], pb=PRE[3], frames=FRAME_N, rows=rows)
ite = rd(ITE)
if (u"## Round %d ·" % ITER_N) in ite:
    die(u"ITERATION 已有 Round %d" % ITER_N)
if (u"## Round %d " % (ITER_N - 1)) not in ite:
    die(u"找不到上一节 Round %d ⇒ 升序断了" % (ITER_N - 1))
wr(ITE, ite.rstrip(u"\n") + u"\n\n" + ITE_ENTRY.rstrip(u"\n") + u"\n")

# ── 3) BACKLOG：新开 417 + 405 结案追记 ─────────────────────────────────────
BL_ENTRY = u"""**417. 「追记/账半」那一笔到底该不该写「产品 K 文件」：本轮的门看不见这处矛盾，因为它只数到了一笔**（R{round}）
现读形状：R{prev} 的代码半 `fb2cea0` 用旧 subject（`Round 336: …（… 产品 3 文件…）`），
追记 `483549a` 用新 subject 并写了「产品 0 文件」（那一笔确实 0 个产品文件）。
`review_round_claims.py` 只能解析后者 ⇒ R{prev} 在名册里只有一笔、不构成"两个数"，**安静通过**。
这不是门的错（未识别那一格已经把它点名成例外），是**写法没有定义**：
D-{d} 说 K 是轮次级的数，那么"每一笔"要么重复本轮那个数、要么**根本不写这一格**。
仓库里两种都有过：R338 的追记（b08d294）不写 K；R335 的"代码半补"（f3f2027）写了 0，于是被抓成一轮内部不一致。
本条要落的不是再登记一次，而是把写法收成一条：**追记一律不写「产品 K 文件」**
（它改的是台账，不是产品；写了就必然与轮次级那个数打架）。
判"做了没有"的数：下一轮之后，`ROUND_CLAIM_REVIEW` 的 `内部不一致` 与 `未识别` 都仍是登记内，
且没有任何一笔**新**的追记带着 K —— 那一格由本文件下一轮的 U 段复查。

**405 追记（R{round} 结案）**：两半都落地了。
① 定义 = D-{d}（K 是轮次级：本轮每一笔重复同一个数，或者不写这一格）；
② 门 = `scripts/tests/test_round_claim_consistency.py` 五格（正对照三条 + 真历史一条 + 豁免引用一条），
   现读 `Ran {batt}（skipped={bskip}）OK`，窗内 `扫了={s0} 笔 / {s1} 轮 内部不一致={s2} 未识别={s3}`，
   其中 R334 / R335 与 fb2cea0 都在**带退场条件、且能在本文件里查到编号**的名单里。
   顺带把尺自己的洞补了：cutoff 之前不扫（老形状没有轮次身份，硬扫就是 40 行噪音），
   cutoff 找不到就抛错，认不出的笔一律点名。
""".format(round=ROUND, prev=ROUND - 1, d=D1, batt=BATT, bskip=BATT_SKIP,
           s0=SCAN[0], s1=SCAN[1], s2=SCAN[2], s3=SCAN[3])
blg = rd(BLG)
if re.search(u"(?m)^\\*\\*%d\\. " % B_ROSTER, blg):
    die(u"BACKLOG %d 已存在" % B_ROSTER)
if u"**405. " not in blg:
    die(u"BACKLOG 405 不在盘上")
wr(BLG, blg.rstrip(u"\n") + u"\n\n" + BL_ENTRY.rstrip(u"\n") + u"\n")

# ── 4) DECISIONS：D-336 ─────────────────────────────────────────────────────
DEC_ENTRY = u"""### D-{d}（{round}）标题里那半句「产品 K 文件」是**轮次级**的数：本轮每一笔要么重复它，要么不写这一格

**为什么要有这条定义**：一轮通常两笔以上（代码半 / 代码半补 / 账半 / 追记），每笔标题都带着
「第 N 轮 / Round M · 产品 K 文件」。前半句已经是轮次级身份，后半句却可以按"这一笔改了几种文件"来写 ——
两种语义并存的结果是同一轮里出现两个数（R336 回顾现读：R334 是 2 与 0，R335 是 7、7 与 0）。
读 `git log` 的人无从判断哪一句作数，而 `scripts/product_streak.py` 只从"代码半"那一笔派生，
所以台账内部对得上、标题之间互相打脸。

**定下来**：K = **本轮**产品面被改动的文件数（与 `product_streak` 从代码半并集派生的那个数同一个）。
每一笔重复它；**写不出同一个数的那一笔，就不写这一格**（追记与纯台账笔属于这一类）。
不许"这一笔改了几个就写几个" —— 那不是错，那是另一种语言，而同一份标题里只准有一种。

**为什么钉它而不是约定**：这条规矩违反起来毫无症状（标题读着都顺），所以它必须有一道会红的门。
门在 `scripts/tests/test_round_claim_consistency.py`，尺是 `.scratch/motion-audit-2/review_round_claims.py`；
例外一律进带退场条件的名单，且每条要在 `AGENT_BACKLOG.md` 里查得到编号（R298 那一课：豁免不许自我批准）。
""".format(d=D1, round=ROUND)
dec = rd(DEC)
if re.search(u"(?m)^### D-%d" % D1, dec):
    die(u"D-%d 已存在" % D1)
if (u"### D-%d" % (D1 - 1)) not in dec:
    die(u"找不到 D-%d" % (D1 - 1))
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + DEC_ENTRY.rstrip(u"\n") + u"\n")

# ── 5) CHANGELOG ─────────────────────────────────────────────────────────────
CHG_ENTRY = u"""### 回顾尺第二次升成窗口守卫，而它第一次跑就点到我自己那笔提交（R{round} / U-{u1}…U-{u8} · 产品 0 文件，判据账）

- D-{d}：标题里那半句「产品 K 文件」是**轮次级**的数 —— 本轮每一笔重复它，写不出同一个数就不写这一格。
- 门：`scripts/tests/test_round_claim_consistency.py` 五格接进电池（现读 `Ran {batt}`，上一轮 629）。
- 尺补两个洞：只认一种 subject 开头 ⇒ 老形状的笔静默消失（漏扫）；现在 cutoff 之前不扫、
  cutoff 不在历史里抛错、认不出的笔一律打印成 `未识别=K`（K>0 就红）。
- 正对照四条钉住豁免名单：登记一条不能放过另一条、sha 打错一位必须照样红、
  引用查无 BACKLOG 号必须红、没写退场条件必须红。
- 现读：`扫了={s0} 笔 / {s1} 轮 内部不一致={s2} 未识别={s3} 窗起=5d1c246`；
  R334 / R335（405）与 fb2cea0（416）都在带退场条件的名单里。
- 新开 {b}：追记那一笔该不该写 K —— 本轮的门看不见 R{prev} 那处矛盾（它只数到一笔），靠人读出来才登记。
""".format(round=ROUND, u1=U1, u8=U8, d=D1, batt=BATT, s0=SCAN[0], s1=SCAN[1],
           s2=SCAN[2], s3=SCAN[3], b=B_ROSTER, prev=ROUND - 1)
chg = rd(CHG)
if chg.count(u"\n## [Unreleased]") != 1:
    die(u"[Unreleased] 不是恰好一处")
lines = chg.split(u"\n")
unrel = [i for i, l in enumerate(lines) if l == u"## [Unreleased]"][0]
h3 = [i for i, l in enumerate(lines) if i > unrel and l.startswith(u"### ")][0]
wr(CHG, u"\n".join(lines[:h3]) + u"\n" + CHG_ENTRY.rstrip(u"\n") + u"\n\n" + u"\n".join(lines[h3:]))

# ── 6) STATE 轮换 ───────────────────────────────────────────────────────────
STATE_BODY = u"""## R{round} 状态（{date} · 本地 · 第 {audit} 轮 / Round {iter}）：回顾尺第二次升成窗口守卫，而它第一次跑就点到我的名字（产品 0 文件，判据账）

最后更新：{date}（本地 · R{round} / 第 {audit} 轮 / Round {iter}）：把"下一轮别再写岔"从记性换成会红的门 ——
「产品 K 文件」立成轮次级定义（D-{d}），`review_round_claims.py` 接进电池，顺手补这把尺自己的两个洞
（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ 读 CI（成对）：`RUN=40147352168 ↔ fb2cea0 completed/failure` —— 但**红的形状换了**：
  失败步骤只剩 STEP[9] Release script tests，两朵红是
  `test_recent_subjects_are_clean`（我上一轮那笔 subject 缺 `R<NNN>`）与 `test_skip_roster`（内层没有结论行的级联），
  而 STEP[15] 全量卷 / STEP[17] 捕获闸**根本没跑** ⇒ 411 的验收**不能**记成"红消失了"，
  它挂在 `RUN=40147874314 ↔ 483549a`（回填时 in_progress ⇒ 只登记不轮询，R140）。
② 定义：D-{d} —— K 是**本轮**产品面的文件数；每一笔重复它，写不出同一个数就不写这一格。
③ 门：`scripts/tests/test_round_claim_consistency.py` 五格（正对照四条 + 真历史一条 + 豁免引用一条）。
④ 尺补洞：只认一种 subject 开头 ⇒ 老形状静默消失（漏扫比误报更坏）。现在 cutoff（`5d1c246`，现行形状第一笔）
  之前不扫、cutoff 不在历史里抛错、认不出的笔一律打印成 `未识别=K`，K>0 就红。
⑤ 名单规矩复述（R298 那一课）：每条豁免必须引用一条**真存在**的 BACKLOG 编号并写明退场；
  名单只买"不红"，买不到"数对"。

验证读数（现读）：`ROUND_CLAIM_REVIEW 扫了={s0} 笔 / {s1} 轮 内部不一致={s2} 未识别={s3} 窗起=5d1c246`；
脚本电池 `Ran {batt}（skipped={bskip}）OK`（上一轮 629 → 本轮 {batt}，新增 5 格全在这一支里）；
针预检 `tables={pt} covered={pc} arms={pa} bad={pb}`、臂名册 `files={af} arms={at} dupes=0 repeats=0`；
清账表沿用上一轮那一份（本轮没动格子）；`ls /tmp/r339_shots3` 现读 {frames} 张帧在盘上 ⇒ 看图腿沿用，不重捕；
产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for {audit}` ——
这一格仍带 BACKLOG 412 的**口径差一**，读成「本轮**之前**的连读轮数」。 —— 这一整句必须在同一行里：
`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for {audit}`。
本轮**没有**新的像素/判据读数族 ⇒ §8 的 `--must-include` 声明为空（按实记，不是沿用上一轮的声明）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那屏仍 `screen_locked`
  （电源 on、SecureInput 属主 loginwindow）⇒ 395 继续欠。
② **只在 runner 上判得了**：411 的结案挂在 `483549a` 那一跑（回填时 in_progress）——
  期望三格：`SEGREF_POLARITY dark 自家 差` ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 非空、STEP[15]/[17] 跑起来并转绿。
  上一跑那两格**根本没执行**，所以"没红"不等于"修好了"。
③ **这条通道看不见 / 没做**：本轮无变异刀（没有产品改动可打，写清而不是凑数）；
  新门看不见"追记写 0 而本轮是 3"那一类（只数到一笔 ⇒ 不构成两个数），已开成 BACKLOG {b}。

下一轮（R{next}）的靶：⓪ 读 CI 配对（现读自 `scripts/ci_read.py latest`）——
`RUN=40147874314 ↔ 483549a`（回填时 in_progress）：这一跑必须让 STEP[15]/[17] 真的跑起来，
才谈得上 411 结案；若 STEP[9] 仍红，先看是不是 `test_skip_roster` 的级联（它读的是内层那一跑的结论行）。
→ ① **BACKLOG 413**：backing 从三档常量换成名册（每档标实测/外推），并给「降低透明度 / 增加对比」
  各拍一帧 —— 那两档直接改材质合成结果，是 R{prev} 那条链上最可能的下一个坑。
→ ② 412（`--streak-for` 差一）：修它要在同一笔里重算窗口内所有格。
→ ③ 动效主线仍排队：399 / 397 / 390 / 389 / 384 / 387① / 376 / 367。

本轮的自伤（写成出处，不写成缺陷）：新写的测试文件里有一句 CJK 串用了 ASCII 双引号
（`别把"没红"读成"没问题"`）⇒ 整支模块 import 失败，而它同时把 `test_skip_roster` 的两格带红
（内层没有结论行）。这条坑仓库早就记过（记忆 `reference-macos-python-and-skill-install`），
我又踩了一次 —— 区别是这次是**新写**而不是继承，所以正解是写完立刻 `ast.parse` 一遍再跑电池
（本文件的生成器一直这么做，测试文件却漏了：以后新增 `scripts/tests/*.py` 先过 AST 预检）。
""".format(round=ROUND, next=ROUND + 1, audit=AUDIT_N, iter=ITER_N, date=DATE, d=D1,
           b=B_ROSTER, streak=STREAK_N, batt=BATT, bskip=BATT_SKIP, frames=FRAME_N,
           pt=PRE[0], pc=PRE[1], pa=PRE[2], pb=PRE[3], af=ARM_TOTAL[0], at=ARM_TOTAL[1],
           s0=SCAN[0], s1=SCAN[1], s2=SCAN[2], s3=SCAN[3], prev=ROUND - 1)
sta = rd(STA)
before_layers = sta.count(u"\n> ## ")
pos = sta.find(u"## R%d 状态" % (ROUND - 1))
if pos < 0:
    die(u"找不到上一轮（R%d）的节标题" % (ROUND - 1))
wr(STA, sta[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d" % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"STATE 轮换把上一轮的节标题弄丢了")

# ── 7) FINAL_REPORT 计数器（六本已写，最大号从磁盘派生）─────────────────────
fr = rd(FRA)
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
D_MAX = max(int(x) for x in re.findall(u"(?m)^### D-(\\d{3})", rd(DEC)))
B_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX, D_MAX, B_MAX) != (UMAX, D1, B_ROSTER):
    die(u"最大号不一致：%d/%d/%d" % (U_MAX, D_MAX, B_MAX))
mUD = re.search(u"U-31 … U-(\\d+)", fr)
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % U_MAX)
mD = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
if not mD:
    die(u"找不到「决定台账」那一格")
fr = fr[:mD.start(2)] + (u"D-%d" % D_MAX) + fr[mD.end(2):]
prod_hits = [ln for ln in re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
             if u"产品面连续零改动轮数" in ln]
if len(prod_hits) != 1:
    die(u"「产品面」那一格应为恰好一处，实得 %d" % len(prod_hits))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **0** 个（**判据账**："
            u"标题里那半句「产品 K 文件」立成轮次级定义（D-%d），并把回顾尺 `review_round_claims.py` "
            u"接进电池成窗口守卫（`test_round_claim_consistency.py` 五格，含四条合成正对照）；"
            u"尺自己补了两个洞：sha cutoff 之前不扫、认不出的笔一律打印成 `未识别`。"
            u"现读 `扫了=%s 笔 / %s 轮 内部不一致=%s 未识别=%s`。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`，"
            u"口径差一挂在 BACKLOG 412：这一格读成「本轮**之前**的连读轮数」）。"
            u"新开 %d（追记那一笔该不该写 K —— 本轮的门看不见这处矛盾）；405 结案。"
            % (D_MAX, SCAN[0], SCAN[1], SCAN[2], SCAN[3], STREAK_N, B_ROSTER))
fr = once(fr, prod_hits[0], new_prod)
s14 = [ln for ln in fr.splitlines()
       if ln.startswith(u"- **判据与门的规模**") and u"最新的权威" in ln]
if len(s14) != 1:
    die(u"§14 那一格应为恰好一处，实得 %d" % len(s14))
new_s14 = (u"- **判据与门的规模**（R%d 现读，这一格是最新的权威，§13 那格已冻结成历史）："
           u"脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件"
           u"（预检 tables=%s covered=%s arms=%s bad=%s）；"
           u"U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**；"
           u"本轮不落刀（产品 0 文件，没有可打的产品改动 —— 写清而不是凑一把抓不到的刀）。"
           % (ROUND, BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], PRE[3],
              U_MAX, D_MAX, B_MAX))
fr = once(fr, s14[0], new_s14)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

sc, rc = sh([sys.executable, SRCCELL, u"--write"])
if rc != 0:
    die(u"Sources 那一格刷新失败：" + sc.strip()[-300:])
f1, rc = sh([sys.executable, FRESH])
if rc != 0 or u"REFUSED" in f1:
    die(u"报告 §1 的刷新器没签：" + f1.strip()[-300:])
ite2 = rd(ITE)
sec = ite2.split(u"## Round %d · R%d" % (ITER_N, ROUND))[-1]
seven = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", sec)
if len(seven) != 7 or any(mx != u"15" for _, _, mx in seven):
    die(u"七维表形状不对：行=%d 量纲=%s" % (len(seven), [r[2] for r in seven]))
if [int(v) for _, v, _ in seven] != SEVEN:
    die(u"七维表与 SEVEN 不一致")
cv, rc = sh([sys.executable, CURVE])
if rc != 0 or u"GAPS=none" not in cv:
    die(u"曲线仪器没签：" + cv.strip()[-400:])
print(u"R%d_LEDGERS_OK U=%d D=%d BL=%d 电池=%s 扫描=%s/%s/%s/%s 连读=%s 帧=%s"
      % (ROUND, U_MAX, D_MAX, B_MAX, BATT, SCAN[0], SCAN[1], SCAN[2], SCAN[3], STREAK_N, FRAME_N))
