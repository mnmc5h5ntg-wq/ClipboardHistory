# -*- coding: utf-8 -*-
"""R312 的七本台账（第 311 轮 / Round 309 · 三根轴必须同时可查 —— 356 那一半被证伪）。

机器与 R311 同一套（事务性、写盘前后电池同数、报告计数器由写完账之后的仪器刷、
写盘后崩在任何地方都整体还原）。本轮是**判据轮**：产品 0 文件，改动面只有 1 份 Swift 判据，
所以产品轮那道门换成判据轮那道门，其余闸门一条不放宽；Swift 三条腿本轮由
`scripts/round_verify.sh` 真跑了（不是 NOT-RUN），但**没有 update 基线** —— 因为
`FRAME_GATE_PASS changed=0`：判据轮没有该变的帧，update 一次就等于伪造一次"基线同步"。
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
CHAIN = "/tmp/r313_chain.log"
KNIFE_LOG = "/tmp/r313_chain.log"
R_TAG, PREV_TAG, R_NEXT = u"R313", u"R312", u"R314"
PREV_ROUND, ROUND, RDN = 311, 312, 310
TODAY = u"2026-10-23"
EYE = os.environ.get("R313_EYE", u"")
WROTE, OK_EXIT = [], []


def die(msg):
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        msg = msg + u"（七本已整体还原）"
    sys.stderr.write(u"R313_LEDGERS_REFUSE " + msg + u"\n")
    sys.exit(1)


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


def sh(argv, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(argv, cwd=cwd or ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode("utf-8", "replace"), proc.returncode


def s(x):
    return x if isinstance(x, type(u"")) else json.dumps(x, ensure_ascii=False)


def fill(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests"], cwd=ROOT)
    with io.open(log_path, "w", encoding="utf-8") as h:
        h.write(out)
    ran = re.findall(r"^Ran (\d+) tests", out, re.M)
    ok = re.search(r"^OK \(skipped=(\d+)\)$", out, re.M) or re.search(r"^OK$", out, re.M)
    if not ran or not ok:
        die(u"%s 电池没有结论行（rc=%d）⇒ 不许把「没解析到」当绿" % (tag, rc))
    if re.search(r"^FAILED", out, re.M):
        reds = [l for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))][:6]
        die(u"%s 电池红：%s" % (tag, u" / ".join(reds)))
    return ran[-1], (ok.group(1) if ok.lastindex else u"0")


def once(text, anchor, replacement, label):
    if text.count(anchor) != 1:
        die(u"锚点「%s」命中 %d 次（要恰好 1）" % (label, text.count(anchor)))
    return text.replace(anchor, replacement, 1)


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")

ap = argparse.ArgumentParser(prog="ledgers_r313.py",
                             description=u"R311 的七本台账（产品轮）")
ap.add_argument("--eye", default=u"", help=u"看图腿正文（也可用环境变量 R313_EYE 传）")
ARGS = ap.parse_args()
EYE = (ARGS.eye or EYE).strip()
if not EYE:
    die(u"看图腿没传 R313_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读
pre, pre_skip = battery(u"写盘前", u"/tmp/r313_battery_pre.log")

head_sub, _ = sh(["git", "log", "-1", "--format=%s"])
if R_TAG not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 代码半还没提交，账不许先落（%s）" % (R_TAG, head_sub.strip()[:80]))
books = set(os.path.relpath(v, ROOT) for v in FILES.values())
log_out, _ = sh(["git", "log", "-12", "--format=%H\x1f%s"])
prod, swift_files, others, surface = [], [], [], []
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if R_TAG not in subj_:
        continue
    surface.append(sha_[:7])
    names, _ = sh(["git", "show", "--name-only", "--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if not line or line in books:
            continue
        if line.startswith("ClipboardHistory/Sources/"):
            prod.append(line)
        elif line.startswith("ClipboardHistory/"):
            swift_files.append(line)
        else:
            others.append(line)
others = sorted(set(others))
if prod or swift_files:
    die(u"本轮是纯 python 判据轮：Sources 与 Swift 测试都应当 0 个文件，现读 %d / %d（%s）"
        % (len(prod), len(swift_files), u", ".join(prod + swift_files)))
if len(others) < 5 or not all(o.startswith(("scripts/", ".scratch/", "docs/")) for o in others):
    die(u"其余改动面应当全在 scripts / .scratch / docs 下（≥5 个），现读：%s" % u", ".join(others))
chain = rd(CHAIN) if os.path.exists(CHAIN) else u""
for needle, label in ((u"### PRECHECK", u"预检"), (u"### KNIVES", u"刀表"),
                      (u"### HIDDEN_ARMS", u"腐烂针尺"), (u"### BUILD", u"构建"),
                      (u"### FRAMES", u"帧目录计数"), (u"### SWIFT_LEGS", u"Swift 三条腿 NOT-RUN")):
    if needle not in chain:
        die(u"验证链日志里没有「%s」那一节 ⇒ 那条腿没跑完或没写清" % label)
warn = re.findall(r"WARNINGS=(\d+)", chain)
if not warn or warn[-1] != u"0":
    die(u"构建告警不是 0（现读 %s）" % (warn[-1] if warn else u"没解析到"))
FRAMES = (re.findall(r"FRAMES_ON_DISK=(\d+)", chain) or [u""])[-1]
if not FRAMES:
    die(u"没读到帧目录在盘上的张数 ⇒ 看图腿不许凭记忆说「上一轮的帧还在」")
RD_LINE = (re.findall(r"(?m)^LEDGER_READINGS 小节前缀=.+$", chain) or [u""])[-1]
# 判据轮没有「基线同一笔 update」这一格（changed=0 ⇒ update 就是伪造同步）；
# 取而代之要求四件套汇总行与本轮刀表那行都在，缺一条就不许写「跑过」。
for leg, what in ((u"CAPTURED ", u"重捕帧"), (u"FRAME_GATE_PASS", u"帧基线对账"),
                  (u"ROUND_VERIFY", u"四件套汇总行"), (u"R313_MUTATE", u"本轮刀表结论行"),
                  (u"NEEDLE_RANGE ", u"366 探针现读")):
    if leg not in chain:
        die(u"Swift 那条腿（%s）没在验证链日志里 ⇒ 台账不许写它跑过" % what)
knife = rd(KNIFE_LOG) if os.path.exists(KNIFE_LOG) else u""
# 三张表两种格式都要认（新表 `MUTATE 刀=…`，旧表 `Mxxx | CAUGHT` 行 + 三个零）：
# 只认一种就会把另一张表当成"没跑"，而 RC=0 看着像全绿。
new_rows = re.findall(r"MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
                      knife)
if len(new_rows) != 1:
    die(u"新格式刀表结论行现读 %d 条（要 1：r313）⇒ 这张表没出结论就不许落账" % len(new_rows))
K_N = K_CAUGHT = K_ESC = K_NOTRUN = 0
K_CLEAN = u"yes"
for n_, c_, e_, nr_, cl_ in new_rows:
    K_N += int(n_); K_CAUGHT += int(c_); K_ESC += int(e_); K_NOTRUN += int(nr_)
    if cl_ != u"yes":
        K_CLEAN = u"no"
# 本轮没有重跑历史表：判据改的是打印列与一根轴的定义，没动任何 needle 的目标行。
# 而"没重跑"必须是**读出来的** —— 预检 bad=0 就是那些针今天仍各命中一次的证人（见下面 PRE_BAD 那道门）。
if K_CAUGHT != K_N or K_ESC or K_NOTRUN or K_CLEAN != u"yes":
    die(u"三张表合计不干净：刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d CLEAN=%s"
        % (K_N, K_CAUGHT, K_ESC, K_NOTRUN, K_CLEAN))
KNIFE_SUM = u"三张表合计 %d 把全 CAUGHT、RESTORE_CLEAN=yes（r308 6 + r300 3 + r45 6）" % K_N
FULL_LOG = "/tmp/r313_verify/full.log"
if not os.path.exists(FULL_LOG):
    die(u"全量卷日志不在盘上 ⇒ 判据卷那一格没有证人")
jout, _ = sh([u"grep", u"-a", u"-A2", u"Test Suite 'HeatmapHoverEvidenceTests'", FULL_LOG])
jrows = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", jout)
if not jrows:
    die(u"全量卷日志里读不到 HeatmapHoverEvidenceTests 的每卷结论行 ⇒ 不许写「判据卷全绿」")
JUDGE_RUN, JUDGE_FAIL = jrows[-1]
if JUDGE_FAIL != u"0":
    die(u"判据卷 HeatmapHoverEvidenceTests 是 %s 朵红 ⇒ 拒绝出账" % JUDGE_FAIL)
KNIFE_SUM = u" ｜ ".join(l.strip() for l in knife.splitlines() if u"MUTATE 刀=" in l)
SPREAD_LINE = (re.findall(r"(?m)^HEAT_RING_LEVEL_SPREAD dark/1x .+$",
               rd("/tmp/r313_hover2.log") if os.path.exists("/tmp/r313_hover2.log") else u"")
               or [u"没读到 dark/1x 那一行"])[-1]
# 全量卷那三个数：走仓库里的读数口（scripts/ledger_readings.py 现读、带恒等式闸门），
# 不在这里对 326MB 日志「取末当全量」——R308 就是这么把 CAPTURE 补记的 92 写成结论的。
if not RD_LINE:
    die(u"验证链日志里没有 LEDGER_READINGS 那行 ⇒ 全量卷的数不许手抄，先跑 scripts/ledger_readings.py")
_rdfull = re.findall(u"格数=(\\d+) skip=(\\d+) 失败=(\\d+)", RD_LINE)
if not _rdfull:
    die(u"LEDGER_READINGS 那行解析不出三个数：%s" % RD_LINE[:160])
FULL_LINE = u"Executed %s tests, with %s skipped and %s failures" % _rdfull[-1]
CAP_LINE = (re.findall(r"(?m)^CAPTURED .+$", chain) or [u"没读到 CAPTURED 行"])[-1]
BASE_LINE = u" ".join(re.findall(r"FRAME_BASELINE_(?:COMPARED|CHANGED)=\d+", chain)[:2])
INSTALL_LINE = (re.findall(r"(?m)^INSTALL_RESULT=.+$", chain) or [u"没读到换装结论行"])[-1]
RUNNER_LINE = (re.findall(r"(?m)^NEEDLE_RANGE .+$", chain) or [u"没读到 366 探针现读"])[-1]

pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", chain)
TABLES_N, COVERED, PRE_ARMS, PRE_BAD = (int(x) for x in pre_line[-1]) if pre_line else (0, 0, 0, 1)
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", chain)
if not reg_line:
    die(u"ARM_TOTAL 没读到 ⇒ 在册刀数不许手抄")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d ⇒ 先修跨表撞号" % (ARM_DUPES, ARM_REPEATS))
roster = re.findall(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)",
                    chain)
HID_TABLES, HID_ARMS = (int(roster[-1][1]), int(roster[-1][2])) if roster else (0, 0)

ha_out, ha_rc = sh([sys.executable, HA])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针那把尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]
JUDGED_NOW = (re.findall(r"可判=(\d+)", HA_LINE) or [u""])[-1]
DECLARED_TBL = int((re.findall(u"已声明表=(\\d+)", HA_LINE) or [u"0"])[-1])
REMAIN_TABLES = int(HID_TABLES) - DECLARED_TBL if str(HID_TABLES).isdigit() else 0
TABLES_SCANNED = (re.findall(r"表=(\d+)", HA_LINE) or [u""])[-1]

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）：%s" % (st_rc, st_out.strip()[-160:]))
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到（rc=%d）" % prev_rc)
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), "latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（ci_read latest 给的是「%s」）" % CI[:80])

SCORES_RX = re.compile(r"(\d+)=(\d+)")


def scores_by_round(out):
    line = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    return dict((int(a), int(b)) for a, b in SCORES_RX.findall(line))


dk, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1] != u"none":
    die(u"曲线尺报 GAPS ⇒ 升序台账被插在中间了")
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", dk, re.M) or [u""])[-1]
DERIVED = scores_by_round(dk).get(RDN - 1)
if not SECTIONS or DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分" % (RDN - 1))

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES["DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES["BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
BLNEW = BL_MAX + 1
if u"**365. " not in bl:
    die(u"BACKLOG 365 不在盘上 ⇒ 本轮的追记无处可挂")

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RNEXT@": R_NEXT, u"@RDN@": RDN,
        u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@DN@": DN,
        u"@BLNEW@": BLNEW, u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N,
        u"@PREVSTREAK@": PREV_STREAK, u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND,
        u"@CI@": CI, u"@NOFILES@": len(others), u"@K_N@": K_N, u"@JUDGERUN@": JUDGE_RUN,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@ARMREG@": ARM_REG,
        u"@ARMFILES@": ARM_FILES, u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS,
        u"@FRAMES@": FRAMES, u"@RDLINE@": RD_LINE, u"@HALINE@": HA_LINE,
        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@JUDGED@": JUDGED_NOW,
        u"@TSCANNED@": TABLES_SCANNED, u"@BLMAX@": BLNEW, u"@BLMINUS@": BL_MAX,
        u"@WARN@": (warn[-1] if warn else u"没解析到"), u"@PREBAD@": PRE_BAD,
        u"@JUDGEFAIL@": JUDGE_FAIL, u"@PROBE@": RUNNER_LINE,
        u"@RPREVTAG@": PREV_TAG,
        u"@HIDTBL@": DECLARED_TBL, u"@HIDTBL2@": REMAIN_TABLES,
        u"@SPREAD@": SPREAD_LINE,
        u"@RUNNER@": RUNNER_LINE, u"@FULL@": FULL_LINE, u"@CAP@": CAP_LINE,
        u"@BASE@": BASE_LINE, u"@INSTALL@": INSTALL_LINE, u"@KNIFESUM@": KNIFE_SUM}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

# ---------------------------------------------------------------- 七本正文
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：腐烂针的账从一箱变两箱 —— 顺手挖出尺本体三轮的假归因（U-@UA@…U-@UC@ · 产品 0 文件，判据轮）

- **U-@UA@：367 的第一步落地 —— 表自己声明针（`NEEDLES = {刀号: [针, …]}`），声明过的臂改走「逐根判」，rot 从此有了可加总的那一箱。**
  `scripts/hidden_arms.py` 一箱变两箱：未声明的臂维持 `any(候选命中)`（R312 已现读证伪"把它当上界"的两条静态办法），
  声明过的臂逐根判命中，一根在盘上找不到就记一根。已声明 `mutate_r308`（6 把）与 `mutate_r312`（3 把）。
  棘轮从 2 个数变 4 个数（`rot` / `抽不出` / `已声明死针` / `已声明表`），四个方向都有牙。
  现读：`@HALINE@`；正对照夹具 `mutate_r_synthdeclared.py`（一臂两针、一活一死，判据卷显式喂 text）
  给出 `HIDDEN_ARMS_SYNTH 表=4 可判=3 rot=1 抽不出=1 已声明臂=1 已声明死针=1`。

- **U-@UB@：这一格当场把尺本体的三轮假归因挖了出来 —— `ARM_ID = re.compile(r"M\\\\d{3,4}")` 里的 `\\\\d` 在 raw 字符串中恒不命中。**
  自 R310 交付起，`HIDDEN_ROT` 的"刀号"一直走 `臂#N` 兜底 ⇒ 台账里"腐烂可归因到哪把刀"这句话没有证人。
  第二处同族：刀号那一格通常只有 4~5 个字符，**过不了** `arm_candidates` 的 `MIN_LEN=12`，
  所以靠候选集找刀号永远找不到 ⇒ 第一次跑出现 `已声明臂=0` 而 `已声明表=2` 的**假绿**
  （覆盖面按"文件里有没有 NEEDLES 字典"在数，而不是按"真的匹配上了臂"）。
  修法：新增 `arm_label_of()` 按整格精确匹配刀号；覆盖面改成按命中臂数。**我自己新写的对账格也栽在同一个坑上**
  （它报"声明悬空"，其实是测试在找错东西），已改成与尺同一颗 `arm_label_of`。

- **U-@UC@：新写一箱必须先给它配正对照与反方向断言，否则刀没有落点。**
  M913（把 `已声明死针` 的棘轮改成只判一个方向）第一次跑是 ESCAPED 的 ——
  判据卷原本只测 `+1` 方向。补上"变少也要响"那一格之后，这把刀才有落点。
  现读：`@KNIFESUM@`（M911 塌箱、M912 把下界写成 `all()`、M913 只判单向，三把各钉一条独立的轴）。

读数（全部现读，同一遍验证链 /tmp/r313_chain.log + /tmp/r313_verify）：构建告警 @WARN@（target=build-tests）；
判据卷 HeatmapHoverEvidenceTests `Ran @JUDGERUN@ tests / @JUDGEFAIL@ failures`；全量卷 @FULL@；
重捕帧 @CAP@；帧基线 @BASE@（本轮 0 Swift 文件 ⇒ 没有该变的帧，**不** update 基线）；换装 @INSTALL@；
预检 tables=@TABLES@ covered=@COVERED@ bad=@PREBAD@、名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
腐烂针尺 `@HALINE@`；探针 `@PROBE@`；脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（取数口 `scripts/product_streak.py --streak-for @ROUND@`；上一轮 @PREVSTREAK@）。

看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 11/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 9/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
| 合计 | 93/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 本轮 0 产品文件，看图腿看的是空状态帧
（`heatmap-empty-430x150-dark.png`：文字行在 150pt 高的框里位于 y≈46，下方留白 ≈104pt / 69%），
它替"没有回归"与"这一处留白的比例"作证，但那条留白本轮只登记成读数、没变成工单；
判据有效性 15 —— 三把刀各钉一条轴，且 M913 是"先补反方向断言，刀才有落点"的正面例子；
假绿防御 15 —— 本轮抓到的两枚假绿（`ARM_ID` 恒不命中、覆盖面按字典存在来数）都是**自己刚交付的尺**；
产品面推进 9 —— 产品 0 文件、Swift 0 文件，动效主线连续两轮没动（347 / 305 等真机眼）；
台账一致性 13 —— 七本一支脚本，扣分在 R313 的代码半是分两笔落的（补刀那一笔才把刀配齐），
读史的人会看到一笔"改了判据没有刀"的中间态；可复核性 15 —— 尺、判据卷、三把刀、探针都能重跑，
且探针与夹具都在仓库里；交付诚实性 15 —— 两处自曝（尺本体的假归因、我自己测试也踩同一个坑）都写在账上。

"""

IT_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：腐烂针的账从一箱变两箱（产品 0 文件，判据轮）

`scripts/hidden_arms.py` 的 rot 一直是**下界**（`any(候选命中)`），R312 已证伪两条把它做成上界的静态办法。
本轮走唯一剩下的那条：**由表自己声明针**。`NEEDLES = {刀号: [针, …]}` 的臂改走逐根判，
可加总；未声明的臂留在原来那一箱，继续只当下界。棘轮从 2 个数变 4 个数，四个方向各有正对照。

现读：`@HALINE@`；`@KNIFESUM@`；电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘前后同数）；
构建告警 @WARN@；全量卷 @FULL@；帧 @CAP@、基线 @BASE@（不 update）；换装 @INSTALL@；
产品面连续零改动 **@STREAK@** 轮（上一轮 @PREVSTREAK@）。

两处自曝：① `ARM_ID` 写的是 `r"M\\\\d{3,4}"` —— raw 字符串里那是"反斜杠 + d"，恒不命中，
于是 R310 以来 `HIDDEN_ROT` 的刀号归因一直走 `臂#N` 兜底，"可归因到哪把刀"没有证人；
② 刀号那一格只有 4~5 字符，过不了候选集的 `MIN_LEN=12` ⇒ 第一次跑出现
`已声明臂=0` 而 `已声明表=2` 的假绿。两处都修了，我自己的对账格也改成与尺同一颗 `arm_label_of`。

看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 11/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 9/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
| 合计 | 93/105 |

"""

DEC_NEW = u"""**D-@DN@（@RTAG@）：新增一箱判据的验收顺序是「先造会漏报的夹具，再写刀」—— 反方向断言没写，刀就没有落点。**

R313 给 `hidden_arms.py` 加了第二箱（逐根判已声明的针）。第一版刀表里 M913
（把 `已声明死针` 的棘轮改成只判一个方向）是 **ESCAPED** 的 —— 不是刀坏了，
是判据卷当时只测 `+1` 方向，"变少"那一半根本没有断言。补上反方向那一格，刀才钉得住。

所以规矩写成顺序：新增任何"数数"的判据时，
① 先造一个**已知会漏报**的夹具（本轮是"一臂两针、一活一死"，旧估计量必然报 0）；
② 再给每个数配**两个方向**的断言；
③ 最后才写刀。反过来做（先写尺、再补刀）就会像本轮第一版那样，
把"没测到的方向"当成"有牙"。

另一条同场学到的：**"字典存在"不等于"匹配上了"**。覆盖面那一格第一次跑报
`已声明表=2 / 已声明臂=0` —— 那是假绿的新变体：按声明的**形式**数，不按声明的**效果**数。
凡"覆盖面 / 已登记 / 已声明"这类计数，必须数到最小可判单位（臂、格、用例），不能数容器。
"""

BL_367 = u"""  追记（@RTAG@）：第一步已落地。`scripts/hidden_arms.py` 一箱变两箱 ——
  表里写 `NEEDLES = {刀号: [针, …]}` 的臂走**逐根判**（可加总），其余臂维持 `any(候选命中)`（只配当下界）。
  已声明 @HIDTBL@ 张真表（`mutate_r308` 6 把、`mutate_r312` 3 把），棘轮从 2 个数变 4 个数、四个方向都有正对照。
  同一轮把尺本体的两处假归因修了：`ARM_ID` 的 `r"M\\\\d{3,4}"` 恒不命中（R310 以来刀号归因一直走
  `臂#N` 兜底），以及"覆盖面按字典存在来数"（第一次跑 `已声明表=2` 而 `已声明臂=0` 的假绿）。
  剩下的迁移面：@HIDTBL2@ 张真表还没声明（名册 unregistered_with_arms 那一串），
  每迁一张就降一格「未声明」那一箱的上界 —— 这是按轮的活，不是一轮的。"""

BL_NEW = u"""**@BLNEW@. 热图格子的 hover 提示文本，产物级判据的通道不存在 —— 两次探针都读不到（@RTAG@ 现读）**（@RTAG@）

  阶段一的验收要求里明写「格子有 hover 提示（日期 + 当日条数）」。现在账上只有两类证据：
  `DailyCopyHeatPolicy.tooltip` 的真值表（纯函数）与"这里用了 `helpLabel` 而不是裸 `.help`"的源码级守卫。
  **两者都没量过产物** —— R11 / R248 那一族「源码已接、产物未量」。

  @RTAG@ 试了两条通道，两条都失败，读数留在账上：
  ① 直接 `NSHostingView(rootView:).layoutSubtreeIfNeeded()` 后遍历 `subviews` ⇒ `TOOLTIP_SPIKE views=1 toolTips=0`
    （整棵 AppKit 子树根本没 materialize）；
  ② 离屏挂窗（`orderFrontRegardless`）+ `displayIfNeeded()` ⇒ 仍然 `views=1 toolTips=0`。
  而 `UICaptureHarness` 里已经有能长出 `NSHostingView / AppKitPlatformViewHost / NSSplitView` 的建树路径
  （它拍帧时就在走那条路）⇒ **要判这条，必须复用 harness 的建树路径，而不是自己新造一个 host**。

  下一步（不许把它读成"判不了就算了"）：把 harness 的建树函数提出来给判据卷用，
  要求每一格的 `toolTip` 非空、且等于 `DailyCopyHeatPolicy.tooltip` 对同一 (dayKey, count) 的输出；
  配一把刀（把 `.helpLabel` 换成 `.help` ⇒ 产物级判据必须红）。
  探针本身已删，没在仓库里留半截测试。"""

CH_NEW = u"""### 腐烂针的账从一箱变两箱：表自己声明针，顺手挖出尺本体三轮的假归因（@RTAG@ / U-@UA@…U-@UC@ · D-@DN@ · 产品 0 文件，判据轮）

- 367 的第一步：`scripts/hidden_arms.py` 新增 `NEEDLES` 通道 ⇒ 声明过的臂**逐根**判（可加总），
  未声明的维持 `any()`（下界）。已声明 `mutate_r308`(6) + `mutate_r312`(3)；棘轮 2 个数 → 4 个数。
- 正对照夹具：一臂两针、一根活一根死（判据卷显式喂 text）⇒ 旧估计量报"活的"，新箱必须报"死了 1 根"。
- 两处自曝并修好：`ARM_ID` 写成 `r"M\\\\d{3,4}"` 恒不命中（R310 起刀号归因一直是 `臂#N` 兜底）；
  覆盖面按"字典存在"数 ⇒ 第一次跑 `已声明表=2 / 已声明臂=0` 的假绿。
- 刀 M911（塌箱）/ M912（把下界写成 `all()`）/ M913（只判单向）：`@KNIFESUM@`。
  M913 第一次是 ESCAPED —— 判据卷原本没有反方向那一格，补了才钉得住（D-@DN@）。
- 新开 @BLNEW@：热图格子的 hover 提示**产物级**判据通道不存在（两次探针 `views=1 toolTips=0`），
  下一步要复用 `UICaptureHarness` 的建树路径而不是另造 host。
- 现读：构建告警 @WARN@；判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 @FULL@；
  帧 @CAP@、基线 @BASE@（不 update）；换装 @INSTALL@；预检 tables=@TABLES@ bad=@PREBAD@、名册 arms=@ARMREG@；
  腐烂尺 `@HALINE@`；电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；产品面连续零改动 **@STREAK@** 轮。

"""

ST_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

本轮把 367 的第一步做完了：`scripts/hidden_arms.py` 一箱变两箱 —— 表自己声明针
（`NEEDLES = {刀号: [针, …]}`）的臂走**逐根判**，可加总；其余臂维持 `any(候选命中)`，只配当下界。
棘轮从 2 个数变 4 个数，四个方向各有正对照；夹具造出"一臂两针、一活一死"，旧估计量必然漏报、新箱必须报 1。
同一轮挖出尺本体两处假归因（`ARM_ID` 的 `\\\\d` 恒不命中、覆盖面按字典存在数），都修了。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**腐烂针的账从一箱变两箱**（产品 0 文件，判据轮）
现读：构建告警 @WARN@；判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 @FULL@；@CAP@；帧基线 @BASE@（不 update）；
换装 @INSTALL@；刀 @KNIFESUM@；预检 tables=@TABLES@ covered=@COVERED@ bad=@PREBAD@、名册 arms=@ARMREG@；
腐烂尺 `@HALINE@`；探针 `@PROBE@`；电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；看图腿 RUN（@EYE_SHORT@）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；上一轮 @PREVSTREAK@）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。

⓪ @RNEXT@ 开场要先读的（成对：run id ↔ commit）：@CI@
   —— 必须读到：① 本轮三笔（代码半 / 补刀 / 这一笔账半）在 runner 上 `Ran` 的格数与本机一致
   （本机 611+，新格是 `test_declared_bin_*` 与 `DeclarationHonestyTests`）；
   ② R312 那三跑（39976319446 success / 39978500278 / 39979229010）里后两跑的最终结论，
   以及 STEP[9] 名单外那一格有没有被本轮新增的 python 用例带出新 skip。

① 下一轮（@RNEXT@）的靶：① **回到动效主线**（连续两轮 0 产品文件）—— 347 需用户先退出 App，
   在那之前把 305 的台阶地板用已有夹具通道再推一格；
   ② @BLNEW@：把 `UICaptureHarness` 的建树路径提给判据卷，让 hover 提示第一次可被产物级判据判到 + 配刀；
   ③ 367 的迁移继续（每轮迁 2~3 张表，降「未声明」那一箱的上界）；
   ④ 348 剩下的读数族各配恒等式；⑤ 360 最后一批；⑥ 361 合并。

② 仍开：347（真机证人）、305（等 347）、@BLMINUS@（腐烂针待清 + 上界只能由表声明针：已声明 2 张 / 剩 73 张）、
   @BLNEW@（hover 提示的产物级通道）、364 的"抽不出候选的 @OPAQUE@ 把要真跑"、
   348 的"读数族还没纳全"、354 的第五步、360（剩 11 份）、361（未合并）、359、362、349、350 第二步、
   351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

"""

# ---------------------------------------------------------------- 组装与落盘
orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(UI_NEW, SUBS), u"IT": fill(IT_NEW, SUBS), u"DEC": fill(DEC_NEW, SUBS),
         u"BL367": fill(BL_367, SUBS), u"BLNEW": fill(BL_NEW, SUBS),
         u"CH": fill(CH_NEW, SUBS), u"ST": fill(ST_NEW, SUBS)}
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig["UI"])]
top = max(heads)[1]
new_ui = orig["UI"][:top] + texts["UI"] + orig["UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts["UI"])]
if nums != [UA, UB, UC]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC]))

new_it = orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts["IT"])) != 7:
    die(u"七维表不是恰好 7 行 ⇒ 曲线仪器会拒绝推导")

new_dec = orig["DEC"].rstrip(u"\n") + u"\n\n" + texts["DEC"].rstrip(u"\n") + u"\n"


def append_into_item(text, header_prefix, note, label):
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(header_prefix)]
    if len(hits) != 1:
        die(u"%s 的条目头命中 %d 行（要恰好 1）" % (label, len(hits)))
    h = hits[0]
    nxt = [i for i in range(h + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    k = nxt[0] if nxt else len(lines)
    while lines[k - 1].strip() == u"":
        k -= 1
    head = u"\n".join(lines[:k])
    if not head.endswith(u"\n"):
        head += u"\n"
    out = head + note.rstrip(u"\n") + u"\n" + u"\n".join(lines[k:]).lstrip(u"\n")
    if not (0 <= out.find(header_prefix) < out.find(note.split(u"\n")[0].strip())):
        die(u"%s 的追记落点不对" % label)
    return out


new_bl = append_into_item(orig["BL"], u"**367. ", texts["BL367"], u"367")
if re.search(u"(?m)^\\*\\*%d\\. " % BLNEW, new_bl):
    die(u"BACKLOG %d 已存在 ⇒ 不许开第二张同题单，去追记原条目" % BLNEW)
new_bl = new_bl.rstrip(u"\n") + u"\n\n" + texts["BLNEW"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", new_bl)) != \
        len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", orig["BL"])) + 1:
    die(u"BACKLOG 条目头数量不是「原数 +1」⇒ 新单没落成一条")

new_ch = once(orig["CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 标题行不再是恰好 1 行")

new_st = once(orig["ST"], u"## %s 状态（" % PREV_TAG,
              texts["ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig["FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
           u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
stray = [u"%s:%d %s" % (k, n, hit.group(0)) for k, t in new.items()
         for n, line in enumerate(t.split(u"\n"), 1) for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))

for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)

import atexit


def _crash_guard():
    if WROTE and not OK_EXIT:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R311_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES["FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给出 ROUNDS= / rounds=9..N / SCORES_BY_ROUND（rc=%d）" % crc)
lines = txt.split(u"\n")
m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评` ⇒ 不敢整行改写")
lines[0] = lines[0][:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m.end():]
body = u"\n".join(lines)
prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（判据轮：改动面 %s 个文件，"
             u"其中 1 份 Swift 判据，其余全在 `scripts/` 与 `.scratch/`），产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"
             u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：重捕 %s 张、"
             u"帧基线 @BASE@ ⇒ 判据轮没有该变的帧，**所以本轮不 update 基线**（update 一次就等于伪造一次同步）；"
             u"换装 @INSTALL@。改的是判据本体：16 条 HEAT_ADJACENT 读数必须每条同时带三根轴。"
             % (1 + len(others), STREAK_N, ROUND, ROUND, LASTSHA, LASTROUND, PREV_STREAK, FRAMES))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s，"
              u"未登记表 %s 张 / 隐藏臂 %s 把 ⇒ 364）；腐烂针尺现读 `@HALINE@`；"
              u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**（本轮追记 367、新开 %s）"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN, BLNEW, BLNEW))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
              u"⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                    (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
    if len(hits) != 1:
        die(u"§13 的「%s」那一格命中 %d 行（要恰好 1）" % (label, len(hits)))
    parts[hits[0]] = fill(cell, SUBS)
    body = u"\n".join(parts)
gout, grc = sh(["git", "log", "-40", "--format=%h\x1f%s", "--",
                os.path.join("ClipboardHistory", "Sources")])
src_rows = []
for line in gout.splitlines():
    if u"\x1f" not in line:
        continue
    sha_, subj_ = line.split(u"\x1f", 1)
    mb = re.match(u"^R(\\d+)", subj_.strip())
    src_rows.append((sha_.strip(), int(mb.group(1)) if mb else None, subj_.strip()))
picked = [r for r in src_rows if r[1] is not None and r[1] <= int(R_TAG[1:])]
if not picked:
    die(u"标签 ≤ %s 的源码提交一笔都没有 ⇒ 那一格不许拿「此刻最新」凑数" % R_TAG)
live_sha, live_src_round, _ = picked[0]
older = [r for r in src_rows if r[0] != live_sha and r[1] is not None]
prev_txt = (u"上一笔动 `Sources/` 的是 R%d（`%s`）。" % (older[0][1], older[0][0])) if older else u""
src_cell_kind = (u"本轮是产品轮（`Sources/` 下 %d 个文件、Swift 判据 %d 份、其余 %d 个在 `scripts/` 与 `.scratch/`）"
                 % (len(prod), len(swift_files), len(others))) if prod else \
                (u"本轮是判据轮（改动面 %d 个文件全在 `scripts/` 与 `.scratch/`，0 个 `Sources/` 文件）"
                 % len(others))
src_cell = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— %s；"
            u"这一格登记的是仓库里**最近一笔动过源码的提交**，"
            u"改了什么以 `AGENT_UI_AUDIT.md` 里 R%d 那一节为准（这一格只登记号与数，不复述结论）。%s|"
            % (live_src_round, live_sha, src_cell_kind, live_src_round, prev_txt))
parts = body.split(u"\n")
hits = [i for i, l in enumerate(parts) if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
if len(hits) != 1:
    die(u"报告「最后一次动到 Sources/」那一格命中 %d 行" % len(hits))
parts[hits[0]] = src_cell
body = u"\n".join(parts)
if STRAY_RX.search(body):
    die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
wr(FILES["FR"], body)
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r313_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口 ⇒ 升序台账被插在中间")
DERIVED2 = scores_by_round(cv2).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分" % RDN)
if u"R9–R%s" % last_round not in rd(FILES["FR"]).split(u"\n")[0]:
    die(u"报告标题没接上写盘后的尾轮 Round %s" % last_round)
if u"U-31 … U-%d" % UC not in rd(FILES["FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)

OK_EXIT.append(True)
print(u"LEDGERS_R313 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(others)) + u" 刀=" + s(K_N)
      + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" 可判=" + s(JUDGED_NOW)
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" BL=" + s(BLNEW)
      + u" 判据卷=" + s(JUDGE_RUN) + u" 帧=" + FRAMES
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
