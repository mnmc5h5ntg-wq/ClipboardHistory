#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R298 的轮次台账（第 297 轮 / Round 295）—— 350 的门 + 一支照到我自己的守卫。

事务形状同前两本：六本先算出来 → 写盘前电池 → 写盘后电池 → 不一致就整体还原（含报告）。
读数一律现取：门那行 / 全量卷 / 帧闸门都来自 `/tmp/r298_verify`，预检现跑，
分箱三个数由 `test_ui_round_interval_parity.check()` 自己算（与判据同一颗尺，不另数一遍）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "tests"))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
}
RUN = "/tmp/r298_verify"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 14, 14, 5, 13, 14, 14]


def die(m):
    sys.stderr.write(u"LEDGERS_R298 REFUSED: " + m + u"\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def sh(argv):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        bad = [l for l in txt.splitlines()
               if l.startswith((u"FAIL:", u"ERROR:")) or u"FINAL_REPORT_" in l or u"ROSTER_" in l]
        return None, tag + u" 电池不绿：" + "\n".join(bad[:12])
    return (ran[-1], ok[-1], names), ""


# ── 读数 ────────────────────────────────────────────────────────────
gate_p = os.path.join(RUN, "warning_gate.log")
if not os.path.exists(gate_p):
    die(u"缺 " + gate_p + u" ⇒ 先跑 scripts/round_verify.sh " + RUN)
gl = re.findall(r"^(ROUND_WARNING_GATE[^\n]*)", rd(gate_p), re.M)
if not gl:
    die(u"门没有结论行")
GATE = gl[-1]

full_p = os.path.join(RUN, "full.log")
if not os.path.exists(full_p) or u"All tests' passed" not in rd(full_p):
    die(u"全量卷不是 passed 或缺文件")
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", rd(full_p))
if not roll:
    die(u"全量卷没有汇总行")
ROLLED, SKIPPED, ROLLED_F = roll[-1]

frames_dir = os.path.join(RUN, "frames")
if not os.path.isdir(frames_dir):
    die(u"找不到帧目录")
frames = [f for f in os.listdir(frames_dir) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", frames_dir, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]
CH_ = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]

pout, prc = sh(["python3", PRECHECK])
PS = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if not PS or prc != 0:
    die(u"预检不是 bad=0：" + pout.strip()[-250:])
PT, PC, PA, PB = PS[-1]

try:
    import test_ui_round_interval_parity as PARITY
except Exception as e:
    die(u"数不出分箱（判据本身没加载）：" + str(e))
struct, narr, bad = PARITY.check(PARITY.read(PARITY.UI))
if not struct or narr < 0:
    die(u"分箱读数没有对象")
BAD_N = str(len(bad))
SINGLE_N = str(len([1 for _ in re.finditer(u"(?m)^## 第 \\d+ 轮", PARITY.read(PARITY.UI))]) - struct - narr)

diffs, _ = sh(["git", "diff", "--name-only", "HEAD~3", "HEAD"])
PROD_N = str(len([l for l in diffs.splitlines() if l.startswith("ClipboardHistory/Sources/")]))

T = {u"@ROLLED@": ROLLED, u"@SKIPPED@": SKIPPED, u"@FAILS@": ROLLED_F,
     u"@PT@": PT, u"@PC@": PC, u"@PA@": PA, u"@PB@": PB,
     u"@FRAMES@": str(len(frames)), u"@CM@": CM, u"@CH@": CH_, u"@MS@": MS, u"@AD@": AD,
     u"@GATE@": GATE, u"@PROD@": PROD_N,
     u"@STRUCT@": str(struct), u"@NARR@": str(narr), u"@BADN@": BAD_N, u"@SINGLE@": SINGLE_N}


def fill(x):
    for k, v in T.items():
        x = x.replace(k, v)
    if re.search(u"@[A-Z_]+@", x):
        die(u"模板里有没被替换的 token：" + " ".join(re.findall(u"@[A-Z_]+@", x)[:6]))
    return x


UI_NEW = fill(u"""## 第 297 轮（R298 · U-974…U-976 · 2026-10-22）：350 的门上了，门先照到我自己写的标签

- **U-974：先量形状再上门。** 新增 `scripts/tests/test_ui_round_interval_parity.py`（5 格）：轮标题声明的
  `U-a…U-b` 必须与该节规范定义的 id 对得上。现读 289 节里区间形 = 结构化 @STRUCT@ 节 + 叙述形 @NARR@ 节
  （旧式整节没有一条定义行）+ 单号标题形 @SINGLE@ 节 —— 一上来按严格判据会造 34 个假正例，所以门只判结构化那一箱。
- **U-975：分箱之后露出的第二层是「尺漏形状」而不是「账缺定义」。** 定义行的粗体里可以夹括注
  （`- **U-351（做对的一格）：…**`、`- **U-344（做对的一格）**：` 冒号在粗体外），旧正则恒不匹配 ⇒
  第 110 / 111 轮差点被误判成缺 U-344 / U-351（R94 同一课第二次：只认一种形状会漏掉一批真的东西）。
  并集三种形状之后结构化箱里真不符的只剩 @BADN@ 节 —— 第 103 轮标题写 U-280…U-289 而正文定义 282…289，
  登记成**恰好等于**的在册名单（名单变长当场红、判据坏掉算不出名单也红），另配正对照「删一条定义行必须被点名」
  与「最新一节必须结构化」防豁免变漏口。
- **U-976：这支守卫当天照到我自己的标签。** `f78b6ac` 的 subject 写 R298，而当时 STATE 现读当前轮是 R297 ——
  正是 `test_commit_subject_hygiene` 要抓的形态。处置**不是放宽窗口**（D-251），而是把这一类登记成具名豁免
  `AHEAD_ROSTER` 并加一格 `test_roster_must_retire`：在册 sha 必须仍在扫描窗口内，窗口滑过去就必须删掉，
  否则它会变成一条永久空白豁免、让下一笔超前标签借它蒙过去（R74：放宽要成对）。本轮台账落地后那条豁免就该退场。

本轮产品文件 @PROD@ 个。门：@GATE@；全量卷 @ROLLED@ / @SKIPPED@ skip / @FAILS@ 失败；
帧 @FRAMES@ 张 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@；预检 tables=@PT@ arms=@PA@ bad=@PB@。

""")

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
T[u"@ROWS@"] = ROWS
T[u"@TOTAL@"] = str(sum(SCORES))
ITER_NEW = fill(u"""## Round 295 · R298（第 297 轮 · 2026-10-22）：台账自身的对账门上了，并且立刻抓到我抄错的轮次标签

本轮做的事：给「轮标题声明的 U 区间 vs 该节实际定义」上一道门（350），并把它顺手照出来的两处
—— 尺漏形状（括注形定义行）与我自己的超前轮次标签 —— 都变成有牙的登记。产品文件 @PROD@ 个。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@
| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 零产品改动，看图腿看的是本轮重捕的台阶帧与基线对账（changed=0），
没有新位点；产品面推进 5 —— 连续第十一轮 0 个产品文件，卡点在 347 的取证通道（主窗口含用户剪贴板原文、不许截屏）；
台账一致性 13 —— 这一轮加的正是台账自身的对账门，且它当天就抓到我的标签超前（登记 + 要求豁免退场）。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 347（真机眼或替代证人）；② 305 的台阶地板（等 347）；③ 348 剩下两格；
④ 349（两颗尺合并）；⑤ 新开 351（单号标题形的 @SINGLE@ 节仍无任何对账 —— 它们的号是否真在别处定义过，今天不知道）；
⑥ 344、341 的 CI 契约半、339、312 具名出口、304、296、291；⑦ 用户闸门 220 路 A / 228② / 265。

""")

DEC_NEW = fill(u"""
**D-279（R298）：给台账上对账门之前，必须先量「同一件事有几种写法」；豁免必须带退场条件。**
350 的门第一次跑就给出 34 个「缺定义」，其中 31 个是旧式叙述节（整节没有定义行）、2 个是定义行夹了括注
（`- **U-351（做对的一格）：…**`、`- **U-344（做对的一格）**：`）被正则漏掉 —— 只有第 103 轮是真不符。
**Why:** 按单一形状写的守卫会把「尺看不见」写成「东西不存在」，一次上三门就淹掉真信号（R94、R277 同一课）。
**How to apply:** 任何扫台账的正则，先跑一遍「几种形状各命中多少」的分箱读数，再决定判哪一箱；
任何为放行而加的具名豁免，必须同时有一格要求它退场（在册对象不在扫描窗口内 = 红），
否则它会变成下一轮借以蒙过去的空白豁免。
""")

BACK_351 = fill(u"""
**351. 区间形之外的 @SINGLE@ 节（旧式单号标题 `## 第 N 轮 · U-xx …`）至今没有任何对账（R298 现读：289 节 = 结构化 @STRUCT@ + 叙述形 @NARR@ + 单号形 @SINGLE@）**：350 的门只判区间形里「有定义行」的那一箱，另两箱按形状豁免。豁免本身是有牙的（叙述形节数必须数得出、最新一节必须结构化），但**单号标题形那批的号是否真在别处定义过、有没有被两轮同时认领**，今天读不到。做法：把 U id 的全局唯一性作为一格判据（同一个号出现在两节的定义行里就红），先量有多少重复再决定门；配一把「把某条定义行复制进另一节」的刀。做完 351，350 与 351 合起来才覆盖整本台账。\n""")

CHG_NEW = fill(u"""### Improved（R298 / 第 297 轮 / Round 295 · 台账区间的对账门 + 豁免要能退场）

新增 `scripts/tests/test_ui_round_interval_parity.py`（5 格）：轮标题声明的 U 区间必须与该节规范定义的 id
对得上，只判「有定义行」的结构化箱（现读 结构化=@STRUCT@ / 叙述形=@NARR@ / 单号形=@SINGLE@），
不符名单要求恰好等于在册那一条（第 103 轮），并配正对照「删一条定义行必须被点名」与「最新一节必须结构化」。
定义行的正则并集三种形状（纯冒号、括注在粗体内、括注在粗体内而冒号在粗体外）—— 旧正则漏后两种，
会把「有定义」误判成「缺定义」。`test_commit_subject_hygiene` 同日加 `AHEAD_ROSTER` 与
`test_roster_must_retire`：我上一笔 f78b6ac 的 subject 标签超前当前轮，正是那支守卫要抓的形态，
处置是具名登记 + 要求退场，而不是放宽窗口（D-251 / D-279）。
新开 351（单号标题形那批仍无对账）。验证：门 @GATE@、全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、
帧 @FRAMES@ 张 changed=@CH@、预检 bad=@PB@、脚本电池写盘前后同数、dmg 已换装本机、产品文件 @PROD@ 个。

""")

STATE_NEW = fill(u"""## R298 状态（第 297 轮 / Round 295 · 2026-10-22）

⓪ 读 CI（R299 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
现取成对号，取不到的写明「push 在台账之后」。本轮已 push 的三笔：`f78b6ac`（350 的门）、
`efeca29`（豁免 + 退场格）、以及本轮这笔 —— 号由 R299 现取。要验的两件事：
① 两道新守卫在 runner 上**有没有对象**（`test_ui_round_interval_parity` 读台账文件、与机器无关，
若报「分箱读数没有对象」就是尺坏了不是产品坏了；`test_commit_subject_hygiene` 依赖 git 历史深度 ——
浅历史会让基线读不到，那一格必须红而不是跳过，见 341 的 sources 浅历史闸门）；
② 台账里那三箱数（结构化=@STRUCT@ / 叙述形=@NARR@ / 单号形=@SINGLE@）在 runner 上是否与本机同数。

最后更新：2026-10-22（本地 · R298 / 第 297 轮 / Round 295）：**台账自身的对账门上了** ——
先量形状再上门（34 个「缺定义」里 31 个是叙述形、2 个是正则漏形状，真不符只剩 1 节），
并集三种定义行形状；不符名单要求恰好等于在册；豁免带退场条件（`AHEAD_ROSTER` + `test_roster_must_retire`），
起因是我自己那笔 f78b6ac 的标签超前。D-279 定规：扫台账的正则先跑分箱读数；具名豁免必须能退场。
门 @GATE@；全量卷 @ROLLED@/@SKIPPED@/@FAILS@；帧 @FRAMES@ 张 changed=@CH@ added=@AD@；
预检 bad=@PB@；dmg ok 且已换装本机；产品文件 @PROD@ 个（连续第十一轮 0 产品改动）。

① 下一轮（R299）的靶：**把 `AHEAD_ROSTER` 那条豁免删掉**（本轮台账已把当前轮推到 R298，它不再需要 ——
留着就是我自己警告过的那种「空白豁免」）；然后 **347**（真机眼或替代证人）→ **305** 的台阶地板；
穿插 348 剩下两格 / 349 / 351。

② 仍开：347（真机或替代证人）、305（等 347）、348 的两格、349、350 的第二步（第 103 轮那处历史标题的两种修法）、
351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""")

if len(re.findall(u"(?m)^- \\*\\*U-9(?:7[456])：", UI_NEW)) != 3:
    die(u"U 定义行形状不符")
if not re.search(u"U-(\\d+)…U-(\\d+)", UI_NEW.splitlines()[0]):
    die(u"标题没有 U 区间")
if u"（R298 ·" not in UI_NEW.splitlines()[0]:
    die(u"标题缺（R298 前缀")
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW)) != 7:
    die(u"七维格子不是 7 行")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R298 / 第 297 轮 / Round 295）", STATE_NEW, re.M):
    die(u"STATE 形状不符")

orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 297 轮" in orig["UI"]:
    die(u"UI 已有第 297 轮")
if re.search(u"(?m)^## Round 295 · ", orig["IT"]):
    die(u"ITERATION 已有 Round 295")
if u"D-279" in orig["DEC"]:
    die(u"D-279 已存在")
if re.search(u"(?m)^(?:\\*\\*)?351[. ] ", orig["BL"].replace(u"*", u"")):
    die(u"351 已存在")
if u"## R298 状态（" in orig["ST"]:
    die(u"STATE 已有 R298")
if u"R298 / 第 297 轮" in orig["CH"]:
    die(u"CHANGELOG 已有 R298")
if orig["UI"].count(u"## 第 296 轮") != 1:
    die(u"UI 锚点不符")
if orig["ST"].count(u"## R297 状态（") != 1:
    die(u"STATE 锚点不符")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl = orig["BL"].splitlines(True)
k = len(bl)
while bl[k - 1].strip() == u"":
    k -= 1
BL_TEXT = u"".join(bl[:k]).rstrip(u"\n") + u"\n" + BACK_351

new = {
    "UI": orig["UI"].replace(u"## 第 296 轮", UI_NEW + u"## 第 296 轮", 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n",
    "BL": BL_TEXT,
    "ST": orig["ST"].replace(u"## R297 状态（", STATE_NEW + u"## R297 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + CHG_NEW, 1),
}
pre, err = battery(u"写盘前")
if pre is None:
    die(err)
for key, text in new.items():
    wr(FILES[key], text)

FR = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
fr_orig = rd(FR)
sh(["python3", REFRESH])
cv0, _ = sh(["python3", CURVE])
ph = re.findall(r"PHASE2 n=\d+ rounds=9\.\.(\d+)", cv0)
if not ph:
    die(u"仪器没打印 rounds=9..N")
tail = ph[-1]
fr_now = rd(FR)
hm = re.search(u"R9–R(\\d+)", fr_now.splitlines()[0])
if not hm:
    die(u"标题没有 R9–R<NNN>")
if hm.group(1) != tail:
    wr(FR, re.sub(u"R9–R(\\d+)", lambda m: u"R9–R" + tail, fr_now, count=1))
    print(u"TITLE_BUMP " + hm.group(1) + u" -> R9–R" + tail)
ui_now = rd(FILES["UI"])
umax = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d+)(?:（[^）]*）)?\\*{0,2}[：:]", ui_now)]
if not umax:
    die(u"数不出 U 定义行")
fr2 = rd(FR)
um = re.search(u"U-31 … U-(\\d+)", fr2)
if not um:
    die(u"§1 找不到 U-31 … U-<NNN>")
if int(um.group(1)) != max(umax):
    wr(FR, re.sub(u"U-31 … U-\\d+", u"U-31 … U-%d" % max(umax), fr2, count=1))
    print(u"UCELL_BUMP " + um.group(1) + u" -> U-%d" % max(umax))

post, err = battery(u"写盘后")
if post is None or post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"写盘后电池不绿或计数变了 ⇒ 已整体还原：" + (err or u""))

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"295=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv) or [u"?"])[-1]
print(u"LEDGERS_R298 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F
      + u" 分箱=" + str(struct) + u"/" + str(narr) + u"/" + SINGLE_N + u" 不符=" + BAD_N
      + u" precheck bad=" + PB + u" frames=" + str(len(frames)) + u" prod=" + PROD_N
      + u" U=974..976 D=279 new=351 派生分=" + score + u" GAPS=" + gaps)
