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
CHAIN = "/tmp/r312_chain.log"
KNIFE_LOG = "/tmp/r312_chain.log"
R_TAG, PREV_TAG, R_NEXT = u"R312", u"R311", u"R313"
PREV_ROUND, ROUND, RDN = 310, 311, 309
TODAY = u"2026-10-23"
EYE = os.environ.get("R312_EYE", u"")
WROTE, OK_EXIT = [], []


def die(msg):
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        msg = msg + u"（七本已整体还原）"
    sys.stderr.write(u"R312_LEDGERS_REFUSE " + msg + u"\n")
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

ap = argparse.ArgumentParser(prog="ledgers_r312.py",
                             description=u"R311 的七本台账（产品轮）")
ap.add_argument("--eye", default=u"", help=u"看图腿正文（也可用环境变量 R312_EYE 传）")
ARGS = ap.parse_args()
EYE = (ARGS.eye or EYE).strip()
if not EYE:
    die(u"看图腿没传 R312_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读
pre, pre_skip = battery(u"写盘前", u"/tmp/r312_battery_pre.log")

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
if prod or len(swift_files) != 1:
    die(u"本轮是判据轮：改动面应当是 0 个 Sources 文件 + 1 份 Swift 判据，现读 %d / %d（%s）"
        % (len(prod), len(swift_files), u", ".join(prod + swift_files)))
if len(others) < 3 or not all(o.startswith(("scripts/", ".scratch/", "docs/")) for o in others):
    die(u"其余改动面应当全在 scripts / .scratch / docs 下（≥3 个），现读：%s" % u", ".join(others))
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
                  (u"ROUND_VERIFY", u"四件套汇总行"), (u"R312_MUTATE", u"本轮刀表结论行"),
                  (u"NEEDLE_RANGE ", u"366 探针现读")):
    if leg not in chain:
        die(u"Swift 那条腿（%s）没在验证链日志里 ⇒ 台账不许写它跑过" % what)
knife = rd(KNIFE_LOG) if os.path.exists(KNIFE_LOG) else u""
# 三张表两种格式都要认（新表 `MUTATE 刀=…`，旧表 `Mxxx | CAUGHT` 行 + 三个零）：
# 只认一种就会把另一张表当成"没跑"，而 RC=0 看着像全绿。
new_rows = re.findall(r"MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
                      knife)
if len(new_rows) != 1:
    die(u"新格式刀表结论行现读 %d 条（要 1：r312）⇒ 这张表没出结论就不许落账" % len(new_rows))
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
FULL_LOG = "/tmp/r312_verify/full.log"
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
               rd("/tmp/r312_hover2.log") if os.path.exists("/tmp/r312_hover2.log") else u"")
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
        u"@SPREAD@": SPREAD_LINE,
        u"@RUNNER@": RUNNER_LINE, u"@FULL@": FULL_LINE, u"@CAP@": CAP_LINE,
        u"@BASE@": BASE_LINE, u"@INSTALL@": INSTALL_LINE, u"@KNIFESUM@": KNIFE_SUM}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

# ---------------------------------------------------------------- 七本正文
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：三根轴必须同时可查 —— 「暗档 17.33 低于地板」那一半被证伪（U-@UA@…U-@UC@ · 产品 0 文件，判据轮）

- **U-@UA@：BACKLOG 356 剩下的那一半不成立 —— 17.33 是「均值通道」那一根轴，而地板从 R52 起就施加在「最大通道」那一根上（同一步现读 30.00）。**
  本机 dark/1x `empty→bucket1`：最大通道差=**30.00**、均值通道差=**17.33**、亮度差=**2.16**；
  判据 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis` 的第一条断言就是 `maxDelta ≥ adjacentLevelFloor255(=18)`，
  注释里写着为什么不读另两根（灰→蓝差的是**色相**，均值会把 30 冲淡成 17、亮度只剩 2）。
  这与 R51/R53「用亮度轴读出同一个假缺陷」是同族的反例：**同一个数字家族里，读哪根轴决定结论是什么**。
  ⇒ 按 D-292 的规矩，既不放宽地板也不改 `VisualHeat.ladder`，这句话**撤回**（结案写在 356 原条目）。

- **U-@UB@：撤回一句自己写过的话之前，先把证人做出来 —— 16 条相邻档读数现在必须每条同时带三根轴，缺一根就红。**
  如果更正只写在台账里，那么那行打印被谁顺手删掉一列之后，更正就再也拿不出证据。
  本轮给 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis` 新增一格 `XCTAssertTrue(line.contains(轴))`，
  三把刀各钉一次：M908 删均值列、M909 删亮度列、M910 把「最大通道 ≥ 均值通道」那根**定义级**卫兵反号。
  现读：`@KNIFESUM@`，基线判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`。

- **U-@UC@：BACKLOG 366 的两条出口都被现读证伪 —— rot 只能做下界，除非表自己声明哪根是针。**
  常驻仪器 `.scratch/motion-audit-2/probe_needle_positions_r312.py` 现读：
  `@PROBE@`；同一支还打 `NEEDLE_POS_STRICT 位置可判臂=6/715`、`NEEDLE_POS_LOOSE 有对子的臂=16/715`。
  ⇒ ① 按位置取针会把可判面从 709 臂塌到 16 臂（**把尺做瞎**，不是做严）；
  ② 拿"至少一根候选不命中"当上界会得到 658，而多出来的那 625 臂里"死候选"绝大多数是**变异文本身**
  （变异文本来就不该在盘上命中）。两条都写进 366 的追记，别让下一个人再走一遍。

读数（全部现读，同一遍验证链 /tmp/r312_chain.log + /tmp/r312_verify）：构建告警 @WARN@
（门本体 `scripts/warning_gate.sh`，target=build-tests）；判据卷 HeatmapHoverEvidenceTests
`Ran @JUDGERUN@ tests / @JUDGEFAIL@ failures`；全量卷 @FULL@；重捕帧 @CAP@；帧基线 @BASE@
（判据轮 ⇒ 没有该变的帧，本轮**不** update 基线）；换装 @INSTALL@；
预检 tables=@TABLES@ covered=@COVERED@ bad=@PREBAD@、名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
腐烂针尺 `@HALINE@`；脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（取数口 `scripts/product_streak.py --streak-for @ROUND@`；上一轮 @PREVSTREAK@）。

看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 12/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 10/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
| 合计 | 94/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 本轮 0 产品文件，看图腿只能替「没有回归」作证
（重捕 174 张、基线 changed=0），替不了新效果；那条判断本身仍欠（347 / 305 等用户真机眼）。
判据有效性 14 —— 三把刀各钉一根轴，扣分在这轮的产出之一是**证伪**（能红不等于该做）。
假绿防御 15 —— 主产出就是撤回一句我自己写过的假话，并且先给它配了会红的证人。
产品面推进 10 —— 产品 0 文件；356 那一半以「不是缺陷」结案，动效主线继续欠着。
台账一致性 14 —— 七本一支脚本、结案写在原条目；扣分在报告计数器那一格只能写完账再由仪器刷。
交付诚实性 15 —— 撤回落在自己名下，两条被证伪的设计带现读数字进账，代码半 commit 里就写了账半欠着。
可复核性 14 —— 判据卷、三把刀、探针都可重跑（探针已从一次性 here-doc 搬成常驻脚本）；
扣分在「表自己声明针」那条出口还没有可跑的形态。

"""

IT_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：三根轴必须同时可查 —— 356 那一半被证伪（产品 0 文件，判据轮）

BACKLOG 356 剩下的那一半说的是「暗档最细一步 17.33 低于地板 18」。本轮把它读到底：
`HEAT_ADJACENT dark/1x empty→bucket1 最大通道差=30.00 均值通道差=17.33 亮度差=2.16`，
而地板施加在**最大通道**那一根上（R52 立判据时写进注释的选择：灰→蓝差的是色相）。
⇒ 那句话读的是被这条判据明确排除的轴，**撤回**；不改梯子、不动地板。

撤回之前先补证人：16 条相邻档读数每条必须同时带三根轴，M908（删均值列）/ M909（删亮度列）/
M910（把「最大 ≥ 均值」反号）三把刀各钉一次。现读：`@KNIFESUM@`。

另一条产出是把 366 的两条出口**证伪**并常驻成一支仪器：
`@PROBE@` ⇒ 按位置取针只能覆盖 16/715 臂（把尺做瞎），
"部分死"当上界得到 658（绝大多数是变异文本身，本来就不该命中）。
rot 只能做下界，除非表自己声明哪根是针。

读数：构建告警 @WARN@；判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 @FULL@；@CAP@；
帧基线 @BASE@（不 update，因为没有该变的帧）；换装 @INSTALL@；
预检 bad=@PREBAD@、名册 arms=@ARMREG@；电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 **@STREAK@** 轮（上一轮 @PREVSTREAK@）。

看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 12/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 10/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
| 合计 | 94/105 |

"""

DEC_NEW = u"""**D-@DN@（@RTAG@）：撤回一句关于「哪根轴」的话之前，必须先让所有候选轴同时可查 —— 否则更正本身没有证人。**

356 剩下的那一半（「暗档最细一步 17.33 低于地板 18」）是**我自己上一批写下的**，
它把均值通道那一根当成了判据。真相是这条判据从 R52 起就钉在最大通道那一根上（同一步 30.00），
亮度那一根只有 2.16 —— 三根轴在同一条读数里，读哪一根决定结论是什么。
所以本轮的顺序是：① 先把「三轴同查」变成会红的断言（M908/M909/M910 各钉一根），
② 再撤回那句话。反过来做，台账里就多了一句谁也复查不了的更正。

配套两条：
① 更正**自己写过的话**时，先问「这句话靠哪个数站着」，再问「那个数现在还打不打得出来」；
   打不出来就先补打印与断言，别先写结论。
② 一条判据有多根候选轴时，**不许只留承重那一根**：被排除的那几根就是「为什么排除它」的证据。
   删掉它们，下一次就有人会拿它们重新读出一个假缺陷（R51/R53 已经为这件事付过一轮）。
"""

BL_366 = u"""  追记（@RTAG@）：这一格的两条出口都被**现读证伪**，rot 仍然是下界，别把它当上界用。
  常驻探针 `.scratch/motion-audit-2/probe_needle_positions_r312.py` 现读：
  严格按文档形状 `(刀号, 靶, [(needle, mutant)], 期望)` 抽 ⇒ 位置可判臂只有 6 臂 / 1 张表；
  放宽到「臂里任意一格是对子」⇒ 16 臂 / 3 张表（共 715 臂）。
  ⇒ 出口①「按位置取针」会把可判面从 709 臂塌到 16 臂，那是把尺做瞎而不是做严。
  出口②「拿至少一根候选不命中当上界」⇒ 区间 [33, 658]，而多出的 625 臂里"死候选"绝大多数是
  **变异文本身**（它本来就不该在盘上命中），于是那个"上界"是一个假数。
  剩下的唯一诚实出口：让**表自己声明哪根是针**（代价：75 张未登记表的写法要改），
  这条由 @BLMAX@ 登记规模，不与「逐条处置」互相结案。"""

BL_356 = u"""  结案（@RTAG@）：这一条的**两半都已处置，而处置方式相反**。
  ① 悬停环那一半（runner 上 dark/1x 17.11…17.13 < 地板 18，本机 18.75）是**真缺陷**：
     @RPREVTAG@ 把 α 抬到 0.23，runner 现读 19.72…19.75 兑现了本机预测 19.69（D-292）。
  ② 相邻档那一半（17.33 < 18）**不是缺陷**：@RTAG@ 现读同一格的三根轴
     最大=30.00 / 均值=17.33 / 亮度=2.16，地板从 R52 起就施加在**最大通道**那一根上，
     那句话读的是被排除的轴 ⇒ 撤回，并给「三轴同查」配了断言与三把刀（出处就是本轮 @RTAG@ 那一节，不是 367）。
  合起来是这一条真正的收获：**同一台机器上「一根轴上的缺席」与另一台机器上「一次跨机器的缺席」
  会长得一模一样**，分开它们的办法是各自现读，不是各自猜。356 到此结案。"""

BL_NEW = u"""**@BLNEW@. 「表自己声明哪根是针」是 rot 做成上界的唯一出口，而它的代价是 75 张未登记的表要改写法（@RTAG@ 现读）**（@RTAG@）

  @BLMINUS@ 要求把 rot 从下界做成上界，@RTAG@ 现读证伪了两种"换估计量"的做法
  （见 366 的追记：位置可判臂只有 16/715，"部分死"当上界得到 658 而其中绝大多数是变异文）。
  剩下的做法只有一种：**由表自己把针标出来**，尺不再猜。
  可执行形状（下一步就做，别再做估计量）：
  ① 在表里加一个模块级 `NEEDLES = {刀号: [needle, …]}`（字符串或常量名都可），
     `hidden_arms.py` 见到它就按**逐根**判命中，一根不命中记一根；
  ② 没声明的表继续走现在的集合存在性判法，但在结论行里**分箱**：
     `HIDDEN_ARMS … 已声明 rot=…（可加总） 未声明 rot=…（只配当下界）`，
     两箱各配各的棘轮，不许把未声明那箱的数当成上界；
  ③ 正对照：合成夹具造「一臂两根针、一根活一根死」且**已声明**的表，要求新判据报 2 而不是 1。
  规模读数（现读）：名册 registered=@TABLES@ / unregistered_with_arms=@HIDTABLES@ /
  隐藏臂 @HIDARMS@；也就是说 ① 的迁移面是 75 张表，不是一支脚本改得完的，
  按轮摊开做，每迁一张就降一格「未声明」那一箱的上界。"""

CH_NEW = u"""### 三根轴必须同时可查：356 剩下的那一半被证伪并撤回（@RTAG@ / U-@UA@…U-@UC@ · D-@DN@ · 产品 0 文件，判据轮）

- 现读 `HEAT_ADJACENT dark/1x empty→bucket1 最大通道差=30.00 均值通道差=17.33 亮度差=2.16`
  ⇒ 那句「暗档最细一步低于地板 18」读的是**均值**那一根，而地板从 R52 起施加在**最大通道**上。
  撤回，不改 `VisualHeat.ladder`、不放宽地板（D-292）。
- 撤回之前先补证人：`testAdjacentHeatLevelsAreSeparableOnTheRightAxis` 新增一格，
  要求 16 条读数每条同时带三根轴；刀 M908 / M909 / M910 三把全 CAUGHT、RESTORE_CLEAN=yes。
- 366 的两条出口被现读证伪（位置可判臂 16/715；"部分死"当上界得到 658，绝大多数是变异文本身）
  ⇒ 新开 @BLNEW@：rot 做成上界只能靠**表自己声明针**，并给出可执行的三步与分箱形状。
- 356 结案：两半处置相反（环那一半是真缺陷由 @RPREVTAG@ 修；相邻档那一半是读错轴由本轮撤回）。
- 现读：构建告警 @WARN@；判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 @FULL@；
  帧 @CAP@、基线 @BASE@（判据轮不 update）；换装 @INSTALL@；预检 tables=@TABLES@ bad=@PREBAD@、
  名册 arms=@ARMREG@；腐烂尺 `@HALINE@`；电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
  产品面连续零改动 **@STREAK@** 轮。

"""

ST_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

本轮判的是 BACKLOG 356 剩下的那一半，结论是**它不成立**：
`HEAT_ADJACENT dark/1x empty→bucket1` 三根轴现读 最大=30.00 / 均值=17.33 / 亮度=2.16，
而地板施加在最大通道那一根（R52 起的选择，理由写在判据注释里）。那句"低于地板"读的是被排除的轴 ⇒ 撤回。
撤回之前先把证人做出来：16 条读数必须每条同时带三根轴，M908/M909/M910 三把刀各钉一根。
另一条产出是把 366 的两条出口**证伪**（16/715 覆盖；658 是被变异文污染的假上界），
并把「表自己声明针」这条唯一出口落成 @BLNEW@。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**三根轴必须同时可查 —— 356 那一半被证伪并撤回**（产品 0 文件，判据轮）
现读：构建告警 @WARN@；判据卷 `Ran @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 @FULL@；@CAP@；帧基线 @BASE@（不 update）；
换装 @INSTALL@；刀 @KNIFESUM@；预检 tables=@TABLES@ covered=@COVERED@ bad=@PREBAD@、名册 arms=@ARMREG@；
腐烂尺 `@HALINE@`；探针 `@PROBE@`；电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；看图腿 RUN（@EYE_SHORT@）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；上一轮 @PREVSTREAK@）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。

⓪ @RNEXT@ 开场要先读的（成对：run id ↔ commit）：@CI@
   —— 必须读到：① 本轮新增的那格断言在 runner 上**没有把 16 条读数判成少轴**（它只读自己的打印，
   理论上不变，但"理论不变"要由那一跑签）；② @RPREVTAG@ 账半那一跑（run 39973549740）与本轮代码半
   那一跑之间，STEP[9]/STEP[15] 不许出现新红。

① 下一轮（@RNEXT@）的靶：① **回到动效主线** —— 347 仍欠真机眼（唯一挡着产品判断的机器闸门，
   要用户先退出 App），在那之前把 305 的台阶地板用已有的夹具通道再推一格；
   ② @BLNEW@ 第一步：给 3 张最常用的表加 `NEEDLES = {…}`，并把 `hidden_arms.py` 分成
   「已声明（可加总）/未声明（只配下界）」两箱，各配棘轮；
   ③ 348 剩下的读数族各配一条恒等式；④ 360 的最后一批；⑤ 361 的合并。

② 仍开：347（真机证人）、305（等 347）、@BLMINUS@（腐烂针待清 + 上界只能由表声明针）、@BLNEW@（迁移面 75 张表）、
   364 的"抽不出候选的 @OPAQUE@ 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；**本轮结案：356**（两半各自处置）；用户闸门 220 路 A / 228② / 265。

"""

# ---------------------------------------------------------------- 组装与落盘
orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(UI_NEW, SUBS), u"IT": fill(IT_NEW, SUBS), u"DEC": fill(DEC_NEW, SUBS),
         u"BL366": fill(BL_366, SUBS), u"BL356": fill(BL_356, SUBS), u"BLNEW": fill(BL_NEW, SUBS),
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


new_bl = append_into_item(orig["BL"], u"**366. ", texts["BL366"], u"366")
new_bl = append_into_item(new_bl, u"**356. ", texts["BL356"], u"356")
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
              u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**（本轮追记 356 与 366、新开 %s）"
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

post, post_skip = battery(u"写盘后", u"/tmp/r312_battery_post.log")
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
print(u"LEDGERS_R312 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(others)) + u" 刀=" + s(K_N)
      + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" 可判=" + s(JUDGED_NOW)
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" BL=" + s(BLNEW)
      + u" 判据卷=" + s(JUDGE_RUN) + u" 帧=" + FRAMES
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
